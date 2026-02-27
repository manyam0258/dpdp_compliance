---
name: dpdp-breach-governance-vpc
description: >
  Use this skill for the Breach Response, Data Governance, and Verifiable Parental Consent
  (VPC) modules of dpdp_compliance on Frappe v16. Triggers include: data breach logging,
  72-hour DPB notification, breach SLA, DPO dashboard, data inventory (RoPA), field-level
  encryption, retention engine, DPIA, Data Processor management, Section 10 (SDF), child
  data protection, DigiLocker integration, age verification, parental consent, or any of
  Sections 8, 9, or 10 of the DPDP Act. Use alongside skill_04 and skill_05 for complete
  compliance coverage. Non-compliance carries fines up to ₹250 crore.
compatibility:
  frappe_version: ">=16.0"
  app: dpdp_compliance
---

# DPDP Breach Response, Governance & VPC

---

## MODULE A: BREACH RESPONSE (Section 8(6))

### Legal Requirement
Data Fiduciaries must notify the DPB and affected principals of breaches
**without delay** — industry and rules align on 72 hours maximum.
Penalty for failure: up to ₹200 crore.

### Data Breach DocType
```json
{
  "name": "Data Breach",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {"fieldname":"breach_id","fieldtype":"Data","read_only":1},
    {"fieldname":"breach_title","fieldtype":"Data","reqd":1},
    {"fieldname":"detection_time","fieldtype":"Datetime","reqd":1},
    {"fieldname":"reporting_deadline","fieldtype":"Datetime","read_only":1},
    {"fieldname":"hours_remaining","fieldtype":"Float","read_only":1},
    {"fieldname":"severity","fieldtype":"Select",
     "options":"Critical\nHigh\nMedium\nLow","reqd":1},
    {"fieldname":"breach_type","fieldtype":"Select",
     "options":"Unauthorized Access\nData Exfiltration\nRansomware\nAccidental Disclosure\nInsider Threat\nPhysical Loss"},
    {"fieldname":"nature_of_breach","fieldtype":"Text","reqd":1},
    {"fieldname":"data_categories","fieldtype":"Small Text"},
    {"fieldname":"affected_users_count","fieldtype":"Int"},
    {"fieldname":"affected_users_file","fieldtype":"Attach"},
    {"fieldname":"systems_affected","fieldtype":"Small Text"},
    {"fieldname":"likely_consequences","fieldtype":"Text"},
    {"fieldname":"remedial_actions","fieldtype":"Text"},
    {"fieldname":"status","fieldtype":"Select",
     "options":"Detected\nAssessing\nContained\nReported to DPB\nPrincipals Notified\nClosed",
     "default":"Detected"},
    {"fieldname":"reported_to_dpb_on","fieldtype":"Datetime"},
    {"fieldname":"principal_notification_sent","fieldtype":"Check","default":0},
    {"fieldname":"assigned_irt_lead","fieldtype":"Link","options":"User"},
    {"fieldname":"dpb_submission_ref","fieldtype":"Data"}
  ],
  "permissions": [
    {"role":"DPO","read":1,"write":1,"create":1,"submit":1,"delete":0},
    {"role":"System Manager","read":1,"write":0,"delete":0}
  ]
}
```

