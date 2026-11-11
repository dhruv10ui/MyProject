import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    User, Student, Room, MessTransaction, MealSkip, GuestMeal,
    LeaveRequest, Payment, RoomChangeRequest, Notice, MessMenu
)
from app.rbac import get_current_user, get_current_student
from app.qr_engine import generate_signed_qr_payload, get_current_meal_session

router = APIRouter(prefix="/student", tags=["Student Portal"])

class MealSkipRequest(BaseModel):
    meal_type: str
    date: str # YYYY-MM-DD
    reason: str = "Dining Outside"

class GuestMealRequest(BaseModel):
    guest_name: str
    meal_type: str
    date: str
    count: int = 1

class RoomChangeReq(BaseModel):
    requested_room_id: str = None
    reason: str

class LeaveReq(BaseModel):
    leave_type: str = "Home Leave" # Home Leave, Day Outpass, Emergency
    from_date: str # ISO string
    to_date: str   # ISO string
    destination: str
    reason: str

@router.get("/dashboard")
def get_student_dashboard(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Consolidated student dashboard."""
    # Room and Roommates
    roommates = []
    if student.room:
        mates = db.query(Student).filter(
            Student.room_id == student.room_id,
            Student.id != student.id
        ).all()
        for m in mates:
            roommates.append({
                "name": m.user.name,
                "roll_no": m.roll_no,
                "bed_no": m.bed_no,
                "branch": m.branch
            })

    # Today's check-in status
    today = datetime.date.today()
    todays_meals = db.query(MessTransaction).filter(
        MessTransaction.student_id == student.id,
        MessTransaction.date == today
    ).all()
    checked_in_meals = [m.meal_type for m in todays_meals]

    # Pending fees
    pending_payments = db.query(Payment).filter(
        Payment.student_id == student.id,
        Payment.payment_status == "Pending"
    ).all()
    total_dues = sum(p.amount for p in pending_payments)

    # Active leave
    active_leave = db.query(LeaveRequest).filter(
        LeaveRequest.student_id == student.id
    ).order_by(LeaveRequest.applied_at.desc()).first()

    return {
        "student": {
            "name": student.user.name,
            "roll_no": student.roll_no,
            "branch": student.branch,
            "semester": student.semester,
            "wallet_balance": student.wallet_balance,
            "remaining_meal_quota": student.remaining_meal_quota,
            "active_plan": student.active_plan.name if student.active_plan else "All-Access Subscription",
            "plan_type": student.active_plan.plan_type if student.active_plan else "subscription"
        },
        "room": {
            "room_number": student.room.room_number if student.room else "Not Allotted",
            "block": student.room.block if student.room else "-",
            "floor": student.room.floor if student.room else "-",
            "bed_no": student.bed_no or "Unassigned",
            "room_type": student.room.room_type if student.room else "-",
            "roommates": roommates
        },
        "mess": {
            "current_session": get_current_meal_session(),
            "checked_in_today": checked_in_meals,
            "can_check_in_current": get_current_meal_session() not in checked_in_meals
        },
        "financials": {
            "total_dues": total_dues,
            "pending_count": len(pending_payments)
        },
        "recent_leave": {
            "id": active_leave.id if active_leave else None,
            "type": active_leave.leave_type if active_leave else None,
            "status": active_leave.approval_status if active_leave else None,
            "destination": active_leave.destination if active_leave else None
        } if active_leave else None
    }

@router.get("/mess-card")
def get_smart_mess_card(student: Student = Depends(get_current_student)):
    """
    Signature Feature: Digital Smart Mess Card.
    Returns rotating short-lived cryptographic signed token (valid for 120 seconds).
    """
    plan_type = student.active_plan.plan_type if student.active_plan else "subscription"
    token_data = generate_signed_qr_payload(
        student_id=student.id,
        roll_no=student.roll_no,
        plan_type=plan_type
    )

    return {
        **token_data,
        "student_name": student.user.name,
        "wallet_balance": student.wallet_balance,
        "remaining_meal_quota": student.remaining_meal_quota,
        "plan_name": student.active_plan.name if student.active_plan else "Standard All-Access Plan",
        "qr_format": "ISO/IEC 18004 Compliant Token"
    }

@router.post("/meal-skip")
def declare_meal_skip(
    req: MealSkipRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Declare a meal skip in advance to prevent kitchen over-preparation."""
    try:
        skip_date = datetime.date.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    existing_skip = db.query(MealSkip).filter(
        MealSkip.student_id == student.id,
        MealSkip.date == skip_date,
        MealSkip.meal_type == req.meal_type
    ).first()

    if existing_skip:
        raise HTTPException(status_code=400, detail=f"You have already marked {req.meal_type} on {req.date} as skipped")

    skip = MealSkip(
        student_id=student.id,
        date=skip_date,
        meal_type=req.meal_type,
        reason=req.reason
    )
    db.add(skip)
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully registered skip for {req.meal_type} on {req.date}. Kitchen attendance forecast updated."
    }

@router.post("/guest-meal")
def book_guest_meal(
    req: GuestMealRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Book a guest meal with wallet deduction."""
    price_per_guest = 80.0 * req.count
    if student.wallet_balance < price_per_guest:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient wallet balance (₹{student.wallet_balance}). Guest meals cost ₹{price_per_guest}. Please recharge wallet."
        )

    try:
        meal_date = datetime.date.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    student.wallet_balance -= price_per_guest
    guest_entry = GuestMeal(
        student_id=student.id,
        guest_name=req.guest_name,
        date=meal_date,
        meal_type=req.meal_type,
        count=req.count,
        amount=price_per_guest,
        payment_status="Paid"
    )
    db.add(guest_entry)
    db.commit()

    return {
        "status": "success",
        "message": f"Booked {req.count} guest meal(s) for {req.guest_name}. Deducted ₹{price_per_guest} from wallet.",
        "remaining_wallet": student.wallet_balance
    }

@router.post("/leave")
def apply_leave(
    req: LeaveReq,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Apply for home leave or day outpass."""
    try:
        from_dt = datetime.datetime.fromisoformat(req.from_date.replace("Z", "+00:00"))
        to_dt = datetime.datetime.fromisoformat(req.to_date.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format")

    leave = LeaveRequest(
        student_id=student.id,
        leave_type=req.leave_type,
        from_date=from_dt,
        to_date=to_dt,
        destination=req.destination,
        reason=req.reason,
        approval_status="Pending"
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)

    return {
        "status": "success",
        "message": "Leave application submitted. Warden review pending.",
        "leave_id": leave.id
    }

@router.post("/room-change")
def request_room_change(
    req: RoomChangeReq,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit a room change request."""
    if not student.room_id:
        raise HTTPException(status_code=400, detail="You currently do not have a room allotted.")

    rc = RoomChangeRequest(
        student_id=student.id,
        current_room_id=student.room_id,
        requested_room_id=req.requested_room_id,
        reason=req.reason,
        status="Pending"
    )
    db.add(rc)
    db.commit()

    return {
        "status": "success",
        "message": "Room change request submitted for Warden inspection and approval."
    }
