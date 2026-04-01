import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import re

def extract_receipt_data(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)

    # VERY basic extraction (good enough for demo)
    amount = re.findall(r'\d+\.\d{2}', text)
    date = re.findall(r'\d{2}/\d{2}/\d{4}', text)

    return {
        "merchant": text.split('\n')[0],
        "date": date[0] if date else "N/A",
        "amount": float(amount[-1]) if amount else 0.0, 
        "currency": "INR"
    }