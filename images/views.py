from logging import info
import os
import io
import math
import subprocess
import tempfile
import time
import numpy as np
from PIL import Image
from django import forms

# models for: images, cluts, and created cluts.
from .models import ImageUpload, CLUTUpload, CLUTCreator

from django.conf import settings

from django.shortcuts import get_object_or_404, redirect, render

from django.core.files import File

from django.core.files.storage import default_storage

from django.core.files.base import ContentFile

from django.contrib.sessions.models import Session

from django.core.exceptions import ValidationError

from django.utils.safestring import mark_safe

from django.core.files.base import ContentFile

from pathlib import Path

from django.views.decorators.http import require_POST


# TODO: implement ascii filter

def apply_ascii():
    pass


def filtered_images(images):

    filtered = []

    for image in images:

        image_open = Image.open(image.image)

        filter_path = os.path.join(settings.CLUT_DIR, image.film)

        filter = Image.open((filter_path))
        print(filter_path)

        if "Black and White" in filter_path:

            filtered.append(apply_filter(
                filter, image_open.convert('L'), True))

        if "ASCII" in filter_path:

            apply_ascii(image_open)

        else:

            filtered.append(apply_filter(filter, image_open))
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


# VALIDATORS

# (switches)

def validate_boolean_list_string(value):

    if not isinstance(value, str):

        raise ValidationError(
            "This field must be a string of comma-separated booleans (e.g., 'true,false,true').")

    boolean_strings = value.split(',')

    for item in boolean_strings:

        normalized_item = item.strip().lower()

        if normalized_item not in ('true', 'false', '1', '0'):

            raise ValidationError(f"'{item}' is not a valid boolean value.")


def validate_film_choice(value):

    if not isinstance(value, str):

        raise ValidationError("This field must be a string of characters.")

    if value == "Color" or value == "Black and White":

        pass  # TODO redirect back to create page


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

            print(f"File does not exist: {path}")

            return False

        with Image.open(path) as img:

            img = img.convert("RGB")

            width, height = img.size

            if width != height:

                print(f"Image is not square: {width}x{height}")

                return False

            # HaldCLUT side length must be n^3

            n = round(width ** (1 / 3))

            if n < 2 or (n ** 3) != width:

                print(f"Image is not a valid HaldCLUT size: {width}x{height}")

                return False

            # Reject one-color/near-one-color HaldCLUTs

            if not is_not_single_color(img):

                print(f"Image is essentially a single color: {width}x{height}")

                return False

        return True

    except Exception as e:

        print(f"Error validating HaldCLUT: {e}")

        return False

# FORMS


class UploadImageForm(forms.ModelForm):

    class Meta:

        model = ImageUpload

        fields = ('image', 'name', 'film')  # or list specific fields

        labels = {

            "image": "",

            "name": "File Name:",

            "film": "Film (needed):"

        }

        widgets = {

            "image": forms.ClearableFileInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'images'}),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['film'].widget.attrs['class'] = 'bold-select-box'


class UploadCLUTForm(forms.ModelForm):

    class Meta:

        model = CLUTUpload

        # or list specific fields
        fields = ('image', 'film', 'exposure', 'info',)

        labels = {

            "image": "",

            "film": mark_safe("Name of the film stock<br />(example: Fuji Superia 400):"),

            "exposure": mark_safe("Exposure in f-stops<br />(examples: -1, 0, +1, +2, -0.5):"),

            "info": "Any additional information:"

        }

        widgets = {

            "image": forms.ClearableFileInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'images'}),

            'exposure': forms.NumberInput(attrs={'class': 'no-spinners'}),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['film'].widget.attrs['class'] = 'bold-select-box'


# TODO takes one or optionally two images and extracts a CLUT from the difference between them usng extract_CLUT.sh

# if only one image is passed, it will use the default image provided as the second image to extract the CLUT from

class CreateCLUTForm(forms.ModelForm):

    class Meta:

        model = CLUTCreator

        fields = ('sample', 'identity', 'filename')  # or list specific fields

        labels = {

            "sample": "The target image (the look you want to clone):",

            "identity": "The identity image (the baseline):",

            "filename": "CLUT Filename:"

        }

        widgets = {

            "sample": forms.ClearableFileInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'images'}),

            "identity": forms.ClearableFileInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'images'}),

        }

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            if 'clut' in self.fields:

                self.fields['clut'].required = False


# VIEWS

@require_POST
def delete_image_handler(request, session_key=None, pk=None):

    # handles delete, and delete all buttons for the image list page.

    if pk is not None:

        # pk = str(pk).replace('-', '')[:8]

        print(f"Deleting image with pk: {pk} for session_key: {session_key}")

        sub_item = get_object_or_404(
            ImageUpload, session_key=session_key, pk=pk)

        sub_item.delete()

        print(f"Deleted image with pk: {pk}")

        # messages.success(ImageUpload, "Single image successfully deleted.")

    else:

        images = ImageUpload.objects.filter(session_key=session_key)
        if not key_images.exists():
            raise Http404("No images found for this session.")

        images.delete()  # Assumes on_delete=models.CASCADE in the model

        print(f"Deleted all images for key: {session_key}")

        # messages.success(request, "Parent item and all sub-items successfully deleted.")

    return redirect('images')


