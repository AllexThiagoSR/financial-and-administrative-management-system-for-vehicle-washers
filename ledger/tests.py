from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .forms import WashForm
from .models import FinancialTransaction, Wash
from .services import confirm_payment

PASSWORD = "test-only-river-lamp-942"
WASH = dict(customer_name="Cliente C", service_type="Lavagem simples",
            service_date="2026-11-13", amount="40,00", payment_status="pending")


class LedgerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user("owner", password=PASSWORD)
        cls.other = get_user_model().objects.create_user("other", password=PASSWORD)

    def test_wash_form_requires_positive_value_and_matching_payment_date(self):
        self.assertFalse(WashForm(dict(WASH, amount="0")).is_valid())
        self.assertFalse(WashForm(dict(WASH, payment_status="paid")).is_valid())
        self.assertFalse(WashForm(dict(WASH, payment_received_date="2026-11-13")).is_valid())
        self.assertTrue(WashForm(WASH).is_valid())

    def test_payment_rule_keeps_original_date(self):
        wash = Wash.objects.create(user=self.owner, customer_name="Cliente C", service_type="Lavagem",
                                   service_date=date(2026, 11, 13), amount_cents=4000,
                                   payment_status="pending")
        query = Wash.objects.filter(pk=wash.pk)
        self.assertEqual(confirm_payment(query, date(2026, 11, 14)), 1)
        self.assertEqual(confirm_payment(query, date(2026, 11, 15)), 0)
        wash.refresh_from_db()
        self.assertEqual(wash.payment_received_date, date(2026, 11, 14))

    def test_wash_registration_filter_and_payment(self):
        self.client.force_login(self.owner)
        self.assertRedirects(self.client.post(reverse("wash_create"), WASH), reverse("wash_list"))
        wash = Wash.objects.get(user=self.owner)
        self.assertEqual(wash.amount_cents, 4000)
        pending = reverse("wash_list") + "?status=pending"
        self.assertContains(self.client.get(pending), "Cliente C")
        payment = reverse("wash_pay", args=[wash.pk])
        self.assertEqual(self.client.get(payment).status_code, 405)
        self.assertRedirects(self.client.post(payment, {"status": "pending"}), pending)
        wash.refresh_from_db()
        first_date = wash.payment_received_date
        self.client.post(payment)
        wash.refresh_from_db()
        self.assertEqual(wash.payment_received_date, first_date)
        self.assertEqual(wash.payment_status, "paid")
        self.assertNotContains(self.client.get(pending), "Cliente C")
        self.assertContains(self.client.get(reverse("wash_list")), "Cliente C")
        self.assertFalse(FinancialTransaction.objects.exists())

    def test_owner_scope_and_csrf(self):
        self.assertRedirects(self.client.get(reverse("wash_list")), "/entrar/?next=/")
        self.client.force_login(self.owner)
        self.client.post(reverse("wash_create"), WASH)
        wash = Wash.objects.get()
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("wash_list")), "Cliente C")
        self.assertEqual(self.client.post(reverse("wash_pay", args=[wash.pk])).status_code, 404)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.owner)
        self.assertEqual(protected.post(reverse("wash_pay", args=[wash.pk])).status_code, 403)
        wash.refresh_from_db()
        self.assertEqual(wash.payment_status, "pending")

    def test_transaction_confirmation_and_invalid_input(self):
        self.client.force_login(self.owner)
        url = reverse("transaction_create")
        data = dict(transaction_type="expense", description="Produtos de limpeza",
                    amount="30,00", transaction_date="2026-11-13")
        self.assertContains(self.client.post(url, dict(data, transaction_type="unknown")), "escolha válida")
        self.assertFalse(FinancialTransaction.objects.exists())
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Movimentação registrada")
        self.assertContains(response, "Produtos de limpeza")
        self.assertEqual(FinancialTransaction.objects.get(user=self.owner).amount_cents, 3000)
        self.assertNotContains(self.client.get(url), "Movimentação registrada")

    def test_login_throttling_and_logout(self):
        url = reverse("login")
        for _ in range(5):
            self.assertContains(self.client.post(url, {"username": "owner", "password": "wrong"}),
                                "Não foi possível entrar")
        self.assertContains(self.client.post(url, {"username": "owner", "password": PASSWORD}),
                            "Não foi possível entrar")
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(url, {"username": "owner", "password": PASSWORD},
                                    REMOTE_ADDR="192.0.2.10")
        self.assertRedirects(response, reverse("wash_list"))
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), url)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(self.owner.password.startswith("pbkdf2_sha256$"))
