from django.contrib.auth.views import LogoutView
from django.urls import path

from ledger import views

urlpatterns = [
    path("entrar/", views.OwnerLoginView.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
    path("", views.wash_list, name="wash_list"),
    path("lavagens/nova/", views.wash_create, name="wash_create"),
    path("lavagens/<int:pk>/pagamento/", views.wash_pay, name="wash_pay"),
    path("movimentacoes/", views.transaction_create, name="transaction_create"),
]
