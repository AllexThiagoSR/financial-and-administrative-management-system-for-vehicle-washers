from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ledger.models import Wash


class Command(BaseCommand):
    help = "Prepare exactly 300 fictional washes for a dedicated test account."

    def add_arguments(self, parser):
        parser.add_argument("username")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Use only an isolated development database.")
        user = get_user_model().objects.filter(username=options["username"]).first()
        if user is None or not user.username.startswith("performance-"):
            raise CommandError("Create a dedicated account with a performance- username.")
        if Wash.objects.filter(user=user).exists():
            raise CommandError("The test account must have no existing washes.")

        today = timezone.localdate()
        washes = []
        for index in range(300):
            paid = index >= 100
            service_date = today - timedelta(days=index % 30)
            washes.append(Wash(
                user=user,
                customer_name=f"Cliente fictício {index + 1:03}",
                service_type="Lavagem simples",
                service_date=service_date,
                amount_cents=4000,
                payment_status=Wash.PaymentStatus.PAID if paid else Wash.PaymentStatus.PENDING,
                payment_received_date=service_date if paid else None,
            ))
        Wash.objects.bulk_create(washes)
        self.stdout.write("Created 300 fictional washes (100 pending).")
