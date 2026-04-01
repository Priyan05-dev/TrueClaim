import pytesseract
from PIL import Image
import re
import os
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)

    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)

    return text


def extract_receipt_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    amount = re.findall(r'[\d,]+\.\d{2}|\d+', text)
    date = re.findall(r'\d{2}/\d{2}/\d{4}', text)

    return {
        "merchant": text.split('\n')[0],
        "date": date[0] if date else "N/A",
        "amount": float(amount[-1].replace(',', '')) if amount else 0.0,
        "currency": "INR",
        "raw_text": text
    }