import secrets
from django.db import models


def seat_token():
    return secrets.token_urlsafe(24)


class Venue(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=160)
    code = models.SlugField(max_length=32, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Screen(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="screens")
    name = models.CharField(max_length=100)
    screen_number = models.PositiveSmallIntegerField()
    total_rows = models.PositiveSmallIntegerField(default=10)
    total_columns = models.PositiveSmallIntegerField(default=12)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["venue", "screen_number"], name="unique_venue_screen")
        ]
        ordering = ["screen_number"]

    def __str__(self):
        return f"{self.venue.name} - {self.name}"


class Seat(models.Model):
    class SeatType(models.TextChoices):
        STANDARD = "STANDARD", "Standard"
        PREMIUM = "PREMIUM", "Premium"
        RECLINER = "RECLINER", "Recliner"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DISABLED = "DISABLED", "Disabled"

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="seats")
    row_label = models.CharField(max_length=4)
    seat_number = models.PositiveSmallIntegerField()
    seat_code = models.CharField(max_length=12)
    seat_type = models.CharField(max_length=16, choices=SeatType.choices, default=SeatType.STANDARD)
    qr_token = models.CharField(max_length=64, unique=True, default=seat_token, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["screen", "seat_code"], name="unique_screen_seat")
        ]
        ordering = ["row_label", "seat_number"]

    def regenerate_token(self):
        self.qr_token = seat_token()
        self.save(update_fields=["qr_token"])

    def __str__(self):
        return f"{self.screen.name} {self.seat_code}"

