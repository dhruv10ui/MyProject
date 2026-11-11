// Hostel 360 - Embedded Database Initializer & Migration Engine
// Uses Node 24 native node:sqlite DatabaseSync
const { DatabaseSync } = require('node:sqlite');
const path = require('node:path');
const crypto = require('node:crypto');
const { hashPassword } = require('./auth');

const DB_PATH = path.join(__dirname, 'hostel360_live.db');
const db = new DatabaseSync(DB_PATH);

// Enable WAL mode for high performance concurrency
db.exec('PRAGMA journal_mode = WAL;');
db.exec('PRAGMA foreign_keys = ON;');

function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL,
      phone TEXT,
      avatar TEXT,
      is_active INTEGER DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rooms (
      id TEXT PRIMARY KEY,
      block TEXT NOT NULL,
      floor INTEGER NOT NULL,
      room_number TEXT UNIQUE NOT NULL,
      capacity INTEGER NOT NULL DEFAULT 2,
      occupied_beds INTEGER NOT NULL DEFAULT 0,
      room_type TEXT DEFAULT 'Double Non-AC',
      status TEXT DEFAULT 'Available',
      amenities TEXT DEFAULT 'Attached Bath, Study Table, Balcony, Wi-Fi'
    );

    CREATE TABLE IF NOT EXISTS mess_plans (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      plan_type TEXT NOT NULL,
      price REAL NOT NULL,
      validity_days INTEGER DEFAULT 30,
      meal_quota INTEGER DEFAULT 60,
      meal_price REAL DEFAULT 65.0,
      description TEXT,
      is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS students (
      id TEXT PRIMARY KEY,
      user_id TEXT UNIQUE NOT NULL,
      roll_no TEXT UNIQUE NOT NULL,
      room_id TEXT,
      bed_no TEXT,
      branch TEXT DEFAULT 'CSE DSAI',
      semester INTEGER DEFAULT 7,
      guardian_name TEXT,
      guardian_contact TEXT,
      guardian_email TEXT,
      active_plan_id TEXT,
      wallet_balance REAL DEFAULT 1500.0,
      remaining_meal_quota INTEGER DEFAULT 60,
      plan_expiry_date TEXT,
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(room_id) REFERENCES rooms(id),
      FOREIGN KEY(active_plan_id) REFERENCES mess_plans(id)
    );

    -- SIGNATURE TRANSACTION: UNIQUE(student_id, date, meal_type) PREVENTS DUPLICATE SCANS
    CREATE TABLE IF NOT EXISTS mess_transactions (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      meal_type TEXT NOT NULL,
      date TEXT NOT NULL,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      status TEXT DEFAULT 'Verified',
      token_id TEXT,
      amount_deducted REAL DEFAULT 0.0,
      plan_type_used TEXT DEFAULT 'subscription',
      verified_by TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id),
      CONSTRAINT uq_student_meal_session UNIQUE(student_id, date, meal_type)
    );

    CREATE TABLE IF NOT EXISTS meal_skips (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      date TEXT NOT NULL,
      meal_type TEXT NOT NULL,
      reason TEXT DEFAULT 'Dining Outside',
      declared_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id),
      CONSTRAINT uq_student_skip UNIQUE(student_id, date, meal_type)
    );

    CREATE TABLE IF NOT EXISTS guest_meals (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      guest_name TEXT NOT NULL,
      date TEXT NOT NULL,
      meal_type TEXT NOT NULL,
      count INTEGER DEFAULT 1,
      amount REAL DEFAULT 80.0,
      payment_status TEXT DEFAULT 'Paid',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS payments (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      category TEXT NOT NULL,
      amount REAL NOT NULL,
      payment_status TEXT DEFAULT 'Success',
      payment_method TEXT DEFAULT 'UPI Sandbox',
      receipt_id TEXT UNIQUE NOT NULL,
      transaction_ref TEXT UNIQUE NOT NULL,
      notes TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS leave_requests (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      leave_type TEXT DEFAULT 'Home Leave',
      from_date TEXT NOT NULL,
      to_date TEXT NOT NULL,
      reason TEXT NOT NULL,
      destination TEXT NOT NULL,
      approval_status TEXT DEFAULT 'Pending',
      approved_by TEXT,
      warden_remarks TEXT,
      qr_gate_pass TEXT,
      applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
      decided_at TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id)
    );

    -- SIGNATURE FEATURE: COMPLAINT LIFECYCLE
    CREATE TABLE IF NOT EXISTS complaints (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      category TEXT NOT NULL,
      room_number TEXT NOT NULL,
      description TEXT NOT NULL,
      photo_url TEXT,
      priority TEXT DEFAULT 'Medium',
      assigned_staff_id TEXT,
      status TEXT DEFAULT 'Submitted',
      resolution_notes TEXT,
      student_feedback_rating INTEGER,
      student_feedback_comment TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      resolved_at TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id),
      FOREIGN KEY(assigned_staff_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS visitors (
      id TEXT PRIMARY KEY,
      host_student_id TEXT NOT NULL,
      visitor_name TEXT NOT NULL,
      relation TEXT NOT NULL,
      phone TEXT NOT NULL,
      visit_date TEXT NOT NULL,
      purpose TEXT DEFAULT 'Family Visit',
      check_in_time TEXT,
      check_out_time TEXT,
      approval_status TEXT DEFAULT 'Approved',
      approved_by TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(host_student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS notices (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      message TEXT NOT NULL,
      audience TEXT DEFAULT 'All',
      category TEXT DEFAULT 'General',
      posted_by TEXT NOT NULL,
      is_urgent INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(posted_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS mess_menus (
      id TEXT PRIMARY KEY,
      day_of_week TEXT NOT NULL,
      meal_type TEXT NOT NULL,
      items_description TEXT NOT NULL,
      dietary_info TEXT DEFAULT 'Standard Indian Vegetarian / Non-Veg options'
    );

    CREATE TABLE IF NOT EXISTS room_change_requests (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      current_room_id TEXT NOT NULL,
      requested_room_id TEXT,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'Pending',
      reviewed_by TEXT,
      remarks TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
      id TEXT PRIMARY KEY,
      actor_id TEXT NOT NULL,
      actor_role TEXT NOT NULL,
      action TEXT NOT NULL,
      entity TEXT NOT NULL,
      details TEXT,
      ip_address TEXT DEFAULT '127.0.0.1',
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS system_configs (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      description TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);
}

function seedInitialData() {
  const userCount = db.prepare('SELECT COUNT(*) as count FROM users').get().count;
  if (userCount > 0) return; // Already seeded

  console.log('Seeding demo database for Hostel 360...');

  // System config
  db.prepare('INSERT INTO system_configs (key, value, description) VALUES (?, ?, ?)')
    .run('ACTIVE_BILLING_MODEL', 'subscription', 'Default active billing model: subscription, wallet, or quota');

  // Rooms
  const rooms = [
    { id: 'rm-101', block: 'Block A', floor: 1, room_number: 'A-101', capacity: 2, occupied: 2, type: 'Double Non-AC', status: 'Occupied' },
    { id: 'rm-102', block: 'Block A', floor: 1, room_number: 'A-102', capacity: 2, occupied: 1, type: 'Double Non-AC', status: 'Available' },
    { id: 'rm-201', block: 'Block A', floor: 2, room_number: 'A-201', capacity: 3, occupied: 0, type: 'Triple Non-AC', status: 'Available' },
    { id: 'rm-202', block: 'Block A', floor: 2, room_number: 'A-202', capacity: 2, occupied: 0, type: 'Double AC', status: 'Available' },
    { id: 'rm-b101', block: 'Block B', floor: 1, room_number: 'B-101', capacity: 2, occupied: 0, type: 'Double Non-AC', status: 'Available' },
    { id: 'rm-b201', block: 'Block B', floor: 2, room_number: 'B-201', capacity: 2, occupied: 0, type: 'Double AC', status: 'Available' }
  ];

  const insertRoom = db.prepare('INSERT INTO rooms (id, block, floor, room_number, capacity, occupied_beds, room_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
  for (const r of rooms) {
    insertRoom.run(r.id, r.block, r.floor, r.room_number, r.capacity, r.occupied, r.type, r.status);
  }

  // Mess Plans
  const plans = [
    { id: 'plan-sub', name: 'All-Access Monthly Subscription', type: 'subscription', price: 4500, days: 30, quota: 120, mealPrice: 65, desc: 'Unlimited Breakfast, Lunch, Snacks & Dinner' },
    { id: 'plan-wal', name: 'Pay-As-You-Eat Prepaid Wallet', type: 'wallet', price: 2000, days: 60, quota: 0, mealPrice: 65, desc: 'Per-meal deductions from balance' },
    { id: 'plan-qta', name: '60-Meal Smart Quota Pack', type: 'quota', price: 3600, days: 45, quota: 60, mealPrice: 60, desc: 'Ideal for frequent weekend commuters' }
  ];
  const insertPlan = db.prepare('INSERT INTO mess_plans (id, name, plan_type, price, validity_days, meal_quota, meal_price, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
  for (const p of plans) {
    insertPlan.run(p.id, p.name, p.type, p.price, p.days, p.quota, p.mealPrice, p.desc);
  }

  // Users (Standard password: Hostel360@demo)
  const defaultPasswordHash = hashPassword('Hostel360@demo');
  const insertUser = db.prepare('INSERT INTO users (id, name, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?, ?)');
  const insertStudent = db.prepare('INSERT INTO students (id, user_id, roll_no, room_id, bed_no, branch, semester, guardian_name, guardian_contact, guardian_email, active_plan_id, wallet_balance, remaining_meal_quota) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');

  // 1. Dhruv Bansal (Student Author)
  insertUser.run('u-dhruv', 'Dhruv Bansal', '11023210138@stu.srmuniversity.ac.in', defaultPasswordHash, 'student', '+91 7291878973');
  insertStudent.run('s-dhruv', 'u-dhruv', '11023210138', 'rm-101', 'Bed A', 'CSE DSAI', 7, 'Mr. Rajesh Bansal', '+91 9811223344', 'guardian@hostel360.edu', 'plan-sub', 1850.0, 54);

  // 2. Arnav Ambasta (Student Author)
  insertUser.run('u-arnav', 'Arnav Ambasta', '11023210146@stu.srmuniversity.ac.in', defaultPasswordHash, 'student', '+91 7779946795');
  insertStudent.run('s-arnav', 'u-arnav', '11023210146', 'rm-101', 'Bed B', 'CSE DSAI', 7, 'Mr. S. K. Ambasta', '+91 9822334455', 'arnav.guardian@gmail.com', 'plan-wal', 2400.0, 45);

  // 3. Janak Vallecha (Student Author)
  insertUser.run('u-janak', 'Janak Vallecha', '11023210195@stu.srmuniversity.ac.in', defaultPasswordHash, 'student', '+91 8178260696');
  insertStudent.run('s-janak', 'u-janak', '11023210195', 'rm-102', 'Bed A', 'CSE DSAI', 7, 'Mr. P. Vallecha', '+91 9833445566', 'janak.guardian@gmail.com', 'plan-qta', 920.0, 38);

  // Staff accounts
  insertUser.run('u-warden', 'Dr. Rakesh Sharma', 'warden@hostel360.edu', defaultPasswordHash, 'warden', '+91 9411220011');
  insertUser.run('u-mess', 'Suresh Kumar (Mess Manager)', 'mess@hostel360.edu', defaultPasswordHash, 'mess_staff', '+91 9411220022');
  insertUser.run('u-maint', 'Ramesh Electrician', 'maintenance@hostel360.edu', defaultPasswordHash, 'maintenance_staff', '+91 9411220033');
  insertUser.run('u-admin', 'Chief Administrator', 'admin@hostel360.edu', defaultPasswordHash, 'admin', '+91 9411220044');
  insertUser.run('u-guardian', 'Mr. Rajesh Bansal (Parent)', 'guardian@hostel360.edu', defaultPasswordHash, 'guardian', '+91 9811223344');

  // Complaints
  const insertComplaint = db.prepare('INSERT INTO complaints (id, student_id, category, room_number, description, priority, assigned_staff_id, status, resolution_notes, student_feedback_rating, student_feedback_comment, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
  insertComplaint.run('cmp-1', 's-dhruv', 'Wi-Fi', 'A-101', 'High latency and packet drops on 5GHz band near study desk.', 'Medium', 'u-maint', 'Resolved', 'Replaced faulty access-point patch cord. Signal verified at -52 dBm.', 5, 'Resolved in 2 hours. Superb speed now!', '2026-11-09 10:15:00', '2026-11-09 12:45:00');
  insertComplaint.run('cmp-2', 's-arnav', 'Plumbing', 'A-101', 'Bathroom faucet leaking water continuously.', 'High', 'u-maint', 'In Progress', 'Inspected washer gasket. Replacing ceramic cartridge.', null, null, '2026-11-11 14:00:00', null);
  insertComplaint.run('cmp-3', 's-janak', 'Electrical', 'A-102', 'Ceiling fan regulator knob stuck on speed 2.', 'Low', 'u-maint', 'Assigned', null, null, null, '2026-11-11 08:30:00', null);
  insertComplaint.run('cmp-4', 's-dhruv', 'Carpentry', 'A-101', 'Wardrobe door magnetic latch misaligned.', 'Low', null, 'Submitted', null, null, null, '2026-11-11 18:00:00', null);

  // Payments
  const insertPayment = db.prepare('INSERT INTO payments (id, student_id, category, amount, payment_status, payment_method, receipt_id, transaction_ref, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
  insertPayment.run('pay-1', 's-dhruv', 'Hostel Rent', 45000.0, 'Success', 'UPI Sandbox', 'REC-2026-94812', 'TXN_4A8F91B2C0D3', 'Semester 7 Hostel Rent - Block A');
  insertPayment.run('pay-2', 's-dhruv', 'Mess Dues', 24000.0, 'Success', 'UPI Sandbox', 'REC-2026-94813', 'TXN_9C7D4E1F8B2A', 'Semester 7 Mess Full Access Subscription');
  insertPayment.run('pay-3', 's-dhruv', 'Security Deposit', 10000.0, 'Success', 'NetBanking', 'REC-2026-94814', 'TXN_7E5B3C1D9F0A', 'Refundable Caution Deposit');
  insertPayment.run('pay-4', 's-dhruv', 'Laundry Charges', 3500.0, 'Pending', 'UPI Sandbox', 'REC-2026-94815', 'TXN_PENDING_001', 'Semester Laundry Subscription');

  // Leaves
  const insertLeave = db.prepare('INSERT INTO leave_requests (id, student_id, leave_type, from_date, to_date, reason, destination, approval_status, approved_by, warden_remarks, qr_gate_pass) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
  insertLeave.run('lv-1', 's-dhruv', 'Home Leave', '2026-11-14T08:00:00', '2026-11-17T20:00:00', 'Attending cousin wedding and family gathering.', 'Delhi (Home)', 'Approved', 'u-warden', 'Granted. Ensure return by Sunday 8:00 PM.', 'GATEPASS-DH1102-20261114');
  insertLeave.run('lv-2', 's-arnav', 'Day Outpass', '2026-11-12T15:00:00', '2026-11-12T20:00:00', 'Purchasing project components & lab stationery.', 'Sonepat City Market', 'Pending', null, null, null);

  // Notices
  const insertNotice = db.prepare('INSERT INTO notices (id, title, message, audience, category, posted_by, is_urgent) VALUES (?, ?, ?, ?, ?, ?, ?)');
  insertNotice.run('not-1', 'Mess Menu Revision - Winter Special Menu', 'Effective next Monday, the mess will introduce hot masala chai, vegetable soup, and seasonal desserts during evening snacks & dinner.', 'All', 'Mess', 'u-warden', 0);
  insertNotice.run('not-2', 'Exam Quiet Hours Notice (Odd Sem 2026)', 'In view of upcoming mid-term exams, strict quiet hours are enforced in all corridors from 10:00 PM to 6:00 AM.', 'Students', 'General', 'u-warden', 1);
  insertNotice.run('not-3', 'Fee Payment Clearance for Semester 7', 'All residents are requested to clear pending laundry and incidental dues on Hostel 360 portal before the 25th.', 'Students', 'Fees', 'u-admin', 0);

  // Mess Menu
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const menuTemplates = {
    Breakfast: 'Aloo Paratha with Curd & Pickle, Boiled Eggs / Banana, Tea / Coffee, Cornflakes with Milk',
    Lunch: 'Paneer Butter Masala / Chicken Curry, Dal Tadka, Jeera Rice, Phulka Roti, Green Salad, Gulab Jamun',
    Snacks: 'Veg Cutlet / Samosa with Mint Chutney, Masala Chai, Biscuits',
    Dinner: 'Shahi Paneer / Egg Curry, Mix Dal, Steamed Rice, Tandoori Roti, Kheer / Fruit Custard'
  };
  const insertMenu = db.prepare('INSERT INTO mess_menus (id, day_of_week, meal_type, items_description) VALUES (?, ?, ?, ?)');
  let menuCounter = 1;
  for (const day of days) {
    for (const [meal, desc] of Object.entries(menuTemplates)) {
      insertMenu.run(`menu-${menuCounter++}`, day, meal, desc);
    }
  }

  // Pre-seed 3 past days transactions for Dhruv
  const insertTxn = db.prepare('INSERT OR IGNORE INTO mess_transactions (id, student_id, meal_type, date, status, amount_deducted, plan_type_used, verified_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
  const today = new Date().toISOString().split('T')[0];
  insertTxn.run('txn-past-1', 's-dhruv', 'Breakfast', '2026-11-09', 'Verified', 0, 'subscription', 'u-mess');
  insertTxn.run('txn-past-2', 's-dhruv', 'Lunch', '2026-11-09', 'Verified', 0, 'subscription', 'u-mess');
  insertTxn.run('txn-past-3', 's-dhruv', 'Dinner', '2026-11-09', 'Verified', 0, 'subscription', 'u-mess');
  insertTxn.run('txn-past-4', 's-dhruv', 'Breakfast', '2026-11-10', 'Verified', 0, 'subscription', 'u-mess');
  insertTxn.run('txn-past-5', 's-dhruv', 'Lunch', '2026-11-10', 'Verified', 0, 'subscription', 'u-mess');

  console.log('Database initialization and seeding complete.');
}

initSchema();
seedInitialData();

module.exports = db;
