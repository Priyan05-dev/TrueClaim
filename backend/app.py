from fastapi import FastAPI, File, UploadFile, Form
import shutil
import os
from ocr import extract_receipt_data
from policy_engine import evaluate_policy
from database import init_db
import sqlite3

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/upload")
async def upload_receipt(file: UploadFile = File(...), purpose: str = Form(...)):
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    data = extract_receipt_data(file_path)

    # Policy Check
    status, explanation = evaluate_policy(data, purpose)

    # Store in DB
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO claims (merchant, date, amount, currency, purpose, status, explanation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
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

    return {
        **data,
        "status": status,
        "explanation": explanation
    }


@app.get("/claims")
def get_claims():
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM claims")
    rows = cursor.fetchall()

    conn.close()

    return rows