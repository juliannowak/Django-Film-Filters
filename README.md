# Django-Film-Filters
### check it out here: http://138-128-247-76.cloud-xip.com/

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
rm -R hald-clut
cd CLUT/Color;
find . -type f -exec mv -t . {} +;
rmdir */
cd ..; cd ..;
cd CLUT/Black\ and\ White
find . -type f -exec mv -t . {} +;
rmdir */
cd ..; cd ..;
#optional: if you want a donate page, remember to replace YOUR_ADDRESS with your BTC address.
cd images/templates/ ;
git clone https://github.com/nstevens1040/btcdonate.git;
sed -i 's/3NHxJ9j1hBxqQGM9BNWXE9j1QLxxikhpGe/YOUR_ADDRESS/g' btcdonate/index.html;
cd ..; cd ..;
#install an environment manager and set it up for the project
sudo apt install miniconda3;
conda create -n django-environment;
conda activate django-environment;
#install requirements (TODO create requirements.txt option)
conda install django pillow numpy;
python -m pip install django-bootstrap5;
#start the server
python manage.py migrate;
python manage.py runserver;

```
## Public Hosting (on VPS or similar):
- connect it to a reverse proxy server like Nginx (using gunicorn)
- change the django secret in the settings file, and switch DEBUG=True
- remember DO NOT host with root account and disable root access when it is not needed

## TODOs:
- BIG UI CHANGE INCOMING: move from page refreshes to AJAX