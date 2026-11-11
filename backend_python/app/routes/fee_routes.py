import datetime
import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Payment
from app.rbac import get_current_user
from app.config import settings

router = APIRouter(prefix="/fees", tags=["Fees & Payments"])

class ProcessPaymentReq(BaseModel):
    category: str # Hostel Rent, Security Deposit, Laundry, Mess Dues, Wallet Recharge
    amount: float
    payment_method: str = "UPI Sandbox" # UPI Sandbox, Card, NetBanking
    vpa_or_card_last4: str = "user@okhdfcbank"

class RechargeWalletReq(BaseModel):
    amount: float
    payment_method: str = "UPI Sandbox"

@router.get("/summary")
def get_fee_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fee breakdown across all 4 mandatory heads:
    Hostel Rent, Security Deposit, Laundry, and Mess Dues.
    """
    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"dues": [], "total_due": 0.0, "wallet_balance": 0.0}
        
        payments = db.query(Payment).filter(Payment.student_id == student.id).order_by(Payment.created_at.desc()).all()
        
        # Standard semester fee heads structure
        fee_heads = [
            {"category": "Hostel Rent", "amount_due": 45000.0, "due_date": "2026-12-01"},
            {"category": "Security Deposit", "amount_due": 10000.0, "due_date": "2026-08-01"},
            {"category": "Laundry Charges", "amount_due": 3500.0, "due_date": "2026-11-30"},
            {"category": "Mess Dues", "amount_due": 24000.0, "due_date": "2026-11-20"}
        ]

        # Calculate paid vs remaining
        history = []
        for p in payments:
            history.append({
                "id": p.id,
                "category": p.category,
                "amount": p.amount,
                "status": p.payment_status,
                "method": p.payment_method,
                "receipt_id": p.receipt_id,
                "transaction_ref": p.transaction_ref,
                "date": p.created_at.strftime("%d %b %Y, %I:%M %p")
            })

        return {
            "student_roll": student.roll_no,
            "student_name": current_user.name,
            "wallet_balance": student.wallet_balance,
            "remaining_quota": student.remaining_meal_quota,
            "fee_heads": fee_heads,
            "payment_history": history
        }
    else:
        # Admin / Warden total collection metrics
        all_payments = db.query(Payment).filter(Payment.payment_status == "Success").all()
        total_collected = sum(p.amount for p in all_payments)
        by_category = {}
        for p in all_payments:
            by_category[p.category] = by_category.get(p.category, 0.0) + p.amount

        return {
            "total_collected": total_collected,
            "total_transactions": len(all_payments),
            "by_category": by_category
        }

@router.post("/pay")
def process_sandbox_payment(
    req: ProcessPaymentReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process payment in sandbox mode and issue verifiable digital receipt.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only students can initiate fee payments")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    # Generate receipt ID and transaction hash
    timestamp_now = datetime.datetime.utcnow()
    rand_suffix = str(uuid.uuid4())[:6].upper()
    receipt_id = f"REC-2026-{rand_suffix}"
    
    raw_hash_str = f"{student.id}:{req.amount}:{timestamp_now.isoformat()}:{settings.SECRET_KEY}"
    txn_ref = f"TXN_{hashlib.sha256(raw_hash_str.encode()).hexdigest()[:16].upper()}"

    payment = Payment(
        student_id=student.id,
        category=req.category,
        amount=req.amount,
        payment_status="Success",
        payment_method=req.payment_method,
        receipt_id=receipt_id,
        transaction_ref=txn_ref,
        notes=f"Paid via Sandbox {req.payment_method} ({req.vpa_or_card_last4})"
    )
    db.add(payment)

    # If wallet recharge, credit balance
    if req.category == "Wallet Recharge":
        student.wallet_balance += req.amount

    db.commit()

    return {
        "status": "success",
        "message": f"Payment of ₹{req.amount:,.2f} completed successfully in Sandbox mode.",
        "receipt": {
            "institution": settings.INSTITUTION_NAME,
            "receipt_id": receipt_id,
            "transaction_ref": txn_ref,
            "student_name": current_user.name,
            "roll_no": student.roll_no,
            "room_number": student.room.room_number if student.room else "N/A",
            "category": req.category,
            "amount_paid": req.amount,
            "payment_method": req.payment_method,
            "timestamp": timestamp_now.strftime("%d-%b-%Y %I:%M:%S %p"),
            "status": "PAID - VERIFIED"
        }
    }
