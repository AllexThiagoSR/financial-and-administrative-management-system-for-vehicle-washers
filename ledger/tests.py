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
        self.assertNotContains(self.client.get(reverse("expense_list")), "Movimentação registrada")

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

    def test_pending_pagination_preserves_filter_and_owner_scope(self):
        def wash(owner, name, status="pending"):
            return Wash(user=owner, customer_name=name, service_type="Lavagem",
                        service_date=date(2026, 11, 13), amount_cents=1000,
                        payment_status=status,
                        payment_received_date=date(2026, 11, 13) if status == "paid" else None)

        Wash.objects.bulk_create(
            [wash(self.owner, f"Cliente {index}") for index in range(21)]
            + [wash(self.owner, "Lavagem recebida", "paid"), wash(self.other, "Outro titular")]
        )
        self.client.force_login(self.owner)
        url = reverse("wash_list")
        response = self.client.get(url, {"status": "pending"})
        self.assertEqual(len(response.context["page_obj"]), 20)
        self.assertContains(response, "page=2&amp;status=pending")
        self.assertNotContains(response, "Lavagem recebida")
        self.assertNotContains(response, "Outro titular")
        second = self.client.get(url, {"status": "pending", "page": 2})
        self.assertEqual(len(second.context["page_obj"]), 1)
        self.assertContains(second, "Cliente 0")

    def test_expense_history_filters_by_type_and_owner(self):
        url = reverse("expense_list")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(url), "Nenhuma despesa registrada")
        for user, kind, description in (
            (self.owner, "expense", "Materiais"),
            (self.owner, "income", "Receita de teste"),
            (self.other, "expense", "Despesa de outra conta"),
        ):
            FinancialTransaction.objects.create(
                user=user, transaction_type=kind, description=description,
                amount_cents=5000, transaction_date=date(2026, 11, 13),
            )
        response = self.client.get(url)
        self.assertContains(response, "Materiais")
        self.assertNotContains(response, "Receita de teste")
        self.assertNotContains(response, "Despesa de outra conta")
        response = self.client.post(reverse("transaction_create"), {
            "transaction_type": "income", "description": "Receita avulsa de teste",
            "amount": "20,00", "transaction_date": "2026-11-13",
        }, follow=True)
        self.assertContains(response, "Receita avulsa de teste")
        self.assertNotContains(self.client.get(url), "Receita avulsa de teste")

    def test_report_uses_receipt_date_and_owner_scope(self):
        self.client.force_login(self.owner)
        for owner, status, received in (
            (self.owner, "paid", date(2026, 11, 8)),
            (self.owner, "paid", date(2026, 11, 15)),
            (self.owner, "pending", None),
            (self.other, "paid", date(2026, 11, 14)),
        ):
            Wash.objects.create(
                user=owner, customer_name="Cliente teste", service_type="Lavagem",
                service_date=date(2026, 11, 7), amount_cents=5000,
                payment_status=status, payment_received_date=received,
            )
        for kind, cents in [("income", 2000), ("expense", 3000)]:
            FinancialTransaction.objects.create(
                user=self.owner, transaction_type=kind, description="Teste",
                amount_cents=cents, transaction_date=date(2026, 11, 14),
            )
        url = reverse("financial_report")
        result = self.client.get(url, {"period": "week", "date": "2026-11-13"}).context["result"]
        self.assertEqual((result.start_date, result.end_date), (date(2026, 11, 8), date(2026, 11, 14)))
        self.assertEqual((result.income, result.expenses, result.net), (70, 30, 40))
        result = self.client.get(url, {"period": "day", "date": "2026-11-14"}).context["result"]
        self.assertEqual(result.net, -10)
        result = self.client.get(url, {"period": "month", "month": "2024-02"}).context["result"]
        self.assertEqual(result.end_date, date(2024, 2, 29))
        self.assertFalse(result.has_entries)
        self.assertIsNone(self.client.get(url, {"period": "month", "month": "2024-13"}).context["result"])

    def test_week_can_cross_year_boundary(self):
        from .reports import period_bounds

        self.assertEqual(period_bounds("week", date(2027, 1, 1)),
                         (date(2026, 12, 27), date(2027, 1, 2)))
