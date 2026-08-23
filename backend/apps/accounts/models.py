from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super admin"
        VENUE_MANAGER = "VENUE_MANAGER", "Venue manager"
        KITCHEN_STAFF = "KITCHEN_STAFF", "Kitchen staff"
        DELIVERY_STAFF = "DELIVERY_STAFF", "Delivery staff"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=24, choices=Role.choices, default=Role.KITCHEN_STAFF)
    venue = models.ForeignKey(
        "venues.Venue", null=True, blank=True, on_delete=models.PROTECT, related_name="staff"
    )

    def __str__(self):
        return self.get_full_name() or self.username


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

