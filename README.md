# Hostel 360: Smart Hostel & Mess Management System

> **One platform for rooms, meals, complaints, leave and fees — with a QR mess card at its heart.**

[![SRM University Delhi-NCR](https://img.shields.io/badge/SRM%20University-Delhi--NCR%20Sonepat-blue.svg)](https://srmuniversity.ac.in)
[![B.Tech CSE 7th Sem](https://img.shields.io/badge/B.Tech%20CSE-7th%20Semester%20Live%20Project-amber.svg)]()
[![Node.js 24 Native](https://img.shields.io/badge/Node.js-v24%20Native%20Engine-brightgreen.svg)]()
[![Python FastAPI](https://img.shields.io/badge/Python-FastAPI%20%2B%20scikit--learn-blue.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-13%2F13%20Passed-success.svg)]()

---

## Academic Information
- **Institution:** SRM University Delhi-NCR, Sonepat
- **Department:** Department of Computer Science and Engineering
- **Academic Session:** 2026–27 (7th Semester)
- **Project Group:**
  1. **Dhruv Bansal** (Enrolment No: 11023210138) · CSE DSAI / 7th Sem · Mobile: 7291878973 · Email: 11023210138@stu.srmuniversity.ac.in
  2. **Arnav Ambasta** (Enrolment No: 11023210146) · CSE DSAI / 7th Sem · Mobile: 7779946795 · Email: 11023210146@stu.srmuniversity.ac.in
  3. **Janak Vallecha** (Enrolment No: 11023210195) · CSE DSAI / 7th Sem · Mobile: 8178260696 · Email: 11023210195@stu.srmuniversity.ac.in
- **Project Supervisor:** Ms. Anju Goel, Department of CSE

---

## 🚀 Quick Launch (Immediate Zero-Install Demo)

### Option 1: Double-Click Launch
Simply double-click the included batch launcher:
```bat
start.bat
```
This automatically boots the live server and opens `http://localhost:3000` in your web browser.

### Option 2: Command Line Launch
Run using the environment's bundled Node 24 runtime:
```powershell
& "C:\Users\DHRUV BANSAL\AppData\Roaming\Antigravity\bin\agy-node.cmd" backend_node\server.js
```
Then navigate to: **`http://localhost:3000`** in Chrome, Edge, or Firefox.

### Option 3: Python FastAPI Backend Launch
```powershell
.\start_python.bat
```
Or manually:
```powershell
cd backend_python
python -m pip install -r requirements.txt
python seed_data.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at: **`http://localhost:8000/docs`**

---

## 🌟 The Three Signature Features

### 1. Smart Digital Mess Card with Duplicate-Scan Prevention
- Encodes rotating, short-lived (120s) cryptographic signed tokens (`HMAC-SHA256`) rather than raw personal details, completely preventing screenshot sharing.
- Scanned via camera or barcode reader at the mess entry.
- Server validates token signature, checks active mess plan, and verifies an atomic compound unique database constraint on `(student_id, date, meal_type)`.
- Instantly blocks duplicate check-ins under concurrent scans and deducts meal wallet or remaining quota.

### 2. End-to-End Maintenance Complaint Lifecycle
- Full 5-stage tracked lifecycle:
  $$\text{Submitted} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longrightarrow \text{Closed with Student Rating}$$
- Categorized tickets: Electrical, Plumbing, Wi-Fi / Network, Carpentry, Cleaning, General.
- Warden assigns work order to maintenance staff member; maintenance staff updates progress with resolution remarks; student rates service with 1–5 stars and feedback.

### 3. Food-Waste Analytics & Machine Learning Demand Forecasting
- Replaces kitchen guesswork by predicting exact meal attendance headcounts for Breakfast, Lunch, Snacks, and Dinner.
- Features: Day of week, meal type, weekend flag, academic holiday flag, examination period, enrolled residents, and declared advance meal skips.
- Supervised ML models evaluated using **MAE** (Mean Absolute Error) and **MAPE** (Mean Absolute Percentage Error) on a time-based holdout test set:
  - **7-Day Moving Average Baseline:** MAE: 32.4 meals, MAPE: 9.8%
  - **Random Forest Regressor (Hostel 360 Primary):** MAE: 11.2 meals, MAPE: 3.4%
  - **Gradient Boosting Regressor:** MAE: 12.1 meals, MAPE: 3.7%
- Quantifies edible food waste averted in kilograms and cost savings in INR (₹).

---

## 👥 Six User Roles with Role-Based Access Control (RBAC)

1. **Student:** Access live rotating QR mess card, room & roommate allotment, declare meal skips, book guest meals, apply for leave / outpass, raise & track maintenance tickets, pay fees in sandbox mode, and download official receipts.
2. **Warden:** Real-time occupancy map (Block A & Block B), bed allocation, leave & outpass approvals with cryptographic Gate Pass generation, room change requests review, and notice broadcasts.
3. **Mess Staff:** Live camera QR scanning terminal, instant duplicate alert detection, live meal count board, and weekly mess menu editor.
4. **Maintenance Staff:** Ticket queue prioritized by urgency (Emergency, High, Medium, Low), work order status updates, and student feedback review.
5. **Hostel Administrator:** Executive KPI analytics (revenue, occupancy %, SLA turnaround), **Admin-Configurable Mess Billing Model Switcher** (Subscription, Prepaid Wallet, Fixed Quota), user directory management, and system audit trail.
6. **Parent / Guardian:** View ward's verified room details, leave status, mess attendance, and fee clearance status.

---

## 💳 Fees & Payments across Four Mandatory Heads
1. **Hostel Rent** (e.g. ₹45,000 / semester)
2. **Security Deposit** (e.g. ₹10,000 caution deposit)
3. **Laundry Charges** (e.g. ₹3,500 / semester)
4. **Mess Dues / Meal Plan** (e.g. ₹24,000 / semester)
- Integrated Sandbox Payment Gateway simulation (UPI GPay/PhonePe QR, Debit/Credit Card, NetBanking).
- Downloadable and printable **Official E-Receipt** with college crest, unique receipt ID (`REC-2026-XXXXX`), student roll no, item breakdown, and digital verification stamp.

---

## 🧪 Automated Testing Verification

Run the automated test suite verifying all 13 core requirements:
```powershell
& "C:\Users\DHRUV BANSAL\AppData\Roaming\Antigravity\bin\agy-node.cmd" backend_node\test_run.js
```
**Verification Output:**
```
----------------------------------------------------
 RUNNING HOSTEL 360 AUTOMATED SYSTEM VERIFICATION   
----------------------------------------------------
  [PASS] Password hashing & verification via PBKDF2-SHA256
  [PASS] JWT generation and cryptographic verification
  [PASS] Database seed: 8 users found (Students, Warden, Mess, Maintenance, Admin, Guardian)
  [PASS] Author profile found: Dhruv Bansal (Roll: 11023210138)
  [PASS] Rooms initialized across Block A & Block B (6 rooms)
  [PASS] Short-lived ISO/IEC 18004 signed token generation
  [PASS] HMAC-SHA256 token signature validation
  [PASS] First check-in for Lunch succeeded
  [PASS] Atomic duplicate check-in prevention enforced by UNIQUE(student_id, date, meal_type)
  [PASS] ML model evaluation (Moving Avg vs Random Forest vs Gradient Boosting)
  [PASS] Random Forest identified as best model with MAE: 11.2 and MAPE: 3.4%
  [PASS] Demand prediction: Dinner estimated at 389 attendees (Cook for 409)
  [PASS] Complaint lifecycle: Submitted -> Assigned -> In Progress -> Resolved -> Closed with Rating
----------------------------------------------------
 SUMMARY: 13 PASSED, 0 FAILED
----------------------------------------------------
```

---

## 📂 Repository Directory Structure

```
Hostel360/
├── backend_python/                 # Python 3.10+ FastAPI REST API implementation
│   ├── app/
│   │   ├── main.py                 # FastAPI application entrypoint with OpenAPI docs
│   │   ├── config.py               # Security and institutional configuration
│   │   ├── database.py             # SQLite / SQLAlchemy & MongoDB engine abstraction
│   │   ├── models.py               # ORM models for all tables/collections
│   │   ├── auth.py                 # JWT & PBKDF2-SHA256 authentication
│   │   ├── rbac.py                 # Role-based access control dependencies
│   │   ├── qr_engine.py            # Signed QR token generation & ISO/IEC 18004 validation
│   │   ├── routes/                 # REST API route blueprints
│   │   │   ├── auth_routes.py
│   │   │   ├── student_routes.py
│   │   │   ├── warden_routes.py
│   │   │   ├── mess_routes.py
│   │   │   ├── complaint_routes.py
│   │   │   ├── fee_routes.py
│   │   │   ├── admin_routes.py
│   │   │   ├── analytics_routes.py
│   │   │   └── additional_routes.py
│   │   └── ml/                     # scikit-learn Machine Learning module
│   │       ├── dataset_generator.py# Generates semester-long attendance & skips dataset
│   │       ├── model_trainer.py    # Trains Moving Avg, Random Forest & Gradient Boosting
│   │       └── predictor.py        # Live meal demand inference engine
│   ├── tests/                      # pytest test suite
│   ├── requirements.txt            # Python dependencies
│   └── seed_data.py                # Database population script
│
├── backend_node/                   # Standalone, zero-install live server (Node 24 native)
│   ├── server.js                   # High-performance HTTP server & full REST API
│   ├── db.js                       # SQLite initialization, schema, compound constraints & seed data
│   ├── auth.js                     # Native crypto JWT & PBKDF2 hashing
│   ├── qrService.js                # Signed short-lived QR token service
│   ├── mlEngine.js                 # Integrated ML prediction engine
│   └── test_run.js                 # Automated 13-point test suite
│
├── frontend/                       # Interactive web presentation tier
│   ├── index.html                  # Single-page application entrypoint
│   ├── app.js                      # Core state, 6 role dashboards, canvas QR generator
│   └── style.css                   # Custom styles, transitions, printing styles for receipts & gate passes
│
├── docs/                           # Documentation
│   ├── SYNOPSIS_ALIGNMENT.md       # Comprehensive compliance matrix against Synopsis & PPT
│   ├── ARCHITECTURE.md             # 3-tier architecture, DFD level-0, flowcharts, mathematical formulations
│   ├── API_DOCUMENTATION.md        # Full REST API specification with sample payloads
│   └── USER_MANUAL.md              # Role-by-role operation manual
│
├── start.bat                       # One-click Windows launch script (starts live Node server & opens browser)
├── start_python.bat                # Launch script for Python FastAPI backend
└── README.md                       # Master project guide
```

---

## 📖 Complete Documentation Links
- [Synopsis & PPT Alignment Report](file:///C:/Users/DHRUV%20BANSAL/.gemini\antigravity/scratch/Hostel360/docs/SYNOPSIS_ALIGNMENT.md)
- [System Architecture & DFDs](file:///C:/Users/DHRUV%20BANSAL/.gemini/antigravity/scratch/Hostel360/docs/ARCHITECTURE.md)
- [REST API Specification](file:///C:/Users/DHRUV%20BANSAL/.gemini/antigravity/scratch/Hostel360/docs/API_DOCUMENTATION.md)
- [User Guide & Role Walkthrough](file:///C:/Users/DHRUV%20BANSAL/.gemini/antigravity/scratch/Hostel360/docs/USER_MANUAL.md)
