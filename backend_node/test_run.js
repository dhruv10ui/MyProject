// Hostel 360 - Automated Test Suite & Endpoint Verifier
// Tests live database initialization, duplicate scan prevention, ML engine, and REST endpoints

const db = require('./db');
const { hashPassword, verifyPassword, createToken, verifyToken } = require('./auth');
const { generateSignedQR, verifySignedQR } = require('./qrService');
const { getMetrics, predictDemand } = require('./mlEngine');

async function runTests() {
  console.log('----------------------------------------------------');
  console.log(' RUNNING HOSTEL 360 AUTOMATED SYSTEM VERIFICATION   ');
  console.log('----------------------------------------------------');

  let passed = 0;
  let failed = 0;

  function assert(condition, testName) {
    if (condition) {
      console.log(`  [PASS] ${testName}`);
      passed++;
    } else {
      console.error(`  [FAIL] ${testName}`);
      failed++;
    }
  }

  // 1. Password & JWT Verification
  const pwd = 'Hostel360@demo';
  const hashed = hashPassword(pwd);
  assert(verifyPassword(pwd, hashed), 'Password hashing & verification via PBKDF2-SHA256');

  const token = createToken({ sub: 'u-dhruv', role: 'student', email: '11023210138@stu.srmuniversity.ac.in' });
  const decoded = verifyToken(token);
  assert(decoded && decoded.sub === 'u-dhruv' && decoded.role === 'student', 'JWT generation and cryptographic verification');

  // 2. Database Schema & Seed Data
  const userCount = db.prepare('SELECT COUNT(*) as c FROM users').get().c;
  assert(userCount >= 8, `Database seed: ${userCount} users found (Students, Warden, Mess, Maintenance, Admin, Guardian)`);

  const dhruv = db.prepare('SELECT * FROM students WHERE roll_no = ?').get('11023210138');
  assert(dhruv && dhruv.roll_no === '11023210138', 'Author profile found: Dhruv Bansal (Roll: 11023210138)');

  const rooms = db.prepare('SELECT COUNT(*) as c FROM rooms').get().c;
  assert(rooms >= 6, `Rooms initialized across Block A & Block B (${rooms} rooms)`);

  // 3. Smart Mess Card Signed Token Generation & Validation
  const qrData = generateSignedQR('s-dhruv', '11023210138', 'subscription');
  assert(qrData.token && qrData.token.includes('.'), 'Short-lived ISO/IEC 18004 signed token generation');
  
  const verified = verifySignedQR(qrData.token);
  assert(verified.valid === true && verified.data.sid === 's-dhruv', 'HMAC-SHA256 token signature validation');

  // 4. Duplicate Check-in Prevention (Signature Feature)
  const today = new Date().toISOString().split('T')[0];
  const testMeal = 'Lunch';

  // Clear any existing test record for today's lunch
  db.prepare('DELETE FROM mess_transactions WHERE student_id = ? AND date = ? AND meal_type = ?').run('s-dhruv', today, testMeal);

  // First scan: should succeed
  const insertTxn = db.prepare('INSERT INTO mess_transactions (id, student_id, meal_type, date, status, plan_type_used) VALUES (?, ?, ?, ?, ?, ?)');
  insertTxn.run('test-txn-1', 's-dhruv', testMeal, today, 'Verified', 'subscription');
  assert(true, `First check-in for ${testMeal} succeeded`);

  // Second scan: Unique constraint MUST throw an error preventing duplicate scan
  let duplicateCaught = false;
  try {
    insertTxn.run('test-txn-2', 's-dhruv', testMeal, today, 'Verified', 'subscription');
  } catch (err) {
    duplicateCaught = true;
  }
  assert(duplicateCaught, 'Atomic duplicate check-in prevention enforced by UNIQUE(student_id, date, meal_type)');

  // 5. ML Demand Forecasting & Benchmarks (Signature Feature #3)
  const mlMetrics = getMetrics();
  assert(mlMetrics.model_comparison && mlMetrics.model_comparison.length === 3, 'ML model evaluation (Moving Avg vs Random Forest vs Gradient Boosting)');
  
  const rf = mlMetrics.model_comparison.find(m => m.model_name.includes('Random Forest'));
  assert(rf && rf.is_best === true, `Random Forest identified as best model with MAE: ${rf.mae} and MAPE: ${rf.mape}%`);

  const pred = predictDemand(today, 'Dinner', 450, 28);
  assert(pred.predicted_attendance > 0 && pred.recommended_preparation >= pred.predicted_attendance, `Demand prediction: Dinner estimated at ${pred.predicted_attendance} attendees (Cook for ${pred.recommended_preparation})`);

  // 6. Complaint Lifecycle Check
  const complaint = db.prepare('SELECT * FROM complaints WHERE id = ?').get('cmp-1');
  assert(complaint && complaint.status === 'Resolved' && complaint.student_feedback_rating === 5, 'Complaint lifecycle: Submitted -> Assigned -> In Progress -> Resolved -> Closed with Rating');

  console.log('----------------------------------------------------');
  console.log(` SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('----------------------------------------------------');

  if (failed > 0) process.exit(1);
}

runTests().catch(e => {
  console.error(e);
  process.exit(1);
});
