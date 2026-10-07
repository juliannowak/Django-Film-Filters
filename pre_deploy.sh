#!/bin/bash
# This script is intended to be run before deploying or re-deploying the Django application.
# It collects static files and applies any necessary migrations and other changes.

#a function that prompts user for required information
prompt_user() {
    read -p "Enter your Bitcoin address: " YOUR_BTC_ADDRESS
    read -p "Enter your Ethereum address: " YOUR_ETH_ADDRESS
    read -p "Enter your email address (optional): " YOUR_EMAIL_ADDRESS
}

filepath="backend/settings.py";
sed -i "s|ALLOWED_HOSTS = \[]|ALLOWED_HOSTS = ['cinefilmpalette.online']|g" "$filepath";
sed -i "s/DEBUG = True/DEBUG = False/g" $filepath;
SECRET_KEY=$(openssl rand -base64 12);
echo "If the next line is blank, your secret key hasn't been changed!\n$SECRET_KEY";
sed -i "s|django-insecure|${SECRET_KEY}|g" "$filepath";
python manage.py collectstatic --noinput;
python manage.py migrate;

cd images/templates/ ;
sed -i 's/YOUR_BITCOIN_ADDRESS/$YOUR_BTC_ADDRESS/g' donate.html;
#repeat for other addresses ETH and LTC
#optional: if you want to leave an email
sed -i 's/YOUR_EMAIL_ADDRESS/$YOUR_EMAIL_ADDRESS/g' about.html;
cd ..; cd ..;
#create superuser if not exists
#restart gunicorn and reload nginx to apply changes
echo "Django application is ready for deployment."