def delete_image(request, session_key, pk=None, name=None):

    key = session_key

    if pk == None and name == None:

        ImageUpload.objects.filter(session_key=key).delete()

    elif pk != None:

        # TODO: Add a check to ensure that the session key matches the current user's session key for security,

        # if not prompt for password

        print("not finished")

        ImageUpload.objects.filter(session_key=pk).delete()

    #     ImageUpload.objects.filter(session_key=key, pk=pk).delete()

    elif name != None:

        ImageUpload.objects.filter(session_key=key, name=name).delete()

    return redirect('key_images', session_key=key)


# TODO rename to create_and_display_images

def display_images(request, session_key=None, switches=None):
    if switches is None:
        switches = []
    raw_switches = request.GET.getlist('switches')
    switches = [val.lower() in ['true', '1', 't', 'yes']
                for val in raw_switches]

    # Grab key from GET or fall back to browser session
    key = request.GET.get('key', '')
    if not key:
        if session_key is None:
            if not request.session.session_key:
                request.session.modified = True
                request.session.save()
            key = request.session.session_key
        else:
            key = session_key

    print(f"Session Key: {key}\nSwitches: {switches}")

    if request.method == 'POST':

        # instatiate form

        form = UploadImageForm(request.POST, request.FILES)

        if form.is_valid():

            instance = form.save(commit=False)  # Don't save yet
            instance.session_key = key
            instance.save()

            # Auto-populate 'user' field with current user
            # instance.session_key = Session.objects.get(session_key=key)

            # instatiate filtered image from each image and filter pair

            for filename, file in request.FILES.items():

                name = request.FILES[filename].name

                open_image = Image.open(file)

                film_choice = form.cleaned_data['film']

                is_cleaned = os.path.exists(film_choice)

                if not is_cleaned:

                    break

                filter_path = os.path.join(settings.CLUT_DIR, film_choice)

                filter = Image.open((filter_path))

                if "Black and White" in filter_path:

                    filtered = apply_filter(
                        filter, open_image.convert('L'), True)

                else:

                    filtered = apply_filter(filter, open_image)

                filtered_byte_arr = io.BytesIO()

                # Or 'JPEG', etc.
                filtered.save(filtered_byte_arr, format='PNG')

                # Rewind to the beginning of the "file"
                filtered_byte_arr.seek(0)

                # put filtered file into db

                instance.filtered.save("filtered%s" % name, filtered_byte_arr)

            if is_cleaned:

                instance.save()

                form.save()

                # Redirect to a success page
                return redirect('key_images', session_key=key)

        else:

            print("Invalid form data:", form.errors)

            return redirect('images')  # redirect back to upload page

    key_images = ImageUpload.objects.filter(session_key=key)

    filtered = filtered_images(key_images)

    # render all images filtered if switches were not passed

    if not switches:

        for i in range(len(key_images)):

            switches.append(False)

    else:

        switches = string_to_boolean_list(switches)

    # create context and render form

    form = UploadImageForm()

    images = list(zip(key_images, filtered, switches))

    # print(list(all))

    # TODO add film context far that parses path under image.film into the name of the film filter used

    context = {'key': key,

               'images': images,

               'switches': switches,

               'form': form

               }

    return render(request, 'image.html', context)


def delete_clut(request, session_key=None, pk=None, name=None):

    key = session_key

    # TODO: Add a check to ensure that the session key matches the current user's session key for security,

    # if not prompt for password

    if pk == None and name == None:

        CLUTCreator.objects.filter(session_key=key).delete()

    elif pk != None:

        CLUTCreator.objects.filter(session_key=key, pk=pk).delete()

    elif name != None:

        CLUTCreator.objects.filter(session_key=key, name=name).delete()

    return redirect('key_images', session_key=key)


