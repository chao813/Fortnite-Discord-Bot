import os

import pytesseract
import easyocr
import requests
from PIL import Image
from urllib.request import Request, urlopen

# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

async def convert_screenshot(image_url):
    req = Request(
        url=image_url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    image = urlopen(req).read()

    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image)
    confidence_percent = 0
    if result != []:
        image_text = result[0][1]
        confidence_percent = result[0][2] * 100
            
    if confidence_percent < 50:
        image_text = pytesseract.image_to_string(image)

    return image_text

