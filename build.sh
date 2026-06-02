#!/usr/bin/env bash
# build.sh — Django backend no Render
set -o errexit

echo "==> Instalando dependências Python..."
pip install -r requirements.txt

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "==> Aplicando migrações..."
python manage.py migrate

echo "==> Criando superusuário se não existir..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='vanderson').exists():
    User.objects.create_superuser('vanderson', 'vanderson0511@gmail.com', 'vanderson')
    print('Superusuário criado.')
else:
    print('Superusuário já existe.')
"

echo "==> Build concluído!"