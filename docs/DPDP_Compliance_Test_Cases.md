# DPDP Act 2023 — Compliance App Test Case Registry

**Framework:** Frappe v16 / ERPNext  
**Regulatory Basis:** DPDP Act 2023 + DPDP Rules (November 2025)  
**Audience:** QA Engineer, DPO, CTO  
**Total Test Cases:** 56 across 6 categories  
**Version:** 1.0

---

## Priority Legend

| Priority | Meaning |
|---|---|
| 🔴 P0 BLOCKER | Statutory violation if failed — go-live is blocked |
| 🟠 P1 Critical | High penalty risk — must fix before release |
| 🟡 P2 Standard | Functional requirement — fix in next sprint |
| 🟣 UAT | DPO + Legal sign-off required |
| 🔵 VAPT | External security team — all Critical/High must be closed |

> **How to use:** Fill in **Actual Result** and **Pass/Fail** (PASS / FAIL / BLOCKED / N/A) after executing each test. All 5 P0 tests must PASS before requesting go-live approval.

---

## Table of Contents

1. [Phase 1 — Foundation](#phase-1--foundation)
2. [Phase 2 — Consent Architecture](#phase-2--consent-architecture)
3. [Phase 3 — Data Rights & Breach Response](#phase-3--data-rights--breach-response)
4. [Phase 4 — Governance & Go-Live](#phase-4--governance--go-live)
5. [UAT Scenarios](#uat-scenarios)
6. [VAPT Security Tests](#vapt-security-tests)

---

## Phase 1 — Foundation

> **Objective:** App installation, master data setup, encryption, and role configuration.  
> **Week:** 1–4 | **Owner:** Backend Dev, DBA

---

### TC1-001 — App Installation

| Field | Detail |
|---|---|
| **Module** | App Setup |
| **Priority** | 🟡 P2 |
| **DPDP Section** | Section 3 (Scope) |
| **Penalty Risk** | — |

**Pre-Conditions**
- Frappe v16 server is running
- `dpdp_compliance` app is cloned to the apps directory

**Test Steps**
1. SSH into the server
2. Run: `bench install-app dpdp_compliance`
3. Run: `bench list-apps`

**Expected Result**  
`dpdp_compliance` appears in the app list with no installation errors.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Run on a fresh dev site first before staging.

---

### TC1-002 — Consent Purpose Creation

| Field | Detail |
|---|---|
| **Module** | Master Data |
| **Priority** | 🟡 P2 |
| **DPDP Section** | Section 6 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- `dpdp_compliance` app installed
- Logged in as Administrator

**Test Steps**
1. Go to Consent Purpose > New
2. Enter: Name = `Email Marketing`, `is_mandatory` = OFF, `validity_days` = 365
3. Save the record
4. Open `/signup` in browser and inspect the consent modal

**Expected Result**  
Record saves successfully. The purpose appears dynamically in the consent modal (fetched from DB, not hardcoded).

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Test both mandatory and optional purposes. Add a new purpose and reload — it must appear without a code deployment.

---

### TC1-003 — Data Asset RoPA Mapping

| Field | Detail |
|---|---|
| **Module** | Master Data |
| **Priority** | 🟡 P2 |
| **DPDP Section** | Section 8 (Safeguards) |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- Data Asset DocType exists in the app

**Test Steps**
1. Go to Data Asset > New
2. Set: DocType = `Customer`, Field = `email`, Classification = `Level 3 — Personal Data`
3. Save and reload the record
4. Check list view for correct classification display

**Expected Result**  
Record links correctly. Classification level shows in list view. Field is traceable back to the DocType.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Cover all PII fields: email, phone, date of birth, address.

---

### TC1-004 — Role-Based Access Control

| Field | Detail |
|---|---|
| **Module** | Roles |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 8 (Safeguards) |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- Roles created: `DPO Manager`, `DPDP Admin`, `Compliance Viewer`
- Test user accounts assigned each role

**Test Steps**
1. Assign test user Role = `Compliance Viewer`
2. Log in as that user
3. Attempt to open the Data Breach DocType
4. Attempt to edit a Consent Log record
5. Repeat steps 1–4 for `DPDP Admin` and `DPO Manager` roles

**Expected Result**  
Compliance Viewer: Data Breach returns Permission Denied. Consent Log is read-only (no Edit button visible). Each role accesses only what it should.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Test all 3 roles separately. Document which permissions each role has vs. what they attempted.

---

### TC1-005 — Consent Expiry Detection

| Field | Detail |
|---|---|
| **Module** | Scheduler |
| **Priority** | 🟡 P2 |
| **DPDP Section** | Section 6(3) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Consent Log DocType has `expiry_date` field
- Daily scheduler is enabled in hooks

**Test Steps**
1. In `bench console`, create a Consent Log with `expiry_date` = yesterday's date
2. Run the daily scheduler manually: `frappe.get_doc("Scheduled Job Type", "consent_expiry_checker").execute()`
3. Reload the Consent Log record and check the status field

**Expected Result**  
Consent Log status auto-updates from `Granted` to `Expired`. Records with future expiry dates are unaffected.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Verify no records are updated that haven't actually expired.

---

### TC1-006 — Encryption at Rest (PAN / Aadhaar) 🔴

| Field | Detail |
|---|---|
| **Module** | Security |
| **Priority** | 🟠 P1 — CRITICAL |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- Fernet encryption key set in `site_config.json`
- PAN / Aadhaar field type set to `Password` in the DocType

**Test Steps**
1. Create an Employee record with PAN = `ABCDE1234F`
2. Open MariaDB directly: `SELECT pan_number FROM tabEmployee WHERE name='TEST-EMP-001'`
3. Note the raw value returned from the database

**Expected Result**  
MariaDB shows an encrypted Fernet hash — **NOT** the plaintext `ABCDE1234F`.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — if plaintext is visible in the DB, this is a direct Section 8 violation. Escalate immediately to the DPO.

---

### TC1-007 — Retention Policy Configuration

| Field | Detail |
|---|---|
| **Module** | Master Data |
| **Priority** | 🟡 P2 |
| **DPDP Section** | Section 12 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Retention Policy DocType created and accessible

**Test Steps**
1. Create Retention Policy: DocType = `Sales Invoice`, `retention_years` = 8, action = `Flag`
2. Save the record
3. Check that the retention engine references it during the daily run configuration

**Expected Result**  
Policy saves correctly. Retention engine reads the policy and applies it during the scheduled job.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Create one policy per major DocType (Customer, Employee, Sales Invoice, Lead).

---

## Phase 2 — Consent Architecture

> **Objective:** Consent modal, consent log creation, withdrawal, VPC for minors, and legacy data remediation.  
> **Week:** 5–10 | **Owner:** Full-Stack Dev

---

### TC2-001 — Consent Modal Renders on Signup

| Field | Detail |
|---|---|
| **Module** | Consent UI |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 5 (Notice) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Privacy Notice with linked Consent Purposes exists and is marked active
- `/signup` page is accessible

**Test Steps**
1. Open `/signup` in an incognito browser window
2. Observe whether the consent modal appears
3. In browser DevTools, inspect the checkboxes — confirm they are fetched from the API
4. Add a new Consent Purpose in the Frappe backend
5. Reload the signup page without a code deployment

**Expected Result**  
Modal appears dynamically with the purpose list fetched from DB. The new purpose added in step 4 appears on reload — no deployment required.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Hardcoded purpose lists are a compliance risk — any change requires a deployment and a new notice version.

---

### TC2-002 — No Pre-Ticked Checkboxes 🔴

| Field | Detail |
|---|---|
| **Module** | Consent UI |
| **Priority** | 🔴 P0 BLOCKER |
| **DPDP Section** | Section 6(1) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Consent modal is live on `/signup`

**Test Steps**
1. Open `/signup` in a fresh browser session
2. Open browser DevTools > Console
3. Run: `document.querySelectorAll('input[type=checkbox]:checked')`
4. Count the elements returned
5. Inspect each checkbox in the DOM for `checked` or `defaultChecked` attributes

**Expected Result**  
The result array is **completely empty** — zero pre-checked boxes. No optional purpose is pre-selected.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — any pre-checked optional checkbox is a direct Section 6 violation. Consent must be an affirmative action.

---

### TC2-003 — Consent Log Created on Signup

| Field | Detail |
|---|---|
| **Module** | Consent Log |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 8 (Audit) |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- Signup form with consent modal is working
- DB access available for verification

**Test Steps**
1. Complete signup with 2 optional purposes consented
2. Query DB: `SELECT * FROM tabConsent_Log WHERE user='new@test.com'`
3. Verify fields: `status`, `ip_address`, `notice_version`, `timestamp`, `purpose`

**Expected Result**  
Exactly 2 records created — one per purpose. Each record has: `status = Granted`, `ip_address` populated, `notice_version` linked to the correct Privacy Notice, `timestamp` accurate to within 1 minute.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Verify the IP address logged matches the actual request IP. This record is legal evidence.

---

### TC2-004 — Withdrawal Equal Ease (Section 6(4))

| Field | Detail |
|---|---|
| **Module** | Consent UI |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 6(4) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- User has active consent
- Privacy Portal is accessible at `/privacy-portal`

**Test Steps**
1. On the signup page, count the number of clicks required to consent to `Email Marketing`
2. Log in as the same user
3. Navigate to Privacy Portal > Manage Consent > Withdraw `Email Marketing`
4. Count the number of clicks required to withdraw

**Expected Result**  
Withdrawal click count is **equal to or fewer** than consent click count. Both actions complete in under 5 seconds.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** If withdrawal requires more navigation steps than consent, that is a Section 6(4) violation.

---

### TC2-005 — Consent Log Immutability 🔴

| Field | Detail |
|---|---|
| **Module** | Consent Log |
| **Priority** | 🔴 P0 BLOCKER |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- A submitted Consent Log record exists
- Postman or equivalent API client installed
- MariaDB access available

**Test Steps**
1. Open the submitted Consent Log in Frappe Desk — confirm the Edit button is absent
2. In Postman: `PUT /api/resource/Consent Log/<name>` with a modified `status` field (with valid auth token)
3. In MariaDB: `UPDATE tabConsent_Log SET status='Withdrawn' WHERE name='...'`
4. Reload the record in Frappe Desk

**Expected Result**  
Step 1: No Edit button visible. Step 2: Returns 403 or validation error, record unchanged. Step 3: DB either rejects the update or the audit log records the attempt.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — this is your legal evidence. Any successful tamper = compliance failure. Test with both admin and non-admin credentials.

---

### TC2-006 — Withdrawal Propagates to Email Queue

| Field | Detail |
|---|---|
| **Module** | Consent |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 6(4) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- User has consented to `Email Marketing`
- A pending marketing email exists in the Frappe Email Queue for that user

**Test Steps**
1. Go to Privacy Portal > Withdraw `Email Marketing` consent
2. Check Frappe Email Queue: `SELECT * FROM tabEmail Queue WHERE recipients LIKE '%user@test.com%'`
3. Query Consent Log for a new withdrawal record
4. Verify the original Granted record still exists

**Expected Result**  
Pending marketing email is suppressed/cancelled. A new Consent Log record exists with `status = Withdrawn`. The original `Granted` record is **intact and unmodified** — withdrawal must be a new record, not an overwrite.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** The immutable history (Grant → Withdraw) is required for audit. Overwriting is a compliance failure.

---

### TC2-007 — Legacy User Identification Count

| Field | Detail |
|---|---|
| **Module** | Legacy Remediation |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 5(2) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Users exist in DB created before Act commencement date
- `bench console` access available

**Test Steps**
1. Run in bench console: `dpdp_compliance.consent.get_unconsented_users()`
2. Manually query DB: `SELECT count(*) FROM tabUser WHERE creation < '2025-01-01' AND name NOT IN (SELECT user FROM tabConsent_Log)`
3. Compare both counts

**Expected Result**  
Both counts match exactly. No discrepancy between the function result and the manual DB query.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Any discrepancy means some users will miss the remediation emails — a Section 5(2) compliance gap.

---

### TC2-008 — Age Gate Triggers VPC Flow

| Field | Detail |
|---|---|
| **Module** | VPC / Children |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 9 |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- Signup form has Date of Birth field
- VPC redirect logic is implemented in the backend

**Test Steps**
1. Complete signup with DOB = today minus 16 years
2. Observe what happens to the signup flow
3. Repeat with DOB = exactly 18 years ago (boundary test)
4. Repeat with DOB = 17 years 364 days ago (one day under boundary)

**Expected Result**  
Age 16: Account frozen, redirect to Parental Consent (VPC) flow. Age 18: Normal signup proceeds. Age 17y364d: Must trigger VPC.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ Test the boundary carefully. A 1-day error in the age calculation = ₹200 Cr penalty exposure.

---

### TC2-009 — Parent Receives VPC Email

| Field | Detail |
|---|---|
| **Module** | VPC / Children |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 9 |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- Minor signup has triggered the VPC flow
- Parent email address has been entered

**Test Steps**
1. Enter parent email in the VPC flow form
2. Check the parent's inbox within 2 minutes
3. Inspect the email link — check if it is time-limited and single-use
4. Click the link twice (after first use) to verify it expires

**Expected Result**  
Email arrives using template `vpc_parental_consent.html` with a secure DigiLocker link. The link expires after first use or after a configured time limit.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** A reusable VPC link is a security vulnerability — it allows replay attacks.

---

### TC2-010 — VPC Token Stored in Consent Log

| Field | Detail |
|---|---|
| **Module** | VPC / Children |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 9 |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- DigiLocker sandbox is configured
- VPC email flow is complete

**Test Steps**
1. Complete the full VPC flow using DigiLocker sandbox authentication
2. Check the Consent Log record for the child user
3. Inspect the `verification_token` field value
4. Check child's account `status`

**Expected Result**  
`verification_token` field is populated with the DigiLocker token. Child account status = `Active`. Without this token, the parental consent is legally unverifiable.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ Without the token, you cannot prove VPC was obtained — this is the key evidential requirement under Section 9.

---

## Phase 3 — Data Rights & Breach Response

> **Objective:** DSR portal, OTP identity verification, erasure engine, retention checks, and 72-hour breach workflow.  
> **Week:** 11–16 | **Owner:** Full-Stack Dev, Legal

---

### TC3-001 — DSR OTP Identity Verification 🔴

| Field | Detail |
|---|---|
| **Module** | DSR |
| **Priority** | 🔴 P0 BLOCKER |
| **DPDP Section** | Section 11 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- DSR privacy portal is live
- OTP service is configured (SMS or email)

**Test Steps**
1. Submit an Access DSR via the portal **without** completing OTP verification
2. Observe the DSR status in the backend
3. Attempt to enter a wrong OTP
4. Enter the correct OTP
5. Observe the DSR status after correct OTP

**Expected Result**  
Step 1: DSR stays in `Pending Verification`. Step 3: OTP rejected with an error message. Step 4–5: DSR moves to `Verified` state and processing can begin.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — skipping identity verification before fulfilling a DSR = data leakage to an impersonator. This is an IDOR risk.

---

### TC3-002 — Access Request Data Summary

| Field | Detail |
|---|---|
| **Module** | DSR |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 11 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Verified Access DSR exists for a test user
- A second test user's data exists in the system

**Test Steps**
1. Process the Access DSR
2. Click `Generate Data Summary`
3. Download and open the generated report
4. Search the report for any data belonging to a different user

**Expected Result**  
Report contains only the requesting user's data: PII fields held, processors the data was shared with, and the consent basis. No other user's data appears anywhere in the report.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** This is an IDOR test disguised as a functional test. Row-level security must be enforced at the query level.

---

### TC3-003 — Correction Request Updates Record

| Field | Detail |
|---|---|
| **Module** | DSR |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 12 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Verified Correction DSR exists with a new `first_name` value specified

**Test Steps**
1. Process the Correction DSR with `first_name = 'Corrected Name'`
2. Check the User record after processing
3. Open the Data Erasure Log for this operation
4. Verify before and after values are recorded

**Expected Result**  
`User.first_name = 'Corrected Name'`. Data Erasure Log records the before value, after value, timestamp, and who processed the request.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** The audit trail of corrections is mandatory. Without it, you cannot prove what was changed and why.

---

### TC3-004 — DSR SLA Timer Countdown

| Field | Detail |
|---|---|
| **Module** | DSR / SLA |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 13 |
| **Penalty Risk** | ₹50 Cr |

**Pre-Conditions**
- DSR DocType with `sla_due_date` field
- Hourly SLA scheduler configured in hooks

**Test Steps**
1. Create a new DSR and note its `sla_due_date`
2. Verify `sla_due_date = creation_datetime + 7 days`
3. In bench console, backdate `sla_due_date` to yesterday
4. Run the hourly SLA calculator manually
5. Check DPO's inbox and the DPO Dashboard

**Expected Result**  
`sla_due_date` defaults to `creation + 7 days`. After backdating and running the job: DPO receives an alert email and the Dashboard shows the DSR in the `Open Past SLA` count.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** The SLA period should align with DPDP Rules (expected 7 days). Confirm with legal before hardcoding.

---

### TC3-005 — Erasure of User with No Financial Records

| Field | Detail |
|---|---|
| **Module** | Erasure |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 12 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Test user exists with absolutely no Sales Invoices, Purchase Orders, or other financial documents

**Test Steps**
1. Submit and verify an Erasure DSR for the test user
2. Process the erasure request
3. Query DB: `SELECT first_name, last_name, email, phone FROM tabUser WHERE name='test@test.com'`
4. Attempt to log in as that user

**Expected Result**  
DB shows: `first_name = 'Anonymized'`, `email` ends in `@anonymized.local`, `phone` is empty. Login fails — the original email no longer exists.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Also check linked CRM records (Lead, Contact) — PII must be scrubbed across all related DocTypes.

---

### TC3-006 — Erasure Blocked by Active Invoices 🔴

| Field | Detail |
|---|---|
| **Module** | Erasure |
| **Priority** | 🔴 P0 BLOCKER |
| **DPDP Section** | Section 12 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Test customer exists with at least 1 submitted Sales Invoice
- Retention Policy set to 8 years for Sales Invoice

**Test Steps**
1. Submit an Erasure DSR for that customer
2. Run in bench console: `dpdp_compliance.erasure.execute_erasure('customer@test.com')`
3. Check the return value
4. Query DB to confirm the Customer name is unchanged

**Expected Result**  
Function returns: `{"status": "Failed", "reason": "Active financial records exist."}`. Customer record is completely unchanged in the DB.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — deleting a customer with invoices breaks GST compliance. The retention hold must take precedence over the erasure request. Notify the Data Principal with the legal reason.

---

### TC3-007 — Retention Engine Respects Policy

| Field | Detail |
|---|---|
| **Module** | Retention |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 12 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Retention Policy: `Sales Invoice = 8 years`
- Two test invoices: one 3 years old, one 9 years old

**Test Steps**
1. Run the retention engine daily job manually
2. Check the 3-year-old invoice — status and data
3. Check the 9-year-old invoice — status and data
4. Verify a Data Erasure Log entry was created for the 9-year-old invoice

**Expected Result**  
3-year invoice: completely untouched (3 < 8, within retention period). 9-year invoice: anonymized or flagged per the policy's configured action. Erasure Log entry created for the processed invoice.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Test each configured action separately: `Anonymize`, `Delete`, `Flag`. The action taken must match the policy.

---

### TC3-008 — Breach DocType 72h Deadline Computed

| Field | Detail |
|---|---|
| **Module** | Breach |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 8(6) |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- Data Breach DocType with `reporting_deadline` formula field exists

**Test Steps**
1. Create a new Data Breach with `detection_time = now()`
2. Save the record
3. Check the `reporting_deadline` field value
4. Verify the timezone of the deadline (must be IST)

**Expected Result**  
`reporting_deadline = detection_time + exactly 72 hours`. The deadline is prominently displayed on the form. Timezone is IST — not UTC or any other offset.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** A common bug is storing timestamps in UTC but displaying in IST — this can cause a 5.5-hour discrepancy and may result in reporting past the actual deadline.

---

### TC3-009 — 72h Breach Escalation Ladder 🔴

| Field | Detail |
|---|---|
| **Module** | Breach |
| **Priority** | 🔴 P0 BLOCKER |
| **DPDP Section** | Section 8(6) |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- Data Breach record exists with `detection_time` set to 48 hours ago
- `status = Under Investigation`
- Hourly breach checker scheduler is configured

**Test Steps**
1. Run the hourly breach checker: check DPO inbox — T+48h alert
2. Change `detection_time` to 66 hours ago, run checker again — check inbox
3. Change `detection_time` to 71 hours ago, run checker again — check inbox
4. Verify the status is still `Under Investigation` (not `Reported`)

**Expected Result**  
T+48h: Alert email with message "24 hours remain to report." T+66h: Alert "6 hours remain — escalate immediately." T+71h: Emergency alert fires to both DPO and IRT team.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** ⚠️ CRITICAL — a missed 72h window = ₹200 Cr penalty. This escalation ladder is your safety net. All three alerts must fire at the correct thresholds.

---

### TC3-010 — IRT Alert Email on Breach Creation

| Field | Detail |
|---|---|
| **Module** | Breach |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 8(6) |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- IRT member email list populated in DPDP Settings
- Email service configured and working

**Test Steps**
1. Create a new Data Breach with `severity = High`
2. Save the record
3. Check IRT members' inboxes within 5 minutes
4. Repeat with `severity = Low` and verify a different (lower priority) alert is sent

**Expected Result**  
High severity: IRT alert email using template `breach_irt_alert.html` arrives within 5 minutes. Low severity: alert fires but with lower urgency messaging.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** The `after_insert` hook on Data Breach triggers this. Verify the hook is wired correctly in `hooks.py`.

---

## Phase 4 — Governance & Go-Live

> **Objective:** DPO Dashboard accuracy, audit trails, role segregation, and end-to-end smoke test.  
> **Week:** 13–16 | **Owner:** DPO, QA, IT

---

### TC4-001 — DPO Dashboard Consent % Accuracy

| Field | Detail |
|---|---|
| **Module** | Dashboard |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 10 (SDF) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- DPO Dashboard page exists
- Clean test environment with no pre-existing users

**Test Steps**
1. Create exactly 10 test users
2. Add a Consent Log with `status = Granted` for exactly 7 of those users
3. Open the DPO Dashboard
4. Check the `Consent Coverage %` widget
5. Add one more consented user and refresh

**Expected Result**  
Widget shows exactly **70.0%** after step 4. After step 5, updates to approximately **72.7%**.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** The dashboard is the DPO's primary monitoring tool. Inaccuracy = blind spots in compliance posture.

---

### TC4-002 — Dashboard Past-SLA Alert Count

| Field | Detail |
|---|---|
| **Module** | Dashboard |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 13 |
| **Penalty Risk** | ₹50 Cr |

**Pre-Conditions**
- DPO Dashboard operational
- A DSR exists that can be backdated

**Test Steps**
1. Create a DSR
2. In bench console, set `sla_due_date = yesterday`
3. Run the hourly SLA calculator
4. Open the DPO Dashboard and check `Open Past SLA` count
5. Close the DSR and verify the count decrements

**Expected Result**  
`Open Past SLA` counter increments by 1 after step 3. Assigned team member receives an alert email. Counter decrements when DSR is closed in step 5.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

---

### TC4-003 — Audit Trail Active on Consent Log

| Field | Detail |
|---|---|
| **Module** | Audit Trail |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 10 (SDF) |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- `Track Changes` enabled on Consent Log DocType in DocType settings

**Test Steps**
1. Submit a new Consent Log
2. Open the record and click the `Version` tab
3. Check the creation event entry
4. Repeat for the Privacy Notice DocType — make a change, check Version history

**Expected Result**  
Full creation event logged with: timestamp, user who created, all field values at the time of creation. Privacy Notice version history shows old and new values side by side.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** For SDFs, periodic audits are mandatory. The audit trail is the primary evidence submitted.

---

### TC4-004 — Role Segregation — DPO-Only Breach Access

| Field | Detail |
|---|---|
| **Module** | Roles |
| **Priority** | 🟠 P1 |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Pre-Conditions**
- Test accounts for `Marketing Manager`, `DPDP Admin`, and `DPO Manager`

**Test Steps**
1. Log in as `Marketing Manager`
2. Navigate to Data Breach DocType list
3. Try to create a new Data Breach record
4. Try to view an existing Data Breach record
5. Log in as `DPDP Admin` and repeat steps 2–4

**Expected Result**  
Both `Marketing Manager` and `DPDP Admin` receive Permission Denied on both list view and form view. Only `DPO Manager` role can access Data Breach.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Data Breach records contain highly sensitive incident details. Over-permissioning is a compliance and confidentiality risk.

---

### TC4-005 — Full Lifecycle End-to-End Smoke Test

| Field | Detail |
|---|---|
| **Module** | E2E Smoke |
| **Priority** | 🟠 P1 |
| **DPDP Section** | All Sections |
| **Penalty Risk** | Up to ₹250 Cr |

**Pre-Conditions**
- All modules working: consent, DSR, erasure, breach
- Test user with no financial records
- DPO present for sign-off

**Test Steps**
1. New user signs up with consent for mandatory + optional purposes
2. User withdraws optional consent via Privacy Portal
3. User submits an Access DSR — verifies via OTP
4. DSR is fulfilled — data summary downloaded
5. User submits an Erasure DSR — processed
6. Verify user is anonymized in DB
7. Create a Data Breach with severity = High
8. IRT alerted, report generated, breach marked `Reported to DPB`

**Expected Result**  
All 8 steps complete without errors. Consent Log shows `Grant` then `Withdraw` records. DSR closed within SLA. User anonymized post-erasure. Breach marked `Reported` before 72h deadline.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Run this on staging with realistic data volumes. The DPO must observe and sign off on this test before go-live approval.

---

## UAT Scenarios

> **Run with:** DPO and Legal team on staging environment with realistic synthetic data.  
> **Sign-off required** from DPO and CTO before go-live.

---

### UAT-001 — New Customer Journey (Mandatory Consent Only)

| Field | Detail |
|---|---|
| **Priority** | 🟣 UAT |
| **DPDP Section** | Sections 5, 6 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Fresh browser session
- Staging environment with test email inbox available

**Test Steps**
1. New customer opens `/signup`
2. Reads the consent modal — unchecks `Email Marketing` (keeps mandatory only)
3. Completes signup
4. Places a test order
5. Check the customer's email inbox for all received emails

**Expected Result**  
Order processed successfully. Order confirmation email received. **No marketing email sent** — because marketing consent was not given.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** DPO to observe and confirm the marketing suppression is working at the email queue level.

---

### UAT-002 — Minor Customer — Full VPC Flow

| Field | Detail |
|---|---|
| **Priority** | 🟣 UAT |
| **DPDP Section** | Section 9 |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- DOB field on signup form
- DigiLocker sandbox configured
- Parent's email inbox accessible

**Test Steps**
1. Signup with DOB = 15 years old
2. Enter parent's email in the VPC prompt
3. Parent opens VPC email and clicks the DigiLocker link
4. Parent completes DigiLocker sandbox authentication
5. Check the child's account status and Consent Log

**Expected Result**  
Child account is locked until parent completes authentication. After DigiLocker auth: account is `Active`, `verification_token` is in Consent Log, minor restrictions are applied (no behavioral tracking flags).

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Legal team must review and approve this flow. This is the highest penalty exposure scenario (₹200 Cr for children's data violations).

---

### UAT-003 — Full Rights Exercise (Access → Correct → Erase)

| Field | Detail |
|---|---|
| **Priority** | 🟣 UAT |
| **DPDP Section** | Sections 11–13 |
| **Penalty Risk** | ₹150 Cr |

**Pre-Conditions**
- Existing customer with no financial records
- All three DSR types (Access, Correction, Erasure) implemented

**Test Steps**
1. Submit Access DSR → verify OTP → fulfill → download data summary report
2. Submit Correction DSR → update name → confirm change in DB
3. Submit Erasure DSR → process → verify anonymization
4. Attempt to log in as the erased user
5. Check that invoice records (if any) retain the anonymized customer reference

**Expected Result**  
All 3 DSRs complete within SLA (7 days each). After erasure: login fails. PII is scrubbed. GST invoice records retain an anonymized customer reference — they are not deleted or broken.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** Legal must verify that the anonymized invoice reference satisfies GST Act record-keeping requirements.

---

### UAT-004 — Breach Drill — Full 72h Workflow

| Field | Detail |
|---|---|
| **Priority** | 🟣 UAT |
| **DPDP Section** | Section 8(6) |
| **Penalty Risk** | ₹200 Cr |

**Pre-Conditions**
- DPO and IRT team are available and monitoring their inboxes
- DPDP Settings fully populated (org name, DPO email, IRT list)

**Test Steps**
1. DPO creates a new High severity Data Breach record with `detection_time = now()`
2. Verify IRT receives the alert email within 5 minutes
3. Verify the 72h countdown is clearly visible on the form
4. Click `Generate Board Report` — review the auto-populated statutory report
5. Confirm all mandatory report fields are populated correctly
6. Mark the breach as `Reported to DPB` and save

**Expected Result**  
IRT alerted promptly. Countdown visible and accurate. Board report auto-populated with: fiduciary name, DPO contact, breach nature, affected principal count, detection time, and remedial actions. Breach closed as `Reported` before simulated 72h deadline.

**Actual Result:** _______________

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL &nbsp; ☐ BLOCKED

**Notes:** DPO must sign off on the board report template to confirm it satisfies the statutory format under DPDP Rules 2025.

---

## VAPT Security Tests

> **Run with:** External security team or designated security QA.  
> **Requirement:** All Critical and High severity findings must be closed before go-live sign-off.

---

### VAPT-001 — Unauthenticated API Access

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | Postman |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. In Postman, send `GET /api/resource/Consent Log` with **no authentication header**
2. Note the HTTP response code and response body

**Expected Result**  
Returns `403 Forbidden`. No data is returned in the response body.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-002 — Non-DPO Access to Data Breach

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | Frappe Desk + Browser |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. Log in as a user with `Marketing Manager` role
2. Navigate to `Data Breach` in Frappe Desk list view
3. Try to open any individual Data Breach record

**Expected Result**  
`Permission Denied` error on both list view and form view.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-003 — SQL Injection in DSR Fields

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | sqlmap / Manual |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. In the DSR description field, enter: `' OR 1=1; DROP TABLE tabUser; --`
2. Submit the form
3. Check DB integrity — confirm `tabUser` still exists and has all records

**Expected Result**  
Input is sanitized. No DB error is leaked to the UI. `tabUser` is intact with all records.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-004 — XSS in Consent Withdrawal Reason

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | OWASP ZAP / Manual |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. In the withdrawal reason field, enter: `<script>alert('XSS')</script>`
2. Submit the withdrawal form
3. Re-open the record as another user and observe

**Expected Result**  
The script tag is HTML-encoded in the output. The `alert()` **does not execute** in any user's browser.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-005 — IDOR: Access Another User's DSR

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | Manual browser testing |
| **DPDP Section** | Section 11 |
| **Penalty Risk** | ₹150 Cr |

**Test Steps**
1. Log in as User A and submit a DSR — note the DSR URL/ID
2. Log out and log in as User B
3. Directly navigate to User A's DSR URL

**Expected Result**  
Returns `403 Forbidden`. User B cannot view or access User A's DSR.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-006 — Encryption Verification via DB Query

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | MariaDB CLI |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. Ensure an Employee record exists with PAN stored
2. In MariaDB CLI run: `SELECT pan_number FROM tabEmployee WHERE name='TEST-EMP'`
3. Note the raw value

**Expected Result**  
Shows a Fernet-encrypted hash — **NOT plaintext**. The PAN is never visible in the database directly.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-007 — Consent Log API Immutability

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | Postman with valid auth token |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. GET an existing submitted Consent Log to retrieve current values
2. Send `PUT /api/resource/Consent Log/<name>` with a modified `status` field (using a valid admin auth token)
3. Check the record in DB after the API call

**Expected Result**  
PUT returns a validation error. The Consent Log record is **completely unchanged** in the DB.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

### VAPT-008 — OTP Rate Limiting

| Field | Detail |
|---|---|
| **Priority** | 🔵 VAPT |
| **Tool** | Locust / curl loop |
| **DPDP Section** | Section 8 |
| **Penalty Risk** | ₹250 Cr |

**Test Steps**
1. Using curl or Locust, send 100 OTP requests in 60 seconds to the same phone number / email
2. Observe HTTP responses as requests progress
3. Note at which request number the rate limit triggers

**Expected Result**  
Rate limit is triggered after the configured threshold (e.g., 5 requests/minute). Returns `429 Too Many Requests` for subsequent attempts within the window.

**Pass / Fail:** ☐ PASS &nbsp; ☐ FAIL

---

## Pre-Go-Live Checklist

> All items must be checked off by the responsible party before DPO + CTO sign the go-live approval.

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | All 5 P0 BLOCKER test cases — PASS | QA | ☐ |
| 2 | All P1 Critical test cases — PASS | QA | ☐ |
| 3 | VAPT complete — no Critical/High open findings | Security | ☐ |
| 4 | UAT sign-off document signed by DPO and CTO | DPO + CTO | ☐ |
| 5 | Incident Response Plan documented and shared with IRT | DPO | ☐ |
| 6 | Audit Trail (Track Changes) enabled on all DPDP DocTypes | IT | ☐ |
| 7 | No over-privileged user roles in production | DPO + IT | ☐ |
| 8 | Data Processor agreements updated with DPDP obligations | Legal | ☐ |
| 9 | Privacy Portal accessible at `/privacy-portal` | QA | ☐ |
| 10 | Scheduled jobs verified running (SLA checker, retention engine, breach hours) | IT | ☐ |
| 11 | Legacy consent remediation emails sent to all pre-Act users | IT | ☐ |
| 12 | Encryption key stored in secrets vault — not in code | Security | ☐ |
| 13 | DPO Dashboard reviewed and confirmed accurate | DPO | ☐ |
| 14 | Multi-language Privacy Notice published (minimum: English + Hindi) | Legal | ☐ |
| 15 | Data Breach drill (UAT-004) completed and signed off | DPO | ☐ |

---

*Document prepared for internal QA use. All test results and actual outcomes must be documented for regulatory audit readiness.*
