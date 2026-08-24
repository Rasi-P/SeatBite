from io import BytesIO
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import decorators, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from apps.accounts.models import AuditLog, User
from apps.accounts.permissions import IsManagerOrAdmin
from .models import Screen, Seat, Venue
from .serializers import ScreenSerializer, SeatSerializer, VenueSerializer


class VenueScopedMixin:
    def scope_queryset(self, queryset, path="venue"):
        if self.request.user.role == User.Role.SUPER_ADMIN:
            return queryset
        return queryset.filter(**{path: self.request.user.venue})


class VenueViewSet(VenueScopedMixin, viewsets.ModelViewSet):
    serializer_class = VenueSerializer
    permission_classes = [IsManagerOrAdmin]
    queryset = Venue.objects.all()
    search_fields = ["name", "code", "city"]

    def get_queryset(self):
        if self.request.user.role == User.Role.SUPER_ADMIN:
            return self.queryset
        return self.queryset.filter(pk=self.request.user.venue_id)


class ScreenViewSet(VenueScopedMixin, viewsets.ModelViewSet):
    serializer_class = ScreenSerializer
    permission_classes = [IsManagerOrAdmin]
    queryset = Screen.objects.select_related("venue").all()
    filterset_fields = ["venue", "status"]

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset()).filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if request.user.role != User.Role.SUPER_ADMIN:
            if not request.user.venue_id:
                return Response(
                    {"detail": "Your account is not assigned to a venue."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data["venue"] = request.user.venue_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def perform_create(self, serializer):
        screen = serializer.save()
        seats = [
            Seat(
                screen=screen,
                row_label=chr(65 + row_index),
                seat_number=seat_number,
                seat_code=f"{chr(65 + row_index)}{seat_number:02d}",
            )
            for row_index in range(screen.total_rows)
            for seat_number in range(1, screen.total_columns + 1)
        ]
        Seat.objects.bulk_create(seats)
        AuditLog.objects.create(
            user=self.request.user,
            action="SCREEN_CREATED",
            entity_type="Screen",
            entity_id=str(screen.pk),
            metadata={
                "venue": screen.venue.name,
                "screen": screen.name,
                "seat_count": len(seats),
            },
        )

    def perform_update(self, serializer):
        screen = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action="SCREEN_UPDATED",
            entity_type="Screen",
            entity_id=str(screen.pk),
            metadata={
                "venue": screen.venue.name,
                "screen": screen.name,
                "fields": list(self.request.data.keys()),
            },
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        scoped_screen = self.get_object()
        screen = Screen.objects.select_for_update().get(pk=scoped_screen.pk)
        metadata = {
            "venue": screen.venue.name,
            "screen": screen.name,
            "seat_count": screen.seats.count(),
        }
        entity_id = str(screen.pk)
        screen.is_deleted = True
        screen.deleted_at = timezone.now()
        screen.deleted_by = request.user
        screen.status = Screen.Status.INACTIVE
        screen.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "status"])
        AuditLog.objects.create(
            user=request.user,
            action="SCREEN_DELETED",
            entity_type="Screen",
            entity_id=entity_id,
            metadata=metadata,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SeatViewSet(VenueScopedMixin, viewsets.ModelViewSet):
    serializer_class = SeatSerializer
    permission_classes = [IsManagerOrAdmin]
    queryset = Seat.objects.select_related("screen", "screen__venue").all()
    filterset_fields = ["screen", "row_label", "status", "seat_type"]
    search_fields = ["seat_code"]

    def get_queryset(self):
        return self.scope_queryset(
            super().get_queryset(), "screen__venue"
        ).filter(screen__is_deleted=False)

    @decorators.action(detail=True, methods=["post"])
    def regenerate_qr(self, request, pk=None):
        seat = self.get_object()
        seat.regenerate_token()
        AuditLog.objects.create(
            user=request.user, action="QR_REGENERATED", entity_type="Seat", entity_id=str(seat.pk)
        )
        return Response(self.get_serializer(seat).data)


class QRCodeViewSet(VenueScopedMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _seat(self, request, pk):
        queryset = Seat.objects.select_related("screen", "screen__venue").filter(
            screen__is_deleted=False
        )
        if request.user.role != User.Role.SUPER_ADMIN:
            queryset = queryset.filter(screen__venue=request.user.venue)
        return get_object_or_404(queryset, pk=pk)

    @decorators.action(detail=True, methods=["get"])
    def image(self, request, pk=None):
        seat = self._seat(request, pk)
        image = qrcode.make(f"{settings.SEATBITE_CUSTOMER_URL}/{seat.qr_token}")
        output = BytesIO()
        image.save(output, format="PNG")
        response = HttpResponse(output.getvalue(), content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="{seat.screen.name}-{seat.seat_code}.png"'
        return response

    @decorators.action(detail=False, methods=["post"])
    def regenerate_screen(self, request):
        screen = get_object_or_404(
            Screen, pk=request.data.get("screen_id"), is_deleted=False
        )
        if request.user.role != User.Role.SUPER_ADMIN and screen.venue_id != request.user.venue_id:
            return Response({"detail": "Outside your venue."}, status=status.HTTP_403_FORBIDDEN)
        for seat in screen.seats.all():
            seat.regenerate_token()
        AuditLog.objects.create(
            user=request.user, action="SCREEN_QR_REGENERATED", entity_type="Screen", entity_id=str(screen.pk)
        )
        return Response({"regenerated": screen.seats.count()})

    @decorators.action(detail=False, methods=["get"], url_path="print-sheet")
    def print_sheet(self, request):
        screen = get_object_or_404(
            Screen.objects.select_related("venue"),
            pk=request.query_params.get("screen"),
            is_deleted=False,
        )
        if request.user.role != User.Role.SUPER_ADMIN and screen.venue_id != request.user.venue_id:
            return Response({"detail": "Outside your venue."}, status=status.HTTP_403_FORBIDDEN)
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=A4)
        page_width, page_height = A4
        margin, gap = 32, 12
        columns, rows = 3, 4
        card_width = (page_width - margin * 2 - gap * (columns - 1)) / columns
        card_height = (page_height - margin * 2 - gap * (rows - 1)) / rows
        for index, seat in enumerate(screen.seats.all()):
            position = index % (columns * rows)
            if index and position == 0:
                pdf.showPage()
            column, row = position % columns, position // columns
            x = margin + column * (card_width + gap)
            y = page_height - margin - (row + 1) * card_height - row * gap
            pdf.setStrokeColorRGB(0.85, 0.82, 0.78)
            pdf.roundRect(x, y, card_width, card_height, 8, stroke=1, fill=0)
            qr_buffer = BytesIO()
            qrcode.make(f"{settings.SEATBITE_CUSTOMER_URL}/{seat.qr_token}").save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            qr_size = min(100, card_height - 62)
            pdf.drawImage(ImageReader(qr_buffer), x + (card_width - qr_size) / 2, y + 46, qr_size, qr_size)
            pdf.setFillColorRGB(0.12, 0.14, 0.15)
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawCentredString(x + card_width / 2, y + 30, f"{screen.name}  ·  Seat {seat.seat_code}")
            pdf.setFont("Helvetica", 7)
            pdf.drawCentredString(x + card_width / 2, y + 17, "Scan to order food to this seat")
        pdf.save()
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{screen.venue.code}-{screen.name}-QR.pdf"'
        return response
