from pydantic import BaseModel

class ClaimResponse(BaseModel):
    merchant: str
    date: str
    amount: float
    currency: str
    status: str
    explanation: str