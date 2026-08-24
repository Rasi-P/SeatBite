from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, User
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
