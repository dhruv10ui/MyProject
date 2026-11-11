from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Student
from app.auth import verify_password, create_access_token, hash_password
from app.rbac import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SwitchRoleRequest(BaseModel):
    target_role: str

@router.post("/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email, User.is_active == True).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})

    student_data = None
    if user.role == "student" and user.student_profile:
        sp = user.student_profile
        student_data = {
            "student_id": sp.id,
            "roll_no": sp.roll_no,
            "room_id": sp.room_id,
            "room_number": sp.room.room_number if sp.room else "Unassigned",
            "bed_no": sp.bed_no,
            "wallet_balance": sp.wallet_balance,
            "remaining_meal_quota": sp.remaining_meal_quota,
            "active_plan": sp.active_plan.name if sp.active_plan else "Default Subscription"
        }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "student_profile": student_data
        }
    }

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student_data = None
    if current_user.role == "student" and current_user.student_profile:
        sp = current_user.student_profile
        student_data = {
            "student_id": sp.id,
            "roll_no": sp.roll_no,
            "room_number": sp.room.room_number if sp.room else "Unassigned",
            "bed_no": sp.bed_no,
            "wallet_balance": sp.wallet_balance,
            "remaining_meal_quota": sp.remaining_meal_quota,
            "active_plan": sp.active_plan.name if sp.active_plan else "Standard Subscription"
        }

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "phone": current_user.phone,
        "student_profile": student_data
    }

@router.post("/switch-demo")
def switch_demo_role(req: SwitchRoleRequest, db: Session = Depends(get_db)):
    """Convenient demo switcher: finds the first user with the requested role and logs in."""
    valid_roles = ["student", "warden", "mess_staff", "maintenance_staff", "admin", "guardian"]
    if req.target_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from {valid_roles}")

    user = db.query(User).filter(User.role == req.target_role, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No active demo user with role {req.target_role} found")

    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
    
    student_data = None
    if user.role == "student" and user.student_profile:
        sp = user.student_profile
        student_data = {
            "student_id": sp.id,
            "roll_no": sp.roll_no,
            "room_number": sp.room.room_number if sp.room else "Unassigned",
            "bed_no": sp.bed_no,
            "wallet_balance": sp.wallet_balance,
            "remaining_meal_quota": sp.remaining_meal_quota,
            "active_plan": sp.active_plan.name if sp.active_plan else "Standard Subscription"
        }

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "student_profile": student_data
        }
    }
