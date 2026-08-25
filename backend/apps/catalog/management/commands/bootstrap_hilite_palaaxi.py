from datetime import timedelta
from decimal import Decimal
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, FoodProduct, Offer
from apps.venues.models import Screen, Seat, Venue

VENUE_CODE = "HILITE-PALAAXI"
DEFAULT_BOOTSTRAP_PASSWORD = "HilitePalaaxi@123"
SHOWCASE_SCREEN_NUMBER = 1
SHOWCASE_SEAT_CODE = "F12"
SHOWCASE_SEAT_TOKEN = "hilite-palaaxi-screen-1-f12"

SCREEN_SPECS = [
    {"screen_number": 1, "name": "Audi 1", "rows": 10, "columns": 16},
    {"screen_number": 2, "name": "Audi 2", "rows": 12, "columns": 18},
    {"screen_number": 3, "name": "Audi 3", "rows": 9, "columns": 14},
]

CATEGORY_DATA = [
    {
        "name": "Popcorn",
        "description": "Freshly popped favourites for the big screen.",
        "image": "https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=900&q=85",
        "products": [
            ("Classic Popcorn", "Freshly popped corn finished with sea salt.", "Classic salted popcorn for every show.", 190, 170, 5, True, 8),
            ("Caramel Popcorn", "Crunchy popcorn coated with warm caramel glaze.", "Buttery caramel popcorn.", 260, 230, 5, True, 8),
            ("Cheese Popcorn", "Golden popcorn tossed with sharp cheddar seasoning.", "Cheesy popcorn with bold flavour.", 270, 240, 5, False, 8),
        ],
    },
    {
        "name": "Drinks",
        "description": "Cold refreshments ready for delivery to your seat.",
        "image": "https://images.unsplash.com/photo-1629203849820-fdd70d49c38e?auto=format&fit=crop&w=900&q=85",
        "products": [
            ("Coke", "Chilled Coca-Cola served cold.", "Classic Coke, cinema cold.", 130, 120, 5, False, 4),
            ("Sprite", "Lemon-lime soda served over ice.", "Fresh lemon-lime fizz.", 130, 120, 5, False, 4),
            ("Pepsi", "Icy cola with the familiar Pepsi taste.", "Pepsi served cold.", 130, 120, 5, False, 4),
            ("Cold Coffee", "Chilled coffee with milk and a smooth finish.", "Cold coffee for late shows.", 190, 180, 5, False, 5),
        ],
    },
    {
        "name": "Snacks",
        "description": "Hot snacks for quick theatre delivery.",
        "image": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=85",
        "products": [
            ("French Fries", "Golden fries with mild seasoning.", "Crispy fries with dip.", 220, 190, 5, False, 10),
            ("Chicken Popcorn", "Crispy chicken bites with spicy seasoning.", "Crispy chicken bites.", 290, 260, 5, True, 12),
            ("Veg Pizza Slice", "Cheese pizza slice with peppers and olives.", "Hot pizza slice.", 260, 230, 5, False, 12),
        ],
    },
    {
        "name": "Combos",
        "description": "Bundled favourites for group and family movie nights.",
        "image": "https://images.unsplash.com/photo-1598387993281-cecf8b71a8f8?auto=format&fit=crop&w=900&q=85",
        "products": [
            ("Movie Combo", "Caramel popcorn with two regular drinks.", "Popcorn and two drinks.", 520, 469, 5, True, 10),
            ("Large Combo", "Cheese popcorn, fries and two large drinks.", "Large combo for sharing.", 760, 699, 5, True, 12),
        ],
    },
    {
        "name": "Desserts",
        "description": "Sweet treats for interval cravings.",
        "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85",
        "products": [
            ("Chocolate Brownie", "Warm chocolate brownie with rich cocoa notes.", "Soft brownie dessert.", 180, 160, 5, False, 6),
        ],
    },
]