### Breach Engine (`breach.py`)
```python
# dpdp_compliance/breach.py
import frappe
from frappe.utils import now_datetime, add_to_date, time_diff_in_hours

BREACH_WINDOW_HOURS = 72


def on_breach_creation(doc, method):
    """Hook: Data Breach.after_insert — auto-set deadline + alert IRT."""
    import secrets
    doc.breach_id = f"BR-{now_datetime().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    doc.reporting_deadline = add_to_date(doc.detection_time, hours=BREACH_WINDOW_HOURS)
    doc.hours_remaining = BREACH_WINDOW_HOURS
    doc.save(ignore_permissions=True)
    _alert_irt(doc)
    frappe.publish_realtime("breach_detected", {"name": doc.name, "severity": doc.severity})


def _alert_irt(breach):
    dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")
    irt_raw = frappe.db.get_single_value("DPDP Settings", "irt_emails") or ""
    recipients = list({dpo_email} | {e.strip() for e in irt_raw.split(",") if e.strip()})
    frappe.sendmail(
        recipients=recipients,
        subject=f"🚨 DATA BREACH — {breach.severity.upper()} | {breach.breach_title}",
        message=f"""
        <h2 style="color:red">Data Breach Detected</h2>
        <table border="1" cellpadding="6">
          <tr><th>Breach ID</th><td>{breach.breach_id}</td></tr>
          <tr><th>Detection Time</th><td>{breach.detection_time}</td></tr>
          <tr><th>Severity</th><td>{breach.severity}</td></tr>
          <tr><th>DPB Deadline</th><td>{breach.reporting_deadline}</td></tr>
          <tr><th>Nature</th><td>{breach.nature_of_breach}</td></tr>
        </table>
        <p><a href="/app/data-breach/{breach.name}">→ Open Breach Record</a></p>
        """,
        now=True,
    )


def check_breach_deadlines():
    """Scheduled hourly: escalating alerts as deadline approaches."""
    open_breaches = frappe.get_all(
        "Data Breach",
        filters={"status": ("not in", ["Closed", "Reported to DPB"]), "docstatus": ("!=", 1)},
        fields=["name", "breach_title", "reporting_deadline", "severity", "breach_id"],
    )
    dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")

    for breach in open_breaches:
        remaining = time_diff_in_hours(breach.reporting_deadline, now_datetime())
        frappe.db.set_value("Data Breach", breach.name, "hours_remaining", max(0, remaining))

        if remaining <= 0:
            # Overdue — maximum urgency
            frappe.sendmail(
                recipients=[dpo_email],
                subject=f"🔴 OVERDUE: DPB report for {breach.breach_id} is past deadline!",
                message=f"Breach {breach.breach_title} missed the 72-hour DPB notification window. "
                        f"Document reasons for delay immediately.",
                now=True,
            )
        elif remaining <= 6:
            frappe.sendmail(
                recipients=[dpo_email],
                subject=f"🔴 CRITICAL: {remaining:.0f}h to report {breach.breach_id} to DPB",
                message=f"Submit DPB report NOW for breach {breach.breach_title}.",
                now=True,
            )
        elif remaining <= 24:
            frappe.sendmail(
                recipients=[dpo_email],
                subject=f"⚠️ {remaining:.0f}h remaining to report {breach.breach_id} to DPB",
                message=f"DPB report for {breach.breach_title} must be submitted within {remaining:.0f} hours.",
            )


@frappe.whitelist()
def generate_dpb_report(breach_id: str) -> dict:
    """Generate the statutory DPB notification report as PDF."""
    breach = frappe.get_doc("Data Breach", breach_id)
    settings = frappe.get_single("DPDP Settings")

    report_data = {
        "act_reference": "Section 8(6), DPDP Act 2023",
        "fiduciary_name": settings.company_name,
        "fiduciary_registration": settings.dpdp_registration_no,
        "dpo_name": settings.dpo_name,
        "dpo_email": settings.dpo_email,
        "breach_id": breach.breach_id,
        "detection_time": str(breach.detection_time),
        "nature_of_breach": breach.nature_of_breach,
        "categories_of_data": breach.data_categories,
        "number_of_affected_principals": breach.affected_users_count,
        "systems_affected": breach.systems_affected,
        "likely_consequences": breach.likely_consequences,
        "remedial_actions": breach.remedial_actions,
        "reporting_time": str(now_datetime()),
        "within_window": time_diff_in_hours(breach.reporting_deadline, now_datetime()) >= 0,
    }

    # Render as HTML → PDF
    from frappe.utils.pdf import get_pdf
    html = frappe.render_template(
        "dpdp_compliance/templates/dpb_report.html",
        {"report": report_data, "breach": breach}
    )
    pdf_bytes = get_pdf(html)

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"DPB_Report_{breach.breach_id}.pdf",
        "is_private": 1,
        "content": pdf_bytes,
        "attached_to_doctype": "Data Breach",
        "attached_to_name": breach_id,
    })
    file_doc.save(ignore_permissions=True)

    frappe.db.set_value("Data Breach", breach_id, {
        "status": "Reported to DPB",
        "reported_to_dpb_on": now_datetime(),
    })

    return {"pdf_url": file_doc.file_url, "report": report_data}


@frappe.whitelist()
def notify_affected_principals(breach_id: str) -> dict:
    """Send breach notification emails to all affected Data Principals."""
    breach = frappe.get_doc("Data Breach", breach_id)
    if not breach.affected_users_file:
        frappe.throw("Upload affected users CSV before sending notifications.")

    import csv, io
    file_content = frappe.get_doc("File", {"file_url": breach.affected_users_file}).get_content()
    reader = csv.DictReader(io.StringIO(
        file_content.decode() if isinstance(file_content, bytes) else file_content
    ))

    sent_count = 0
    for row in reader:
        email = row.get("email") or row.get("Email")
        if email:
            frappe.sendmail(
                recipients=[email],
                subject="Important Notice: Personal Data Breach",
                template="breach_principal_notification",
                args={
                    "breach_title": breach.breach_title,
                    "nature": breach.nature_of_breach,
                    "data_categories": breach.data_categories,
                    "remedial_actions": breach.remedial_actions,
                    "dpo_email": frappe.db.get_single_value("DPDP Settings", "dpo_email"),
                },
            )
            sent_count += 1

    frappe.db.set_value("Data Breach", breach_id, "principal_notification_sent", 1)
    return {"sent": sent_count}
```

