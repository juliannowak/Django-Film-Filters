from logging import info
import os
import io
import math
import subprocess
import time
import numpy as np
from PIL import Image
from django import forms
from .models import ImageUpload, CLUTUpload, CLUTCreate
from django.conf import settings
from django.shortcuts import redirect, render
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.core.files.base import ContentFile
from pathlib import Path

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

def is_not_single_color(image: Image.Image, tolerance: int = 8, min_unique_colors: int = 10) -> bool:
    """
    Return True if the image is not essentially one solid color.
    Works for both color and grayscale HaldCLUTs.
    """
    img = image.convert("RGB")
    pixels = list(img.getdata())

    if not pixels:
        return False

    # Sample a manageable number of pixels to keep this fast
    step = max(1, len(pixels) // 20000)
    sampled = pixels[::step]

    if len(sampled) < 2:
        return False

    r = [p[0] for p in sampled]
    g = [p[1] for p in sampled]
    b = [p[2] for p in sampled]

    # If all sampled pixels are nearly identical, reject it as a single-color image
    if (
        max(r) - min(r) < tolerance
        and max(g) - min(g) < tolerance
        and max(b) - min(b) < tolerance
    ):
        return False

    # Extra sanity check: require some color diversity
    if len(set(sampled)) < min_unique_colors:
        return False

    return True

def is_haldclut(file_path: str | Path) -> bool:
    """
    Return True if the file appears to be a valid HaldCLUT image.
    Checks:
      - file exists
      - image opens successfully
      - image is square
      - side length is a perfect cube (n^3)
      - not a flat/solid image
    """
    try:
        path = Path(file_path)
        if not path.is_file():
            return False

        with Image.open(path) as img:
            img = img.convert("RGB")

            width, height = img.size
            if width != height:
                return False

            # HaldCLUT side length must be n^3
            n = round(width ** (1 / 3))
            if n < 2 or (n ** 3) != width:
                return False

            # Reject one-color/near-one-color HaldCLUTs
            if not is_not_single_color(img):
                return False

        return True

    except Exception:
        return False
#FORMS    
class UploadImageForm(forms.ModelForm):
    class Meta:
        model = ImageUpload
        fields = ('image', 'name', 'film') # or list specific fields
        labels = {
            "image" : "",
            "name": "File Name:",
            "film": "Film (needed):"
        }
        widgets = {
	        "image" : forms.ClearableFileInput(attrs={'class':'form-control form-control-lg', 'placeholder':'images' }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['film'].widget.attrs['class'] = 'bold-select-box'

class DisplayImagesForm(forms.Form):
    session_key = forms.CharField(max_length=200)
    switches_string = forms.CharField(
        label="List of boolean 'switches' (comma-separated)",
        validators=[validate_boolean_list_string]
    )

class UploadCLUTForm(forms.ModelForm):
    class Meta:
        model = CLUTUpload
        fields = ('image', 'film', 'exposure', 'info',) # or list specific fields
        labels = {
            "image" : "",
            "film": mark_safe("Name of the film stock<br />(example: Fuji Superia 400):"),
            "exposure": mark_safe("Exposure in f-stops<br />(examples: -1, 0, +1, +2, -0.5):"),
            "info": "Any additional information:"
        }
        widgets = {
            "image" : forms.ClearableFileInput(attrs={'class':'form-control form-control-lg', 'placeholder':'images' }),
            'exposure': forms.NumberInput(attrs={'class': 'no-spinners'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['film'].widget.attrs['class'] = 'bold-select-box'

#TODO takes one or optionally two images and extracts a CLUT from the difference between them usng extract_CLUT.sh
# if only one image is passed, it will use the default image provided as the second image to extract the CLUT from
class CreateCLUTForm(forms.ModelForm):
    class Meta:
        model = CLUTCreate
        fields = ('sample', 'identity', 'info') # or list specific fields
        labels = {
            "sample" : "The target image (the look you want to clone):",
            "identity" : "The identity image (the baseline):",
            "info": "Any additional information:"
        }
        widgets = {
            "sample" : forms.ClearableFileInput(attrs={'class':'form-control form-control-lg', 'placeholder':'images' }),
            "identity" : forms.ClearableFileInput(attrs={'class':'form-control form-control-lg', 'placeholder':'images' }),
        }

        def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                if 'clut' in self.fields:
                    self.fields['clut'].required = False

#VIEWS
def upload_image(request):
    if request.method == 'POST':
        #make sure session key exists
        if not request.session.session_key:
            request.session.save()
        key = request.session.session_key
        #instatiate form
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False) # Don't save yet
            instance.session_key =  Session.objects.get(session_key=key) # Auto-populate 'user' field with current user
            #instatiate filtered image from each image and filter pair
            for filename, file in request.FILES.items(): #TODO FIX filename is the prop name, name is the file name
                name = request.FILES[filename].name
                open_image = Image.open(file) #TODO rename
                film_choice = form.cleaned_data['film']
                is_cleaned = os.path.exists(film_choice)
                if not is_cleaned:
                    break
                filter_path = os.path.join(settings.CLUT_DIR, film_choice)
                filter = Image.open((filter_path))
                if "Black and White" in filter_path:
                    filtered = apply_filter(filter, open_image.convert('L'), True)
                else:
                    filtered = apply_filter(filter, open_image)
                filtered_byte_arr = io.BytesIO()
                filtered.save(filtered_byte_arr, format='PNG') # Or 'JPEG', etc.
                filtered_byte_arr.seek(0) # Rewind to the beginning of the "file"
                #put filtered file into db
                instance.filtered.save("filtered%s" % name, filtered_byte_arr)
            if is_cleaned:
                instance.save()
                form.save()
                return redirect('key_uploads', session_key=key) # Redirect to a success page
        else:
            print("Invalid form data:", form.errors)
            return redirect('images_create') #redirect back to upload page
    else:
        form = UploadImageForm()
        
    return render(request, 'imageForm.html', {'form': form})

#TODO use this instead of image_upload and clut views
def generic_image_upload(request, form_class, redirect_to):
    """
    Generic view for handling a ModelForm upload.

    Args:
        request: The Django request object.
        form_class: The form class to instantiate.
        redirect_to: A Django URL name or URL to redirect to after success.
    """
    if not request.session.session_key:
        request.session.save()

    key = request.session.session_key

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.session_key = Session.objects.get(session_key=key)
            instance.save()

            return redirect(redirect_to)

        print("Invalid form data:", form.errors)
    else:
        form = form_class()

    return render(request, "imageForm.html", {"form": form})

def display_images(request, session_key=None, switches=[]):
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
    form = UploadImageForm()
    all = list(zip(key_images, filtered, switches))
    #print(list(all))
    #TODO add film context far that parses path under image.film into the name of the film filter used
    context = {'id': key,
                'context': all, #rename to images, dont include switches
                'switches': switches,
                'form': form
                }
    return render(request, 'dashboard.html', context)

def clut(request):
    if request.method == 'POST':
        #make sure session key exists
        if not request.session.session_key:
            request.session.save()
        key = request.session.session_key
        #instatiate form
        form = UploadCLUTForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False) # Don't save yet
            instance.session_key =  Session.objects.get(session_key=key) # Auto-populate 'user' field with current user
            # TODO check if the uploaded CLUT file is actually a CLUT
            if not is_haldclut(instance.image):
                print("Uploaded file is not a valid HaldCLUT.")
                return redirect('clut') #TODO redirect to error page
            else:
                print("Uploaded file is a valid HaldCLUT.")
                instance.save()
                form.save()
                return redirect('clut') #TODO Redirect to a success page
        else:
            print("Invalid form data:", form.errors)
            return redirect('clut') #TODO redirect to error page
    else:
        form = UploadCLUTForm()
        
    return render(request, 'imageForm.html', {'form': form})

def clut_create(request, print_benchmarks=False):
    #The Recommended Architecture if you want to use Celery (Asynchronous)
    # If the Bash script takes more than 2 seconds, you should implement an asynchronous pattern
    # .1 Django View Saves sample and identity using default model handling
    # .2 Django ViewCommits instance to DB with a status flag (status='processing')
    # .3 Celery TaskTriggers background task with instance.id and runs the subprocess
    # .4 FrontendRedirects user immediately to a loading page that polls the server for completion.
    if request.method == 'POST':
        if not request.session.session_key:
            request.session.save()
        key = request.session.session_key
        
        form = CreateCLUTForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            try:
                instance.session_key = Session.objects.get(session_key=key)
            except Session.DoesNotExist:
                # Handle edge case where session expired mid-request
                return redirect('error_page')

            # 1. Define paths and save uploaded files to disk safely
            sample_file = request.FILES['sample']
            identity_file = request.FILES['identity']
            
            # Use safe file naming to prevent path traversal issues
            sample_rel_path = f'session/{key}/sample/{sample_file.name}'
            identity_rel_path = f'session/{key}/identity/{identity_file.name}'
            clut_rel_path = f'session/{key}/clut/clut.png'

            # Save uploaded files into Django's storage system
            sample_path = default_storage.save(sample_rel_path, ContentFile(sample_file.read()))
            identity_path = default_storage.save(identity_rel_path, ContentFile(identity_file.read()))
            
            absolute_sample_path = os.path.join(settings.MEDIA_ROOT, sample_path)
            absolute_identity_path = os.path.join(settings.MEDIA_ROOT, identity_path)
            absolute_output_path = os.path.join(settings.MEDIA_ROOT, clut_rel_path)
            
            os.makedirs(os.path.dirname(absolute_output_path), exist_ok=True)

            # 2. Run bash script safely using absolute paths
            command = [
                'bash',
                'extract_CLUT.sh',
                absolute_sample_path,
                absolute_identity_path,
                absolute_output_path,
            ]

             # 1. Start the high-precision timer
            start_time = time.perf_counter()

            try:
                # 2. Run the process (with a defensive 15-second timeout)
                subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
                
                # 3. Calculate total elapsed time
                execution_time = time.perf_counter() - start_time
                
                if print_benchmarks:
                    print(f"[BENCHMARK] CLUT extraction completed successfully in {execution_time:.3f} seconds.")

                if os.path.exists(absolute_output_path):
                    instance.clut = clut_rel_path
                    instance.save()
                    return redirect('clut')
                else:
                    raise FileNotFoundError(f"Bash process failed to write output.")
                    
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # Log error here (e.g., logger.error(e))
                return redirect('error_page') 
        else:
            return render(request, 'clut.html', {'form': form})
            
    else:
        form = CreateCLUTForm()
        
    return render(request, 'clut.html', {'form': form})

def display_cluts(request, session_key=None):
    if request.method == "GET":
        key = request.GET.get('key', '')

    #get the key manually if not passed
    if not session_key:
        key = request.session.session_key
    else:
        key = session_key
    
    key_cluts = CLUTCreate.objects.filter(session_key=key)
    print(len(key_cluts))
    #create context and render form
    form = CreateCLUTForm()
    context = {'id': key,
                'cluts': key_cluts,
                'form': form
            }
    #TODO refactor dashboard into a list
    return render(request, 'clut_dashboard.html', context)


def donate(request):
    return render(request, 'donate.html')

def about(request):
    return render(request, 'about.html')