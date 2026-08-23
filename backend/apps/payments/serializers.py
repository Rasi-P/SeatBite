from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["public_id", "provider", "transaction_id", "amount", "status", "paid_at"]

