import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, Student, MessPlan, MessTransaction
from app.auth import hash_password

def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_duplicate_mess_checkin_prevention():
    db = setup_in_memory_db()

    # Create dummy user & student
    user = User(
        name="Test Student", email="test@hostel360.edu",
        password_hash=hash_password("demo123"), role="student"
    )
    db.add(user)
    db.flush()

    student = Student(user_id=user.id, roll_no="TEST101", wallet_balance=500.0, remaining_meal_quota=30)
    db.add(student)
    db.flush()

    today = datetime.date.today()
    meal_type = "Lunch"

    # First check-in succeeds
    txn1 = MessTransaction(
        student_id=student.id,
        meal_type=meal_type,
        date=today,
        status="Verified",
        amount_deducted=0.0
    )
    db.add(txn1)
    db.commit()

    # Second check-in on the exact same date & meal MUST trigger DB unique constraint violation
    txn2 = MessTransaction(
        student_id=student.id,
        meal_type=meal_type,
        date=today,
        status="Verified",
        amount_deducted=0.0
    )
    db.add(txn2)

    with pytest.raises(Exception): # SQLite IntegrityError
        db.commit()

    db.rollback()

def test_wallet_and_quota_deductions():
    db = setup_in_memory_db()
    user = User(name="Test Student 2", email="test2@hostel360.edu", password_hash="hash", role="student")
    db.add(user)
    db.flush()

    student = Student(user_id=user.id, roll_no="TEST102", wallet_balance=100.0, remaining_meal_quota=5)
    db.add(student)
    db.commit()

    # Wallet deduction
    meal_cost = 65.0
    student.wallet_balance -= meal_cost
    assert student.wallet_balance == 35.0

    # Quota deduction
    student.remaining_meal_quota -= 1
    assert student.remaining_meal_quota == 4
