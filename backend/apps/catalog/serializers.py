from rest_framework import serializers
from .models import Category, FoodProduct, Offer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    venue = serializers.IntegerField(source="category.venue_id", read_only=True)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings = serializers.SerializerMethodField()

    class Meta:
        model = FoodProduct
        fields = "__all__"

    def get_savings(self, obj):
        return str(max(obj.base_price - obj.selling_price, 0))


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"

