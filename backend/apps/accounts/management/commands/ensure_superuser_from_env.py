import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


def env_flag(name):
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Create or update a Django superuser from environment variables."

    def handle(self, *args, **options):
        if not env_flag("CREATE_DJANGO_SUPERUSER"):
            self.stdout.write("CREATE_DJANGO_SUPERUSER is disabled; skipping superuser setup.")
            return

        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")

        missing = [
            name
            for name, value in (
                ("DJANGO_SUPERUSER_USERNAME", username),
                ("DJANGO_SUPERUSER_EMAIL", email),
                ("DJANGO_SUPERUSER_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            raise CommandError(
                f"CREATE_DJANGO_SUPERUSER is enabled, but required variables are missing: {', '.join(missing)}"
            )

        User = get_user_model()
        existing = User.objects.filter(username=username).first()
        if existing:
            existing.email = email
            existing.is_staff = True
            existing.is_superuser = True
            existing.is_active = True
            if hasattr(existing, "role"):
                existing.role = User.Role.SUPER_ADMIN
            if hasattr(existing, "venue_id"):
                existing.venue = None
            existing.set_password(password)
            update_fields = ["email", "is_staff", "is_superuser", "is_active", "password"]
            if hasattr(existing, "role"):
                update_fields.append("role")
            if hasattr(existing, "venue_id"):
                update_fields.append("venue")
            existing.save(update_fields=update_fields)
            self.stdout.write(f"Superuser '{username}' already existed and was updated.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=getattr(getattr(User, "Role", None), "SUPER_ADMIN", None),
            venue=None if hasattr(User, "venue") else None,
        )
        self.stdout.write(f"Superuser '{username}' was created.")
