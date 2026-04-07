import pytesseract
from PIL import Image
import re
import os
from pdf2image import convert_from_path

# Configurable Tesseract path — check env var first, then fallback to common install paths
_tesseract_paths = [
    os.environ.get("TESSERACT_CMD", ""),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]

for _path in _tesseract_paths:
    if _path and os.path.isfile(_path):
        pytesseract.pytesseract.tesseract_cmd = _path
        break
else:
    # Fallback: let pytesseract try to find it on PATH
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        # Hard fallback
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def get_ocr_confidence(image):
    """Get average OCR confidence score from an image."""
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data["conf"] if int(c) > 0]
        if confidences:
            return sum(confidences) / len(confidences)
    except Exception:
        pass
    return 0.0


def extract_text_from_image(image_path):
    """Extract text and confidence from a single image."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    confidence = get_ocr_confidence(img)
    return text, confidence


def extract_text_from_pdf(pdf_path):
    """Extract text and confidence from a PDF (converts pages to images)."""
    try:
        images = convert_from_path(pdf_path)
    except Exception:
        # If poppler is not installed, try PyMuPDF as fallback
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text, 50.0  # default confidence for text-based PDFs

    text = ""
    confidences = []
    for img in images:
        page_text = pytesseract.image_to_string(img)
        page_conf = get_ocr_confidence(img)
        text += page_text
        confidences.append(page_conf)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return text, avg_confidence


def detect_currency(text):
    """Detect currency from receipt text."""
    currency_patterns = [
        (r"[₹]|INR|Rs\.?|Rupees?", "INR"),
        (r"[$]|USD|US\s*Dollars?", "USD"),
        (r"[£]|GBP|Pounds?", "GBP"),
        (r"[€]|EUR|Euros?", "EUR"),
    ]
    for pattern, currency in currency_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return currency
    return "INR"  # default


def extract_dates(text):
    """Extract dates from text using multiple format patterns."""
    date_patterns = [
        r"\d{2}/\d{2}/\d{4}",      # DD/MM/YYYY
        r"\d{2}-\d{2}-\d{4}",      # DD-MM-YYYY
        r"\d{4}-\d{2}-\d{2}",      # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{2}",      # DD/MM/YY
        r"\d{2}\.\d{2}\.\d{4}",    # DD.MM.YYYY
        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}",  # 1 Jan 2024
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]
    return "N/A"


def extract_amount(text):
    """Extract the most likely total amount from receipt text."""
    # Look for "Total" line first
    total_pattern = re.findall(
        r"(?:total|grand\s*total|amount\s*due|net\s*amount|balance)\s*[:\s]*[₹$£€]?\s*([\d,]+\.?\d*)",
        text, re.IGNORECASE
    )
    if total_pattern:
        try:
            return float(total_pattern[-1].replace(",", ""))
        except ValueError:
            pass

    # Fallback: find all amounts and pick the largest
    amounts = re.findall(r"[\d,]+\.\d{2}", text)
    if amounts:
        try:
            return max(float(a.replace(",", "")) for a in amounts)
        except ValueError:
            pass

    # Last resort: any number
    amounts = re.findall(r"\d+", text)
    if amounts:
        try:
            return float(amounts[-1])
        except ValueError:
            pass

    return 0.0


def extract_merchant(text):
    """Extract merchant name — typically the first non-empty line."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        # Take the first meaningful line (skip very short lines like "---")
        for line in lines[:3]:
            if len(line) > 2 and not line.startswith("-"):
                return line
    return "Unknown Merchant"


def extract_receipt_data(file_path):
    """Main extraction function — returns structured data with confidence."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text, confidence = extract_text_from_pdf(file_path)
    else:
        text, confidence = extract_text_from_image(file_path)

    # Determine if receipt is readable
    is_readable = confidence >= 40.0
    confidence_warning = None

    if confidence < 25.0:
        confidence_warning = "Receipt appears to be very blurry or unreadable. Please upload a clearer image."
    elif confidence < 40.0:
        confidence_warning = "Receipt quality is low. Some data may be inaccurate. Consider re-uploading."
    elif confidence < 60.0:
        confidence_warning = "Receipt quality is moderate. Please verify the extracted data."

    return {
        "merchant": extract_merchant(text),
        "date": extract_dates(text),
        "amount": extract_amount(text),
        "currency": detect_currency(text),
        "raw_text": text,
        "confidence": round(confidence, 1),
        "is_readable": is_readable,
        "confidence_warning": confidence_warning,
    }