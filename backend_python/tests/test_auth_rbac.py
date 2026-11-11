import pytest
from app.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.qr_engine import generate_signed_qr_payload, verify_signed_qr_payload

def test_password_hashing():
    pwd = "Hostel360@demo"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert "$" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_flow():
    payload = {"sub": "user-12345", "role": "student", "email": "dhruv@hostel360.edu"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-12345"
    assert decoded["role"] == "student"

def test_signed_qr_token_freshness_and_tampering():
    student_id = "test-student-001"
    roll_no = "11023210138"
    token_data = generate_signed_qr_payload(student_id, roll_no, "subscription")
    token = token_data["token"]

    # 1. Valid token check
    verification = verify_signed_qr_payload(token)
    assert verification["valid"] is True
    assert verification["data"]["sid"] == student_id
    assert verification["data"]["roll"] == roll_no

    # 2. Tampered token check
    tampered_token = token[:-5] + "XXXXX"
    bad_verification = verify_signed_qr_payload(tampered_token)
    assert bad_verification["valid"] is False
    assert "signature" in bad_verification["error"].lower() or "tampered" in bad_verification["error"].lower()
