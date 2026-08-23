from django.conf import settings
from django.db import models


class DeliveryAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        PICKED_UP = "PICKED_UP", "Picked up"
        COMPLETED = "COMPLETED", "Completed"

    order = models.OneToOneField("orders.Order", on_delete=models.PROTECT, related_name="delivery_assignment")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="deliveries")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ASSIGNED)
    assigned_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-assigned_at"]

