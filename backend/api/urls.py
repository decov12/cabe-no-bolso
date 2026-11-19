from django.urls import path

from . import views

urlpatterns = [
    path("auth/cadastro/", views.CadastroView.as_view(), name="cadastro"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/eu/", views.EuView.as_view(), name="eu"),
    path("lugares/", views.LugaresView.as_view(), name="lugares"),
    path("simulacoes/", views.SimulacoesView.as_view(), name="simulacoes"),
    path("simulacoes/limite/", views.LimiteView.as_view(), name="simulacoes-limite"),
    path("simulacoes/<int:pk>/", views.SimulacaoDetalheView.as_view(), name="simulacao-detalhe"),
]
