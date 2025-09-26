from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Rotas PÚBLICAS:
    path('', views.home_view, name='home'),  # Home (Pública)
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Dashboard (Pública)
    path('cadastro/', views.register_view, name='cadastro'),  # Cadastro (Pública)
    path('login/', views.LoginView.as_view(), name='login'),  # Login (Pública)
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Rota PROTEGIDA:
    path('configuracao/', views.configuracao_view, name='configuracao'),  # AGORA SÓ ESTA EXIGE LOGIN
]