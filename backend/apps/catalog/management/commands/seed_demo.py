from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, FoodProduct, Offer
from apps.orders.models import CustomerSession, Order, OrderItem, OrderStatusEvent
from apps.payments.models import Payment
from apps.venues.models import Screen, Seat, Venue


PRODUCTS = {
    "Popcorn": [
        ("Classic Salted Popcorn", "Hot, airy kernels finished with sea salt.", 180, 150, "photo-1585647347483-22b66260dfff"),
        ("Caramel Popcorn", "Crunchy popcorn glazed in buttery golden caramel.", 280, 220, "photo-1578849278619-e73505e9610f"),
        ("Cheese Popcorn", "Bold cheddar seasoning on freshly popped corn.", 250, 210, "photo-1586190848861-99aa4a171e90"),
    ],
    "Beverages": [
        ("Regular Coke", "Ice-cold classic cola, 350 ml.", 120, 100, "photo-1629203849820-fdd70d49c38e"),
        ("Large Coke", "Ice-cold classic cola, 500 ml.", 160, 140, "photo-1581006852262-e4307cf6283a"),
        ("Sprite", "Crisp lemon-lime refreshment, 350 ml.", 120, 100, "photo-1625772299848-391b6a87d7b3"),
        ("Fanta", "Bright orange fizz, 350 ml.", 120, 100, "photo-1624517452488-04869289c4ca"),
    ],
    "Combos": [
        ("Classic Movie Combo", "Large salted popcorn with two chilled Cokes.", 480, 399, "photo-1598387993281-cecf8b71a8f8"),
        ("Couple Combo", "Caramel popcorn, nachos and two drinks.", 690, 579, "photo-1572802419224-296b0aeee0d9"),
        ("Family Combo", "Two large popcorns, four drinks and fries.", 1050, 849, "photo-1521305916504-4a1121188589"),
    ],
    "Snacks": [
        ("Loaded Nachos", "Corn chips with warm cheese and jalapenos.", 280, 240, "photo-1513456852971-30c0b8199d4d"),
        ("Crispy French Fries", "Golden fries with smoked paprika salt.", 220, 190, "photo-1573080496219-bb080dd4f877"),
        ("Chicken Nuggets", "Six crisp chicken bites with chilli dip.", 290, 250, "photo-1562967914-608f82629710"),
    ],
    "Desserts": [
        ("Chocolate Brownie", "Fudgy chocolate brownie with cocoa crumble.", 190, 160, "photo-1606313564200-e75d5e30476c"),
        ("Vanilla Ice Cream", "Creamy vanilla cup with caramel drizzle.", 160, 140, "photo-1560008581-09826d1de69e"),
    ],
}


