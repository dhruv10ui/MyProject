# Hostel 360 - REST API Documentation & Endpoint Specification

Base URL: `http://localhost:3000/api` (or `http://localhost:8000/api` for Python FastAPI)

All requests requiring authentication must include the HTTP header:
`Authorization: Bearer <access_token>`

---

## 1. Authentication Endpoints

### `POST /auth/login`
Authenticates a user and issues a JWT token.
- **Request Body:**
```json
{
  "email": "11023210138@stu.srmuniversity.ac.in",
  "password": "Hostel360@demo"
}
```
- **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "u-dhruv",
    "name": "Dhruv Bansal",
    "email": "11023210138@stu.srmuniversity.ac.in",
    "role": "student",
    "phone": "+91 7291878973"
  }
}
```

### `POST /auth/switch-demo`
Demo switcher to test all 6 roles seamlessly without entering passwords.
- **Request Body:** `{"target_role": "student" | "warden" | "mess_staff" | "maintenance_staff" | "admin" | "guardian"}`

---

## 2. Student Portal Endpoints

### `GET /student/dashboard`
Returns consolidated student profile, room details, roommates, wallet balance, quota, and today's meal status.

### `GET /student/mess-card`
Generates a fresh, rotating short-lived ISO/IEC 18004 signed token with 120-second countdown.
- **Response (200 OK):**
```json
{
  "token": "eyJzaWQiOiJzLWRocnV2Iiwicm9sbCI6IjExMDIzMjEwMTM4In0.8a7b9c...",
  "expires_at": 1731341200,
  "validity_seconds": 120,
  "meal_session": "Dinner",
  "student_name": "Dhruv Bansal",
  "wallet_balance": 1850.0,
  "remaining_meal_quota": 54
}
```

### `POST /student/meal-skip`
Declares an advance meal skip to prevent kitchen food waste.
- **Request Body:** `{"date": "2026-11-12", "meal_type": "Dinner", "reason": "Dining outside with family"}`

### `POST /student/guest-meal`
Books a guest meal with automatic wallet deduction.
- **Request Body:** `{"guest_name": "Rahul Verma", "date": "2026-11-12", "meal_type": "Lunch", "count": 1}`

### `POST /student/leave`
Submits a leave or day outpass application for Warden sign-off.
- **Request Body:**
```json
{
  "leave_type": "Home Leave",
  "from_date": "2026-11-14T08:00:00",
  "to_date": "2026-11-17T20:00:00",
  "destination": "Delhi (Home)",
  "reason": "Family function"
}
```

---

## 3. Mess Staff & QR Scanning Endpoints

### `POST /mess/scan-qr`
Validates student mess card and records attendance.
- **Request Body:** `{"token": "<signed_qr_token>"}`
- **Responses:**
  - `status: "verified"`: Valid check-in recorded, wallet or quota deducted.
  - `status: "duplicate"`: Duplicate check-in blocked by database unique compound index. Shows previous scan timestamp.
  - `status: "rejected"`: Expired token or insufficient funds.

### `GET /mess/today-board`
Returns live headcount counter across Breakfast, Lunch, Snacks, and Dinner sessions, alongside declared skips.

### `GET /mess/menu`
Returns weekly meal schedules and dietary highlights.

---

## 4. Maintenance & Complaints Endpoints

### `GET /complaints`
Retrieves complaint tickets tailored to user role.

### `POST /complaints`
Registers a new maintenance complaint.
- **Request Body:**
```json
{
  "category": "Plumbing",
  "room_number": "A-101",
  "priority": "High",
  "description": "Bathroom faucet continuously dripping"
}
```

### `PUT /complaints/{id}/assign`
Warden assigns ticket to technician.

### `PUT /complaints/{id}/status`
Technician updates ticket to "In Progress" or "Resolved" with resolution remarks.

### `PUT /complaints/{id}/feedback`
Student rates resolution from 1 to 5 stars and leaves feedback comment.

---

## 5. Fees & Payments Endpoints

### `GET /fees/summary`
Lists dues across all 4 mandatory heads: Hostel Rent, Security Deposit, Laundry, and Mess Dues.

### `POST /fees/pay`
Processes fee payment via Sandbox Gateway and generates verifiable official digital receipt with college crest and receipt ID (`REC-2026-XXXXX`).

---

## 6. Machine Learning Analytics Endpoints

### `GET /analytics/ml-forecast`
Returns AI recommended meal headcount for today, model comparison metrics (Moving Average vs Random Forest vs Gradient Boosting), and quantified food waste saved in kilograms and INR.
