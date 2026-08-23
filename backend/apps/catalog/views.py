from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.models import AuditLog, User
from apps.accounts.permissions import IsManagerOrAdmin
from .models import Category, FoodProduct, Offer
from .serializers import CategorySerializer, OfferSerializer, ProductSerializer


class CatalogPermissionMixin:
    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [IsManagerOrAdmin()]

    def scope(self, queryset, venue_path="venue"):
        venue = self.request.query_params.get("venue")
        if self.request.user.is_authenticated and self.request.user.role != User.Role.SUPER_ADMIN:
            venue = self.request.user.venue_id
        if venue:
            lookup = venue_path if str(venue).isdigit() else f"{venue_path}__code"
            queryset = queryset.filter(**{lookup: venue})
        return queryset

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="CATALOG_UPDATED",
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            metadata={"fields": list(self.request.data.keys())},
        )


class CategoryViewSet(CatalogPermissionMixin, viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.select_related("venue").all()
    filterset_fields = ["venue", "is_active"]
    search_fields = ["name"]

    def get_queryset(self):
        queryset = self.scope(super().get_queryset())
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True, venue__status="ACTIVE")
        return queryset


class ProductViewSet(CatalogPermissionMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = FoodProduct.objects.select_related("category", "category__venue").all()
    filterset_fields = ["category", "is_available", "is_featured"]
    search_fields = ["name", "description", "short_description"]

    def get_queryset(self):
        queryset = self.scope(super().get_queryset(), "category__venue")
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_available=True, category__is_active=True)
        return queryset


class OfferViewSet(CatalogPermissionMixin, viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    queryset = Offer.objects.select_related("venue").all()
    filterset_fields = ["venue", "is_active", "offer_type"]

    def get_queryset(self):
        return self.scope(super().get_queryset())
