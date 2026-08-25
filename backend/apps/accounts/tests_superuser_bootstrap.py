from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.accounts.models import User


class EnsureSuperuserFromEnvTests(TestCase):
    def test_noop_when_flag_is_unset(self):
        output = StringIO()

        with patch.dict("os.environ", {}, clear=True):
            call_command("ensure_superuser_from_env", stdout=output)

        self.assertEqual(User.objects.count(), 0)
        self.assertIn("skipping superuser setup", output.getvalue())

    def test_creates_superuser_when_flag_is_enabled(self):
        output = StringIO()
        env = {
            "CREATE_DJANGO_SUPERUSER": "true",
            "DJANGO_SUPERUSER_USERNAME": "render_admin",
            "DJANGO_SUPERUSER_EMAIL": "render_admin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "render-password-123",
        }

        with patch.dict("os.environ", env, clear=True):
            call_command("ensure_superuser_from_env", stdout=output)

        user = User.objects.get(username="render_admin")
        self.assertEqual(user.email, "render_admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.assertIsNone(user.venue_id)
        self.assertTrue(user.check_password("render-password-123"))
        self.assertIn("was created", output.getvalue())
        self.assertNotIn("render-password-123", output.getvalue())

    def test_updates_existing_user_idempotently(self):
        user = User.objects.create_user(
            username="render_admin",
            email="old@example.com",
            password="old-password",
            role=User.Role.KITCHEN_STAFF,
        )
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])

        output = StringIO()
        env = {
            "CREATE_DJANGO_SUPERUSER": "true",
            "DJANGO_SUPERUSER_USERNAME": "render_admin",
            "DJANGO_SUPERUSER_EMAIL": "new_admin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "new-password-123",
        }

        with patch.dict("os.environ", env, clear=True):
            call_command("ensure_superuser_from_env", stdout=output)
            call_command("ensure_superuser_from_env", stdout=output)

        self.assertEqual(User.objects.filter(username="render_admin").count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.email, "new_admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.assertIsNone(user.venue_id)
        self.assertTrue(user.check_password("new-password-123"))
        self.assertIn("already existed and was updated", output.getvalue())
        self.assertNotIn("new-password-123", output.getvalue())

    def test_raises_when_flag_enabled_but_required_values_missing(self):
        env = {
            "CREATE_DJANGO_SUPERUSER": "true",
            "DJANGO_SUPERUSER_USERNAME": "render_admin",
        }

        with patch.dict("os.environ", env, clear=True):
            with self.assertRaises(CommandError):
                call_command("ensure_superuser_from_env")
