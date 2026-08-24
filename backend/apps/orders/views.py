from datetime import timedelta
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import decorators, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.catalog.models import FoodProduct
from apps.venues.models import Seat
from .models import Cart, CustomerSession, Order
from .serializers import CartSerializer, CustomerSessionSerializer, OrderSerializer
from .services import checkout, recalculate_cart, set_cart_item, transition_order


def request_session(request):
    token = request.headers.get("X-Session-Token")
    session = get_object_or_404(
        CustomerSession.objects.select_related("seat", "seat__screen", "seat__screen__venue"),
        session_token=token, status=CustomerSession.Status.ACTIVE, expires_at__gt=timezone.now(),
    )
    return session


class CustomerSessionViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @decorators.action(detail=False, methods=["post"])
    def resolve(self, request):
        seat = get_object_or_404(
            Seat.objects.select_related("screen", "screen__venue"),
            qr_token=request.data.get("qr_token"), status=Seat.Status.ACTIVE,
            screen__status="ACTIVE", screen__is_deleted=False, screen__venue__status="ACTIVE",
        )
        session = CustomerSession.objects.create(
            seat=seat,
            device_identifier=str(request.data.get("device_identifier", ""))[:160],
            expires_at=timezone.now() + timedelta(hours=6),
        )
        Cart.objects.create(session=session)
        return Response(CustomerSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=["get"])
    def current(self, request):
        return Response(CustomerSessionSerializer(request_session(request)).data)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def _cart(self, request):
        session = request_session(request)
        cart, _ = Cart.objects.prefetch_related("items__product", "items__product__category").get_or_create(
            session=session, status=Cart.Status.ACTIVE
        )
        return recalculate_cart(cart)

    @decorators.action(detail=False, methods=["get"])
    def current(self, request):
        return Response(CartSerializer(self._cart(request)).data)

    @decorators.action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        cart = self._cart(request)
        product = get_object_or_404(FoodProduct.objects.select_related("category"), pk=request.data.get("product_id"))
        try:
            cart = set_cart_item(cart, product, int(request.data.get("quantity", 1)))
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CartSerializer(cart).data)

    @decorators.action(detail=False, methods=["delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def remove_item(self, request, item_id=None):
        cart = self._cart(request)
        item = get_object_or_404(cart.items, pk=item_id)
        item.delete()
        return Response(CartSerializer(recalculate_cart(cart)).data)

    @decorators.action(detail=False, methods=["post"])
    def checkout(self, request):
        try:
            order = checkout(self._cart(request))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.select_related("venue", "screen", "seat").prefetch_related(
        "items", "status_events", "status_events__changed_by"
    )
    filterset_fields = ["status", "payment_status", "screen", "seat"]
    search_fields = ["order_number", "seat__seat_code"]

    def get_permissions(self):
        if self.action == "track":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != User.Role.SUPER_ADMIN:
            queryset = queryset.filter(venue=self.request.user.venue)
        return queryset

    @decorators.action(detail=False, methods=["get"], url_path=r"(?P<public_id>[0-9a-f-]+)/track")
    def track(self, request, public_id=None):
        session = request_session(request)
        order = get_object_or_404(self.queryset, public_id=public_id, customer_session=session)
        return Response(self.get_serializer(order).data)

    @decorators.action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        order = self.get_object()
        try:
            order = transition_order(order, request.data.get("status"), request.user, request.data.get("note", ""))
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(order).data)

    @decorators.action(detail=False, methods=["get"])
    def board(self, request):
        orders = self.get_queryset().exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        grouped = {key: [] for key in ["CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY"]}
        for order in orders:
            if order.status in grouped:
                grouped[order.status].append(self.get_serializer(order).data)
        return Response(grouped)
