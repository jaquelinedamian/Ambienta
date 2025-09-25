from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpRequest

def login_view(request: HttpRequest):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # Redireciona o usuário para a página do dashboard após o login
            return redirect('dashboard_view')  
        else:
            return render(request, 'accounts/login.html', {'error_message': 'Credenciais inválidas. Por favor, tente novamente.'})
    
    return render(request, 'accounts/login.html')