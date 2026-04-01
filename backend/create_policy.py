from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("policy.pdf")
styles = getSampleStyleSheet()

content = []

policy_text = """
Company Travel & Expense Policy

1. General Guidelines
All expenses must be directly related to business activities.
Employees must provide valid receipts for all claims.
Any fraudulent or misleading claims will be rejected.

2. Meals Policy
- Maximum allowable limit for meals is 2000 per day.
- Meals must be associated with business meetings, travel, or client interactions.
- Alcohol expenses are strictly NOT reimbursable.
- Personal dining or entertainment is not allowed.

3. Transport Policy
- Maximum allowable limit for transport is 3000 per trip.
- Allowed transport includes taxi, cab, train, and airfare.
- Luxury transport services are not reimbursable.
- Local commute (home to office) is not reimbursable.

4. Lodging Policy
- Maximum allowable limit for lodging is 5000 per night.
- Only business travel-related accommodation is allowed.
- Premium or luxury hotels beyond limits are not reimbursable.

5. Prohibited Expenses
- Alcohol purchases are strictly prohibited.
- Personal entertainment (movies, parties) is not reimbursable.
- Expenses without valid receipts will be rejected.

6. Validation Rules
- The receipt date must match the claimed expense date.
- Blurry or unreadable receipts will be flagged for review.
- Missing details such as amount or merchant name will lead to rejection.

7. Approval Rules
- Expenses within limits and compliant with policy → Approved
- Minor inconsistencies → Flagged
- Policy violations → Rejected
"""

for line in policy_text.split("\n"):
    content.append(Paragraph(line, styles["Normal"]))
    content.append(Spacer(1, 10))

doc.build(content)

print("policy.pdf created successfully!")