---

## MODULE B: DATA GOVERNANCE (Sections 8 & 10)

### Key DocTypes
**Data Asset** (RoPA) — maps DocType fields to classification levels  
**Data Processor** — tracks third parties with DPA status  
**DPDP Settings** — single-record configuration hub  
**DPIA Record** — required for Significant Data Fiduciaries  

### Field-Level Encryption
```python
# Use Frappe's built-in Password fieldtype for automatic Fernet encryption
# For custom fields not using Password type:
from frappe.utils.password import encrypt, decrypt

class Employee(Document):
    def before_save(self):
        sensitive = ["aadhaar_no", "pan_number"]
        for field in sensitive:
            val = self.get(field)
            if val and not val.startswith("ENC:"):
                self.set(field, "ENC:" + encrypt(val))

    def after_load(self):
        sensitive = ["aadhaar_no", "pan_number"]
        for field in sensitive:
            val = self.get(field)
            if val and val.startswith("ENC:"):
                self.set(field, decrypt(val[4:]))
```

### Retention Engine (`retention.py`)
```python
# dpdp_compliance/retention.py
import frappe
from frappe.utils import today, add_days

RETENTION_POLICIES_DEFAULT = {
    "Sales Invoice":    ("posting_date",    2920),  # 8 years — GST Act §36
    "Purchase Invoice": ("posting_date",    2920),
    "Employee":         ("date_of_joining", 1825),  # 5 years
    "Lead":             ("creation",        730),   # 2 years
    "Communication":    ("creation",        1095),  # 3 years
    "Web Form Log":     ("creation",        365),   # 1 year
    "Error Log":        ("creation",        90),    # 90 days
}


def run_retention_engine():
    """Scheduled daily: flag/anonymize/delete records past retention."""
    policies = frappe.get_all(
        "Retention Policy",
        fields=["doctype_name", "date_field", "retention_days", "override_erasure"],
    )
    results = {}

    for policy in policies:
        cutoff = add_days(today(), -policy.retention_days)
        try:
            expired = frappe.get_all(
                policy.doctype_name,
                filters={policy.date_field: ("<", cutoff)},
                fields=["name"],
                limit=500,
            )
            for record in expired:
                if policy.override_erasure:
                    _flag_for_review(policy.doctype_name, record.name)
                else:
                    _anonymize_record(policy.doctype_name, record.name)
            results[policy.doctype_name] = len(expired)
        except Exception as e:
            frappe.log_error(f"Retention error {policy.doctype_name}: {e}")

    frappe.log_error(f"Retention engine run: {results}", "Retention Engine")


def _flag_for_review(doctype, name):
    if frappe.get_meta(doctype).get_field("dpdp_retention_flag"):
        frappe.db.set_value(doctype, name, "dpdp_retention_flag", 1)
    dpo = frappe.db.get_single_value("DPDP Settings", "dpo_email")
    frappe.get_doc({
        "doctype": "ToDo",
        "owner": dpo,
        "description": f"Retention review needed: {doctype} {name}",
        "priority": "Medium",
        "reference_type": doctype,
        "reference_name": name,
    }).insert(ignore_permissions=True)


def _anonymize_record(doctype, name):
    from dpdp_compliance.erasure import ANONYMIZATION_MAP
    if doctype not in ANONYMIZATION_MAP:
        return
    doc = frappe.get_doc(doctype, name)
    for field, transform in ANONYMIZATION_MAP[doctype].items():
        if hasattr(doc, field):
            setattr(doc, field, transform(name))
    doc.flags.ignore_validate = True
    doc.save(ignore_permissions=True)
```

