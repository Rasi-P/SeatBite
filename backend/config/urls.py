from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import AuditLogViewSet, CurrentUserView, StaffViewSet
from apps.analytics.views import AnalyticsViewSet
from apps.catalog.views import CategoryViewSet, OfferViewSet, ProductViewSet
from apps.delivery.views import DeliveryAssignmentViewSet
from apps.orders.views import CartViewSet, CustomerSessionViewSet, OrderViewSet
from apps.payments.views import PaymentViewSet
from apps.venues.views import QRCodeViewSet, ScreenViewSet, SeatViewSet, VenueViewSet

router = DefaultRouter()
router.register("venues", VenueViewSet)
router.register("screens", ScreenViewSet)
router.register("seats", SeatViewSet)
router.register("qr", QRCodeViewSet, basename="qr")
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("offers", OfferViewSet)
router.register("sessions", CustomerSessionViewSet, basename="session")
router.register("cart", CartViewSet, basename="cart")
router.register("orders", OrderViewSet, basename="order")
router.register("payments", PaymentViewSet, basename="payment")
router.register("staff", StaffViewSet)
router.register("delivery", DeliveryAssignmentViewSet, basename="delivery")
router.register("analytics", AnalyticsViewSet, basename="analytics")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("api/v1/", include(router.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

