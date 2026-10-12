"""Provider webhook handling.

Webhooks are untrusted input until verified (docs/API-CONVENTIONS.md §11).
Processing is idempotent: a replayed notification resolves to the same event row
and never applies a second effect.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.payments.models import Payment, PaymentProvider, PaymentWebhookEvent
from apps.payments.providers.midtrans import (
    map_transaction_status,
    notification_event_key,
    verify_signature,
)
from apps.payments.services import apply_provider_status

logger = logging.getLogger("portatap.payments")


@transaction.atomic
def process_midtrans_notification(payload: dict) -> PaymentWebhookEvent:
    """Verify, deduplicate and apply one Midtrans notification."""
    signature_valid = verify_signature(payload, server_key=settings.MIDTRANS_SERVER_KEY)
    event_key = notification_event_key(payload)

    event, created = PaymentWebhookEvent.objects.get_or_create(
        provider=PaymentProvider.MIDTRANS,
        event_key=event_key,
        defaults={
            "event_type": payload.get("transaction_status", ""),
            "provider_reference": payload.get("transaction_id", ""),
            "payload": payload,
            "signature_valid": signature_valid,
        },
    )

    if not created and event.processed_at is not None:
        # Duplicate delivery of an already-processed event.
        return event

    if not signature_valid:
        event.signature_valid = False
        event.processing_note = "Signature tidak valid; event diabaikan."
        event.save(update_fields=["signature_valid", "processing_note"])
        logger.warning("Midtrans webhook dengan signature tidak valid: %s", event_key)
        return event

    order_id = payload.get("order_id", "")
    payment = (
        Payment.objects.filter(
            provider=PaymentProvider.MIDTRANS, provider_reference=order_id
        )
        .select_related("order")
        .first()
    )
    if payment is None:
        event.processing_note = f"Payment untuk order_id={order_id} tidak ditemukan."
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_note", "processed_at"])
        logger.warning("Midtrans webhook tanpa payment: %s", order_id)
        return event

    new_status = map_transaction_status(
        payload.get("transaction_status", ""), payload.get("fraud_status")
    )
    apply_provider_status(
        payment=payment,
        new_status=new_status,
        provider_reference=payload.get("transaction_id", ""),
        payload=payload,
    )

    event.processed_at = timezone.now()
    event.processing_note = f"status={new_status}"
    event.save(update_fields=["processed_at", "processing_note"])
    return event
