from django.conf import settings
from django.db import models
from django.db.models import Q


class Wash(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100)
    service_date = models.DateField()
    amount_cents = models.PositiveIntegerField()
    payment_status = models.CharField(max_length=7, choices=PaymentStatus)
    payment_received_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "services"
        ordering = ["-service_date", "-pk"]
        indexes = [models.Index(fields=["user", "payment_status", "-service_date"])]
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="wash_positive_amount"),
            models.CheckConstraint(
                condition=Q(payment_status="paid", payment_received_date__isnull=False)
                | Q(payment_status="pending", payment_received_date__isnull=True),
                name="wash_payment_consistency",
            ),
        ]

    @property
    def amount(self):
        from decimal import Decimal
        return Decimal(self.amount_cents).scaleb(-2)


class FinancialTransaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "income", "Receita avulsa"
        EXPENSE = "expense", "Despesa"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=7, choices=TransactionType)
    description = models.CharField(max_length=120)
    amount_cents = models.PositiveIntegerField()
    transaction_date = models.DateField()

    class Meta:
        db_table = "financial_transactions"
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="transaction_positive_amount"),
            models.CheckConstraint(
                condition=Q(transaction_type__in=["income", "expense"]),
                name="transaction_valid_type",
            ),
        ]

    @property
    def amount(self):
        from decimal import Decimal
        return Decimal(self.amount_cents).scaleb(-2)


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    failures = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
