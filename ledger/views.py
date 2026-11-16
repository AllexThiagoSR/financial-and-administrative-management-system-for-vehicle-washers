from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import TransactionForm, WashForm
from .models import FinancialTransaction, LoginAttempt, Wash
from .services import confirm_payment

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_ERROR = "Não foi possível entrar. Confira os dados ou aguarde antes de tentar novamente."


class OwnerLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        identity = request.POST.get("username", "").strip().casefold()[:150]
        address = request.META.get("REMOTE_ADDR", "")
        self.attempt_key = salted_hmac("login-throttle", f"{identity}:{address}").hexdigest()
        now = timezone.now()
        LoginAttempt.objects.filter(expires_at__lte=now).delete()
        if LoginAttempt.objects.filter(pk=self.attempt_key, failures__gte=5).exists():
            form = self.get_form_class()(data={})
            form.add_error(None, LOGIN_ERROR)
            return self.render_to_response(self.get_context_data(form=form))
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        now = timezone.now()
        LoginAttempt.objects.get_or_create(pk=self.attempt_key, defaults={"expires_at": now + LOGIN_WINDOW})
        attempts = LoginAttempt.objects.filter(pk=self.attempt_key, failures__lt=5)
        attempts.filter(failures=4).update(failures=5, expires_at=now + LOGIN_WINDOW) or attempts.update(
            failures=F("failures") + 1
        )
        display_form = self.get_form_class()(data={})
        display_form.add_error(None, LOGIN_ERROR)
        return super().form_invalid(display_form)

    def form_valid(self, form):
        LoginAttempt.objects.filter(pk=self.attempt_key).delete()
        return super().form_valid(form)


@never_cache
@login_required
def wash_list(request):
    washes = Wash.objects.filter(user=request.user)
    pending = request.GET.get("status") == "pending"
    if pending:
        washes = washes.filter(payment_status=Wash.PaymentStatus.PENDING)
    page_obj = Paginator(washes, 20).get_page(request.GET.get("page"))
    return render(request, "washes/list.html", {"page_obj": page_obj, "pending": pending})


@never_cache
@login_required
def wash_create(request):
    form = WashForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        Wash.objects.create(user=request.user, amount_cents=int(data.pop("amount") * 100), **data)
        messages.success(request, "Lavagem registrada.")
        return redirect("wash_list")
    return render(request, "washes/form.html", {"form": form})


@never_cache
@login_required
@require_POST
def wash_pay(request, pk):
    washes = Wash.objects.filter(user=request.user, pk=pk)
    get_object_or_404(washes)
    if confirm_payment(washes):
        messages.success(request, "Pagamento registrado.")
    else:
        messages.info(request, "Esta lavagem já está paga.")
    if request.POST.get("status") == "pending":
        from django.urls import reverse
        return redirect(reverse("wash_list") + "?status=pending")
    return redirect("wash_list")


@never_cache
@login_required
def expense_list(request):
    expenses = FinancialTransaction.objects.filter(
        user=request.user, transaction_type=FinancialTransaction.TransactionType.EXPENSE,
    ).order_by("-transaction_date", "-pk")
    page_obj = Paginator(expenses, 20).get_page(request.GET.get("page"))
    confirmation_id = request.session.pop("confirmed_transaction", None)
    transaction = FinancialTransaction.objects.filter(
        user=request.user, pk=confirmation_id,
    ).first() if confirmation_id is not None else None
    return render(request, "finances/expenses.html", {
        "page_obj": page_obj, "transaction": transaction,
    })


@never_cache
@login_required
def transaction_create(request):
    form = TransactionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        transaction = FinancialTransaction.objects.create(
            user=request.user, amount_cents=int(data.pop("amount") * 100), **data,
        )
        request.session["confirmed_transaction"] = transaction.pk
        return redirect("expense_list")
    return render(request, "finances/form.html", {"form": form})
