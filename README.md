# Django-Film-Filters
### check it out here: http://cinefilmpalette.online/

## Local Self-Hosting:
execute these statements line by line, or collapse them all (remove all comment lines and '\n' occurrences) and copy-paste the result into a bash shell.
```bash
#clone my django project repo
git clone Django-Film-Filters;
cd Django-Film-Filters;
#clone the hald-clut repo into the project and copy over the files to where they need to be.
git clone https://github.com/cedeber/hald-clut.git;
mkdir CLUT;
mkdir CLUT/Color;
mkdir CLUT/Black\ and\ White;
cp -r hald-clut/HaldCLUT/Film\ Simulation/Color/* CLUT/Color ;
cp -r hald-clut/HaldCLUT/Film\ Simulation/Black\ and\ White/* CLUT/Black\ and\ White ;
#optional, remove the hald-clut repo
rm -R hald-clut;
cd CLUT/Color;
find . -type f -exec mv -t . {} +;
rmdir */
cd ..; cd ..;
cd CLUT/Black\ and\ White
find . -type f -exec mv -t . {} +;
rmdir */
cd ..; cd ..;
#optional: if you want a donate page, remember to replace $YOUR_BTC_ADDRESS with your BTC address.
cd images/templates/ ;
sed -i 's/YOUR_BITCOIN_ADDRESS/$YOUR_BTC_ADDRESS/g' donate.html;
#repeat for other addresses ETH and LTC
#optional: if you want to leave an email
sed -i 's/YOUR_EMAIL_ADDRESS/$YOUR_EMAIL_ADDRESS/g' about.html;
cd ..; cd ..;
#install prerequisite for creating CLUTs
sudo apt install gmic
#install an environment manager and set it up for the project
sudo apt install miniconda3;
conda create -n django-environment;
conda activate django-environment;
#install requirements (TODO create requirements.txt option)
conda install django pillow numpy;
python -m pip install django-bootstrap5;
#start the server
python manage.py migrate;
python manage.py collectstatic;
python manage.py runserver;

```
## Public Hosting (on VPS or similar):
- connect it to a reverse proxy server like Nginx (using gunicorn)
- change the django secret in the settings file, and switch DEBUG=True
- remember DO NOT host with root account and disable root access when it is not needed

## GOALS:
- add password to CLUT/ImageUpload models and 
    lock changes to session behind it 
    when it's not the active one
- Docker support
- CDN ALB support
- fetch API

## Automated TODO List
- **image2ascii.py** (Line 30): write an argparse, args: input, output, width, rotate, invert, contrast, brightness
- **backend/settings.py** (Line 40): Add support for CDN or ALB or other options and default to public bucket
- **images/models.py** (Line 38): split by color and black and white, and add a separator in the choices list.
- **images/models.py** (Line 128): maybe make this not nullable, but make sure to process the file before saving the model instance and display a loading spinner while the file is being processed.
- **images/views.py** (Line 39): implement ascii filter
- **images/views.py** (Line 144): redirect back to create page
- **images/views.py** (Line 360): raise error instead
- **images/views.py** (Line 367): rename to create_and_display_images
- **images/views.py** (Line 468): add film context far that parses path under image.film into the name of the film filter used
- **images/views.py** (Line 489): raise error instead
- **images/views.py** (Line 500): Add a check to ensure that the session key matches the current user's session key for security,
- **images/views.py** (Line 604): redirect to error page
- **images/views.py** (Line 681): redirect to error page
- **images/views.py** (Line 690): Redirect to a success page
