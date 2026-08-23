from django.contrib import admin
from .models import Cart, CartItem, CustomerSession, Order, OrderItem, OrderStatusEvent

admin.site.register([CustomerSession, Cart, CartItem, Order, OrderItem, OrderStatusEvent])
