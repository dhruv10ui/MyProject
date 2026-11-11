import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="student") # student, warden, mess_staff, maintenance_staff, admin, guardian
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    block = Column(String(20), nullable=False) # e.g. Block A, Block B
    floor = Column(Integer, nullable=False)    # e.g. 1, 2, 3
    room_number = Column(String(20), unique=True, nullable=False, index=True) # e.g. A-101
    capacity = Column(Integer, nullable=False, default=2)
    occupied_beds = Column(Integer, nullable=False, default=0)
    room_type = Column(String(30), default="Double Non-AC") # Single AC, Double AC, Triple Non-AC, etc.
    status = Column(String(20), default="Available") # Available, Occupied, Maintenance
    amenities = Column(String(200), default="Attached Bath, Study Table, Balcony, Wi-Fi")

    students = relationship("Student", back_populates="room")


class MessPlan(Base):
    __tablename__ = "mess_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    plan_type = Column(String(30), nullable=False) # subscription, wallet, quota
    price = Column(Float, nullable=False)
    validity_days = Column(Integer, default=30)
    meal_quota = Column(Integer, default=60) # meals per pack for quota model
    meal_price = Column(Float, default=65.0) # per meal deduction for wallet model
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    roll_no = Column(String(50), unique=True, nullable=False, index=True) # e.g. 11023210138
    room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    bed_no = Column(String(10), nullable=True) # Bed A, Bed B, Bed C
    branch = Column(String(50), default="CSE DSAI")
    semester = Column(Integer, default=7)
    guardian_name = Column(String(100), nullable=True)
    guardian_contact = Column(String(20), nullable=True)
    guardian_email = Column(String(120), nullable=True)
    
    # Mess parameters
    active_plan_id = Column(String(36), ForeignKey("mess_plans.id"), nullable=True)
    wallet_balance = Column(Float, default=1500.0) # For prepaid wallet billing
    remaining_meal_quota = Column(Integer, default=60) # For quota billing
    plan_expiry_date = Column(Date, nullable=True) # For subscription billing

    user = relationship("User", back_populates="student_profile")
    room = relationship("Room", back_populates="students")
    active_plan = relationship("MessPlan")


class MessTransaction(Base):
    __tablename__ = "mess_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    meal_type = Column(String(20), nullable=False) # Breakfast, Lunch, Snacks, Dinner
    date = Column(Date, nullable=False, index=True) # YYYY-MM-DD
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="Verified") # Verified, Rejected, Duplicate
    token_id = Column(String(100), nullable=True)
    amount_deducted = Column(Float, default=0.0)
    plan_type_used = Column(String(30), default="subscription")
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    # UNIQUE COMPOUND CONSTRAINT: Prevents duplicate check-in for same student, date, and meal
    __table_args__ = (
        UniqueConstraint("student_id", "date", "meal_type", name="uq_student_meal_session"),
    )


class MealSkip(Base):
    __tablename__ = "meal_skips"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    meal_type = Column(String(20), nullable=False)
    reason = Column(String(200), default="Personal / Dining Outside")
    declared_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("student_id", "date", "meal_type", name="uq_student_meal_skip"),
    )


class GuestMeal(Base):
    __tablename__ = "guest_meals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    guest_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    count = Column(Integer, default=1)
    amount = Column(Float, default=80.0)
    payment_status = Column(String(20), default="Paid")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    category = Column(String(40), nullable=False) # Hostel Rent, Security Deposit, Laundry, Mess Dues
    amount = Column(Float, nullable=False)
    payment_status = Column(String(20), default="Success") # Success, Pending, Failed
    payment_method = Column(String(30), default="UPI Sandbox") # UPI Sandbox, Card, NetBanking
    receipt_id = Column(String(50), unique=True, nullable=False, index=True) # e.g. REC-2026-9481
    transaction_ref = Column(String(64), unique=True, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    leave_type = Column(String(30), default="Home Leave") # Home Leave, Day Outpass, Emergency
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    destination = Column(String(150), nullable=False)
    parent_contact_confirmed = Column(Boolean, default=True)
    approval_status = Column(String(20), default="Pending") # Pending, Approved, Rejected
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    warden_remarks = Column(Text, nullable=True)
    qr_gate_pass = Column(String(255), nullable=True)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    category = Column(String(40), nullable=False) # Electrical, Plumbing, Wi-Fi, Carpentry, Cleaning, General
    room_number = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    photo_url = Column(String(255), nullable=True)
    priority = Column(String(20), default="Medium") # Low, Medium, High, Emergency
    assigned_staff_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="Submitted") # Submitted, Assigned, In Progress, Resolved, Closed
    resolution_notes = Column(Text, nullable=True)
    student_feedback_rating = Column(Integer, nullable=True) # 1-5 stars
    student_feedback_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    host_student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    visitor_name = Column(String(100), nullable=False)
    relation = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    visit_date = Column(Date, nullable=False)
    purpose = Column(String(200), default="Family visit")
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    approval_status = Column(String(20), default="Approved") # Pending, Approved, Rejected
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Notice(Base):
    __tablename__ = "notices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    audience = Column(String(30), default="All") # All, Students, Wardens, Mess, Maintenance
    category = Column(String(30), default="General") # General, Mess, Fees, Maintenance, Emergency
    posted_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_urgent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MessMenu(Base):
    __tablename__ = "mess_menus"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    day_of_week = Column(String(15), nullable=False) # Monday, Tuesday, ...
    meal_type = Column(String(20), nullable=False)   # Breakfast, Lunch, Snacks, Dinner
    items_description = Column(Text, nullable=False)
    dietary_info = Column(String(100), default="Vegetarian / Non-Veg options")


class RoomChangeRequest(Base):
    __tablename__ = "room_change_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    current_room_id = Column(String(36), ForeignKey("rooms.id"), nullable=False)
    requested_room_id = Column(String(36), ForeignKey("rooms.id"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="Pending") # Pending, Approved, Rejected
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), nullable=False)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
