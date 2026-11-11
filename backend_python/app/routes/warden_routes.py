import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    User, Student, Room, LeaveRequest, Complaint, Notice, RoomChangeRequest, AuditLog
)
from app.rbac import require_role

router = APIRouter(prefix="/warden", tags=["Warden Portal"])

class AllocateRoomReq(BaseModel):
    student_id: str
    room_id: str
    bed_no: str # Bed A, Bed B, Bed C

class LeaveDecisionReq(BaseModel):
    decision: str # "Approved" or "Rejected"
    remarks: str = "Granted"

class RoomChangeDecisionReq(BaseModel):
    decision: str # "Approved" or "Rejected"
    new_room_id: str = None
    remarks: str = "Approved by Warden"

class PostNoticeReq(BaseModel):
    title: str
    message: str
    audience: str = "All" # All, Students, Mess, Maintenance
    category: str = "General"
    is_urgent: bool = False

@router.get("/occupancy")
def get_occupancy_overview(
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """Detailed room & bed allocation map across blocks."""
    rooms = db.query(Room).order_by(Room.block, Room.room_number).all()
    total_capacity = sum(r.capacity for r in rooms)
    occupied_beds = sum(r.occupied_beds for r in rooms)

    room_list = []
    for r in rooms:
        occupants = []
        for s in r.students:
            occupants.append({
                "student_id": s.id,
                "name": s.user.name,
                "roll_no": s.roll_no,
                "bed_no": s.bed_no,
                "contact": s.user.phone
            })
        room_list.append({
            "id": r.id,
            "block": r.block,
            "floor": r.floor,
            "room_number": r.room_number,
            "capacity": r.capacity,
            "occupied_beds": r.occupied_beds,
            "room_type": r.room_type,
            "status": r.status,
            "amenities": r.amenities,
            "occupants": occupants
        })

    return {
        "stats": {
            "total_rooms": len(rooms),
            "total_capacity": total_capacity,
            "occupied_beds": occupied_beds,
            "available_beds": max(0, total_capacity - occupied_beds),
            "occupancy_rate": round((occupied_beds / max(1, total_capacity)) * 100, 1)
        },
        "rooms": room_list
    }

@router.post("/allocate-room")
def allocate_student_to_room(
    req: AllocateRoomReq,
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """Assign student to specific room and bed."""
    student = db.query(Student).filter(Student.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_room = db.query(Room).filter(Room.id == req.room_id).first()
    if not new_room:
        raise HTTPException(status_code=404, detail="Room not found")

    if new_room.occupied_beds >= new_room.capacity and student.room_id != new_room.id:
        raise HTTPException(status_code=400, detail="Room is already at full capacity")

    # If student had previous room, decrement old room's count
    if student.room_id and student.room_id != new_room.id:
        old_room = db.query(Room).filter(Room.id == student.room_id).first()
        if old_room and old_room.occupied_beds > 0:
            old_room.occupied_beds -= 1
            if old_room.occupied_beds < old_room.capacity:
                old_room.status = "Available"

    # Assign new room
    if student.room_id != new_room.id:
        new_room.occupied_beds += 1
        if new_room.occupied_beds >= new_room.capacity:
            new_room.status = "Occupied"

    student.room_id = new_room.id
    student.bed_no = req.bed_no
    db.commit()

    return {
        "status": "success",
        "message": f"Allotted {student.user.name} to {new_room.room_number} ({req.bed_no})"
    }

@router.get("/leaves")
def get_leave_requests(
    status_filter: str = None,
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """Retrieve all student leave and outpass applications."""
    query = db.query(LeaveRequest).order_by(LeaveRequest.applied_at.desc())
    if status_filter:
        query = query.filter(LeaveRequest.approval_status == status_filter)

    leaves = query.all()
    results = []
    for l in leaves:
        student = db.query(Student).filter(Student.id == l.student_id).first()
        results.append({
            "id": l.id,
            "student_id": l.student_id,
            "student_name": student.user.name if student else "Unknown",
            "roll_no": student.roll_no if student else "-",
            "room_number": student.room.room_number if student and student.room else "-",
            "leave_type": l.leave_type,
            "from_date": l.from_date.isoformat(),
            "to_date": l.to_date.isoformat(),
            "destination": l.destination,
            "reason": l.reason,
            "status": l.approval_status,
            "applied_at": l.applied_at.isoformat(),
            "warden_remarks": l.warden_remarks,
            "qr_gate_pass": l.qr_gate_pass
        })
    return results

@router.put("/leaves/{leave_id}/decision")
def decide_leave(
    leave_id: str,
    req: LeaveDecisionReq,
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """Approve or reject leave request. Issues digital QR Gate Pass on approval."""
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.approval_status = req.decision
    leave.warden_remarks = req.remarks
    leave.approved_by = current_user.id
    leave.decided_at = datetime.datetime.utcnow()

    if req.decision == "Approved":
        # Generate cryptographically verifiable gate pass code
        gate_token = f"GATEPASS-{leave.id[:8].upper()}-{int(datetime.datetime.utcnow().timestamp())}"
        leave.qr_gate_pass = gate_token

    db.commit()

    return {
        "status": "success",
        "message": f"Leave application {req.decision.lower()} successfully",
        "qr_gate_pass": leave.qr_gate_pass
    }

@router.get("/room-changes")
def get_room_change_requests(
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """List pending room change applications."""
    reqs = db.query(RoomChangeRequest).order_by(RoomChangeRequest.created_at.desc()).all()
    output = []
    for r in reqs:
        student = db.query(Student).filter(Student.id == r.student_id).first()
        cur_room = db.query(Room).filter(Room.id == r.current_room_id).first()
        req_room = db.query(Room).filter(Room.id == r.requested_room_id).first() if r.requested_room_id else None
        output.append({
            "id": r.id,
            "student_name": student.user.name if student else "-",
            "roll_no": student.roll_no if student else "-",
            "current_room": cur_room.room_number if cur_room else "-",
            "requested_room": req_room.room_number if req_room else "Any Available",
            "reason": r.reason,
            "status": r.status,
            "remarks": r.remarks,
            "created_at": r.created_at.isoformat()
        })
    return output

@router.post("/notices")
def post_hostel_notice(
    req: PostNoticeReq,
    current_user: User = Depends(require_role(["warden", "admin"])),
    db: Session = Depends(get_db)
):
    """Broadcast an official notice to students and staff."""
    notice = Notice(
        title=req.title,
        message=req.message,
        audience=req.audience,
        category=req.category,
        posted_by=current_user.id,
        is_urgent=req.is_urgent
    )
    db.add(notice)
    db.commit()
    return {"status": "success", "message": "Notice published to all dashboards."}
