#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py ensure_superuser_from_env
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --timeout ${GUNICORN_TIMEOUT:-60}
