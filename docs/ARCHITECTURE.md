# Hostel 360 - System Architecture & Technical Specification

## 1. Three-Tier System Architecture

Hostel 360 employs a standard, modular, enterprise-grade three-tier architecture:

```
+---------------------------------------------------------------------------------------+
|                           PRESENTATION TIER (Web Client)                             |
|  - Single-Page Responsive Application (React / HTML5 / Tailwind CSS)                  |
|  - 6 Role Portals: Student, Warden, Mess Staff, Maintenance, Admin, Guardian          |
|  - Smart Canvas QR Code Generator & Browser Camera QR Scanner                         |
|  - Real-Time Charting & Printable E-Receipts / Gate Passes                            |
+---------------------------------------------------------------------------------------+
                                           |
                                [HTTPS / JSON REST API]
                                           |
+---------------------------------------------------------------------------------------+
|                         APPLICATION TIER (REST API Server)                            |
|  - FastAPI (Python 3.10+) & Node 24 Native Engines                                    |
|  - JSON Web Token (JWT) Bearer Authentication & PBKDF2-SHA256 Password Hashing         |
|  - Role-Based Access Control (RBAC) Enforcement Middleware                            |
|  - Cryptographic ISO/IEC 18004 QR Token Issuance & Signature Verification             |
|  - Configurable Billing Engine (Subscription / Prepaid Wallet / Meal Quota)           |
|  - Maintenance Complaint 5-Stage Lifecycle State Machine                              |
|  - Machine Learning Module (scikit-learn Random Forest & Gradient Boosting)          |
+---------------------------------------------------------------------------------------+
                                           |
                                [SQL / ORM Query Layer]
                                           |
+---------------------------------------------------------------------------------------+
|                            DATA TIER (Storage & Logs)                                 |
|  - Relational Database (SQLite / MySQL) with Compound Unique Constraints              |
|  - Atomic Concurrency Protection on (student_id, date, meal_type)                     |
|  - Append-Only Security & Administrative Audit Log Trail                              |
+---------------------------------------------------------------------------------------+
```

---

## 2. Level-0 Data Flow Diagram (Context Diagram)

The Level-0 DFD defines the boundary of the Hostel 360 system and its interactions with the six external entities:

```
                         [Student]
                            |  ^
   Requests, Complaints,    |  |  Allotment, Mess Card,
   Payments, Leaves         v  |  Receipts, Notices
             +----------------------------------+
             |                                  | <--- Configuration, Policy,
             |                                  |      User Management
[Warden] <---|                0                 | ---> [Administrator]
Approvals,   |            HOSTEL 360            |      Financial & System Reports
Rooms,       |      MANAGEMENT PLATFORM         |
Notices      |                                  | <--- Assign / Resolve Tasks
             |                                  | ---> [Maintenance Staff]
             +----------------------------------+
                            |  ^
   QR Scans, Verification,  |  |  Meal Count, Roster,
   Attendance Logging       v  |  Demand Forecast
                        [Mess Staff]
                             |
                             v
                     [Parent / Guardian]
                  (Leave status & Notices)
```

---

## 3. QR Mess Check-in Flow & Duplicate Prevention Algorithm

The primary operational transaction of Hostel 360 is the digital mess check-in. The sequence follows a zero-trust, 4-step cryptographic protocol:

```
[Student Device]                 [Mess Terminal / Scanner]             [Backend Server & DB]
       |                                    |                                    |
       |-- 1. Requests fresh QR Mess Card ->|                                    |
       |<-- Returns HMAC-signed token ------|                                    |
       |    (Expires in 120 seconds)        |                                    |
       |                                    |                                    |
       |==== 2. Student displays QR =======>|                                    |
       |    Camera scans ISO/IEC 18004 code |                                    |
       |                                    |-- 3. POST /api/mess/scan-qr ------>|
       |                                    |      (Token, Session)              |
       |                                    |                                    |-- Verify HMAC signature
       |                                    |                                    |-- Check token expiry (now < exp)
       |                                    |                                    |-- Check student active plan
       |                                    |                                    |-- Check UNIQUE(student_id, date, meal)
       |                                    |                                    |
       |                                    |                                    | [If Already Checked In]
       |                                    |<-- 4b. Status: Duplicate Scan -----| (Return existing timestamp)
       |                                    |
       |                                    |                                    | [If First Valid Scan]
       |                                    |                                    |-- Deduct Wallet / Quota
       |                                    |                                    |-- INSERT mess_transactions
       |                                    |<-- 4a. Status: Verified Success ---| (Return student name, room)
       |<=== Visual & Audio Feedback =======|
```

### Why it is impossible to cheat:
1. **Dynamic Time-Limited Tokens:** Tokens expire every 120 seconds. Static screenshots shared over WhatsApp/Telegram expire immediately and are rejected.
2. **Cryptographic HMAC-SHA256:** Students cannot tamper with their wallet balance or expiration date because modifying a single character invalidates the digital signature.
3. **Database-Level Compound Unique Index:** Even under simultaneous burst scans across multiple counters, SQLite / MySQL enforces `UNIQUE(student_id, date, meal_type)` at the storage layer, rejecting any secondary scan atomically.

---

## 4. Machine Learning Food-Waste Prediction Formulation

Traditional hostel kitchens operate on fixed rule-of-thumb guesswork (e.g., preparing food for 85–90% of enrolled residents every meal), leading to severe food waste on weekends and shortages during examination periods.

### Mathematical Formulation
The regression target is:
$$\hat{Y}_{d, m} = f(\mathbf{x}_{d, m})$$

Where $\mathbf{x}_{d, m}$ is the feature vector composed of:
1. $D \in \{0, \dots, 6\}$: Day of the week.
2. $M \in \{\text{Breakfast}, \text{Lunch}, \text{Snacks}, \text{Dinner}\}$: One-hot encoded meal session.
3. $W \in \{0, 1\}$: Weekend indicator flag.
4. $H \in \{0, 1\}$: Academic holiday flag.
5. $E \in \{0, 1\}$: Examination period indicator.
6. $N$: Total currently enrolled students in hostel.
7. $S_{d, m}$: Total declared meal skips logged prior to session cutoff.
8. $\bar{A}_{7}$: Rolling 7-day moving average attendance for meal $M$.

### Error Metrics
Models are judged on a chronological holdout test set using:
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
- **Mean Absolute Percentage Error (MAPE):**
  $$\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^n \left|\frac{y_i - \hat{y}_i}{y_i}\right|$$

Recommended preparation quantity prepared with a safety buffer:
$$C_{\text{prep}} = \lceil 1.05 \times \hat{Y}_{d, m} \rceil$$
Food waste prevented:
$$\text{Waste Saved (kg)} = \max(0, C_{\text{traditional}} - C_{\text{prep}}) \times 0.42\text{ kg/meal}$$
Monetary savings:
$$\text{Cost Savings (₹)} = \text{Waste Saved (kg)} \times 75.00\text{ ₹/kg}$$

---

## 5. Security and Privacy Architecture (DPDP Act 2023)

In accordance with India's **Digital Personal Data Protection Act, 2023**:
- **Data Minimization:** Only operational parameters (name, roll no, room, meal counts) are stored. Biometric raw imagery is excluded from the first release.
- **Credential Protection:** Passwords are never stored in plain text. PBKDF2 with 100,000 SHA-256 iterations and per-user cryptographic salts are enforced.
- **Audit Logging:** Every administrative permission modification, leave approval, and attendance override is timestamped and logged in `audit_logs` with actor ID and IP address.
- **Ephemeral QR Codes:** Student QR codes encode transient session tokens rather than student Aadhaar or personal phone numbers.
