import pickle
import os
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def load_policy_chunks(company_id):
    """Load policy chunks from pickle file."""
    path = os.path.join(BACKEND_DIR, "policies", company_id, "policy_chunks.pkl")
    if not os.path.exists(path):
        return get_default_policy_chunks()
    with open(path, "rb") as f:
        return pickle.load(f)


def get_default_policy_chunks():
    """Return default policy rules if no company policy is uploaded."""
    return [
        "All expenses must be directly related to business activities.",
        "Employees must provide valid receipts for all claims.",
        "Any fraudulent or misleading claims will be rejected.",
        "Maximum allowable limit for meals is 2000 per day.",
        "Meals must be associated with business meetings, travel, or client interactions.",
        "Alcohol expenses are strictly NOT reimbursable.",
        "Personal dining or entertainment is not allowed.",
        "Maximum allowable limit for transport is 3000 per trip.",
        "Allowed transport includes taxi, cab, train, and airfare.",
        "Luxury transport services are not reimbursable.",
        "Local commute (home to office) is not reimbursable.",
        "Maximum allowable limit for lodging is 5000 per night.",
        "Only business travel-related accommodation is allowed.",
        "Premium or luxury hotels beyond limits are not reimbursable.",
        "Alcohol purchases are strictly prohibited.",
        "Personal entertainment (movies, parties) is not reimbursable.",
        "Expenses without valid receipts will be rejected.",
        "The receipt date must match the claimed expense date.",
        "Blurry or unreadable receipts will be flagged for review.",
        "Missing details such as amount or merchant name will lead to rejection.",
    ]


# Category keywords for matching
CATEGORY_KEYWORDS = {
    "meals": ["meal", "food", "restaurant", "lunch", "dinner", "breakfast", "cafe",
              "dining", "eat", "snack", "coffee", "tea", "catering", "canteen"],
    "transport": ["transport", "taxi", "cab", "uber", "ola", "train", "flight",
                  "airfare", "bus", "metro", "fuel", "petrol", "diesel", "toll",
                  "parking", "auto", "rickshaw", "commute", "travel"],
    "lodging": ["hotel", "lodge", "accommodation", "stay", "room", "hostel",
                "airbnb", "resort", "inn", "motel", "rent"],
    "entertainment": ["movie", "party", "concert", "event", "show", "game",
                      "club", "bar", "lounge"],
}

# Category-specific spending limits (INR)
CATEGORY_LIMITS = {
    "meals": 2000,
    "transport": 3000,
    "lodging": 5000,
    "entertainment": 0,  # not reimbursable
}

# Prohibited keywords
PROHIBITED_KEYWORDS = ["alcohol", "beer", "wine", "whiskey", "vodka", "rum",
                       "cocktail", "liquor", "spirits", "champagne", "brew"]


def detect_category(text):
    """Detect expense category from text."""
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "general"


def find_relevant_rules(company_id, text, category):
    """Find all policy rules relevant to the expense text and category."""
    chunks = load_policy_chunks(company_id)
    text_lower = text.lower()
    relevant = []

    # Category-specific keywords to search for
    search_terms = CATEGORY_KEYWORDS.get(category, []) + text_lower.split()[:5]

    for chunk in chunks:
        chunk_lower = chunk.lower()
        if any(word in chunk_lower for word in search_terms):
            if chunk.strip() and len(chunk.strip()) > 10:
                relevant.append(chunk.strip())

    if not relevant:
        relevant = ["General policy applies — all expenses must be business-related with valid receipts."]

    return relevant[:3]  # Return top 3 most relevant rules


def check_date_match(receipt_date, claimed_date):
    """Check if receipt date matches claimed expense date."""
    if not receipt_date or receipt_date == "N/A" or not claimed_date:
        return None, "Receipt date could not be verified."

    # Normalize date formats for comparison
    date_formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y",
        "%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d",
    ]

    parsed_receipt = None
    parsed_claimed = None

    for fmt in date_formats:
        if not parsed_receipt:
            try:
                parsed_receipt = datetime.strptime(receipt_date, fmt)
            except ValueError:
                continue

    for fmt in date_formats:
        if not parsed_claimed:
            try:
                parsed_claimed = datetime.strptime(claimed_date, fmt)
            except ValueError:
                continue

    if parsed_receipt and parsed_claimed:
        if parsed_receipt.date() == parsed_claimed.date():
            return True, "Receipt date matches claimed date."
        else:
            return False, f"Date mismatch: receipt shows {receipt_date}, but claimed date is {claimed_date}."

    return None, "Could not parse dates for comparison."


