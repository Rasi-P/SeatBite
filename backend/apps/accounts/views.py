from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog, User
from .permissions import IsAdmin, IsManagerOrAdmin
from .serializers import AuditLogSerializer, UserSerializer


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsManagerOrAdmin]
    queryset = User.objects.select_related("venue").all()
    search_fields = ["first_name", "last_name", "email"]
    filterset_fields = ["role", "venue", "is_active"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != User.Role.SUPER_ADMIN:
            queryset = queryset.filter(venue=self.request.user.venue)
        return queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    queryset = AuditLog.objects.select_related("user").all()
    filterset_fields = ["entity_type", "entity_id", "user"]

