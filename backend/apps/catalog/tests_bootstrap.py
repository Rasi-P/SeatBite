from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, FoodProduct, Offer
from apps.venues.models import Screen, Seat, Venue


@override_settings(SEATBITE_CUSTOMER_URL="https://seat-bite.vercel.app/customer/qr")
class HiliteBootstrapCommandTests(TestCase):
    def test_bootstrap_creates_expected_records_and_customer_flow_works(self):
        output = StringIO()

        call_command("bootstrap_hilite_palaaxi", stdout=output)

        venue = Venue.objects.get(code="HILITE-PALAAXI")
        self.assertEqual(venue.name, "Hilite Palaaxi")
        self.assertEqual(Screen.objects.filter(venue=venue, is_deleted=False).count(), 3)
        self.assertEqual(Seat.objects.filter(screen__venue=venue, screen__is_deleted=False).count(), 502)
        self.assertEqual(Category.objects.filter(venue=venue).count(), 5)
        self.assertEqual(FoodProduct.objects.filter(category__venue=venue).count(), 13)
        self.assertEqual(Offer.objects.filter(venue=venue, is_active=True).count(), 1)
        self.assertEqual(
            User.objects.filter(
                username__in=["hilite_admin", "hilite_manager", "hilite_kitchen", "hilite_delivery"]
            ).count(),
            4,
        )

        showcase_seat = Seat.objects.get(
            screen__venue=venue,
            screen__screen_number=1,
            seat_code="F12",
        )
        self.assertEqual(showcase_seat.qr_token, "hilite-palaaxi-screen-1-f12")

        output_text = output.getvalue()
        self.assertIn(
            "https://seat-bite.vercel.app/customer/qr/hilite-palaaxi-screen-1-f12",
            output_text,
        )
        self.assertNotIn("HilitePalaaxi@123", output_text)

        client = APIClient()
        response = client.post(
            "/api/v1/sessions/resolve/",
            {"qr_token": showcase_seat.qr_token, "device_identifier": "bootstrap-test"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        session_token = response.data["session_token"]
        client.credentials(HTTP_X_SESSION_TOKEN=session_token)

        product = FoodProduct.objects.get(
            category__venue=venue,
            name="Caramel Popcorn",
        )
        response = client.post(
            "/api/v1/cart/items/",
            {"product_id": product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["item_count"], 2)

        response = client.post("/api/v1/cart/checkout/", {}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        public_id = response.data["public_id"]

        response = client.post(
            "/api/v1/payments/simulate/",
            {"order_id": public_id, "payment_method": "UPI"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)

        response = client.get(f"/api/v1/orders/{public_id}/track/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "CONFIRMED")
        self.assertEqual(response.data["seat_code"], "F12")

    def test_bootstrap_is_idempotent_and_preserves_qr_tokens(self):
        first_output = StringIO()
        second_output = StringIO()

        call_command("bootstrap_hilite_palaaxi", stdout=first_output)
        showcase_seat = Seat.objects.get(screen__screen_number=1, screen__venue__code="HILITE-PALAAXI", seat_code="F12")
        first_token = showcase_seat.qr_token

        first_counts = {
            "venues": Venue.objects.filter(code="HILITE-PALAAXI").count(),
            "screens": Screen.objects.filter(venue__code="HILITE-PALAAXI", is_deleted=False).count(),
            "seats": Seat.objects.filter(screen__venue__code="HILITE-PALAAXI", screen__is_deleted=False).count(),
            "categories": Category.objects.filter(venue__code="HILITE-PALAAXI").count(),
            "products": FoodProduct.objects.filter(category__venue__code="HILITE-PALAAXI").count(),
            "offers": Offer.objects.filter(venue__code="HILITE-PALAAXI").count(),
            "users": User.objects.filter(
                username__in=["hilite_admin", "hilite_manager", "hilite_kitchen", "hilite_delivery"]
            ).count(),
        }

        call_command("bootstrap_hilite_palaaxi", stdout=second_output)
        showcase_seat.refresh_from_db()

        second_counts = {
            "venues": Venue.objects.filter(code="HILITE-PALAAXI").count(),
            "screens": Screen.objects.filter(venue__code="HILITE-PALAAXI", is_deleted=False).count(),
            "seats": Seat.objects.filter(screen__venue__code="HILITE-PALAAXI", screen__is_deleted=False).count(),
            "categories": Category.objects.filter(venue__code="HILITE-PALAAXI").count(),
            "products": FoodProduct.objects.filter(category__venue__code="HILITE-PALAAXI").count(),
            "offers": Offer.objects.filter(venue__code="HILITE-PALAAXI").count(),
            "users": User.objects.filter(
                username__in=["hilite_admin", "hilite_manager", "hilite_kitchen", "hilite_delivery"]
            ).count(),
        }

        self.assertEqual(first_counts, second_counts)
        self.assertEqual(showcase_seat.qr_token, first_token)
        self.assertEqual(
            Seat.objects.filter(screen__venue__code="HILITE-PALAAXI").count(),
            Seat.objects.filter(screen__venue__code="HILITE-PALAAXI").values("qr_token").distinct().count(),
        )
