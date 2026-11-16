from django.utils import timezone

from .models import Wash


def confirm_payment(washes, today=None):
    return washes.filter(payment_status=Wash.PaymentStatus.PENDING).update(
        payment_status=Wash.PaymentStatus.PAID,
        payment_received_date=today or timezone.localdate(),
    )
