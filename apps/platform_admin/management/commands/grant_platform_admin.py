"""Grant platform-admin access to an existing account."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.platform_admin.services import grant_platform_admin

User = get_user_model()


class Command(BaseCommand):
    help = "Beri akses admin platform ke akun berdasarkan email."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email akun yang akan dijadikan admin platform.")

    def handle(self, *args, **options):
        email = options["email"].lower()
        user = User.objects.filter(email=email).first()
        if user is None:
            raise CommandError(f"Akun dengan email {email} tidak ditemukan.")

        grant_platform_admin(user)
        self.stdout.write(self.style.SUCCESS(f"{email} sekarang admin platform."))
