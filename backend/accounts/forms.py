# Em accounts/forms.py
from django.contrib.auth import get_user_model # Melhor forma de obter o modelo de usuário
from django.contrib.auth.forms import UserCreationForm

User = get_user_model() # Obtém o modelo User configurado (pode ser o padrão ou o customizado)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta): # Herda as configurações padrão, mais seguro
        model = User
        fields = ("username", "email") + UserCreationForm.Meta.fields
        # Não é necessário listar password1 e password2 se UserCreationForm.Meta.fields já os inclui.