class Command(BaseCommand):
    help = "Create the complete SeatBite demonstration dataset"

    @transaction.atomic
    def handle(self, *args, **options):
        venue, _ = Venue.objects.update_or_create(
            code="CMX-CAL", defaults={
                "name": "CineMax Calicut", "address": "Mavoor Road, Kozhikode",
                "city": "Calicut", "status": Venue.Status.ACTIVE,
            },
        )
        screen_specs = [(1, 10, 12, 120), (2, 9, 12, 100), (3, 10, 15, 150)]
        screens = []
        for number, rows, columns, count in screen_specs:
            screen = Screen.objects.filter(
                venue=venue, screen_number=number, is_deleted=False
            ).first()
            if not screen:
                screen = Screen.objects.filter(
                    venue=venue, screen_number=number
                ).order_by("is_deleted").first()
            if not screen:
                screen = Screen.objects.create(
                    venue=venue,
                    screen_number=number,
                    name=f"Screen {number}",
                    total_rows=rows,
                    total_columns=columns,
                )
            screens.append(screen)
            created = 0
            for row_index in range(rows):
                for seat_number in range(1, columns + 1):
                    if created >= count:
                        break
                    row = chr(65 + row_index)
                    seat, _ = Seat.objects.get_or_create(
                        screen=screen, seat_code=f"{row}{seat_number:02d}",
                        defaults={"row_label": row, "seat_number": seat_number},
                    )
                    if number == 2 and row == "F" and seat_number == 12:
                        seat.qr_token = "uJ7cV2nQ9mL4xR8pK6sT3wZ5aB1dF0hG"
                        seat.save(update_fields=["qr_token"])
                    created += 1

        categories = {}
        for index, (name, products) in enumerate(PRODUCTS.items()):
            category, _ = Category.objects.update_or_create(
                venue=venue, name=name,
                defaults={"description": f"Cinema-ready {name.lower()}", "display_order": index},
            )
            categories[name] = category
            for product_index, (name, description, base, sale, photo) in enumerate(products):
                FoodProduct.objects.update_or_create(
                    category=category, name=name,
                    defaults={
                        "description": description, "short_description": description,
                        "image": f"https://images.unsplash.com/{photo}?auto=format&fit=crop&w=900&q=85",
                        "base_price": base, "discount_price": sale, "tax_percentage": 5,
                        "is_featured": product_index == 0, "preparation_time": 10 + product_index * 2,
                        "display_order": product_index,
                    },
                )
        Offer.objects.update_or_create(
            venue=venue, name="Movie Night 10% Off",
            defaults={
                "description": "10% off orders above Rs. 399", "offer_type": Offer.OfferType.PERCENTAGE,
                "discount_value": 10, "minimum_order_amount": 399,
                "start_at": timezone.now() - timedelta(days=30),
                "end_at": timezone.now() + timedelta(days=365), "is_active": True,
            },
        )

        users = [
            ("admin", "admin@seatbite.demo", "Asha", "Menon", User.Role.SUPER_ADMIN, True),
            ("manager", "manager@seatbite.demo", "Nikhil", "Das", User.Role.VENUE_MANAGER, False),
            ("kitchen", "kitchen@seatbite.demo", "Riya", "Thomas", User.Role.KITCHEN_STAFF, False),
            ("delivery", "delivery@seatbite.demo", "Arun", "Kumar", User.Role.DELIVERY_STAFF, False),
        ]
        for username, email, first, last, role, superuser in users:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "email": email, "first_name": first, "last_name": last, "role": role,
                    "venue": None if superuser else venue, "is_staff": superuser, "is_superuser": superuser,
                    "is_active": True,
                },
            )
            user.set_password("SeatBite@123")
            user.save(update_fields=["password"])

        self._seed_orders(venue, screens[1])
        self.stdout.write(self.style.SUCCESS("SeatBite demo data is ready."))
        self.stdout.write("Customer demo: /customer/qr/uJ7cV2nQ9mL4xR8pK6sT3wZ5aB1dF0hG")
        if settings.SEATBITE_SHOW_SEED_CREDENTIALS:
            self.stdout.write("All staff passwords: SeatBite@123")

    def _seed_orders(self, venue, screen):
        products = list(FoodProduct.objects.filter(category__venue=venue)[:8])
        seats = list(screen.seats.exclude(seat_code="F12")[:10])
        statuses = [
            Order.Status.CONFIRMED, Order.Status.PREPARING, Order.Status.READY,
            Order.Status.DELIVERED, Order.Status.DELIVERED, Order.Status.DELIVERED,
        ]
        now = timezone.now()
        for index, status_value in enumerate(statuses):
            number = f"SB-{timezone.localdate():%Y%m%d}-{9001 + index}"
            transaction_id = f"SEED-{9001 + index}"
            if Order.objects.filter(order_number=number).exists() or Payment.objects.filter(transaction_id=transaction_id).exists():
                continue
            seat = seats[index]
            session = CustomerSession.objects.create(
                seat=seat, expires_at=now + timedelta(hours=6), status=CustomerSession.Status.ACTIVE
            )
            product = products[index % len(products)]
            unit = product.selling_price
            tax = (unit * Decimal("0.05")).quantize(Decimal("0.01"))
            order = Order.objects.create(
                order_number=number, venue=venue, screen=screen, seat=seat, customer_session=session,
                status=status_value, subtotal=product.base_price, discount=product.base_price - unit,
                tax=tax, delivery_fee=0, total=unit + tax, payment_status=Order.PaymentStatus.SUCCESS,
                confirmed_at=now, preparing_at=now if status_value != Order.Status.CONFIRMED else None,
                ready_at=now if status_value in [Order.Status.READY, Order.Status.DELIVERED] else None,
                delivered_at=now if status_value == Order.Status.DELIVERED else None,
            )
            OrderItem.objects.create(
                order=order, product=product, product_name=product.name, product_image=product.image,
                quantity=1, unit_price=unit, discount=product.base_price - unit, tax=tax, total=unit + tax,
            )
            OrderStatusEvent.objects.create(order=order, to_status=status_value, note="Seeded demo order")
            Payment.objects.create(
                order=order, transaction_id=transaction_id, amount=order.total,
                status=Payment.Status.SUCCESS, payment_method=Payment.Method.UPI, paid_at=now,
            )
