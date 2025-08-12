#!/usr/bin/env bash
set -e

# Ждём Postgres
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.5
  done
  echo "Postgres is up."
fi

# Миграции и (опц.) статика
python manage.py migrate --noinput
# если нужна статика: раскомментируй
# python manage.py collectstatic --noinput || true

# Запуск приложения
exec gunicorn authsys.wsgi:application \
    --bind 0.0.0.0:${APP_PORT:-8001} \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout ${GUNICORN_TIMEOUT:-60}