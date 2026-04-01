# Policy-First Expense Auditor

## Features Implemented
- Receipt upload (image)
- OCR extraction (merchant, date, amount)
- Basic policy engine
- Claim classification (Approved / Flagged / Rejected)
- SQLite database storage
- View all claims

## Tech Stack
- FastAPI (Backend)
- HTML/CSS/JS (Frontend)
- Tesseract OCR

## How to Run

### Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

### Frontend
Open index.html in browser

## Sample Rules
- Amount > ₹2000 → Rejected
- Suspicious purpose → Flagged
- Otherwise → Approved
