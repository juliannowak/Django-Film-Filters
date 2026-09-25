#!/bin/bash
# Pass the graded file as $1 and the original as $2
# and the output name as $3 (without extension)
# Example: ./extract_CLUT.sh graded.tif raw.tif

POST_IMG="$1"
PRE_IMG="$2"
OUTPUT_NAME="${3%.*}.png"

# change the extension to lowercase for comparison
EXTENSION="${POST_IMG##*.}"
EXTENSION_LOWER=$(echo "$EXTENSION" | tr '[:upper:]' '[:lower:]')

GMIC_NATIVE=" png jpg jpeg gif tif tiff bmp pnm "

# Find the non native extension and convert it to PNG using ImageMagick if necessary
if [[ ! "$GMIC_NATIVE" =~ " $EXTENSION_LOWER " ]]; then
    echo "⚠️ The format .$EXTENSION_LOWER is not natively supported by G'MIC."
    echo "🔄 Converting $POST_IMG to a temporary PNG file using ImageMagick..."
    
    # Creating a temporary PNG file name based on the original file name
    TEMP_IMG="${POST_IMG%.*}_converted_tmp.png"
    
    # Use ImageMagick to convert the file to PNG
    magick "$POST_IMG" "$TEMP_IMG"
    POST_IMG="$TEMP_IMG"
fi

echo "Extracting film look from $POST_IMG..."
# blocks with wait command to not accidentally delete the temp file before gmic is done with it
gmic -input "$POST_IMG" -input "$PRE_IMG" fx_clut_from_ab 0,4,.,none,50 rm. o "$OUTPUT_NAME" -wait

#clean up
if [ -n "$TEMP_IMG" ] && [ -f "$TEMP_IMG" ]; then
    rm "$TEMP_IMG"
fi

echo "Success! Created $OUTPUT_NAME"