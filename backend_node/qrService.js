// Hostel 360 - Cryptographic QR Mess Card Service
// Encodes short-lived ISO/IEC 18004 compliant tokens signed with HMAC-SHA256
const crypto = require('node:crypto');
const { SECRET_KEY } = require('./auth');

const QR_EXPIRE_SECONDS = 120; // 2 minutes rotation countdown

const MEAL_TIMINGS = {
  Breakfast: { start: '07:30', end: '09:30', price: 50.0 },
  Lunch: { start: '12:00', end: '14:30', price: 75.0 },
  Snacks: { start: '16:30', end: '18:00', price: 30.0 },
  Dinner: { start: '19:30', end: '22:00', price: 80.0 }
};

function getCurrentMealSession(now = new Date()) {
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const timeStr = `${hours}:${minutes}`;

  for (const [meal, bounds] of Object.entries(MEAL_TIMINGS)) {
    if (timeStr >= bounds.start && timeStr <= bounds.end) {
      return meal;
    }
  }

  // Graceful hour fallback
  const h = now.getHours();
  if (h >= 5 && h < 11) return 'Breakfast';
  if (h >= 11 && h < 16) return 'Lunch';
  if (h >= 16 && h < 19) return 'Snacks';
  return 'Dinner';
}

function generateSignedQR(studentId, rollNo, planType = 'subscription') {
  const now = Math.floor(Date.now() / 1000);
  const expiresAt = now + QR_EXPIRE_SECONDS;
  const nonce = crypto.randomBytes(4).toString('hex');
  const mealSession = getCurrentMealSession();

  const payload = {
    sid: studentId,
    roll: rollNo,
    iat: now,
    exp: expiresAt,
    non: nonce,
    meal: mealSession,
    plan: planType
  };

  const payloadJson = JSON.stringify(payload);
  const payloadB64 = Buffer.from(payloadJson).toString('base64url');
  const signature = crypto.createHmac('sha256', SECRET_KEY).update(payloadB64).digest('hex');

  const token = `${payloadB64}.${signature}`;

  return {
    token,
    expires_at: expiresAt,
    validity_seconds: QR_EXPIRE_SECONDS,
    meal_session: mealSession,
    student_id: studentId,
    roll_no: rollNo
  };
}

function verifySignedQR(token) {
  try {
    if (!token || !token.includes('.')) {
      return { valid: false, error: 'Malformed token structure' };
    }

    const [payloadB64, signature] = token.split('.');
    const expectedSig = crypto.createHmac('sha256', SECRET_KEY).update(payloadB64).digest('hex');

    if (signature !== expectedSig) {
      return { valid: false, error: 'Cryptographic signature mismatch (Token tampered or counterfeit)' };
    }

    const payloadJson = Buffer.from(payloadB64, 'base64url').toString('utf-8');
    const payload = JSON.parse(payloadJson);

    const now = Math.floor(Date.now() / 1000);
    if (now > payload.exp) {
      return { valid: false, error: 'QR Mess Card expired. Please tap refresh on the student screen.' };
    }

    return { valid: true, data: payload, signature };
  } catch (e) {
    return { valid: false, error: `Token validation error: ${e.message}` };
  }
}

module.exports = {
  MEAL_TIMINGS,
  getCurrentMealSession,
  generateSignedQR,
  verifySignedQR
};
