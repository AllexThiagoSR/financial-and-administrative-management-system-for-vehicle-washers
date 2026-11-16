from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum

from .models import FinancialTransaction, Wash


def period_bounds(period, selected_date):
    if period == "day":
        return selected_date, selected_date
    if period == "week":
        start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)
        return start, start + timedelta(days=6)
    end_day = monthrange(selected_date.year, selected_date.month)[1]
    return selected_date.replace(day=1), selected_date.replace(day=end_day)


@dataclass(frozen=True)
class FinancialReport:
    start_date: date
    end_date: date
    income: Decimal
    expenses: Decimal
    net: Decimal
    has_entries: bool


def calculate_report(user, start_date, end_date):
    period = (start_date, end_date)
    paid_washes = Wash.objects.filter(
        user=user, payment_status=Wash.PaymentStatus.PAID, payment_received_date__range=period,
    ).aggregate(total=Sum("amount_cents", default=0))["total"]
    totals = FinancialTransaction.objects.filter(
        user=user, transaction_date__range=period,
    ).aggregate(
        income=Sum("amount_cents", filter=Q(transaction_type="income"), default=0),
        expenses=Sum("amount_cents", filter=Q(transaction_type="expense"), default=0),
    )
    income = Decimal(paid_washes + totals["income"]).scaleb(-2)
    expenses = Decimal(totals["expenses"]).scaleb(-2)
    return FinancialReport(start_date, end_date, income, expenses,
                           income - expenses, bool(income or expenses))