### DPO Dashboard
```python
@frappe.whitelist()
def get_dpo_dashboard() -> dict:
    total_users = frappe.db.count("User", {"enabled": 1, "name": ("!=", "Guest")})
    consented_users = frappe.db.sql(
        "SELECT COUNT(DISTINCT user) as c FROM `tabConsent Log` WHERE status='Granted' AND docstatus=1"
    )[0][0]
    consent_pct = round(consented_users / total_users * 100, 1) if total_users else 0

    open_dsrs = frappe.get_all(
        "Data Subject Request",
        filters={"status": ("not in", ["Completed", "Rejected"]), "docstatus": ("!=", 1)},
        fields=["name", "request_type", "sla_deadline", "hours_until_breach"],
    )
    open_breaches = frappe.db.count(
        "Data Breach", {"status": ("not in", ["Closed"]), "docstatus": ("!=", 1)}
    )
    processors_no_dpa = frappe.db.count("Data Processor", {"dpa_signed": 0, "is_active": 1})

    alerts = []
    if consent_pct < 80:
        alerts.append({"level": "warning", "message": f"Consent coverage {consent_pct}% — run legacy remediation"})
    if open_breaches:
        alerts.append({"level": "critical", "message": f"{open_breaches} open breach(es) require immediate action"})
    if processors_no_dpa:
        alerts.append({"level": "warning", "message": f"{processors_no_dpa} processors without signed DPA"})

    return {
        "consent_coverage_pct": consent_pct,
        "total_users": total_users,
        "consented_users": consented_users,
        "open_dsrs": len(open_dsrs),
        "dsrs_near_sla": [d for d in open_dsrs if (d.hours_until_breach or 999) < 24],
        "open_breaches": open_breaches,
        "processors_no_dpa": processors_no_dpa,
        "alerts": alerts,
    }
```

---

## MODULE C: CHILDREN'S DATA & VPC (Section 9)

### Legal Requirements
- Age < 18 → Verifiable Parental Consent (VPC) required
- No behavioral monitoring, tracking, or targeted advertising for minors
- Guardian must also be verified as an adult

### User DocType Custom Fields (Fixtures)
```json
[
  {"dt":"User","fieldname":"date_of_birth","fieldtype":"Date","label":"Date of Birth"},
  {"dt":"User","fieldname":"is_minor","fieldtype":"Check","label":"Is Minor","read_only":1},
  {"dt":"User","fieldname":"guardian_email","fieldtype":"Data","label":"Guardian Email"},
  {"dt":"User","fieldname":"vpc_status","fieldtype":"Select",
   "label":"VPC Status","options":"Not Required\nPending\nVerified\nExpired","read_only":1},
  {"dt":"User","fieldname":"vpc_token","fieldtype":"Data","label":"VPC Token","read_only":1},
  {"dt":"User","fieldname":"account_status","fieldtype":"Select",
   "options":"Active\nPending VPC\nSuspended","default":"Active","read_only":1}
]
```
Save as `dpdp_compliance/fixtures/custom_fields.json` and list in `hooks.py`:
```python
fixtures = ["Custom Field"]
```

