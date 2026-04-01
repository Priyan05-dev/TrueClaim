def evaluate_policy(data, purpose):
    amount = data["amount"]

    # Simple demo rules
    if amount > 2000:
        return "Rejected", "Amount exceeds ₹2000 meal limit"

    if "party" in purpose.lower():
        return "Flagged", "Purpose unclear or non-business"

    return "Approved", "Within policy limits"