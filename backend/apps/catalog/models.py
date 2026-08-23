from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    venue = models.ForeignKey("venues.Venue", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class FoodProduct(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    description = models.TextField()
    short_description = models.CharField(max_length=180)
    image = models.URLField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    preparation_time = models.PositiveSmallIntegerField(default=10, help_text="Minutes")
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    @property
    def selling_price(self):
        if self.discount_price is not None and self.discount_price < self.base_price:
            return self.discount_price
        return self.base_price

    def __str__(self):
        return self.name


class Offer(models.Model):
    class OfferType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED = "FIXED", "Fixed"
        COMBO = "COMBO", "Combo"

    venue = models.ForeignKey("venues.Venue", on_delete=models.CASCADE, related_name="offers")
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    offer_type = models.CharField(max_length=16, choices=OfferType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_at"]

    def __str__(self):
        return self.name

