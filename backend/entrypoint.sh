#!/usr/bin/env bash
set -e

echo "==> [1/4] Ejecutando migraciones de base de datos..."
python manage.py migrate --no-input

echo "==> [2/4] Recolectando archivos estaticos..."
python manage.py collectstatic --no-input

echo "==> [3/4] Ejecutando seeders del sistema (idempotentes)..."
python manage.py seed_all || echo "Aviso: seed_all finalizó con observaciones, continuando inicio..."

echo "==> [4/4] Iniciando servidor web..."
PORT="${PORT:-8000}"
exec gunicorn config.wsgi:application --bind "0.0.0.0:$PORT" --workers 3 --timeout 120
