import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Room, Payment, Complaint, MessTransaction, SystemConfig, AuditLog
from app.rbac import require_role
from app.auth import hash_password
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Administrator Dashboard & Settings"])

class UpdateBillingModelReq(BaseModel):
    model: str # "subscription", "wallet", "quota"

class CreateUserReq(BaseModel):
    name: str
    email: str
    password: str
    role: str # student, warden, mess_staff, maintenance_staff, admin, guardian
    phone: str = None
    roll_no: str = None # if student

@router.get("/overview")
def get_admin_overview(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Hostel 360 executive statistics."""
    total_students = db.query(Student).count()
    rooms = db.query(Room).all()
    total_capacity = sum(r.capacity for r in rooms)
    occupied_beds = sum(r.occupied_beds for r in rooms)

    total_revenue = db.query(Payment).filter(Payment.payment_status == "Success").all()
    revenue_amount = sum(p.amount for p in total_revenue)

    total_complaints = db.query(Complaint).count()
    resolved_complaints = db.query(Complaint).filter(Complaint.status.in_(["Resolved", "Closed"])).count()

    today = datetime.date.today()
    todays_meals = db.query(MessTransaction).filter(MessTransaction.date == today).count()

    # Active billing configuration
    config_entry = db.query(SystemConfig).filter(SystemConfig.key == "ACTIVE_BILLING_MODEL").first()
    active_billing = config_entry.value if config_entry else settings.ACTIVE_BILLING_MODEL

    return {
        "stats": {
            "total_students": total_students,
            "total_capacity": total_capacity,
            "occupied_beds": occupied_beds,
            "available_beds": max(0, total_capacity - occupied_beds),
            "occupancy_rate": round((occupied_beds / max(1, total_capacity)) * 100, 1),
            "total_revenue_collected": revenue_amount,
            "total_complaints": total_complaints,
            "resolved_complaints": resolved_complaints,
            "complaint_resolution_rate": round((resolved_complaints / max(1, total_complaints)) * 100, 1),
            "meals_served_today": todays_meals
        },
        "active_billing_model": active_billing
    }

@router.put("/billing-model")
def update_billing_model(
    req: UpdateBillingModelReq,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Switch mess billing model dynamically without restarting or modifying code.
    Options: 'subscription', 'wallet', 'quota'
    """
    valid_models = ["subscription", "wallet", "quota"]
    if req.model.lower() not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid billing model '{req.model}'. Must be one of: {valid_models}"
        )

    config_entry = db.query(SystemConfig).filter(SystemConfig.key == "ACTIVE_BILLING_MODEL").first()
    if not config_entry:
        config_entry = SystemConfig(
            key="ACTIVE_BILLING_MODEL",
            value=req.model.lower(),
            description="Active billing model: subscription, wallet, or quota"
        )
        db.add(config_entry)
    else:
        config_entry.value = req.model.lower()
        config_entry.updated_at = datetime.datetime.utcnow()

    # Log to audit trail
    log = AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="UPDATE_BILLING_MODEL",
        entity="SystemConfig",
        details=f"Admin switched mess billing model to '{req.model.lower()}'"
    )
    db.add(log)
    db.commit()

    return {
        "status": "success",
        "message": f"Mess billing model successfully changed to '{req.model.lower()}'.",
        "active_billing_model": req.model.lower()
    }

@router.get("/users")
def list_system_users(
    role: str = None,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """List system users with role details."""
    query = db.query(User).order_by(User.created_at.desc())
    if role:
        query = query.filter(User.role == role)

    users = query.all()
    output = []
    for u in users:
        student_info = None
        if u.role == "student" and u.student_profile:
            sp = u.student_profile
            student_info = {
                "roll_no": sp.roll_no,
                "room": sp.room.room_number if sp.room else "Unassigned",
                "bed": sp.bed_no or "-"
            }
        output.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "phone": u.phone,
            "created_at": u.created_at.strftime("%d-%b-%Y"),
            "student_info": student_info
        })
    return output

@router.get("/audit-logs")
def get_audit_trail(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Retrieve security and administrative audit trail."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "actor_role": l.actor_role,
            "action": l.action,
            "entity": l.entity,
            "details": l.details,
            "timestamp": l.timestamp.strftime("%d-%b-%Y %I:%M:%S %p")
        }
        for l in logs
    ]
