from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import sqlite3
from datetime import datetime

from ocr import extract_receipt_data
from policy_engine import evaluate_policy
from policy_processor import process_policy
from database import init_db, get_db, DB_PATH

from auth import register_user, login_user

app = FastAPI(title="Policy-First Expense Auditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()


# ──────────────────────────────────────────
# Auth & User endpoints
# ──────────────────────────────────────────

@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    company_id: str = Form(...)
):
    register_user(username, password, role, company_id)
    return {"message": "User registered"}


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = login_user(username, password)

    if not user:
        return {"error": "Invalid credentials"}

    return {
        "username": user[1],
        "role": user[3],
        "company_id": user[4]
    }


@app.get("/employees")
def get_employees(company_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, role FROM users WHERE company_id=? AND role='employee' ORDER BY username ASC", 
        (company_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"id": row["id"], "username": row["username"], "role": row["role"]} for row in rows]


# ──────────────────────────────────────────
# Policy upload
# ──────────────────────────────────────────

@app.post("/upload_policy")
async def upload_policy(company_id: str = Form(...), file: UploadFile = File(...)):
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(backend_dir, "policies", company_id)
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, "policy.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_policy(company_id, file_path)

    return {"message": "Policy uploaded successfully"}


# ──────────────────────────────────────────
# Receipt upload & claim creation
# ──────────────────────────────────────────

@app.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    purpose: str = Form(...),
    company_id: str = Form(...),
    username: str = Form(...),
    claimed_date: str = Form("")
):
    # Save the uploaded file
    safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract data via OCR
    data = extract_receipt_data(file_path)

    # Evaluate against policy
    status, explanation, risk_level, policy_snippet = evaluate_policy(
        data, purpose, company_id, claimed_date, username
    )

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO claims (
        company_id, username, merchant, date, claimed_date,
        amount, currency, purpose, status, explanation,
        risk_level, policy_snippet, receipt_path,
        ocr_confidence, raw_text
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company_id,
        username,
        data["merchant"],
        data["date"],
        claimed_date,
        data["amount"],
        data["currency"],
        purpose,
        status,
        explanation,
        risk_level,
        policy_snippet,
        safe_filename,
        data["confidence"],
        data["raw_text"]
    ))

    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Create notification for the employee
    _create_notification(
        username,
        claim_id,
        f"Your expense claim #{claim_id} for ₹{data['amount']:.0f} has been {status.lower()}.",
        "success" if status == "Approved" else ("warning" if status == "Flagged" else "error")
    )

    return {
        "id": claim_id,
        **data,
        "status": status,
        "explanation": explanation,
        "risk_level": risk_level,
        "policy_snippet": policy_snippet,
    }


# ──────────────────────────────────────────
# Claims endpoints
# ──────────────────────────────────────────

@app.get("/claims")
def get_claims(role: str = "", username: str = "", company_id: str = ""):
    conn = get_db()
    cursor = conn.cursor()

    if role == "company":
        cursor.execute(
            "SELECT * FROM claims WHERE company_id=? ORDER BY "
            "CASE risk_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, "
            "created_at DESC",
            (company_id,)
        )
    elif username:
        cursor.execute(
            "SELECT * FROM claims WHERE username=? ORDER BY created_at DESC",
            (username,)
        )
    else:
        cursor.execute(
            "SELECT * FROM claims ORDER BY "
            "CASE risk_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, "
            "created_at DESC"
        )

    rows = cursor.fetchall()
    conn.close()

    # Convert Row objects to dicts
    claims = []
    for row in rows:
        claims.append({
            "id": row["id"],
            "company_id": row["company_id"],
            "username": row["username"],
            "merchant": row["merchant"],
            "date": row["date"],
            "claimed_date": row["claimed_date"],
            "amount": row["amount"],
            "currency": row["currency"],
            "purpose": row["purpose"],
            "status": row["override_status"] or row["status"],
            "original_status": row["status"],
            "explanation": row["explanation"],
            "risk_level": row["risk_level"],
            "policy_snippet": row["policy_snippet"],
            "receipt_path": row["receipt_path"],
            "ocr_confidence": row["ocr_confidence"],
            "override_status": row["override_status"],
            "override_comment": row["override_comment"],
            "override_by": row["override_by"],
            "created_at": row["created_at"],
        })

    return claims


@app.get("/claims/{claim_id}")
def get_claim_detail(claim_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM claims WHERE id=?", (claim_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "id": row["id"],
        "company_id": row["company_id"],
        "username": row["username"],
        "merchant": row["merchant"],
        "date": row["date"],
        "claimed_date": row["claimed_date"],
        "amount": row["amount"],
        "currency": row["currency"],
        "purpose": row["purpose"],
        "status": row["override_status"] or row["status"],
        "original_status": row["status"],
        "explanation": row["explanation"],
        "risk_level": row["risk_level"],
        "policy_snippet": row["policy_snippet"],
        "receipt_path": row["receipt_path"],
        "ocr_confidence": row["ocr_confidence"],
        "raw_text": row["raw_text"],
        "override_status": row["override_status"],
        "override_comment": row["override_comment"],
        "override_by": row["override_by"],
        "created_at": row["created_at"],
    }


# ──────────────────────────────────────────
# Override endpoint (Human-in-the-Loop)
# ──────────────────────────────────────────

@app.post("/claims/{claim_id}/override")
async def override_claim(
    claim_id: int,
    new_status: str = Form(...),
    comment: str = Form(...),
    auditor: str = Form(...)
):
    if new_status not in ["Approved", "Flagged", "Rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check claim exists
    cursor.execute("SELECT username, amount FROM claims WHERE id=?", (claim_id,))
    claim = cursor.fetchone()
    if not claim:
        conn.close()
        raise HTTPException(status_code=404, detail="Claim not found")

    employee_username = claim[0]
    amount = claim[1]

    # Update the override fields
    cursor.execute("""
    UPDATE claims
    SET override_status=?, override_comment=?, override_by=?
    WHERE id=?
    """, (new_status, comment, auditor, claim_id))

    conn.commit()
    conn.close()

    # Notify the employee
    _create_notification(
        employee_username,
        claim_id,
        f"Your claim #{claim_id} (₹{amount:.0f}) has been updated to '{new_status}' by a finance auditor. Comment: {comment}",
        "success" if new_status == "Approved" else ("warning" if new_status == "Flagged" else "error")
    )

    return {"message": f"Claim #{claim_id} overridden to {new_status}"}


# ──────────────────────────────────────────
# Receipt image serving
# ──────────────────────────────────────────

@app.get("/receipt/{filename}")
def get_receipt(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Receipt not found")
    return FileResponse(file_path)


# ──────────────────────────────────────────
# Notifications
# ──────────────────────────────────────────

def _create_notification(username, claim_id, message, notif_type="info"):
    """Internal helper to create a notification."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO notifications (username, claim_id, message, type)
        VALUES (?, ?, ?, ?)
        """, (username, claim_id, message, notif_type))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Non-critical — don't break the main flow


@app.get("/notifications")
def get_notifications(username: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM notifications WHERE username=? ORDER BY created_at DESC LIMIT 50",
        (username,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "claim_id": row["claim_id"],
            "message": row["message"],
            "type": row["type"],
            "is_read": row["is_read"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@app.get("/notifications/unread_count")
def get_unread_count(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE username=? AND is_read=0",
        (username,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return {"count": count}


@app.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()
    return {"message": "Notification marked as read"}


@app.post("/notifications/read_all")
async def mark_all_read(username: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read=1 WHERE username=?", (username,))
    conn.commit()
    conn.close()
    return {"message": "All notifications marked as read"}
