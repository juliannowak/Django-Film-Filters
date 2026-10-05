print("working...")

import photos
import PIL
import ui
import console

#11 character ascii list ordered from darkest to lifgtest
ASCII_TABLE = [ '@', '#', '$', '%', '?', '*',  '+', ';', ':', ',', '.' ]

def rotate(image, angle):
	for x in range(0,angle):
		image.rotate(x)

def resize(image, width2):
	width, height = image.size
	ratio = (height / width)
	height2 = int(ratio * width2 * 0.30)
	return image.resize((width2,height2))
	
def process(image):
	grayscale = image.convert('L')
	return grayscale
	
def imgToAscii(image):
	pixels = image.getdata()
	chars = "".join([ASCII_TABLE[pixel//25] for pixel in pixels])
	return chars

#TODO write an argparse, args: input, output, width, rotate, invert, contrast, brightness

#get image
#pickPhoto = photos.pick_asset(title='Pick some assets', multi=False)
#img = pickPhoto.get_image()

#asciiData = imgToAscii(process(resize(img, SIZE)))

#format
#pixelCount = len(asciiData)
#asciiImg = "\n".join([asciiData[index:(index+SIZE)] for index in range(0,pixelCount,SIZE)])

#print(asciiImg)
