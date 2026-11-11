import hmac
import hashlib
import json
import base64
import time
import uuid
import datetime
from app.config import settings

def get_current_meal_session(now: datetime.datetime = None) -> str:
    """Determine the active meal session based on configured timings or current hour."""
    if now is None:
        now = datetime.datetime.now()
    
    current_time_str = now.strftime("%H:%M")
    
    for meal, times in settings.MEAL_TIMINGS.items():
        if times["start"] <= current_time_str <= times["end"]:
            return meal
            
    # Default fallback to nearest session
    hour = now.hour
    if 5 <= hour < 11:
        return "Breakfast"
    elif 11 <= hour < 16:
        return "Lunch"
    elif 16 <= hour < 19:
        return "Snacks"
    else:
        return "Dinner"

def generate_signed_qr_payload(student_id: str, roll_no: str, plan_type: str = "subscription") -> dict:
    """
    Generate short-lived signed cryptographic token for digital mess card.
    Encodes ISO/IEC 18004 compatible payload with expiry countdown.
    """
    now = int(time.time())
    expires_at = now + settings.QR_TOKEN_EXPIRE_SECONDS
    nonce = str(uuid.uuid4())[:8]
    meal_type = get_current_meal_session()

    payload = {
        "sid": student_id,
        "roll": roll_no,
        "iat": now,
        "exp": expires_at,
        "non": nonce,
        "meal": meal_type,
        "plan": plan_type
    }

    # Canonical JSON string
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')

    # HMAC-SHA256 signature
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    token = f"{payload_b64}.{signature}"

    return {
        "token": token,
        "expires_at": expires_at,
        "validity_seconds": settings.QR_TOKEN_EXPIRE_SECONDS,
        "meal_session": meal_type,
        "student_id": student_id,
        "roll_no": roll_no
    }

def verify_signed_qr_payload(token: str) -> dict:
    """
    Validate HMAC signature, freshness, and payload structure.
    Returns: (is_valid: bool, data: dict, error_message: str)
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return {"valid": False, "error": "Invalid token format"}

        payload_b64, signature = parts

        # Verify HMAC signature
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            return {"valid": False, "error": "Cryptographic signature verification failed (tampered token)"}

        # Decode payload
        # Restore base64 padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding

        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)

        # Check expiration
        now = int(time.time())
        if now > payload.get("exp", 0):
            return {"valid": False, "error": "QR Mess Card expired. Please refresh your screen."}

        return {"valid": True, "data": payload, "token_signature": signature}

    except Exception as e:
        return {"valid": False, "error": f"Token verification error: {str(e)}"}
