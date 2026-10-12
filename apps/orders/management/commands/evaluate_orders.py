"""Evaluate pending-order timers (3-minute warning, 5-minute late).

Run periodically, e.g. every minute:

    python manage.py evaluate_orders

Celery is not part of the MVP stack (docs/ARCHITECTURE.md §11); a scheduled
management command is enough for the cashier timers.
"""

from django.core.management.base import BaseCommand

from apps.orders.services import evaluate_pending_orders
from apps.tenants.models import Branch


class Command(BaseCommand):
    help = "Terapkan peringatan 3 menit dan penanda terlambat 5 menit pada order PENDING."

    def add_arguments(self, parser):
        parser.add_argument("--branch", help="Batasi ke satu branch id (opsional).")

    def handle(self, *args, **options):
        branch = None
        if options.get("branch"):
            branch = Branch.objects.filter(id=options["branch"]).first()
            if branch is None:
                self.stderr.write("Branch tidak ditemukan.")
                return
        result = evaluate_pending_orders(branch=branch)
        self.stdout.write(
            self.style.SUCCESS(f"warned={result['warned']} late={result['late']}")
        )
