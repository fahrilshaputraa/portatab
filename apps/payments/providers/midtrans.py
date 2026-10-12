"""Midtrans (Snap) integration adapter.

All provider-specific behaviour lives behind this boundary (docs/API-CONVENTIONS.md
§11). Nothing outside this module assumes Midtrans' schema, and provider secrets
are never logged.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import httpx
from django.conf import settings

from apps.orders.models import PaymentStatus


class MidtransError(Exception):
    pass


# Map Midtrans transaction_status/fraud_status onto our payment vocabulary.
_STATUS_MAP = {
    "capture": PaymentStatus.PAID,
    "settlement": PaymentStatus.PAID,
    "pending": PaymentStatus.PENDING,
    "deny": PaymentStatus.FAILED,
    "cancel": PaymentStatus.FAILED,
    "failure": PaymentStatus.FAILED,
    "expire": PaymentStatus.EXPIRED,
    # A refund leaves the original payment successful; refunds are modelled
    # separately in the payments app.
    "refund": PaymentStatus.PAID,
    "partial_refund": PaymentStatus.PAID,
    "chargeback": PaymentStatus.PAID,
    "partial_chargeback": PaymentStatus.PAID,
}

_TERMINAL_FAILURES = {"deny", "cancel", "expire", "failure"}


class MidtransClient:
    """Thin Snap/API client. Inject a stub in tests instead of hitting the network."""

    def __init__(
        self,
        *,
        server_key: str,
        snap_base_url: str,
        api_base_url: str,
        timeout: int = 15,
    ) -> None:
        self.server_key = server_key
        self.snap_base_url = snap_base_url.rstrip("/")
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> MidtransClient:
        return cls(
            server_key=settings.MIDTRANS_SERVER_KEY,
            snap_base_url=settings.MIDTRANS_SNAP_BASE_URL,
            api_base_url=settings.MIDTRANS_API_BASE_URL,
            timeout=settings.MIDTRANS_TIMEOUT_SECONDS,
        )

    def _auth_header(self) -> str:
        raw = f"{self.server_key}:".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def create_snap_transaction(
        self, *, order_id: str, gross_amount: int | str, customer: dict | None = None, items: list | None = None
    ) -> dict:
        """Create a Snap transaction and return its ``token`` and ``redirect_url``."""
        payload: dict = {
            "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
        }
        if customer:
            payload["customer_details"] = customer
        if items:
            payload["item_details"] = items

        try:
            response = httpx.post(
                f"{self.snap_base_url}/transactions",
                json=payload,
                headers={
                    "Authorization": self._auth_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network path
            raise MidtransError("Gagal membuat transaksi Midtrans.") from exc
        return response.json()

    def get_transaction_status(self, order_id: str) -> dict:
        """Reconcile an uncertain payment outcome directly from the provider."""
        try:
            response = httpx.get(
                f"{self.api_base_url}/{order_id}/status",
                headers={"Authorization": self._auth_header(), "Accept": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network path
            raise MidtransError("Gagal mengambil status transaksi Midtrans.") from exc
        return response.json()


def verify_signature(payload: dict, *, server_key: str) -> bool:
    """Verify Midtrans' ``signature_key`` = sha512(order_id + status_code + gross_amount + key)."""
    required = {"order_id", "status_code", "gross_amount", "signature_key"}
    if not required.issubset(payload):
        return False
    raw = (
        f"{payload['order_id']}{payload['status_code']}{payload['gross_amount']}{server_key}"
    ).encode()
    expected = hashlib.sha512(raw).hexdigest()
    return hmac.compare_digest(expected, str(payload["signature_key"]))


def map_transaction_status(transaction_status: str, fraud_status: str | None = None) -> str:
    """Translate a provider status to our ``PaymentStatus``.

    A ``capture`` only counts as PAID when fraud review accepts it.
    """
    if transaction_status == "capture" and fraud_status == "challenge":
        return PaymentStatus.PENDING
    return _STATUS_MAP.get(transaction_status, PaymentStatus.PENDING)


def is_terminal_failure(transaction_status: str) -> bool:
    return transaction_status in _TERMINAL_FAILURES


def notification_event_key(payload: dict) -> str:
    """Deterministic key so a replayed notification dedupes to one event row."""
    parts = [
        str(payload.get("order_id", "")),
        str(payload.get("transaction_id", "")),
        str(payload.get("transaction_status", "")),
        str(payload.get("status_code", "")),
        str(payload.get("fraud_status", "")),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()
