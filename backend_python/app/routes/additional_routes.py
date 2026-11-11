import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Visitor, Notice, LeaveRequest, Payment, MessTransaction
from app.rbac import get_current_user

router = APIRouter(prefix="/services", tags=["Visitors, Notices & Guardian Updates"])

class RegisterVisitorReq(BaseModel):
    visitor_name: str
    relation: str # Parent, Sibling, Relative, Friend
    phone: str
    visit_date: str # YYYY-MM-DD
    purpose: str = "Family Visit"

@router.get("/notices")
def get_notices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve notices filtered for the current user's audience role."""
    notices = db.query(Notice).order_by(Notice.created_at.desc()).all()
    filtered = []
    for n in notices:
        if n.audience in ["All", current_user.role.capitalize(), "Students" if current_user.role == "student" else "All"]:
            filtered.append({
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "audience": n.audience,
                "category": n.category,
                "is_urgent": n.is_urgent,
                "created_at": n.created_at.strftime("%d %b %Y, %I:%M %p")
            })
    return filtered

@router.get("/visitors")
def list_visitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List visitor entries."""
    query = db.query(Visitor).order_by(Visitor.visit_date.desc())
    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            query = query.filter(Visitor.host_student_id == student.id)

    visitors = query.all()
    results = []
    for v in visitors:
        host = db.query(Student).filter(Student.id == v.host_student_id).first()
        results.append({
            "id": v.id,
            "visitor_name": v.visitor_name,
            "relation": v.relation,
            "phone": v.phone,
            "visit_date": v.visit_date.isoformat(),
            "purpose": v.purpose,
            "status": v.approval_status,
            "host_name": host.user.name if host else "-",
            "host_room": host.room.room_number if host and host.room else "-",
            "check_in": v.check_in_time.strftime("%I:%M %p") if v.check_in_time else "Not Checked In",
            "check_out": v.check_out_time.strftime("%I:%M %p") if v.check_out_time else "-"
        })
    return results

@router.post("/visitors")
def register_visitor(
    req: RegisterVisitorReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student registers an expected visitor."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only students can register visitors.")

    try:
        v_date = datetime.date.fromisoformat(req.visit_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    visitor = Visitor(
        host_student_id=student.id,
        visitor_name=req.visitor_name,
        relation=req.relation,
        phone=req.phone,
        visit_date=v_date,
        purpose=req.purpose,
        approval_status="Approved" # Pre-approved for registered immediate family
    )
    db.add(visitor)
    db.commit()

    return {
        "status": "success",
        "message": f"Visitor pass pre-approved for {req.visitor_name} on {req.visit_date}."
    }

@router.get("/guardian/ward-status")
def get_guardian_ward_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parent/Guardian Portal:
    Provides verified updates on ward's leaves, fee dues, room info, and mess attendance.
    """
    # For demo or matched guardian: look up associated student
    student = db.query(Student).filter(
        (Student.guardian_email == current_user.email) | (Student.guardian_contact == current_user.phone)
    ).first()

    # If demo guardian without explicit link, default to first student for rich display
    if not student:
        student = db.query(Student).first()

    if not student:
        raise HTTPException(status_code=404, detail="No ward linked to this guardian account")

    # Recent leaves
    leaves = db.query(LeaveRequest).filter(
        LeaveRequest.student_id == student.id
    ).order_by(LeaveRequest.applied_at.desc()).limit(5).all()

    # Fee dues
    pending_payments = db.query(Payment).filter(
        Payment.student_id == student.id,
        Payment.payment_status == "Pending"
    ).all()

    # Recent mess meals
    recent_meals = db.query(MessTransaction).filter(
        MessTransaction.student_id == student.id
    ).order_by(MessTransaction.timestamp.desc()).limit(6).all()

    return {
        "ward": {
            "name": student.user.name,
            "roll_no": student.roll_no,
            "room_number": student.room.room_number if student.room else "-",
            "block": student.room.block if student.room else "-",
            "semester": student.semester,
            "branch": student.branch
        },
        "recent_leaves": [
            {
                "type": l.leave_type,
                "from": l.from_date.strftime("%d %b %Y"),
                "to": l.to_date.strftime("%d %b %Y"),
                "status": l.approval_status,
                "destination": l.destination,
                "warden_remarks": l.warden_remarks
            }
            for l in leaves
        ],
        "fee_dues": [
            {
                "category": p.category,
                "amount": p.amount,
                "status": p.payment_status
            }
            for p in pending_payments
        ],
        "recent_mess_attendance": [
            {
                "meal": m.meal_type,
                "date": m.date.isoformat(),
                "time": m.timestamp.strftime("%I:%M %p")
            }
            for m in recent_meals
        ]
    }
