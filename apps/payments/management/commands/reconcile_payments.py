"""Reconcile uncertain digital payments against the provider.

Payments can end up in limbo when a webhook never arrives (network hiccup, wrong
URL, provider outage). This command asks the provider for the authoritative
status and applies it idempotently, so the database converges on the truth.

    python manage.py reconcile_payments
    python manage.py reconcile_payments --minutes 10 --dry-run
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.orders.models import PaymentStatus
from apps.payments.models import Payment, PaymentMethod, PaymentProvider
from apps.payments.providers.midtrans import (
    MidtransClient,
    MidtransError,
    map_transaction_status,
)
from apps.payments.services import apply_provider_status


class Command(BaseCommand):
    help = "Cek ulang pembayaran digital yang menggantung ke penyedia pembayaran."

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=None,
            help="Hanya periksa pembayaran yang lebih tua dari N menit.",
        )
        parser.add_argument(
            "--limit", type=int, default=50, help="Maksimal pembayaran diperiksa sekali jalan."
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Tampilkan hasil tanpa mengubah data."
        )

    def handle(self, *args, **options):
        # `0` is a meaningful value here ("check everything"), so it must not be
        # treated as "unset" by a truthiness check.
        minutes = (
            options["minutes"]
            if options["minutes"] is not None
            else settings.PAYMENT_EXPIRY_MINUTES
        )
        cutoff = timezone.now() - timedelta(minutes=minutes)

        pending = (
            Payment.objects.filter(
                method=PaymentMethod.DIGITAL,
                provider=PaymentProvider.MIDTRANS,
                status=PaymentStatus.PENDING,
                created_at__lt=cutoff,
            )
            .select_related("order")
            .order_by("created_at")[: options["limit"]]
        )

        client = MidtransClient.from_settings()
        checked = 0
        skipped = 0
        failed = 0

        for payment in pending:
            reference = payment.provider_reference
            if not reference:
                skipped += 1
                continue

            try:
                payload = client.get_transaction_status(reference)
            except MidtransError as exc:
                failed += 1
                self.stderr.write(f"{reference}: {exc}")
                continue

            new_status = map_transaction_status(
                payload.get("transaction_status", ""), payload.get("fraud_status")
            )
            checked += 1

            if options["dry_run"]:
                self.stdout.write(f"{reference}: {payment.status} -> {new_status}")
                continue

            apply_provider_status(
                payment=payment,
                new_status=new_status,
                provider_reference=payload.get("transaction_id", ""),
                payload=payload,
            )
            self.stdout.write(f"{reference}: -> {new_status}")

        self.stdout.write(
            self.style.SUCCESS(
                f"diperiksa={checked} dilewati={skipped} gagal={failed}"
                + (" (dry-run, tidak ada perubahan)" if options["dry_run"] else "")
            )
        )