### VPC Engine (`vpc.py`)
```python
# dpdp_compliance/vpc.py
import frappe
from frappe.utils import now_datetime, add_days, date_diff, today


def detect_minor_on_save(doc, method):
    """Hook: User.before_save"""
    if doc.date_of_birth:
        age_days = date_diff(today(), doc.date_of_birth)
        is_minor = age_days < (18 * 365.25)
        doc.is_minor = 1 if is_minor else 0
        if is_minor and doc.vpc_status not in ["Verified"]:
            doc.vpc_status = "Pending"
            doc.account_status = "Pending VPC"
            doc.enabled = 0  # Lock account until VPC complete


@frappe.whitelist()
def initiate_vpc(user_id: str, guardian_email: str, guardian_name: str) -> dict:
    """Called after minor signs up. Sends VPC request to guardian."""
    import secrets
    token = secrets.token_urlsafe(32)
    expiry = add_days(now_datetime(), 7)

    frappe.cache().set_value(
        f"vpc:{token}",
        {"user": user_id, "guardian_email": guardian_email, "expiry": str(expiry)},
        expires_in_sec=7 * 24 * 3600,
    )
    frappe.db.set_value("User", user_id, "vpc_token", token)

    minor_name = frappe.get_value("User", user_id, "full_name")
    portal_url = frappe.utils.get_url()
    vpc_link = f"{portal_url}/vpc-consent?token={token}"

    frappe.sendmail(
        recipients=[guardian_email],
        subject=f"Parental Consent Required for {minor_name}'s Account",
        template="vpc_guardian_request",
        args={"guardian_name": guardian_name, "minor_name": minor_name, "vpc_link": vpc_link},
        now=True,
    )
    return {"token": token, "link": vpc_link}


@frappe.whitelist(allow_guest=True)
def get_vpc_session(token: str) -> dict | None:
    """Check if a VPC token is valid. Used by the VPC consent web page."""
    cached = frappe.cache().get_value(f"vpc:{token}")
    if not cached:
        return None
    user_name = frappe.get_value("User", cached["user"], "full_name")
    return {"minor_name": user_name, "valid": True}


def initiate_digilocker_auth(token: str) -> dict:
    """Redirect guardian to DigiLocker OAuth2 for identity verification."""
    import urllib.parse
    settings = frappe.get_single("DPDP Settings")
    params = {
        "response_type": "code",
        "client_id": settings.digilocker_client_id,
        "redirect_uri": f"{frappe.utils.get_url()}/vpc-callback",
        "state": token,
        "scope": "aadhaar_number name dob",
    }
    auth_url = (
        "https://api.digitallocker.gov.in/public/oauth2/1/authorize?"
        + urllib.parse.urlencode(params)
    )
    return {"redirect_url": auth_url}


def handle_digilocker_callback(code: str, state_token: str) -> dict:
    """Process DigiLocker callback, verify guardian age, activate minor account."""
    import requests
    from datetime import datetime

    settings = frappe.get_single("DPDP Settings")

    # Exchange code for access token
    token_resp = requests.post(
        "https://api.digitallocker.gov.in/public/oauth2/1/token",
        data={
            "code": code,
            "grant_type": "authorization_code",
            "client_id": settings.digilocker_client_id,
            "client_secret": settings.digilocker_client_secret,
            "redirect_uri": f"{frappe.utils.get_url()}/vpc-callback",
        },
        timeout=30,
    )
    if token_resp.status_code != 200:
        frappe.throw("DigiLocker authentication failed.")

    access_token = token_resp.json()["access_token"]

    # Get guardian profile
    profile_resp = requests.get(
        "https://api.digitallocker.gov.in/public/oauth2/1/xml/account",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if profile_resp.status_code != 200:
        frappe.throw("Failed to fetch identity from DigiLocker.")

    profile = profile_resp.json()

    # Verify guardian is an adult
    guardian_dob_str = profile.get("dob", "")  # DD-MM-YYYY
    if guardian_dob_str:
        dob = datetime.strptime(guardian_dob_str, "%d-%m-%Y")
        guardian_age_days = (datetime.now() - dob).days
        if guardian_age_days < (18 * 365.25):
            frappe.throw("Guardian must be 18 years or older to grant parental consent.")

    # Get cached session
    cached = frappe.cache().get_value(f"vpc:{state_token}")
    if not cached:
        frappe.throw("VPC session expired. The minor must request a new consent link.")

    user_id = cached["user"]

    # Activate account
    frappe.db.set_value("User", user_id, {
        "vpc_status": "Verified",
        "vpc_token": state_token,
        "account_status": "Active",
        "enabled": 1,
    })

    # Block prohibited purposes
    _block_prohibited_purposes_for_minor(user_id)

    # Grant mandatory consents
    from dpdp_compliance.consent import create_consent_log
    for p in frappe.get_all("Consent Purpose", filters={"is_mandatory": 1, "is_active": 1}):
        create_consent_log(
            user=user_id, purpose_id=p.name,
            status="Granted", notice_version_id=None,
            channel="Web", is_minor=True, token=state_token,
        )

    frappe.cache().delete_value(f"vpc:{state_token}")

    # Notify
    frappe.sendmail(
        recipients=[frappe.get_value("User", user_id, "email")],
        subject="Your Account Has Been Activated",
        message="Parental consent verified via DigiLocker. Your account is now active.",
        now=True,
    )
    return {"success": True, "user": user_id}


def _block_prohibited_purposes_for_minor(user: str):
    """Hard-block tracking, marketing, analytics for minor accounts."""
    prohibited_keywords = ["marketing", "analytics", "tracking", "advertising", "profiling"]
    for purpose in frappe.get_all("Consent Purpose", fields=["name", "purpose_name"]):
        if any(kw in purpose.purpose_name.lower() for kw in prohibited_keywords):
            from dpdp_compliance.consent import create_consent_log
            create_consent_log(
                user=user, purpose_id=purpose.name,
                status="Denied", notice_version_id=None,
                channel="System", is_minor=True,
            )
    # Unsubscribe from all email groups
    user_email = frappe.get_value("User", user, "email")
    frappe.db.set_value("Email Group Member", {"email": user_email}, "unsubscribed", 1)
```