USER_SPECS = [
    {
        "username": "hilite_admin",
        "email": "admin@hilitepalaaxi.demo",
        "first_name": "Hilite",
        "last_name": "Admin",
        "role": User.Role.SUPER_ADMIN,
        "superuser": True,
    },
    {
        "username": "hilite_manager",
        "email": "manager@hilitepalaaxi.demo",
        "first_name": "Palaaxi",
        "last_name": "Manager",
        "role": User.Role.VENUE_MANAGER,
        "superuser": False,
    },
    {
        "username": "hilite_kitchen",
        "email": "kitchen@hilitepalaaxi.demo",
        "first_name": "Kitchen",
        "last_name": "Lead",
        "role": User.Role.KITCHEN_STAFF,
        "superuser": False,
    },
    {
        "username": "hilite_delivery",
        "email": "delivery@hilitepalaaxi.demo",
        "first_name": "Delivery",
        "last_name": "Runner",
        "role": User.Role.DELIVERY_STAFF,
        "superuser": False,
    },
]


class Command(BaseCommand):
    help = "Create or update the Hilite Palaaxi demo dataset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            dest="password",
            help="Password to apply to the bootstrap staff accounts. Defaults to SEATBITE_BOOTSTRAP_PASSWORD or a local demo password.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options.get("password") or os.getenv("SEATBITE_BOOTSTRAP_PASSWORD") or DEFAULT_BOOTSTRAP_PASSWORD
        venue = self._bootstrap_venue()
        showcase_seat = self._bootstrap_screens_and_seats(venue)
        self._bootstrap_catalog(venue)
        self._bootstrap_offer(venue)
        self._bootstrap_users(venue, password)

        product_count = FoodProduct.objects.filter(category__venue=venue).count()
        screen_count = Screen.objects.filter(venue=venue, is_deleted=False).count()
        seat_count = Seat.objects.filter(screen__venue=venue, screen__is_deleted=False).count()
        category_count = Category.objects.filter(venue=venue).count()

        self.stdout.write(self.style.SUCCESS("Hilite Palaaxi bootstrap is ready."))
        self.stdout.write(
            f"Venue: {venue.name} ({venue.code}) · screens: {screen_count} · seats: {seat_count} · categories: {category_count} · products: {product_count}"
        )
        self.stdout.write(
            f"Showcase customer URL: {settings.SEATBITE_CUSTOMER_URL}/{showcase_seat.qr_token}"
        )
        self.stdout.write(
            "Staff users: hilite_admin, hilite_manager, hilite_kitchen, hilite_delivery"
        )

    def _bootstrap_venue(self):
        venue, _ = Venue.objects.update_or_create(
            code=VENUE_CODE,
            defaults={
                "name": "Hilite Palaaxi",
                "address": "Hilite Mall, Kozhikode Bypass",
                "city": "Kozhikode",
                "timezone": "Asia/Kolkata",
                "status": Venue.Status.ACTIVE,
            },
        )
        return venue

    def _bootstrap_screens_and_seats(self, venue):
        showcase_seat = None
        for spec in SCREEN_SPECS:
            screen = self._ensure_screen(venue, spec)
            for row_index in range(spec["rows"]):
                row_label = chr(65 + row_index)
                for seat_number in range(1, spec["columns"] + 1):
                    seat_code = f"{row_label}{seat_number:02d}"
                    defaults = {
                        "row_label": row_label,
                        "seat_number": seat_number,
                        "seat_type": self._seat_type(row_index, spec["rows"]),
                        "status": Seat.Status.ACTIVE,
                    }
                    if spec["screen_number"] == SHOWCASE_SCREEN_NUMBER and seat_code == SHOWCASE_SEAT_CODE:
                        defaults["qr_token"] = SHOWCASE_SEAT_TOKEN
                    seat, created = Seat.objects.get_or_create(
                        screen=screen,
                        seat_code=seat_code,
                        defaults=defaults,
                    )
                    if not created:
                        update_fields = []
                        for field, value in defaults.items():
                            if field == "qr_token":
                                continue
                            if getattr(seat, field) != value:
                                setattr(seat, field, value)
                                update_fields.append(field)
                        if update_fields:
                            seat.save(update_fields=update_fields)
                    if spec["screen_number"] == SHOWCASE_SCREEN_NUMBER and seat_code == SHOWCASE_SEAT_CODE:
                        showcase_seat = seat
        return showcase_seat

    def _ensure_screen(self, venue, spec):
        screen = Screen.objects.filter(
            venue=venue,
            screen_number=spec["screen_number"],
            is_deleted=False,
        ).first()
        if not screen:
            screen = Screen.objects.filter(
                venue=venue,
                screen_number=spec["screen_number"],
            ).order_by("is_deleted").first()
        if screen:
            changed = []
            desired = {
                "name": spec["name"],
                "total_rows": spec["rows"],
                "total_columns": spec["columns"],
                "status": Screen.Status.ACTIVE,
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None,
            }
            for field, value in desired.items():
                if getattr(screen, field) != value:
                    setattr(screen, field, value)
                    changed.append(field)
            if changed:
                screen.save(update_fields=changed)
            return screen
        return Screen.objects.create(
            venue=venue,
            name=spec["name"],
            screen_number=spec["screen_number"],
            total_rows=spec["rows"],
            total_columns=spec["columns"],
            status=Screen.Status.ACTIVE,
        )

    def _seat_type(self, row_index, total_rows):
        if row_index == total_rows - 1:
            return Seat.SeatType.RECLINER
        if row_index >= total_rows - 3:
            return Seat.SeatType.PREMIUM
        return Seat.SeatType.STANDARD

    def _bootstrap_catalog(self, venue):
        for category_index, category_data in enumerate(CATEGORY_DATA):
            category, _ = Category.objects.update_or_create(
                venue=venue,
                name=category_data["name"],
                defaults={
                    "description": category_data["description"],
                    "image": category_data["image"],
                    "display_order": category_index,
                    "is_active": True,
                },
            )
            for product_index, product_data in enumerate(category_data["products"]):
                (
                    name,
                    description,
                    short_description,
                    base_price,
                    selling_price,
                    tax_percentage,
                    is_featured,
                    preparation_time,
                ) = product_data
                FoodProduct.objects.update_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "description": description,
                        "short_description": short_description,
                        "image": category_data["image"],
                        "base_price": Decimal(str(base_price)),
                        "discount_price": Decimal(str(selling_price)),
                        "tax_percentage": Decimal(str(tax_percentage)),
                        "is_available": True,
                        "is_featured": is_featured,
                        "preparation_time": preparation_time,
                        "display_order": product_index,
                    },
                )

    def _bootstrap_offer(self, venue):
        now = timezone.now()
        Offer.objects.update_or_create(
            venue=venue,
            name="Palaaxi Movie Night Offer",
            defaults={
                "description": "10% off on orders above ₹499",
                "offer_type": Offer.OfferType.PERCENTAGE,
                "discount_value": Decimal("10"),
                "minimum_order_amount": Decimal("499"),
                "start_at": now - timedelta(days=30),
                "end_at": now + timedelta(days=365),
                "is_active": True,
            },
        )

    def _bootstrap_users(self, venue, password):
        for user_spec in USER_SPECS:
            user, _ = User.objects.update_or_create(
                username=user_spec["username"],
                defaults={
                    "email": user_spec["email"],
                    "first_name": user_spec["first_name"],
                    "last_name": user_spec["last_name"],
                    "role": user_spec["role"],
                    "venue": None if user_spec["superuser"] else venue,
                    "is_staff": user_spec["superuser"],
                    "is_superuser": user_spec["superuser"],
                    "is_active": True,
                },
            )
            user.set_password(password)
            user.save(update_fields=["password"])
