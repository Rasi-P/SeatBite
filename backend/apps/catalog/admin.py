from django.contrib import admin
from .models import Category, FoodProduct, Offer

admin.site.register([Category, FoodProduct, Offer])

