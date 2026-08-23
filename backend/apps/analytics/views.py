from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, ExtractHour
from django.utils import timezone
from rest_framework import decorators, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.orders.models import Order, OrderItem


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _orders(self, request):
        queryset = Order.objects.all()
        if request.user.role != User.Role.SUPER_ADMIN:
            queryset = queryset.filter(venue=request.user.venue)
        venue = request.query_params.get("venue")
        if venue and request.user.role == User.Role.SUPER_ADMIN:
            queryset = queryset.filter(venue=venue)
        return queryset

    @decorators.action(detail=False, methods=["get"])
    def overview(self, request):
        today = timezone.localdate()
        orders = self._orders(request).filter(created_at__date=today).exclude(status=Order.Status.CANCELLED)
        revenue = orders.filter(payment_status=Order.PaymentStatus.SUCCESS).aggregate(
            value=Coalesce(Sum("total"), 0, output_field=DecimalField())
        )["value"]
        count = orders.count()
        status_counts = {item["status"]: item["count"] for item in orders.values("status").annotate(count=Count("id"))}
        items_sold = OrderItem.objects.filter(order__in=orders).aggregate(value=Coalesce(Sum("quantity"), 0))["value"]
        top_products = list(
            OrderItem.objects.filter(order__in=orders)
            .values("product_name").annotate(quantity=Sum("quantity"), revenue=Sum("total"))
            .order_by("-quantity")[:5]
        )
        hourly = list(
            orders.annotate(hour=ExtractHour("created_at")).values("hour")
            .annotate(orders=Count("id"), revenue=Sum("total")).order_by("hour")
        )
        return Response({
            "date": today,
            "revenue": revenue,
            "orders": count,
            "average_order_value": revenue / count if count else 0,
            "items_sold": items_sold,
            "status_counts": status_counts,
            "top_products": top_products,
            "orders_by_hour": hourly,
        })

