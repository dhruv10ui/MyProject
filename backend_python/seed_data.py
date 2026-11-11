import datetime
import uuid
from app.database import SessionLocal, engine, Base
from app.models import (
    User, Student, Room, MessPlan, MessTransaction, MealSkip,
    Complaint, Payment, LeaveRequest, Notice, MessMenu, SystemConfig, Visitor
)
from app.auth import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if data already exists
    if db.query(User).first():
        print("Database already populated. Skipping seed.")
        db.close()
        return

    print("Seeding initial Hostel 360 database records...")
    password_hash = hash_password("Hostel360@demo")

    # 1. System Config
    db.add(SystemConfig(key="ACTIVE_BILLING_MODEL", value="subscription", description="Active billing model: subscription, wallet, or quota"))
    db.add(SystemConfig(key="ACADEMIC_YEAR", value="2026-27", description="Current academic year"))
    db.commit()

    # 2. Rooms
    rooms_data = [
        {"block": "Block A", "floor": 1, "room_number": "A-101", "capacity": 2, "room_type": "Double Non-AC"},
        {"block": "Block A", "floor": 1, "room_number": "A-102", "capacity": 2, "room_type": "Double Non-AC"},
        {"block": "Block A", "floor": 2, "room_number": "A-201", "capacity": 3, "room_type": "Triple Non-AC"},
        {"block": "Block A", "floor": 2, "room_number": "A-202", "capacity": 2, "room_type": "Double AC"},
        {"block": "Block B", "floor": 1, "room_number": "B-101", "capacity": 2, "room_type": "Double Non-AC"},
        {"block": "Block B", "floor": 2, "room_number": "B-201", "capacity": 2, "room_type": "Double AC"},
    ]
    room_map = {}
    for r in rooms_data:
        room_obj = Room(**r, status="Available", occupied_beds=0)
        db.add(room_obj)
        db.flush()
        room_map[r["room_number"]] = room_obj

    # 3. Mess Plans
    sub_plan = MessPlan(name="All-Access Monthly Subscription", plan_type="subscription", price=4500.0, validity_days=30, meal_quota=120, meal_price=65.0, description="Unlimited daily access to Breakfast, Lunch, Snacks & Dinner")
    wallet_plan = MessPlan(name="Pay-As-You-Eat Prepaid Wallet", plan_type="wallet", price=2000.0, validity_days=60, meal_quota=0, meal_price=65.0, description="Flexible per-meal deductions based on actual consumption")
    quota_plan = MessPlan(name="60-Meal Smart Quota Pack", plan_type="quota", price=3600.0, validity_days=45, meal_quota=60, meal_price=60.0, description="Ideal for students dining outside frequently on weekends")
    db.add_all([sub_plan, wallet_plan, quota_plan])
    db.flush()

    # 4. Users & Students
    # Student 1: Dhruv Bansal (Project Author)
    u_dhruv = User(name="Dhruv Bansal", email="11023210138@stu.srmuniversity.ac.in", password_hash=password_hash, role="student", phone="+91 7291878973")
    db.add(u_dhruv)
    db.flush()
    s_dhruv = Student(
        user_id=u_dhruv.id, roll_no="11023210138", room_id=room_map["A-101"].id, bed_no="Bed A",
        branch="CSE DSAI", semester=7, guardian_name="Mr. Rajesh Bansal", guardian_contact="+91 9811223344",
        guardian_email="guardian@hostel360.edu", active_plan_id=sub_plan.id, wallet_balance=1850.0, remaining_meal_quota=54
    )
    room_map["A-101"].occupied_beds += 1

    # Student 2: Arnav Ambasta (Project Author)
    u_arnav = User(name="Arnav Ambasta", email="11023210146@stu.srmuniversity.ac.in", password_hash=password_hash, role="student", phone="+91 7779946795")
    db.add(u_arnav)
    db.flush()
    s_arnav = Student(
        user_id=u_arnav.id, roll_no="11023210146", room_id=room_map["A-101"].id, bed_no="Bed B",
        branch="CSE DSAI", semester=7, guardian_name="Mr. S. K. Ambasta", guardian_contact="+91 9822334455",
        guardian_email="arnav.guardian@gmail.com", active_plan_id=wallet_plan.id, wallet_balance=2400.0, remaining_meal_quota=45
    )
    room_map["A-101"].occupied_beds += 1
    room_map["A-101"].status = "Occupied"

    # Student 3: Janak Vallecha (Project Author)
    u_janak = User(name="Janak Vallecha", email="11023210195@stu.srmuniversity.ac.in", password_hash=password_hash, role="student", phone="+91 8178260696")
    db.add(u_janak)
    db.flush()
    s_janak = Student(
        user_id=u_janak.id, roll_no="11023210195", room_id=room_map["A-102"].id, bed_no="Bed A",
        branch="CSE DSAI", semester=7, guardian_name="Mr. P. Vallecha", guardian_contact="+91 9833445566",
        guardian_email="janak.guardian@gmail.com", active_plan_id=quota_plan.id, wallet_balance=920.0, remaining_meal_quota=38
    )
    room_map["A-102"].occupied_beds += 1

    # Staff Accounts
    u_warden = User(name="Dr. Rakesh Sharma", email="warden@hostel360.edu", password_hash=password_hash, role="warden", phone="+91 9411220011")
    u_mess = User(name="Suresh Kumar (Mess Manager)", email="mess@hostel360.edu", password_hash=password_hash, role="mess_staff", phone="+91 9411220022")
    u_maint = User(name="Ramesh Electrician", email="maintenance@hostel360.edu", password_hash=password_hash, role="maintenance_staff", phone="+91 9411220033")
    u_admin = User(name="Chief Administrator", email="admin@hostel360.edu", password_hash=password_hash, role="admin", phone="+91 9411220044")
    u_guardian = User(name="Mr. Rajesh Bansal (Parent)", email="guardian@hostel360.edu", password_hash=password_hash, role="guardian", phone="+91 9811223344")
    db.add_all([u_dhruv, s_dhruv, u_arnav, s_arnav, u_janak, s_janak, u_warden, u_mess, u_maint, u_admin, u_guardian])
    db.flush()

    # 5. Complaints (Lifecycle: Submitted -> Assigned -> In Progress -> Resolved -> Closed)
    c1 = Complaint(
        student_id=s_dhruv.id, category="Wi-Fi", room_number="A-101",
        description="High latency and packet drops on 5GHz band near study desk.",
        priority="Medium", status="Resolved", assigned_staff_id=u_maint.id,
        resolution_notes="Replaced faulty access-point patch cord. Signal strength verified at -52 dBm.",
        student_feedback_rating=5, student_feedback_comment="Fixed within 2 hours. Excellent speed now!",
        created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2),
        resolved_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=20)
    )
    c2 = Complaint(
        student_id=s_arnav.id, category="Plumbing", room_number="A-101",
        description="Bathroom faucet leaking water continuously.",
        priority="High", status="In Progress", assigned_staff_id=u_maint.id,
        resolution_notes="Inspected washer gasket. Replacing with new ceramic cartridge.",
        created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    )
    c3 = Complaint(
        student_id=s_janak.id, category="Electrical", room_number="A-102",
        description="Ceiling fan regulator knob stuck on speed 2.",
        priority="Low", status="Assigned", assigned_staff_id=u_maint.id,
        created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    )
    c4 = Complaint(
        student_id=s_dhruv.id, category="Carpentry", room_number="A-101",
        description="Wardrobe door magnetic latch misaligned.",
        priority="Low", status="Submitted",
        created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    )
    db.add_all([c1, c2, c3, c4])

    # 6. Payments
    p1 = Payment(student_id=s_dhruv.id, category="Hostel Rent", amount=45000.0, payment_status="Success", payment_method="UPI Sandbox", receipt_id="REC-2026-94812", transaction_ref="TXN_4A8F91B2C0D3", notes="Semester 7 Hostel Rent - Block A")
    p2 = Payment(student_id=s_dhruv.id, category="Mess Dues", amount=24000.0, payment_status="Success", payment_method="UPI Sandbox", receipt_id="REC-2026-94813", transaction_ref="TXN_9C7D4E1F8B2A", notes="Semester 7 Mess Full Access Subscription")
    p3 = Payment(student_id=s_dhruv.id, category="Security Deposit", amount=10000.0, payment_status="Success", payment_method="NetBanking", receipt_id="REC-2026-94814", transaction_ref="TXN_7E5B3C1D9F0A", notes="Refundable Hostel Caution Deposit")
    p4 = Payment(student_id=s_dhruv.id, category="Laundry Charges", amount=3500.0, payment_status="Pending", payment_method="UPI Sandbox", receipt_id="REC-2026-94815", transaction_ref="TXN_PENDING_001", notes="Semester Laundry Subscription")
    db.add_all([p1, p2, p3, p4])

    # 7. Leave Requests
    l1 = LeaveRequest(
        student_id=s_dhruv.id, leave_type="Home Leave",
        from_date=datetime.datetime.utcnow() + datetime.timedelta(days=2),
        to_date=datetime.datetime.utcnow() + datetime.timedelta(days=5),
        destination="Delhi (Home)", reason="Attending cousin wedding and family gathering.",
        approval_status="Approved", approved_by=u_warden.id, warden_remarks="Granted. Ensure return by Sunday 8:00 PM.",
        qr_gate_pass="GATEPASS-DH1102-20261114"
    )
    l2 = LeaveRequest(
        student_id=s_arnav.id, leave_type="Day Outpass",
        from_date=datetime.datetime.utcnow() + datetime.timedelta(hours=3),
        to_date=datetime.datetime.utcnow() + datetime.timedelta(hours=8),
        destination="Sonepat City Market", reason="Purchasing project electronics components & lab books.",
        approval_status="Pending"
    )
    db.add_all([l1, l2])

    # 8. Notices
    n1 = Notice(title="Mess Menu Revision - Winter Special Menu", message="Effective next Monday, the mess committee will introduce hot masala chai, vegetable soup, and seasonal dessert items during evening snacks and dinner.", audience="All", category="Mess", posted_by=u_warden.id)
    n2 = Notice(title="Exam Quiet Hours Notice (Odd Sem 2026)", message="In view of upcoming mid-term examinations, strict quiet hours will be enforced across all hostel corridors from 10:00 PM to 6:00 AM.", audience="Students", category="General", is_urgent=True, posted_by=u_warden.id)
    n3 = Notice(title="Fee Payment Clearance for Semester 7", message="All residents are requested to clear pending laundry and incidental dues on Hostel 360 portal before the 25th of this month.", audience="Students", category="Fees", posted_by=u_admin.id)
    db.add_all([n1, n2, n3])

    # 9. Mess Menu
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    menu_templates = {
        "Breakfast": "Aloo Paratha with Curd & Pickle, Boiled Eggs / Banana, Tea / Coffee, Cornflakes with Milk",
        "Lunch": "Paneer Butter Masala / Chicken Curry, Dal Tadka, Jeera Rice, Phulka Roti, Green Salad, Gulab Jamun",
        "Snacks": "Veg Cutlet / Samosa with Mint Chutney, Masala Chai, Biscuits",
        "Dinner": "Shahi Paneer / Egg Curry, Mix Dal, Steamed Rice, Tandoori Roti, Kheer / Fruit Custard"
    }
    for day in days:
        for meal, desc in menu_templates.items():
            db.add(MessMenu(day_of_week=day, meal_type=meal, items_description=desc))

    # 10. Sample historical transactions for Dhruv (Past 3 days)
    today = datetime.date.today()
    for offset in range(1, 4):
        past_date = today - datetime.timedelta(days=offset)
        for m in ["Breakfast", "Lunch", "Dinner"]:
            db.add(MessTransaction(
                student_id=s_dhruv.id, meal_type=m, date=past_date,
                status="Verified", amount_deducted=0.0, plan_type_used="subscription",
                verified_by=u_mess.id
            ))

    db.commit()
    db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed()
