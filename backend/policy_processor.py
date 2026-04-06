import fitz
import os
import pickle

def process_policy(company_id, pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    chunks = [chunk.strip() for chunk in text.split("\n") if chunk.strip()]

    folder = f"policies/{company_id}"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/policy_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    return chunks