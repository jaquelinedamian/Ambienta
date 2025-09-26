# backend/Ambienta/urls.py - CÓDIGO FINAL CORRIGIDO

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Admin
    path('admin/', admin.site.urls),

    # 2. Rotas Principais: Home, Cadastro, Login, Configuração (no 'accounts.urls')
    #    Tudo na raiz, pois o seu app 'accounts' lida com a autenticação e as páginas.
    path('', include('home.urls')),

    # 🛑 AJUSTE CRÍTICO: Incluímos APENAS o seu urls.py customizado de accounts,
    # que deve conter as rotas de login, cadastro, etc.
    path('', include('accounts.urls')),

    # 3. Outros Apps com prefixos claros:
    path('dashboard/', include('dashboard.urls')),
    path('sensors/', include('sensors.urls')),

    # 🛑 REMOVIDO: Rotas duplicadas e a inclusão redundante de django.contrib.auth.urls.
]
```eof

### 🚀 Ação Final: Corrigir, Commit e Limpar Cache

1. ** Substitua ** o
conteúdo
do
seu
`backend / Ambienta / urls.py`
local
com
o
código
corrigido
acima.
2. ** Commit
e
Push: ** Envie
a
versão
corrigida
para
o
GitHub:
```bash
git
add
backend / Ambienta / urls.py
git
commit - m
"Corrige erro fatal de roteamento Ambienta/urls.py"
git
push
origin
main
```
3. ** No
Render, force
a
limpeza: ** Vá
para
o
serviço ** Ambienta **, clique
em ** Manual
Deploy **, e
escolha ** `Clear
build
cache & deploy
` **.

Essa
correção
é
a
única
maneira
de
resolver
o
erro
fatal
de
inicialização.Se
o
"Internal Server Error"
persistir
após
esta
correção, o
problema
estará
nos
novos
arquivos ** `views.py` ** ou ** `forms.py` ** (por erro de sintaxe)
e
não
mais
no
roteamento.