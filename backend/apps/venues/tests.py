from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, User
from apps.orders.models import CustomerSession
from .models import Screen, Seat, Venue


class ScreenCreationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="CineMax Test", code="CMX-TEST", city="Calicut")
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@test.dev",
            role=User.Role.VENUE_MANAGER,
            venue=self.venue,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.manager)

    def test_manager_creates_screen_with_complete_secure_seat_grid(self):
        response = self.client.post(
            "/api/v1/screens/",
            {
                "venue": self.venue.pk,
                "name": "Screen 4",
                "screen_number": 4,
                "total_rows": 3,
                "total_columns": 5,
                "status": "ACTIVE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        screen = Screen.objects.get(pk=response.data["id"])
        self.assertEqual(screen.seats.count(), 15)
        self.assertTrue(screen.seats.filter(seat_code="A01").exists())
        self.assertTrue(screen.seats.filter(seat_code="C05").exists())
        self.assertEqual(screen.seats.values("qr_token").distinct().count(), 15)
        self.assertEqual(AuditLog.objects.get(entity_id=str(screen.pk)).action, "SCREEN_CREATED")

    def test_manager_cannot_create_screen_in_another_venue(self):
        other = Venue.objects.create(name="Other Cinema", code="OTHER", city="Kochi")
        response = self.client.post(
            "/api/v1/screens/",
            {
                "venue": other.pk,
                "name": "Injected Screen",
                "screen_number": 9,
                "total_rows": 2,
                "total_columns": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Screen.objects.get(pk=response.data["id"]).venue, self.venue)
        self.assertFalse(Screen.objects.filter(venue=other).exists())

    def test_rejects_screen_dimensions_outside_demo_limits(self):
        response = self.client.post(
            "/api/v1/screens/",
            {
                "venue": self.venue.pk,
                "name": "Too Large",
                "screen_number": 5,
                "total_rows": 27,
                "total_columns": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Seat.objects.count(), 0)

    def test_manager_edits_screen_metadata_without_rewriting_seats(self):
        screen = Screen.objects.create(
            venue=self.venue,
            name="Old Name",
            screen_number=2,
            total_rows=2,
            total_columns=3,
        )
        Seat.objects.create(
            screen=screen,
            row_label="A",
            seat_number=1,
            seat_code="A01",
        )

        response = self.client.patch(
            f"/api/v1/screens/{screen.pk}/",
            {"name": "Premium Screen", "screen_number": 7, "status": "INACTIVE"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        screen.refresh_from_db()
        self.assertEqual(screen.name, "Premium Screen")
        self.assertEqual(screen.screen_number, 7)
        self.assertEqual(screen.status, Screen.Status.INACTIVE)
        self.assertEqual(screen.seats.count(), 1)
        self.assertTrue(AuditLog.objects.filter(entity_id=str(screen.pk), action="SCREEN_UPDATED").exists())

    def test_rejects_dimension_changes_after_screen_creation(self):
        screen = Screen.objects.create(
            venue=self.venue,
            name="Screen 2",
            screen_number=2,
            total_rows=2,
            total_columns=3,
        )

        response = self.client.patch(
            f"/api/v1/screens/{screen.pk}/",
            {"total_rows": 4},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        screen.refresh_from_db()
        self.assertEqual(screen.total_rows, 2)

    def test_manager_deletes_screen_without_customer_history(self):
        screen = Screen.objects.create(
            venue=self.venue,
            name="Temporary Screen",
            screen_number=3,
            total_rows=1,
            total_columns=2,
        )
        Seat.objects.bulk_create([
            Seat(screen=screen, row_label="A", seat_number=1, seat_code="A01"),
            Seat(screen=screen, row_label="A", seat_number=2, seat_code="A02"),
        ])
        screen_id = screen.pk

        response = self.client.delete(f"/api/v1/screens/{screen_id}/")

        self.assertEqual(response.status_code, 204)
        screen.refresh_from_db()
        self.assertTrue(screen.is_deleted)
        self.assertEqual(screen.status, Screen.Status.INACTIVE)
        self.assertEqual(screen.deleted_by, self.manager)
        self.assertIsNotNone(screen.deleted_at)
        self.assertEqual(Seat.objects.filter(screen_id=screen_id).count(), 2)
        self.assertEqual(self.client.get(f"/api/v1/screens/{screen_id}/").status_code, 404)
        self.assertTrue(AuditLog.objects.filter(entity_id=str(screen_id), action="SCREEN_DELETED").exists())

    def test_soft_deletion_preserves_customer_history(self):
        screen = Screen.objects.create(
            venue=self.venue,
            name="In Use",
            screen_number=6,
            total_rows=1,
            total_columns=1,
        )
        seat = Seat.objects.create(
            screen=screen,
            row_label="A",
            seat_number=1,
            seat_code="A01",
        )
        CustomerSession.objects.create(
            seat=seat,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.delete(f"/api/v1/screens/{screen.pk}/")

        self.assertEqual(response.status_code, 204)
        screen.refresh_from_db()
        self.assertTrue(screen.is_deleted)
        self.assertTrue(Screen.objects.filter(pk=screen.pk).exists())
        self.assertTrue(CustomerSession.objects.filter(seat=seat).exists())

    def test_screen_number_can_be_reused_after_soft_deletion(self):
        old_screen = Screen.objects.create(
            venue=self.venue,
            name="Old Screen 8",
            screen_number=8,
            total_rows=1,
            total_columns=1,
            status=Screen.Status.INACTIVE,
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=self.manager,
        )

        response = self.client.post(
            "/api/v1/screens/",
            {
                "venue": self.venue.pk,
                "name": "New Screen 8",
                "screen_number": 8,
                "total_rows": 2,
                "total_columns": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotEqual(response.data["id"], old_screen.pk)
        self.assertEqual(
            Screen.objects.filter(venue=self.venue, screen_number=8, is_deleted=False).count(),
            1,
        )
