from datetime import timezone
import math
import os
import io
import numpy as np
from PIL import Image
from django import forms
from django.shortcuts import render
from django.contrib.sessions.models import Session
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import ImageUpload

#BUGS
#session key not found on first upload attempt
#uploads from dashboard don't work
#Color in film choices is a valid field

def filtered_images(images):
    filtered = []
    for image in images:
        open_image = Image.open(image.image) #TODO rename
        filter_path = os.path.join(settings.CLUT_DIR, image.film)
        filter = Image.open((filter_path))
        print(filter_path)
        if "Black and White" in filter_path:
            filtered.append(apply_filter(filter, open_image.convert('L'), True))
        else:
            filtered.append(apply_filter(filter, open_image))
    return filtered
    
def apply_filter(hald_img, img, is_monochrome=False):
    hald_w, hald_h = hald_img.size
    img_w, img_h = img.size
    clut_size = int(round(math.pow(hald_w, 1/3)))
    # We square the clut_size because a 12-bit HaldCLUT has the same amount of information as a 144-bit 3D CLUT
    scale = (clut_size * clut_size - 1) / 255
    # Convert the PIL image to numpy array
    img = np.asarray(img)
    if not is_monochrome:
        # We are reshaping to (144 * 144 * 144, 3) - it helps with indexing
        hald = np.asarray(hald_img)
        hald_img = np.asarray(hald_img).reshape(clut_size ** 6, 3)
        # Figure out the 3D CLUT indexes corresponding to the pixels in our image
        clut_r = np.rint(img[:, :, 0] * scale).astype(int)
        clut_g = np.rint(img[:, :, 1] * scale).astype(int)
        clut_b = np.rint(img[:, :, 2] * scale).astype(int)
        filtered_image = np.zeros((img_h, img_w, 3))
        # Convert the 3D CLUT indexes into indexes for our HaldCLUT numpy array and copy over the colors to the new image
        ndarr = clut_r + clut_size ** 2 * clut_g + clut_size ** 4 * clut_b
        filtered_image[:, :] = hald_img[ndarr]
        filtered_image = Image.fromarray(filtered_image.astype('uint8'), 'RGB')
    else:
        hald_img = np.asarray(hald_img).reshape(clut_size ** 6)
        clut_grey = np.rint(img[:, :] * scale).astype(int)
        filtered_image = np.zeros((img.shape))
        filtered_image[:, :] = hald_img[clut_grey]
        filtered_image = Image.fromarray(filtered_image.astype('uint8'), 'L')
    return filtered_image

def string_to_boolean_list(str):
    return [s.strip().lower() == "true" for s in str.split(',')]

#VALIDATORS
#(switches)
def validate_boolean_list_string(value):
    if not isinstance(value, str):
        raise ValidationError("This field must be a string of comma-separated booleans (e.g., 'true,false,true').")
    
    boolean_strings = value.split(',')
    
    for item in boolean_strings:
        normalized_item = item.strip().lower()
        if normalized_item not in ('true', 'false', '1', '0'):
            raise ValidationError(f"'{item}' is not a valid boolean value.")

def validate_film_choice(value):
    if not isinstance(value, str):
        raise ValidationError("This field must be a string of characters.")
    
    if value == "Color" or value == "Black and White":
        pass #TODO redirect back to create page

#FORMS    
class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageUpload
        fields = ('image', 'name', 'film') # or list specific fields
        labels = {
            "image" : "Image:",
            "name": "Name (optional, just to keep record of original file name):",
            "film": "Film (manadatory):"
        }
        widgets = {
	        "image" : forms.ClearableFileInput(attrs={'class':'form-control form-control-lg', 'placeholder':'images' }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['film'].widget.attrs['class'] = 'bold-select-box'

class DashboardForm(forms.Form):
    session_key = forms.CharField(max_length=200)
    switches_string = forms.CharField(
        label="List of boolean 'switches' (comma-separated)",
        validators=[validate_boolean_list_string]
    )

#VIEWS  
# TODO rename to successImageUpload
def uploadSuccess(request, context):
    return render(request, 'uploadSuccess.html', context)

# TODO rename to createImageUpload / create_image_upload
def createImageForm(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False) # Don't save yet
            if not request.session.session_key:
                request.session.save()
            key = request.session.session_key
            instance.session_key =  Session.objects.get(session_key=key) # Auto-populate 'user' field with current user
            for filename, file in request.FILES.items(): #TODO FIX filename is the prop name, name is the file name
                name = request.FILES[filename].name
                open_image = Image.open(file) #TODO rename
                filter_path = os.path.join(settings.CLUT_DIR, form.cleaned_data['film'])
                filter = Image.open((filter_path))
                if "Black and White" in filter_path:
                    print("yo")
                    filtered = apply_filter(filter, open_image.convert('L'), True)
                else:
                    print("no")
                    filtered = apply_filter(filter, open_image)
                filtered_byte_arr = io.BytesIO()
                filtered.save(filtered_byte_arr, format='PNG') # Or 'JPEG', etc.
                filtered_byte_arr.seek(0) # Rewind to the beginning of the "file"
                #put filtered file into db
                instance.filtered.save("filtered%s" % name, filtered_byte_arr)
            instance.save()
            form.save()
            return uploadSuccess(request, {'id': key}) # Redirect to a success page
    else:
        form = ImageUploadForm()
        return render(request, 'imageForm.html', {'form': form})

# TODO rename to displayImageDashboard
def image_dashboard(request, session_key=None, switches=[]):
    if request.method == "GET":
        key = request.GET.get('key', '')
        switches = request.GET.get('switches', [])

    #get the key manually if not passed
    if not session_key:
        key = request.session.session_key
    else:
        key = session_key
    
    key_images = ImageUpload.objects.filter(session_key=key)
    filtered = filtered_images(key_images)

    #render all images filtered if switches were not passed
    if not switches:
        for i in range(len(key_images)):
            switches.append(False)
    else:
        switches = string_to_boolean_list(switches)
        
    #create context and render form
    form = ImageUploadForm()
    all = list(zip(key_images, filtered, switches))
    #print(list(all))
    #TODO add film context far that parses path under image.film into the name of the film filter used
    context = {'id': key,
                'context': all, #rename to images, dont include switches
                'switches': switches,
                'form': form
                }
    return render(request, 'single.html', context)

# TODO a script that auto cleans up database
# def clean_up_old(): #by date arguement
#     images = ImageUpload.objects.all
#     for image in images:
#         if image.date_created < date:
#             #remove from DB
#             pass