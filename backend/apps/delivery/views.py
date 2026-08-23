from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import decorators, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import AuditLog, User
from apps.orders.models import Order
from apps.venues.models import Screen, Seat
from .models import DeliveryAssignment
from .serializers import DeliveryAssignmentSerializer


class DeliveryAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryAssignmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = DeliveryAssignment.objects.select_related(
        "staff", "order", "order__venue", "order__screen", "order__seat"
    ).prefetch_related("order__items", "order__status_events")
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == User.Role.SUPER_ADMIN:
            return queryset
        queryset = queryset.filter(order__venue=self.request.user.venue)
        if self.request.user.role == User.Role.DELIVERY_STAFF:
            queryset = queryset.filter(staff=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=request.data.get("order"), status=Order.Status.READY)
        if request.user.role != User.Role.SUPER_ADMIN and order.venue_id != request.user.venue_id:
            return Response({"detail": "Outside your venue."}, status=status.HTTP_403_FORBIDDEN)
        staff_id = request.data.get("staff") or request.user.pk
        staff = get_object_or_404(User, pk=staff_id, role=User.Role.DELIVERY_STAFF, venue=order.venue)
        assignment, created = DeliveryAssignment.objects.get_or_create(
            order=order, defaults={"staff": staff, "notes": request.data.get("notes", "")}
        )
        if not created:
            return Response({"detail": "Order is already assigned."}, status=status.HTTP_400_BAD_REQUEST)
        AuditLog.objects.create(
            user=request.user, action="DELIVERY_ASSIGNED", entity_type="Order",
            entity_id=str(order.public_id), metadata={"staff": staff.get_full_name()},
        )
        return Response(self.get_serializer(assignment).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=["get"], url_path="seat-map")
    def seat_map(self, request):
        screen = get_object_or_404(Screen, pk=request.query_params.get("screen"))
        if request.user.role != User.Role.SUPER_ADMIN and screen.venue_id != request.user.venue_id:
            return Response({"detail": "Outside your venue."}, status=status.HTTP_403_FORBIDDEN)
        active_order = Order.objects.filter(
            seat=OuterRef("pk"),
            status__in=[Order.Status.CONFIRMED, Order.Status.PREPARING, Order.Status.READY, Order.Status.OUT_FOR_DELIVERY],
        ).order_by("-created_at")
        seats = Seat.objects.filter(screen=screen).annotate(
            active_status=Subquery(active_order.values("status")[:1]),
            active_order_id=Subquery(active_order.values("id")[:1]),
            active_order_number=Subquery(active_order.values("order_number")[:1]),
        )
        return Response({
            "screen": {"id": screen.pk, "name": screen.name, "number": screen.screen_number},
            "seats": [{
                "id": seat.pk, "row_label": seat.row_label, "seat_number": seat.seat_number,
                "seat_code": seat.seat_code, "status": seat.status, "order_status": seat.active_status,
                "order_id": seat.active_order_id, "order_number": seat.active_order_number,
            } for seat in seats],
        })

