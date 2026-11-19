#!/usr/bin/env bash
# Build do backend no Render: roda a cada deploy, dentro de backend/.
set -o errexit  # para no primeiro erro, para o deploy não subir pela metade

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
