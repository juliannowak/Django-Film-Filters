#!/bin/bash
# This script is intended to be run before deploying the Django application.
# It collects static files and applies any necessary migrations and other changes.

filepath="backend/settings.py"
sed -i "s|ALLOWED_HOSTS = \[]|ALLOWED_HOSTS = ['67.217.243.109', 'cinefilmpalette.online', 'www.cinfilmpalette.online']|g" "$filepath"
sed -i "s/DEBUG = True/DEBUG = False/g" $filepath
SECRET_KEY=$(openssl rand -base64 12)
sed -i "s/django-insecure/${SECRET_KEY}/g" $filepath
python manage.py collectstatic --noinput
python manage.py migrate
#create superuser if not exists
#restart gunicorn and reload nginx to apply changes
echo "Django application is ready for deployment."