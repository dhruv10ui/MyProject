# Hostel 360 - User Guide & Role Operations Manual

Welcome to **Hostel 360: Smart Hostel & Mess Management System**. This guide provides a step-by-step walkthrough for each of the six supported user roles.

---

## 1. Quick Start & Role Switcher
When you open **Hostel 360** in your web browser (`http://localhost:3000`), the top navigation strip includes a quick **Role Switcher** that allows examiners, evaluators, and administrators to experience each portal view instantly:
- `🎓 Student`: Profile of Dhruv Bansal (Roll: 11023210138), Room A-101.
- `🛡️ Warden`: Console of Dr. Rakesh Sharma (Hostel Warden).
- `🍽️ Mess Staff`: Terminal of Suresh Kumar (Mess Manager & Scanner).
- `🔧 Maintenance`: Dashboard of Ramesh Electrician (Maintenance Staff).
- `⚙️ Administrator`: Executive control room of Chief Administrator.
- `👨‍👩‍👧 Guardian`: Portal of Mr. Rajesh Bansal (Parent).

Default demo credentials for manual login:
- **Email:** `11023210138@stu.srmuniversity.ac.in` (or `warden@hostel360.edu`, `mess@hostel360.edu`, `admin@hostel360.edu`)
- **Password:** `Hostel360@demo`

---

## 2. Student Portal Guide
1. **Smart Digital Mess Card:**
   - Displayed in the center column.
   - Encodes a 120-second rotating cryptographic signed token. Notice the countdown circle ticking down from 120. When it reaches 0, the token rotates automatically.
   - Shows active plan, current wallet balance, and remaining quota.
   - Tap **"Declare Meal Skip"** to inform the mess before cutoff time.
   - Tap **"Book Guest Meal"** to purchase meals for visiting friends/parents.
2. **Room & Roommate Details:**
   - Shows your room number (`A-101`), bed number (`Bed A`), block, and floor.
   - Lists registered roommates (e.g., Arnav Ambasta in Bed B).
   - Tap **"Request Room Change"** if you wish to apply for transfer.
3. **Leave & Outpass Applications:**
   - Tap **"+ Apply Leave"** to apply for Home Leave, Day Outpass, or Emergency Leave.
   - Once the Warden approves your leave, tap **"View Digital QR Gate Pass"** to display your secure exit gate pass to the campus security guard.
4. **Maintenance Complaints Lifecycle:**
   - Tap **"+ Raise Ticket"** to report an issue (Wi-Fi, Electrical, Plumbing, Carpentry, Cleaning).
   - Watch the progress node move from `1. Submitted -> 2. Assigned -> 3. In Progress -> 4. Resolved`.
   - When marked resolved, tap **"Rate & Give Feedback ★★★★★"** to rate the service.
5. **Fee Payment & Receipts:**
   - Review pending dues across the 4 mandatory heads: Hostel Rent, Security Deposit, Laundry, and Mess Dues.
   - Tap **"Pay with Sandbox"** to simulate an immediate checkout (UPI QR / VPA, Card, NetBanking).
   - Tap **"Print Receipt 🖨️"** to view and print the official SRM University E-Receipt.

---

## 3. Mess Staff QR Scanner Guide
1. **Scanning Student Cards:**
   - Switch to `🍽️ Mess Staff`.
   - The scanner box displays an active laser line ready to scan student phones.
   - Tap **"✔ Scan Student QR (Dhruv)"**: Instantly records the check-in and updates quota/wallet balance with a green verification card.
   - Tap **"⚠ Test Duplicate Scan Alert"**: Immediately demonstrates the duplicate prevention engine! An alert card appears showing the exact previous check-in time and student identity.
2. **Today's Kitchen Board:**
   - Displays real-time check-in counts for Breakfast, Lunch, Snacks, and Dinner alongside declared skips.
3. **Weekly Menu Viewer:**
   - Displays breakfast, lunch, snacks, and dinner meal items for each day of the week.

---

## 4. Warden Portal Guide
1. **Occupancy Map:**
   - View real-time occupancy rate, total beds, and vacancy status across Block A and Block B.
   - Inspect individual rooms and see which students occupy Bed A, Bed B, or Bed C.
   - Tap **"+ Allocate Student Bed"** to assign incoming students to available rooms.
2. **Leave Approvals:**
   - Review pending student leave applications with destination and parent contact status.
   - Tap **"Approve & Issue Gate Pass"** to sign off and automatically generate a verified cryptographic Gate Pass.
   - Or tap **"Reject"** with mandatory remarks.
3. **Broadcast Notices:**
   - Submit official announcements directly to student dashboards.

---

## 5. Maintenance Staff Portal Guide
1. Review tickets categorized by priority (Emergency, High, Medium, Low).
2. Tap **"Mark In Progress"** when work commences.
3. Tap **"Mark Resolved with Notes"** upon completion to notify the student.
4. View student star ratings and comments once closed.

---

## 6. Administrator Dashboard Guide
1. **Executive Metrics:** View total fee revenue collected, overall hostel occupancy %, and complaint resolution SLA.
2. **Switch Mess Billing Architecture:**
   - Switch between **Monthly Subscription**, **Prepaid Wallet**, and **Fixed Quota** with one click.
   - The system immediately persists the change and applies it across all scanner terminals without restarting the application!
3. **System Users & Credentials:** Manage residents, staff, and view audit trail logs.
