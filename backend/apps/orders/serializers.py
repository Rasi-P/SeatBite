from rest_framework import serializers
from apps.catalog.serializers import ProductSerializer
from apps.venues.serializers import SeatPublicSerializer
from .models import Cart, CartItem, CustomerSession, Order, OrderItem, OrderStatusEvent


class CustomerSessionSerializer(serializers.ModelSerializer):
    seat = SeatPublicSerializer(read_only=True)

    class Meta:
        model = CustomerSession
        fields = ["session_token", "seat", "started_at", "expires_at", "status"]


class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_detail", "quantity", "unit_price", "discount", "tax", "total"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "status", "items", "item_count", "subtotal", "discount", "tax", "delivery_fee", "total", "updated_at"]

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "product_image", "quantity", "unit_price", "discount", "tax", "total"]


class OrderStatusEventSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True)

    class Meta:
        model = OrderStatusEvent
        fields = ["from_status", "to_status", "changed_by_name", "note", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_events = OrderStatusEventSerializer(many=True, read_only=True)
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    screen_name = serializers.CharField(source="screen.name", read_only=True)
    seat_code = serializers.CharField(source="seat.seat_code", read_only=True)
    row_label = serializers.CharField(source="seat.row_label", read_only=True)
    seat_number = serializers.IntegerField(source="seat.seat_number", read_only=True)

    class Meta:
        model = Order
        exclude = ["customer_session"]

