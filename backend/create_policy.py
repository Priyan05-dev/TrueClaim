from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("policy_document.pdf")
styles = getSampleStyleSheet()

content = []

policy_text = """
TrueClaim Corporation - Global Corporate Travel & Expense Policy

1. Introduction & General Scope
This document outlines the standard guidelines and allowable limits for all business-related travel and entertainment expenses incurred by employees of TrueClaim Corporation. All expenses must be strictly necessary, reasonable, and directly related to official business activities. Valid documentation and itemized receipts are required for all submitted claims. Fraudulent, non-compliant, or misleading claims will result in immediate rejection and potential disciplinary action.

2. Meals and Client Entertainment
- The maximum allowable reimbursement limit for daily meals is set at 2000 INR per day.
- Meals must be exclusively associated with active business meetings, official travel, or client interactions.
- Alcohol and related expenses are strictly NOT reimbursable under any circumstances.
- Personal dining, solitary entertainment, or meals unrelated to specific business purposes are not allowed.
- Single-person meal expenses claimed during weekend team-building events will be flagged as highly suspicious and require secondary verification.

3. Transportation and Ground Travel
- The maximum allowable limit for transportation is 3000 INR per business trip.
- Approved transportation methods include taxi services, corporate cabs, regional trains, and economy airfare.
- Premium or luxury transport services (e.g., limousines, premium-class upgrades) are explicitly not reimbursable.
- Standard daily local commute expenses (travel strictly between an employee's home and their primary office location) are not reimbursable.

4. Lodging and Accommodations
- The maximum allowable limit for hotel and lodging is 5000 INR per night.
- Lodging is solely permitted for overnight stays deemed necessary for verified business travel.
- Premium, five-star, or luxury hotel accommodations exceeding the nightly spending threshold are prohibited and the excess will not be reimbursed.

5. Strictly Prohibited Expenses
The following items and services will not be reimbursed and will cause the claim to be automatically rejected:
- Alcohol, beer, wine, whiskey, vodka, rum, cocktails, liquor, spirits, champagne, or any alcoholic brews.
- Personal entertainment (including but not limited to movies, private parties, concerts, private events, club passes, bar tabs, and lounge access).
- Any expense completely lacking a valid, itemized receipt.

6. Required Documentation and Validation Rules
- An itemized, legible, and completely valid receipt must accompany every expense line item.
- The receipt transaction date must exactly match the claimed expense date on the report.
- Blurry, unreadable, or intentionally obfuscated receipts will be instantly flagged for manual audit review.
- Missing critical data details on the receipt, such as the total amount or the explicit merchant name, will directly lead to claim rejection.

7. Audit and Approval Matrix
- Approved: Expenses strictly within limits, highly confident receipt OCR reads, and entirely compliant with policy rules.
- Flagged: Claims containing minor data inconsistencies, dates that mismatch, lower receipt quality, or weekend anomalies. Requires manual Auditor input.
- Rejected: Claims directly violating limits, involving explicitly prohibited items (e.g., alcohol), or completely failing validation compliance.
"""

for line in policy_text.split("\n"):
    content.append(Paragraph(line, styles["Normal"]))
    content.append(Spacer(1, 10))

doc.build(content)

print("policy.pdf created successfully!")