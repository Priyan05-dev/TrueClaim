import pickle

def load_policy_chunks(company_id):
    with open(f"policies/{company_id}/policy_chunks.pkl", "rb") as f:
        return pickle.load(f)

def find_relevant_rule(company_id, text):
    chunks = load_policy_chunks(company_id)
    text = text.lower()

    for chunk in chunks:
        if any(word in chunk.lower() for word in text.split()):
            return chunk.strip()

    return "General policy applies"

def evaluate_policy(data, purpose, company_id):
    text = (data["raw_text"] + " " + purpose).lower()
    amount = data["amount"]

    rule = find_relevant_rule(company_id, text)

    if "alcohol" in text:
        return "Rejected", f"Alcohol not allowed ({rule})"

    if "saturday" in text or "sunday" in text or "combo" in text:
        return "Flagged", f"Suspicious context ({rule})"

    if amount > 2000:
        return "Rejected", f"Amount exceeds limit ({rule})"

    return "Approved", f"Within policy ({rule})"