def display_cluts(request, session_key=None, print_benchmarks=True):

    key = request.GET.get('key', None)

    if key is None:

        if session_key is None:

            # make sure session key exists

            if not request.session.session_key:

                request.session.save()

            key = request.session.session_key

        else:

            key = session_key

    print(f"Session Key: {key}")

    if request.method == 'POST':

        # instatiate form

        form = CreateCLUTForm(request.POST, request.FILES)

        if form.is_valid():

            instance = form.save(commit=False)  # Don't save to DB yet

            short_id = str(instance.short_id).replace('-', '')[:8]

            filename = instance.filename

            # Auto-populate 'user' field with current user
            instance.session_key = Session.objects.get(session_key=key)

            # 1. Define paths and save uploaded files to disk safely

            sample_file = request.FILES['sample']

            identity_file = request.FILES['identity']

            # Use safe file naming to prevent path traversal issues

            sample_rel_path = f'session/{key}/generated/{short_id}/samples/{sample_file.name}'

            identity_rel_path = f'session/{key}/generated/{short_id}/identities/{identity_file.name}'

            # TODO replace with filename
            clut_rel_path = f'session/{key}/generated/{short_id}/cluts/clut.png'

            # Save uploaded files into Django's storage system

            sample_path = default_storage.save(
                sample_rel_path, ContentFile(sample_file.read()))

            identity_path = default_storage.save(
                identity_rel_path, ContentFile(identity_file.read()))

            absolute_sample_path = os.path.join(
                settings.MEDIA_ROOT, sample_path)

            absolute_identity_path = os.path.join(
                settings.MEDIA_ROOT, identity_path)

            absolute_output_path = os.path.join(
                settings.MEDIA_ROOT, clut_rel_path)

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

                subprocess.run(command, capture_output=True,
                               text=True, check=True, timeout=15)

                # 3. Calculate total elapsed time

                execution_time = time.perf_counter() - start_time

                if print_benchmarks:

                    print(
                        f"[BENCHMARK] CLUT extraction completed successfully in {execution_time:.3f} seconds.")

                if os.path.exists(absolute_output_path):

                    instance.clut = clut_rel_path

                    instance.save()

                    return redirect('cluts')

                else:

                    raise FileNotFoundError(
                        f"Bash process failed to write output.")

            except subprocess.TimeoutExpired:

                execution_time = time.perf_counter() - start_time

                if print_benchmarks:

                    print(
                        f"[BENCHMARK] CRITICAL: Script timed out and was killed after {execution_time:.3f} seconds.")

                # return redirect('error_page')

            except subprocess.CalledProcessError as e:

                execution_time = time.perf_counter() - start_time

                if print_benchmarks:

                    print(
                        f"[BENCHMARK] ERROR: Script failed after {execution_time:.3f} seconds.")

                    print(f"[BENCHMARK] Stderr output: {e.stderr}")

                # return redirect('error_page')

        else:

            print("Invalid form data:", form.errors)

            return redirect('cluts')  # TODO: redirect to error page

    else:

        form = CreateCLUTForm()

    key_cluts = CLUTCreator.objects.filter(session_key=key)

    print(len(key_cluts))

    # create context and render form - maybe unecessary

    form = CreateCLUTForm()

    context = {'key': key,

               'cluts': key_cluts,

               'form': form

               }

    # change  form into context
    return render(request, 'clut.html', context)


def upload_clut(request, session_key=None):

    # The Recommended Architecture if you want to use Celery (Asynchronous)

    # If the Bash script takes more than 2 seconds, you should implement an asynchronous pattern

    # .1 Django View Saves sample and identity using default model handling

    # .2 Django ViewCommits instance to DB with a status flag (status='processing')

    # .3 Celery TaskTriggers background task with instance.id and runs the subprocess

    # .4 FrontendRedirects user immediately to a loading page that polls the server for completion.

    key = request.GET.get('key', None)

    if key is None:

        if session_key is None:

            # make sure session key exists

            if not request.session.session_key:

                request.session.save()

            key = request.session.session_key

        else:

            key = session_key

    print(f"Session Key: {key}")

    if request.method == 'POST':

        form = UploadCLUTForm(request.POST, request.FILES)

        if form.is_valid():

            instance = form.save(commit=False)

            uploaded_file = form.cleaned_data['image']

            uploaded_file.seek(0)  # Reset file pointer

            tmp_path = None

            try:

                # 1. Write the temporary file inside the 'with' block

                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:

                    for chunk in uploaded_file.chunks():

                        tmp.write(chunk)

                    tmp_path = tmp.name

                # --- The 'with' block ends here, which safely CLOSES and flushes the file ---

                # 2. Now the file is safely closed on disk, validate it:

                if not is_haldclut(tmp_path):

                    print("Uploaded file is not a valid HaldCLUT.")

                    return redirect('cluts')  # TODO: redirect to error page

                else:

                    print("Uploaded file is a valid HaldCLUT.")

                    # 3. Save the instance ONCE (do not call form.save() again)

                    instance.save()

                    # TODO: Redirect to a success page
                    return redirect('cluts')

            finally:

                # 4. Always clean up the temporary file

                if tmp_path and os.path.exists(tmp_path):

                    os.remove(tmp_path)

                else:

                    print("Temporary file does not exist.")

        else:

            print("Invalid form data:", form.errors)

            return redirect('create_clut')

    else:

        form = UploadCLUTForm()

    return render(request, 'upload_clut.html', {'form': form})


def donate(request):

    return render(request, 'donate.html')


def about(request):

    return render(request, 'about.html')
