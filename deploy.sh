#!/bin/bash
# This script is intended to be run before deploying or re-deploying the Django application.
# It collects static files and applies any necessary migrations and other changes.

# prompts the user for input if the variable is empty
prompt_if_empty() {
    local var_name="$1"
    local prompt_text="$2"

    # Check if the variable's value is empty using indirect expansion
    if [[ -z "${!var_name}" ]]; then
        read -r -p "$prompt_text: " input_val
        # Assign the input back to the original variable name
        printf -v "$var_name" '%s' "$input_val"
    fi
}

# prompts user for required information
prompt_user() {
    prompt_if_empty "BTC_ADDRESS" "Enter your Bitcoin address"
    prompt_if_empty "ETH_ADDRESS" "Enter your Ethereum address"
    prompt_if_empty "EMAIL_ADDRESS" "Enter your email address"
    prompt_if_empty "APP_NAME" "Enter your app / project name"
    prompt_if_empty "ALLOWED_HOSTS" "Enter allowed hosts / domain (comma-separated)"
}

filepath="backend/settings.py";
sed -i "s|ALLOWED_HOSTS = \[]|ALLOWED_HOSTS = ['${ALLOWED_HOSTS}']|g" "$filepath";
sed -i "s/DEBUG = True/DEBUG = False/g" $filepath;
SECRET_KEY=$(openssl rand -base64 12);
echo "If the next line is blank, your secret key hasn't been changed!\n$SECRET_KEY";
sed -i "s|django-insecure|${SECRET_KEY}|g" "$filepath";
python manage.py collectstatic --noinput;
python manage.py migrate;

cd images/templates/ ;
sed -i 's/BITCOIN_ADDRESS/$YOUR_BTC_ADDRESS/g' donate.html;
sed -i 's/ETHEREUM_ADDRESS/$YOUR_ETH_ADDRESS/g' donate.html;
#repeat for other addresses ETH and LTC
# go through all templates for these
sed -i 's/EMAIL_ADDRESS/$YOUR_EMAIL_ADDRESS/g' about.html;
sed -i 's/APP_NAME/$YOUR_APP_NAME/g' about.html;
cd ..; cd ..;

# TODO finish deploy.sh
#create superuser if not exists

#restart gunicorn and reload nginx to apply changes
sudo systemctl restart gunicorn;
sudo systemctl reload nginx;
echo "Django application is (re)deployed.\nMigrations may be required.\nPlease check the logs for any errors.";