from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import FinancialTransaction, Wash

plain_text = RegexValidator(r"^[^<>]+\Z", "Digite apenas texto, sem marcação HTML.")


def date_field(label, required=True):
    return forms.DateField(label=label, required=required,
                           widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))


class AmountForm(forms.Form):
    amount = forms.DecimalField(
        label="Valor (R$)", localize=True, max_digits=9, decimal_places=2,
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < Decimal("0.01"):
            raise ValidationError("Informe um valor maior que zero.")
        return amount


class WashForm(AmountForm):
    customer_name = forms.CharField(label="Cliente", max_length=100, validators=[plain_text])
    service_type = forms.CharField(label="Tipo de serviço", max_length=100, validators=[plain_text])
    service_date = date_field("Data da lavagem")
    payment_status = forms.ChoiceField(label="Situação do pagamento", choices=Wash.PaymentStatus.choices)
    payment_received_date = date_field("Data de recebimento", required=False)
    field_order = ["customer_name", "service_type", "service_date", "amount",
                   "payment_status", "payment_received_date"]

    def clean(self):
        data = super().clean()
        status = data.get("payment_status")
        date = data.get("payment_received_date")
        if status == Wash.PaymentStatus.PAID and not date:
            self.add_error("payment_received_date", "Informe a data de recebimento.")
        if status == Wash.PaymentStatus.PENDING and date:
            self.add_error("payment_received_date", "Deixe a data vazia para uma lavagem pendente.")
        return data


class TransactionForm(AmountForm):
    transaction_type = forms.ChoiceField(
        label="Tipo de movimentação", choices=FinancialTransaction.TransactionType.choices,
    )
    description = forms.CharField(label="Descrição", max_length=120, validators=[plain_text])
    transaction_date = date_field("Data")
    field_order = ["transaction_type", "description", "amount", "transaction_date"]
