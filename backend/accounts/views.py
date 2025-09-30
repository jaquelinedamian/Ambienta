from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
# IMPORT NECESSÁRIO para resolver o ValueError
from django.contrib.auth.backends import ModelBackend


# ======================================================================
# 1. View de Registro (Cadastro)
# ======================================================================

def register_view(request):
    """
    Trata o formulário de criação de novo usuário (Registro).
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # CORREÇÃO: Especifica o backend
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, f"Conta criada com sucesso para {user.username}!")

            # Redireciona para o dashboard principal
            return redirect('dashboard:dashboard')
        else:
            # Se o formulário for inválido, exibe a primeira mensagem de erro
            for field, errors in form.errors.items():
                messages.error(request, f"Erro no campo {field}: {errors[0]}")

    else:
        form = UserCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


# ======================================================================
# 2. View de Login (Entrar)
# ======================================================================

def login_view(request):
    """
    Trata o formulário de login e autenticação.
    """
    if request.user.is_authenticated:
        # Se o usuário já estiver logado, redireciona para evitar re-login
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # CORREÇÃO: Especifica o backend
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, f"Bem-vindo(a), {user.username}!")

            # Ajuste de Segurança: Previne ataques de Open Redirect.
            next_url = request.GET.get('next')

            # FIX: Using the new function 'url_has_allowed_host_and_scheme'
            if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
            ):
                return redirect(next_url)

            # Se não houver 'next' ou se ele não for seguro, redireciona para o dashboard
            return redirect('dashboard:dashboard')

        else:
            messages.error(request, "Nome de usuário ou senha inválidos.")

    else:
        form = AuthenticationForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/login.html', context)


# ======================================================================
# 3. View de Logout (Sair)
# ======================================================================

def logout_view(request):
    """
    Faz o logout do usuário e redireciona.
    """
    if request.user.is_authenticated:
        username = request.user.username
        auth_logout(request)
        messages.info(request, f"Você saiu da conta ({username}).")

    # Redireciona para a página inicial (home) após o logout
    return redirect(reverse('home'))