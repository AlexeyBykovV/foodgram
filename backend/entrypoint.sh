#!/bin/sh

echo 'Running migrations...'
python manage.py makemigrations
python manage.py migrate
python manage.py import_ingredients

echo 'Collecting static files...'
python manage.py collectstatic --no-input

echo 'Copying static files...'
cp -r /app/collected_static/. /backend_static/static/ 

gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi

exec "$@"