def check_weekend(text, receipt_date):
    """Check if expense was made on a weekend (Saturday or Sunday)."""
    date_formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d.%m.%Y"]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(receipt_date, fmt)
            if dt.weekday() >= 5:  # Saturday=5, Sunday=6
                return True, "Expense claimed on a weekend (Saturday or Sunday) — requires verification."
            break
        except ValueError:
            continue

    return False, ""


def evaluate_policy(data, purpose, company_id, claimed_date=None, username=None):
    """
    Evaluate an expense against company policy.
    Returns: (status, explanation, risk_level, policy_snippet)
    """
    text = (data.get("raw_text", "") + " " + purpose).lower()
    amount = float(data.get("amount", 0))
    receipt_date = data.get("date", "N/A")
    confidence = data.get("confidence", 100)

    # Detect category
    category = detect_category(text)

    # Find relevant policy rules
    relevant_rules = find_relevant_rules(company_id, text, category)
    policy_snippet = " | ".join(relevant_rules)

    violations = []
    flags = []

    # 1. Check OCR confidence / readability
    if confidence < 25:
        return (
            "Rejected",
            "Receipt is unreadable or too blurry. Please re-upload a clearer image.",
            "high",
            "Blurry or unreadable receipts will be flagged for review."
        )
    elif confidence < 40:
        flags.append("Low receipt quality — data may be inaccurate")

    # 2. Check for prohibited items
    for keyword in PROHIBITED_KEYWORDS:
        if keyword in text:
            return (
                "Rejected",
                f"Rejected: Alcohol/prohibited item detected ('{keyword}'). Policy states: Alcohol expenses are strictly NOT reimbursable.",
                "high",
                "Alcohol purchases are strictly prohibited. Alcohol expenses are strictly NOT reimbursable."
            )

    # 3. Check category limits using cumulative sum
    limit = CATEGORY_LIMITS.get(category)
    if limit is not None:
        if limit == 0:
            violations.append(
                f"'{category}' expenses are not reimbursable per company policy."
            )
        else:
            past_sum = 0
            date_to_check = claimed_date if claimed_date else receipt_date
            
            if username and date_to_check and date_to_check != "N/A":
                import sqlite3
                import os
                DB_PATH = os.path.join(os.path.dirname(__file__), "claims.db")
                try:
                    conn = sqlite3.connect(DB_PATH)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT amount, raw_text, purpose FROM claims WHERE username=? AND (claimed_date=? OR date=?) AND status != 'Rejected'",
                        (username, date_to_check, date_to_check)
                    )
                    rows = cursor.fetchall()
                    conn.close()
                    for row in rows:
                        past_text = (str(row["raw_text"] or "") + " " + str(row["purpose"] or "")).lower()
                        if detect_category(past_text) == category:
                            past_sum += float(row["amount"] or 0)
                except Exception:
                    pass

            total_sum = past_sum + amount
            if total_sum > limit:
                if past_sum > 0:
                    violations.append(
                        f"Cumulative {category} expenses on {date_to_check} (₹{total_sum:.0f}) exceed the daily limit of ₹{limit}. Past amount: ₹{past_sum:.0f}."
                    )
                else:
                    violations.append(
                        f"Amount ₹{amount:.0f} exceeds the {category} limit of ₹{limit}. "
                    )

    # 4. Check date match
    if claimed_date:
        date_match, date_msg = check_date_match(receipt_date, claimed_date)
        if date_match is False:
            flags.append(date_msg)

    # 5. Check weekend / contextual audit
    is_suspicious, weekend_msg = check_weekend(text, receipt_date)
    if is_suspicious:
        flags.append(weekend_msg)

    # 6. Check for missing data
    if data.get("merchant", "Unknown") == "Unknown Merchant":
        flags.append("Merchant name could not be extracted from receipt.")
    if receipt_date == "N/A":
        flags.append("Receipt date could not be extracted.")
    if amount <= 0:
        violations.append("No valid amount found on receipt.")

    # 7. Personal expense check
    personal_keywords = ["personal", "gift", "party", "movie", "entertainment"]
    for kw in personal_keywords:
        if kw in text:
            flags.append(f"Possible personal expense detected ('{kw}').")
            break

    # Determine final status
    if violations:
        explanation = "Rejected: " + "; ".join(violations)
        return "Rejected", explanation, "high", policy_snippet

    if flags:
        explanation = "Flagged: " + "; ".join(flags)
        risk = "high" if len(flags) >= 2 else "medium"
        return "Flagged", explanation, risk, policy_snippet

    return (
        "Approved",
        f"Approved: Expense of ₹{amount:.0f} for {category} is within policy limits.",
        "low",
        policy_snippet
    )