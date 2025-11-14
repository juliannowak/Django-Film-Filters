# Django-Film-Filters
## check it out here: http://138-128-247-76.cloud-xip.com/

# Local Self Hosting Instruction:
```bash
#clone my django project repo
git clone Django-Film-Filters
cd Django-Film-Filters
#clone the hald-clut repo into the project and copy over the files to where they need to be.
git clone hald-clut
mkdir CLUT
cp \hald-clut\HaldCLUT\Film Simulation\Color\* CLUT\
cp \hald-clut\HaldCLUT\Film Simulation\Black and White\* CLUT\
cd CLUT\Color
find . -type f -exec mv {} . \;
cd ..; cd ..;
cd CLUT\Black and White
find . -type f -exec mv {} . \;
cd ..; cd ..;
#install an environment manager and set it up for the project
sudo apt install miniconda3
conda create -n django-environment
conda activate django-environment
#install requirements (TODO create requirements.txt option)
conda install django django-bootstrap5 pillow numpy
#start the server
python manage.py migrate
python manage.py runserver

```
# Public Hosting:
- connect it to a reverse proxy like Nginx (using gunicorn)
-  change the django secret in the settings file
- DO NOT host with root account and disable root access when it is not needed
