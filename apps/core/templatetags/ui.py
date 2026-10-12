"""Shared template filters.

Status tones live here once so every template renders a status the same way and
never invents its own colour mapping.
"""

from django import template

register = template.Library()

ORDER_TONES = {
    "PENDING": "warning",
    "CONFIRMED": "info",
    "PREPARING": "info",
    "READY": "success",
    "COMPLETED": "success",
    "REJECTED": "danger",
    "CANCELLED": "neutral",
}

PAYMENT_TONES = {
    "UNPAID": "warning",
    "PENDING": "info",
    "PAID": "success",
    "FAILED": "danger",
    "EXPIRED": "neutral",
}

REFUND_TONES = {
    "REQUESTED": "warning",
    "APPROVED": "info",
    "PROCESSING": "info",
    "SUCCEEDED": "success",
    "FAILED": "danger",
    "REJECTED": "danger",
    "CANCELLED": "neutral",
}


@register.filter
def order_tone(value) -> str:
    return ORDER_TONES.get(value, "neutral")


@register.filter
def payment_tone(value) -> str:
    return PAYMENT_TONES.get(value, "neutral")


@register.filter
def refund_tone(value) -> str:
    return REFUND_TONES.get(value, "neutral")
