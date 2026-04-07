# TrueClaim — Policy-First Expense Auditor

**TrueClaim** is an AI-powered expense auditing platform that automates receipt verification and policy compliance checking for organizations. It provides a role-based interface for employees to submit expense claims and for finance auditors to review, flag, and override decisions — all driven by company-specific policy documents.

---

## The Problem

Organizations struggle with manual expense auditing — it is time-consuming, error-prone, and inconsistently enforced. Finance teams must manually cross-reference every receipt against company expense policies, check for fraudulent or duplicate claims, and verify receipt authenticity. This leads to delayed reimbursements, overlooked policy violations, and wasted auditor hours.

## The Solution

TrueClaim automates the entire expense audit pipeline using OCR and rule-based policy intelligence:

- **Automated Receipt Scanning**: Employees upload receipt images or PDFs. The system extracts merchant name, date, amount, and currency using Tesseract OCR, and provides a confidence score for each extraction.
- **Policy-First Verification**: Uploaded expense claims are automatically evaluated against the company's expense policy document. The system detects spending limit violations, prohibited items (e.g., alcohol), date mismatches, weekend claims, and personal expenses — citing the specific policy rule that was triggered.
- **Custom Policy Upload**: Finance auditors can upload their organization's expense policy as a PDF. The system parses it into rule chunks and applies it to all employees under that company, ensuring every claim is checked against the latest policy.
- **Human-in-the-Loop Overrides**: Auditors can review flagged/rejected claims on a dashboard, override the automated decision with an approval, flag, or rejection, and leave comments — with real-time notifications sent to the employee.
- **Role-Based Access**: Employees see only their claims and submission form. Auditors get a full dashboard with statistics, risk-sorted claim tables, filtering, and a settings panel to manage employees and policies.
- **Real-Time Notifications**: Employees receive instant notifications when claims are processed or overridden, with a slide-out notification panel and unread badge.

---

## Tech Stack

| Layer        | Technology                                                                 |
|--------------|----------------------------------------------------------------------------|
| **Backend**  | Python, [FastAPI](https://fastapi.tiangolo.com/)                           |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (Single Page Application)                  |
| **Database** | SQLite (via Python `sqlite3`)                                              |
| **OCR**      | [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via `pytesseract` |
| **PDF Parsing** | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/), `pdf2image`, `reportlab` |
| **Image Processing** | [Pillow (PIL)](https://pillow.readthedocs.io/)                      |
| **Server**   | [Uvicorn](https://www.uvicorn.org/) (ASGI server)                         |

---

## Setup Instructions

### Prerequisites

- **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
- **Tesseract OCR** installed on your system:
  - **Windows**: Download and install from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - **macOS**: `brew install tesseract`
  - **Linux**: `sudo apt install tesseract-ocr`

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Priyan05-dev/expense-auditor.git
cd expense-auditor
```

### Step 2 — Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 3 — Start the Backend Server

```bash
cd backend
```

```bash
uvicorn app:app --reload
```
- OR
```bash
python -m uvicorn app:app --reload
```

The API server will start at `http://127.0.0.1:8000`.

### Step 4 — Open the Frontend

Open `frontend/index.html` directly in your browser, or serve it using any local HTTP server:

```bash
# Option A: Open directly
start frontend/index.html          # Windows
open frontend/index.html           # macOS

# Option B: Using Python's built-in HTTP server
cd frontend
python -m http.server 5500
# Then open http://localhost:5500 in your browser
```

### Step 5 — Register and Use

1. Navigate to the **Register** page and create an account.
   - Choose **Employee** role to submit expense claims.
   - Choose **Finance Auditor** role to review and manage claims.
   - Use the same **Company ID** (e.g., `C101`) for both roles so they share the same organization.
2. **As an Auditor**: Go to **Settings** → upload your company's expense policy PDF. This policy will automatically apply to all employees under your company.
3. **As an Employee**: Upload a receipt image/PDF with a business purpose and expense date. The system will automatically verify it against the company policy.
4. **As an Auditor**: View all claims on the **Dashboard**, click into any claim to see details, and override the automated decision if needed.

---

## Project Structure

```
expense-auditor/
├── backend/
│   ├── app.py              # FastAPI application & API routes
│   ├── auth.py             # User registration & login
│   ├── database.py         # SQLite database initialization
│   ├── ocr.py              # Tesseract OCR receipt extraction
│   ├── policy_engine.py    # Policy evaluation & rule matching
│   ├── policy_processor.py # PDF policy parsing into rule chunks
│   ├── policies/           # Stored company policy files
│   ├── uploads/            # Uploaded receipt files
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main SPA entry point
│   ├── script.js           # Application logic & routing
│   ├── style.css           # UI styling (dark theme)
│   └── logo/               # Brand assets
├── sample_receipts/        # Example receipts for testing
└── README.md
```
