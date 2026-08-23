import secrets
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import decorators, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import AuditLog, User
from apps.orders.models import Order
from apps.orders.services import transition_order
from apps.orders.views import request_session
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("order", "order__venue").all()

    def get_permissions(self):
        return [AllowAny()] if self.action == "simulate" else [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != User.Role.SUPER_ADMIN:
            queryset = queryset.filter(order__venue=self.request.user.venue)
        return queryset

    @decorators.action(detail=False, methods=["post"])
    @transaction.atomic
    def simulate(self, request):
        session = request_session(request)
        order = get_object_or_404(
            Order.objects.select_for_update(), public_id=request.data.get("order_id"), customer_session=session
        )
        method = request.data.get("payment_method", Payment.Method.UPI)
        if method not in Payment.Method.values:
            return Response({"detail": "Unsupported payment method."}, status=status.HTTP_400_BAD_REQUEST)
        existing = order.payments.filter(status=Payment.Status.SUCCESS).first()
        if existing:
            return Response(self.get_serializer(existing).data)
        if order.status != Order.Status.PENDING:
            return Response({"detail": "This order cannot be paid."}, status=status.HTTP_400_BAD_REQUEST)
        payment = Payment.objects.create(
            order=order,
            transaction_id=f"DEMO-{timezone.now():%Y%m%d}-{secrets.token_hex(5).upper()}",
            amount=order.total,
            status=Payment.Status.SUCCESS,
            payment_method=method,
            paid_at=timezone.now(),
        )
        order.payment_status = Order.PaymentStatus.SUCCESS
        order.save(update_fields=["payment_status"])
        transition_order(order, Order.Status.CONFIRMED, note="Demo payment approved")
        AuditLog.objects.create(
            action="PAYMENT_SUCCESS", entity_type="Payment", entity_id=str(payment.public_id),
            metadata={"order_number": order.order_number, "amount": str(order.total), "method": method},
        )
        return Response(self.get_serializer(payment).data, status=status.HTTP_201_CREATED)

