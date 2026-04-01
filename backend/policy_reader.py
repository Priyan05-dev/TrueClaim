import fitz  # PyMuPDF

def load_policy_text(pdf_path="policy.pdf"):
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    return text