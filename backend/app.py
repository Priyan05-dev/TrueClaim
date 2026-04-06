from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import sqlite3

from ocr import extract_receipt_data
from policy_engine import evaluate_policy
from policy_processor import process_policy
from database import init_db

from auth import register_user, login_user

app = FastAPI()

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

# Upload policy
@app.post("/upload_policy")
async def upload_policy(company_id: str = Form(...), file: UploadFile = File(...)):
    folder = f"policies/{company_id}"
    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/policy.pdf"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_policy(company_id, file_path)

    return {"message": "Policy uploaded successfully"}

# Upload receipt
@app.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    purpose: str = Form(...),
    company_id: str = Form(...),
    username: str = Form(...)
):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    data = extract_receipt_data(file_path)

    status, explanation = evaluate_policy(data, purpose, company_id)

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO claims (company_id, username, merchant, date, amount, currency, purpose, status, explanation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company_id,
        username,
        data["merchant"],
        data["date"],
        data["amount"],
        data["currency"],
        purpose,
        status,
        explanation
    ))

    conn.commit()
    conn.close()

    return {**data, "status": status, "explanation": explanation}

# Get claims
@app.get("/claims")
def get_claims(role: str, username: str, company_id: str):
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    if role == "company":
        cursor.execute("SELECT * FROM claims WHERE company_id=?", (company_id,))
    else:
        cursor.execute("SELECT * FROM claims WHERE username=?", (username,))

    rows = cursor.fetchall()
    conn.close()

    return rows

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
