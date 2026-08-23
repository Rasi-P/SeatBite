from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, FoodProduct
from apps.venues.models import Screen, Seat, Venue
from .models import Cart, CustomerSession, Order
from .services import checkout, set_cart_item, transition_order


class OrderFlowTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Test Cinema", code="TEST", city="Calicut")
        self.screen = Screen.objects.create(venue=self.venue, name="Screen 1", screen_number=1)
        self.seat = Seat.objects.create(screen=self.screen, row_label="F", seat_number=12, seat_code="F12")
        self.session = CustomerSession.objects.create(
            seat=self.seat, expires_at=timezone.now() + timedelta(hours=1)
        )
        self.cart = Cart.objects.create(session=self.session)
        category = Category.objects.create(venue=self.venue, name="Popcorn")
        self.product = FoodProduct.objects.create(
            category=category, name="Caramel Popcorn", description="Fresh", short_description="Fresh",
            image="https://example.com/popcorn.jpg", base_price=Decimal("280"),
            discount_price=Decimal("220"), tax_percentage=Decimal("5"),
        )
        self.kitchen = User.objects.create_user(
            username="kitchen", email="kitchen@test.dev", role=User.Role.KITCHEN_STAFF, venue=self.venue
        )

    def test_prices_are_snapshotted_at_checkout(self):
        set_cart_item(self.cart, self.product, 2)
        order = checkout(self.cart)
        self.product.discount_price = Decimal("250")
        self.product.save()
        item = order.items.get()
        self.assertEqual(item.unit_price, Decimal("220"))
        self.assertEqual(item.quantity, 2)

    def test_order_transition_state_machine_and_roles(self):
        set_cart_item(self.cart, self.product, 1)
        order = checkout(self.cart)
        transition_order(order, Order.Status.CONFIRMED)
        transition_order(order, Order.Status.PREPARING, self.kitchen)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
        with self.assertRaises(ValueError):
            transition_order(order, Order.Status.DELIVERED, self.kitchen)

    def test_complete_qr_payment_kitchen_delivery_api_flow(self):
        client = APIClient()
        response = client.post("/api/v1/sessions/resolve/", {"qr_token": self.seat.qr_token}, format="json")
        self.assertEqual(response.status_code, 201)
        token = response.data["session_token"]
        client.credentials(HTTP_X_SESSION_TOKEN=token)

        response = client.post(
            "/api/v1/cart/items/", {"product_id": self.product.pk, "quantity": 2}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["item_count"], 2)
        self.assertEqual(Decimal(response.data["total"]), Decimal("462.00"))

        response = client.post("/api/v1/cart/checkout/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        order_id = response.data["id"]
        public_id = response.data["public_id"]
        response = client.post(
            "/api/v1/payments/simulate/",
            {"order_id": public_id, "payment_method": "UPI"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount"], "462.00")

        client.force_authenticate(self.kitchen)
        response = client.post(
            f"/api/v1/orders/{order_id}/transition/", {"status": "PREPARING"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = client.post(
            f"/api/v1/orders/{order_id}/transition/", {"status": "READY"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

        delivery = User.objects.create_user(
            username="delivery", email="delivery@test.dev", role=User.Role.DELIVERY_STAFF, venue=self.venue
        )
        client.force_authenticate(delivery)
        response = client.post(
            f"/api/v1/orders/{order_id}/transition/", {"status": "OUT_FOR_DELIVERY"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = client.post(
            f"/api/v1/orders/{order_id}/transition/", {"status": "DELIVERED"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

        client.force_authenticate(user=None)
        client.credentials(HTTP_X_SESSION_TOKEN=token)
        response = client.get(f"/api/v1/orders/{public_id}/track/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "DELIVERED")
        self.assertEqual(response.data["seat_code"], "F12")

    def test_admin_can_download_individual_and_print_sheet_qr(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@test.dev", role=User.Role.SUPER_ADMIN, password="test"
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get(f"/api/v1/qr/{self.seat.pk}/image/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))

        response = client.get("/api/v1/qr/print-sheet/", {"screen": self.screen.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
