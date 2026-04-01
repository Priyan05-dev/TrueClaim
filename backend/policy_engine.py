from policy_reader import load_policy_text

policy_text = load_policy_text()

def find_relevant_rule(category):
    lines = policy_text.lower().split("\n")

    for line in lines:
        if category in line:
            return line.strip()

    return "General policy applies"


def evaluate_policy(data, purpose):
    amount = data["amount"]
    text = (data["raw_text"] + " " + purpose).lower()

    if "saturday" in text or "sunday" in text or "combo" in text:
        return "Flagged", "Flagged: Suspicious context detected in receipt"
    
    # Detect category
    if "restaurant" in text or "food" in text or "lunch" in text:
        category = "meals"
        limit = 2000
    elif "taxi" in text or "uber" in text:
        category = "transport"
        limit = 3000
    else:
        category = "general"
        limit = 2500

    rule = find_relevant_rule(category)

    if "alcohol" in text:
        return "Rejected", f"Rejected: Alcohol not allowed as per policy ({rule})"

    if amount > limit:
        return "Rejected", f"Rejected: Amount exceeds limit ({rule})"

    if "party" in purpose.lower():
        return "Flagged", f"Flagged: Suspicious purpose ({rule})"

    return "Approved", f"Approved: Within limits ({rule})"