from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required  # Importado para proteger views
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm


def home_view(request):
    return render(request, 'home.html')


# View do Dashboard (PÚBLICA)
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html', {'user': request.user})


# View de Cadastro (PÚBLICA)
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta criada com sucesso! Faça o login.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/cadastro.html', {'form': form})


# View de Login (PÚBLICA)
class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


@login_required(login_url='/login/')
def configuracao_view(request):
    return render(request, 'accounts/configuracao.html', {'user': request.user})
