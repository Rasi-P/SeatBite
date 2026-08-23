from rest_framework import serializers
from apps.orders.serializers import OrderSerializer
from .models import DeliveryAssignment


class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    order_detail = OrderSerializer(source="order", read_only=True)
    staff_name = serializers.CharField(source="staff.get_full_name", read_only=True)

    class Meta:
        model = DeliveryAssignment
        fields = "__all__"
        read_only_fields = ["assigned_at", "picked_up_at", "completed_at"]

