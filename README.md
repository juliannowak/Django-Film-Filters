# Django-Film-Filters
# check it out here:
# http://138-128-247-76.cloud-xip.com/

# Local Self Hosting Instruction:
# git clone Django-Film-Filters
# cd Django-Film-Filters
# git clone hald-clut
# mkdir CLUT
# cp \hald-clut\HaldCLUT\Film Simulation\Color\* CLUT\
# cp \hald-clut\HaldCLUT\Film Simulation\Black and White\* CLUT\
# cd CLUT\Color
# find . -type f -exec mv {} . \;
# cd ..; cd ..;
# cd CLUT\Black and White
# find . -type f -exec mv {} . \;
# cd ..; cd ..;
# sudo apt install miniconda3
# conda create -n django-environment
# conda activate django-environment
# conda install django django-bootstrap5 pillow numpy
# python manage.py migrate
# python manage.py runserver

# Public Hosting:
# connect it to a reverse proxy like Nginx (using gunicorn)
# change the django secret in the settings file
# DO NOT host with root account and disable root access when it is not needed