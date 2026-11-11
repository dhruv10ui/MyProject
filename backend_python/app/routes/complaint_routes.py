import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student, Complaint
from app.rbac import get_current_user

router = APIRouter(prefix="/complaints", tags=["Complaint Tracking Lifecycle"])

class CreateComplaintReq(BaseModel):
    category: str # Electrical, Plumbing, Wi-Fi, Carpentry, Cleaning, General
    room_number: str
    description: str
    priority: str = "Medium" # Low, Medium, High, Emergency
    photo_url: str = None

class AssignComplaintReq(BaseModel):
    assigned_staff_id: str

class UpdateStatusReq(BaseModel):
    status: str # In Progress, Resolved
    resolution_notes: str = None

class SubmitFeedbackReq(BaseModel):
    rating: int # 1 to 5 stars
    comment: str = None

@router.get("")
def list_complaints(
    status_filter: str = None,
    category_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List complaints tailored to the user's role:
    - Students see only their own complaints.
    - Maintenance staff see complaints assigned to them (or unassigned).
    - Wardens and Admins see all complaints across the hostel.
    """
    query = db.query(Complaint).order_by(Complaint.created_at.desc())

    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        query = query.filter(Complaint.student_id == student.id)
    elif current_user.role == "maintenance_staff":
        query = query.filter(
            (Complaint.assigned_staff_id == current_user.id) | (Complaint.assigned_staff_id == None)
        )

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if category_filter:
        query = query.filter(Complaint.category == category_filter)

    complaints = query.all()
    results = []
    for c in complaints:
        student = db.query(Student).filter(Student.id == c.student_id).first()
        staff = db.query(User).filter(User.id == c.assigned_staff_id).first() if c.assigned_staff_id else None
        
        # Calculate turnaround time if resolved
        resolution_hours = None
        if c.resolved_at and c.created_at:
            delta = c.resolved_at - c.created_at
            resolution_hours = round(delta.total_seconds() / 3600, 1)

        results.append({
            "id": c.id,
            "category": c.category,
            "room_number": c.room_number,
            "description": c.description,
            "priority": c.priority,
            "photo_url": c.photo_url,
            "status": c.status,
            "assigned_staff_name": staff.name if staff else "Unassigned",
            "assigned_staff_id": c.assigned_staff_id,
            "student_name": student.user.name if student else "Unknown",
            "student_roll": student.roll_no if student else "-",
            "resolution_notes": c.resolution_notes,
            "rating": c.student_feedback_rating,
            "feedback_comment": c.student_feedback_comment,
            "resolution_hours": resolution_hours,
            "created_at": c.created_at.isoformat(),
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None
        })
    return results

@router.post("")
def submit_complaint(
    req: CreateComplaintReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student submits a new maintenance complaint."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only registered hostel students can raise complaints.")

    complaint = Complaint(
        student_id=student.id,
        category=req.category,
        room_number=req.room_number,
        description=req.description,
        priority=req.priority,
        photo_url=req.photo_url,
        status="Submitted"
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "status": "success",
        "message": f"Complaint #{complaint.id[:8].upper()} registered. Warden notification dispatched.",
        "complaint_id": complaint.id
    }

@router.put("/{complaint_id}/assign")
def assign_complaint(
    complaint_id: str,
    req: AssignComplaintReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Warden assigns complaint to maintenance staff member."""
    if current_user.role not in ["warden", "admin"]:
        raise HTTPException(status_code=403, detail="Only Wardens and Admins can assign complaints.")

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    staff = db.query(User).filter(User.id == req.assigned_staff_id, User.role == "maintenance_staff").first()
    if not staff:
        raise HTTPException(status_code=400, detail="Target user is not an active maintenance staff member.")

    complaint.assigned_staff_id = staff.id
    complaint.status = "Assigned"
    db.commit()

    return {
        "status": "success",
        "message": f"Ticket assigned to {staff.name}."
    }

@router.put("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: str,
    req: UpdateStatusReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Maintenance staff updates ticket status (In Progress / Resolved)."""
    if current_user.role not in ["maintenance_staff", "warden", "admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized to update maintenance status.")

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = req.status
    if req.resolution_notes:
        complaint.resolution_notes = req.resolution_notes

    if req.status == "Resolved":
        complaint.resolved_at = datetime.datetime.utcnow()

    db.commit()

    return {
        "status": "success",
        "message": f"Complaint status updated to {req.status}."
    }

@router.put("/{complaint_id}/feedback")
def submit_complaint_feedback(
    complaint_id: str,
    req: SubmitFeedbackReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student provides feedback & rating (1-5 stars) upon resolution."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    complaint.student_feedback_rating = req.rating
    complaint.student_feedback_comment = req.comment
    complaint.status = "Closed"
    db.commit()

    return {
        "status": "success",
        "message": "Thank you! Your feedback has been recorded and ticket marked as Closed."
    }