---

## DPDP Settings (Single DocType) — All Fields
```
company_name, dpdp_registration_no, act_commencement_date, is_sdf
dpo_name, dpo_email, dpo_phone
irt_emails (comma-separated)
grievance_url, default_sla_days
digilocker_client_id, digilocker_client_secret, digilocker_enabled
last_audit_date, next_audit_date
```

---

## Combined Go-Live Checklist

**Breach Response**
- [ ] `Data Breach` DPO-only permissions confirmed
- [ ] `after_insert` hook sets deadline (T + 72h) automatically  
- [ ] Hourly scheduler for `check_breach_deadlines` is running
- [ ] IRT email list configured in DPDP Settings
- [ ] DPB report PDF template exists at `templates/dpb_report.html`

**Governance**
- [ ] All DocTypes with personal data catalogued in `Data Asset`
- [ ] Level 4 fields (Aadhaar, PAN, bank) use Password fieldtype or `ENC:` prefix
- [ ] `Retention Policy` entries exist for all financial DocTypes
- [ ] Retention engine scheduled daily and tested in dry-run mode
- [ ] All active processors have `dpa_signed = 1`
- [ ] Export permission removed from non-DPO roles

**VPC / Children**
- [ ] Custom fields added to User DocType via fixtures
- [ ] `detect_minor_on_save` hook tested: DOB < 18 → account suspended
- [ ] DigiLocker Client ID/Secret configured and OAuth2 sandbox tested
- [ ] `/vpc-consent` and `/vpc-callback` routes registered
- [ ] Marketing/analytics auto-denied for all minor accounts
- [ ] Guardian age verification (must be 18+) working in DigiLocker callback
