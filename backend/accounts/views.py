from django.shortcuts import render, redirect

# --- Views que estavam causando o erro no template e URLs ---

def register_view(request):


    return render(request, 'accounts/register.html', {})


def login_view(request):

    return render(request, 'accounts/login.html', {})


def logout_view(request):

    return redirect('home')