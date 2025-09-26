from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required  # Importado para proteger views
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm


# ----------------------------------------------------------------------
# 1. VIEWS PÚBLICAS (NÃO PRECISAM DE LOGIN)
# ----------------------------------------------------------------------

# View da Home (PÚBLICA)
def home_view(request):
    """
    Página inicial. Acessível a todos.
    """
    return render(request, 'home.html')


# View do Dashboard (PÚBLICA)
def dashboard_view(request):
    """
    Dashboard. Acessível a todos (exibindo dados públicos ou um resumo).
    """
    return render(request, 'accounts/dashboard.html', {'user': request.user})


# View de Cadastro (PÚBLICA)
def register_view(request):
    """
    Processa o formulário de cadastro de novo usuário.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta criada com sucesso! Faça o login.')
            return redirect('accounts:login')
        # ... (lógica de erro)
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/cadastro.html', {'form': form})


# View de Login (PÚBLICA)
class LoginView(DjangoLoginView):
    """
    View de Login que usa o template accounts/login.html.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


# ----------------------------------------------------------------------
# 2. VIEWS PROTEGIDAS (APENAS ESTA PRECISA DE LOGIN)
# ----------------------------------------------------------------------

@login_required(login_url='/login/')
def configuracao_view(request):
    """
    Página de Configuração. SÓ PODE SER ACESSADA POR USUÁRIOS LOGADOS.
    """
    return render(request, 'accounts/configuracao.html', {'user': request.user})