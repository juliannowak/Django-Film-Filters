#!/bin/bash
# Pass the graded file as $1 and the original as $2
# Example: ./extract_CLUT.sh graded.tif raw.tif

POST_IMG="$1"
PRE_IMG="$2"
OUTPUT_NAME="${POST_IMG%.*}_HaldCLUT.png"
echo "Extracting film look from $POST_IMG..."
gmic "$POST_IMG" "$PRE_IMG" fx_clut_from_ab 0,4,"","",50 rm. o "$OUTPUT_NAME"
echo "Success! Created $OUTPUT_NAME"