import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, MessTransaction, MessPlan, MealSkip, MessMenu, SystemConfig
from app.rbac import require_role
from app.qr_engine import verify_signed_qr_payload, get_current_meal_session
from app.config import settings

router = APIRouter(prefix="/mess", tags=["Mess Staff & QR Operations"])

class ScanQRRequest(BaseModel):
    token: str
    meal_type_override: str = None # Optional manual override by staff if near session border

class ManualCheckInRequest(BaseModel):
    roll_no: str
    meal_type: str = None

class UpdateMenuRequest(BaseModel):
    day_of_week: str
    meal_type: str
    items_description: str
    dietary_info: str = "Standard Vegetarian & Non-Veg"

@router.post("/scan-qr")
def process_qr_scan(
    req: ScanQRRequest,
    current_user: User = Depends(require_role(["mess_staff", "admin", "warden"])),
    db: Session = Depends(get_db)
):
    """
    Signature Transaction: 4-Step Verification & Atomic Duplicate Prevention.
    1. Verify cryptographic token signature & freshness.
    2. Validate student profile & active mess plan.
    3. Atomic compound check (student_id, date, meal_type) for duplicate prevention.
    4. Deduct quota/wallet according to active billing model and log transaction.
    """
    # 1. Cryptographic token verification
    verification = verify_signed_qr_payload(req.token)
    if not verification["valid"]:
        return {
            "status": "rejected",
            "reason": "INVALID_TOKEN",
            "message": verification["error"],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    token_data = verification["data"]
    student_id = token_data["sid"]
    roll_no = token_data["roll"]
    meal_session = req.meal_type_override or token_data.get("meal") or get_current_meal_session()
    today = datetime.date.today()

    # 2. Check student existence
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        student = db.query(Student).filter(Student.roll_no == roll_no).first()
    
    if not student:
        return {
            "status": "rejected",
            "reason": "STUDENT_NOT_FOUND",
            "message": f"Student with Roll No {roll_no} not registered in hostel records.",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    # 3. Duplicate Prevention Check (Enforced at application & DB compound index)
    existing_txn = db.query(MessTransaction).filter(
        MessTransaction.student_id == student.id,
        MessTransaction.date == today,
        MessTransaction.meal_type == meal_session
    ).first()

    if existing_txn:
        checkin_time = existing_txn.timestamp.strftime("%I:%M %p")
        return {
            "status": "duplicate",
            "reason": "DUPLICATE_CHECKIN_ATTEMPT",
            "message": f"DUPLICATE DETECTED: {student.user.name} ({student.roll_no}) already scanned for {meal_session} today at {checkin_time}.",
            "student_name": student.user.name,
            "roll_no": student.roll_no,
            "first_scanned_at": existing_txn.timestamp.isoformat(),
            "meal_session": meal_session
        }

    # 4. Check active billing model and apply business rules
    # Check if admin configured global billing model or plan-level
    config_billing = db.query(SystemConfig).filter(SystemConfig.key == "ACTIVE_BILLING_MODEL").first()
    active_billing_mode = config_billing.value if config_billing else (
        student.active_plan.plan_type if student.active_plan else settings.ACTIVE_BILLING_MODEL
    )

    amount_deducted = 0.0
    quota_remaining = student.remaining_meal_quota
    wallet_remaining = student.wallet_balance

    if active_billing_mode == "wallet":
        meal_cost = settings.MEAL_TIMINGS.get(meal_session, {}).get("default_price", 65.0)
        if student.wallet_balance < meal_cost:
            return {
                "status": "rejected",
                "reason": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient wallet balance (₹{student.wallet_balance:.2f}). {meal_session} requires ₹{meal_cost:.2f}.",
                "student_name": student.user.name,
                "roll_no": student.roll_no,
                "wallet_balance": student.wallet_balance
            }
        student.wallet_balance -= meal_cost
        amount_deducted = meal_cost
        wallet_remaining = student.wallet_balance

    elif active_billing_mode == "quota":
        if student.remaining_meal_quota <= 0:
            return {
                "status": "rejected",
                "reason": "QUOTA_EXHAUSTED",
                "message": f"Monthly meal quota exhausted (0 meals left). Please renew quota plan.",
                "student_name": student.user.name,
                "roll_no": student.roll_no,
                "remaining_quota": 0
            }
        student.remaining_meal_quota -= 1
        quota_remaining = student.remaining_meal_quota

    elif active_billing_mode == "subscription":
        # Check validity date if set
        if student.plan_expiry_date and student.plan_expiry_date < today:
            return {
                "status": "rejected",
                "reason": "PLAN_EXPIRED",
                "message": f"Mess subscription expired on {student.plan_expiry_date}. Please renew dues.",
                "student_name": student.user.name,
                "roll_no": student.roll_no
            }

    # Record verified transaction
    txn = MessTransaction(
        student_id=student.id,
        meal_type=meal_session,
        date=today,
        timestamp=datetime.datetime.utcnow(),
        status="Verified",
        token_id=token_data.get("non"),
        amount_deducted=amount_deducted,
        plan_type_used=active_billing_mode,
        verified_by=current_user.id
    )
    db.add(txn)
    db.commit()

    return {
        "status": "verified",
        "message": f"Check-in verified successfully for {meal_session}!",
        "student": {
            "name": student.user.name,
            "roll_no": student.roll_no,
            "room_number": student.room.room_number if student.room else "N/A",
            "bed_no": student.bed_no or "A",
            "branch": student.branch,
            "plan_type": active_billing_mode,
            "wallet_balance": round(wallet_remaining, 2),
            "remaining_quota": quota_remaining
        },
        "transaction": {
            "id": txn.id,
            "meal_session": meal_session,
            "timestamp": txn.timestamp.isoformat(),
            "amount_deducted": amount_deducted
        }
    }

@router.get("/today-board")
def get_today_kitchen_board(db: Session = Depends(get_db)):
    """Live meal counts for today across all sessions."""
    today = datetime.date.today()
    total_students = db.query(Student).count()

    sessions = ["Breakfast", "Lunch", "Snacks", "Dinner"]
    board = {}

    for s in sessions:
        checked_in = db.query(MessTransaction).filter(
            MessTransaction.date == today,
            MessTransaction.meal_type == s,
            MessTransaction.status == "Verified"
        ).count()

        skips = db.query(MealSkip).filter(
            MealSkip.date == today,
            MealSkip.meal_type == s
        ).count()

        board[s] = {
            "checked_in": checked_in,
            "skips_declared": skips,
            "expected_total": max(0, int(total_students * 0.85) - skips)
        }

    return {
        "date": today.isoformat(),
        "total_enrolled": total_students,
        "current_session": get_current_meal_session(),
        "sessions": board
    }

@router.get("/menu")
def get_mess_menu(db: Session = Depends(get_db)):
    """Retrieve full weekly mess menu."""
    menus = db.query(MessMenu).all()
    grouped = {}
    for m in menus:
        if m.day_of_week not in grouped:
            grouped[m.day_of_week] = {}
        grouped[m.day_of_week][m.meal_type] = {
            "items": m.items_description,
            "dietary": m.dietary_info
        }
    return grouped

@router.post("/menu")
def update_mess_menu(
    req: UpdateMenuRequest,
    current_user: User = Depends(require_role(["mess_staff", "admin"])),
    db: Session = Depends(get_db)
):
    """Update items for a specific day and meal."""
    menu_item = db.query(MessMenu).filter(
        MessMenu.day_of_week == req.day_of_week,
        MessMenu.meal_type == req.meal_type
    ).first()

    if not menu_item:
        menu_item = MessMenu(
            day_of_week=req.day_of_week,
            meal_type=req.meal_type,
            items_description=req.items_description,
            dietary_info=req.dietary_info
        )
        db.add(menu_item)
    else:
        menu_item.items_description = req.items_description
        menu_item.dietary_info = req.dietary_info

    db.commit()
    return {"status": "success", "message": f"Updated menu for {req.day_of_week} {req.meal_type}"}
