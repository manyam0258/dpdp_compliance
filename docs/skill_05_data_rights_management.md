---
name: dpdp-data-rights-management
description: >
  Use this skill for the Data Principal Rights Management (DPRM) module of dpdp_compliance
  on Frappe v16. Covers Data Subject Requests (DSR), identity verification (OTP), right to
  access, right to correction, right to erasure with retention checks, anonymization engine,
  right to nomination, grievance redressal, and SLA management. Use when the user mentions
  "DSR", "erasure", "right to access", "anonymize", "data subject request", "SLA", "OTP
  verification", "retention check", "nomination", "grievance", or Sections 11–14 of DPDP.
  Always read skill_01_frappe_fullstack_core.md for DocType patterns first.
compatibility:
  frappe_version: ">=16.0"
  app: dpdp_compliance
---

# DPDP Data Principal Rights Management (DPRM)

## Legal Basis: Sections 11–14 DPDP Act 2023
- §11: Right to Access — summary of data processed + processors/fiduciaries it's shared with
- §12: Right to Correction & Erasure
- §13: Right to Grievance Redressal — mandatory internal mechanism
- §14: Right to Nomination — designate someone to exercise rights after death/incapacity

---

## DocType: Data Subject Request

```json
{
  "name": "Data Subject Request",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {"fieldname":"user","fieldtype":"Link","options":"User","reqd":1,"in_list_view":1},
    {"fieldname":"request_type","fieldtype":"Select",
     "options":"Access\nCorrection\nErasure\nNomination\nGrievance","reqd":1,"in_list_view":1},
    {"fieldname":"description","fieldtype":"Text","reqd":1},
    {"fieldname":"status","fieldtype":"Select",
     "options":"Open\nID Verified\nProcessing\nCompleted\nRejected",
     "default":"Open","in_list_view":1},
    {"fieldname":"identity_verified","fieldtype":"Check","default":0,"read_only":1},
    {"fieldname":"verification_method","fieldtype":"Select",
     "options":"OTP Email\nOTP SMS\nAadhaar OTP\nDijiLocker"},
    {"fieldname":"received_on","fieldtype":"Datetime","read_only":1},
    {"fieldname":"sla_deadline","fieldtype":"Datetime","read_only":1},
    {"fieldname":"hours_until_breach","fieldtype":"Float","read_only":1},
    {"fieldname":"assigned_to","fieldtype":"Link","options":"User"},
    {"fieldname":"rejection_reason","fieldtype":"Small Text"},
    {"fieldname":"resolution_notes","fieldtype":"Text"},
    {"fieldname":"nominee_name","fieldtype":"Data"},
    {"fieldname":"nominee_contact","fieldtype":"Data"},
    {"fieldname":"nominee_relationship","fieldtype":"Data"}
  ]
}
```

## DocType: Retention Policy

```json
{
  "name": "Retention Policy",
  "fields": [
    {"fieldname":"policy_name","fieldtype":"Data","reqd":1,"unique":1},
    {"fieldname":"doctype_name","fieldtype":"Link","options":"DocType","reqd":1},
    {"fieldname":"retention_days","fieldtype":"Int","reqd":1},
    {"fieldname":"legal_basis","fieldtype":"Small Text"},
    {"fieldname":"date_field","fieldtype":"Data","default":"posting_date",
     "description":"Field name on the DocType that stores the record date"},
    {"fieldname":"override_erasure","fieldtype":"Check","default":1,
     "description":"If 1, records within retention window block erasure requests"}
  ]
}
```

---

## DSR Engine (`dsr.py`)

```python
# dpdp_compliance/dsr.py
import frappe
from frappe.utils import now_datetime, add_days, time_diff_in_hours

SLA_DAYS = 7  # Update when DPDP Rules specify exact period


# ── Hooks ──────────────────────────────────────────────────────────────────

def set_sla_deadline(doc, method):
    """Hook: Data Subject Request.before_insert"""
    doc.received_on = now_datetime()
    sla_days = int(
        frappe.db.get_single_value("DPDP Settings", "default_sla_days") or SLA_DAYS
    )
    doc.sla_deadline = add_days(now_datetime(), sla_days)


def on_status_change(doc, method):
    """Hook: Data Subject Request.on_update — update hours_until_breach"""
    if doc.sla_deadline:
        remaining = time_diff_in_hours(doc.sla_deadline, now_datetime())
        doc.hours_until_breach = max(0, remaining)
        # Direct DB set to avoid recursion
        frappe.db.set_value(
            "Data Subject Request", doc.name, "hours_until_breach", doc.hours_until_breach
        )


# ── Submission ────────────────────────────────────────────────────────────

@frappe.whitelist()
def submit_dsr(
    request_type: str,
    description: str,
    nominee_name: str = "",
    nominee_email: str = "",
) -> dict:
    """API: Data Principal submits a DSR. Triggers OTP identity verification."""
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)

    dsr = frappe.get_doc({
        "doctype": "Data Subject Request",
        "user": user,
        "request_type": request_type,
        "description": description,
        "status": "Open",
        "nominee_name": nominee_name,
        "nominee_contact": nominee_email,
    })
    dsr.insert(ignore_permissions=True)

    # Send OTP
    _send_verification_otp(user, dsr.name)

    return {
        "dsr_id": dsr.name,
        "sla_deadline": str(dsr.sla_deadline),
        "message": "Request submitted. OTP sent to your registered email for verification.",
    }


# ── Identity Verification ─────────────────────────────────────────────────

def _send_verification_otp(user: str, dsr_id: str):
    """Generate and send a 6-digit OTP to the user's email."""
    import random
    otp = str(random.randint(100000, 999999))
    frappe.cache().set_value(f"dsr_otp:{dsr_id}", otp, expires_in_sec=600)  # 10 min

    email = frappe.get_value("User", user, "email")
    frappe.sendmail(
        recipients=[email],
        subject="Verify Your Identity — Privacy Request",
        message=(
            f"Your verification code for request <b>{dsr_id}</b> is: "
            f"<h2>{otp}</h2>"
            f"This code expires in 10 minutes."
        ),
        now=True,  # Immediate — don't queue
    )


@frappe.whitelist()
def verify_dsr_otp(dsr_id: str, otp: str) -> dict:
    """Verify OTP and mark DSR as identity-verified."""
    user = frappe.session.user
    dsr = frappe.get_doc("Data Subject Request", dsr_id)

    if dsr.user != user:
        frappe.throw("Unauthorized: This is not your request.", frappe.PermissionError)

    stored_otp = frappe.cache().get_value(f"dsr_otp:{dsr_id}")
    if not stored_otp:
        frappe.throw("OTP expired. Please submit a new request.")
    if stored_otp != otp.strip():
        frappe.throw("Invalid OTP. Please check and try again.")

    frappe.cache().delete_value(f"dsr_otp:{dsr_id}")
    frappe.db.set_value("Data Subject Request", dsr_id, {
        "status": "ID Verified",
        "identity_verified": 1,
        "verification_method": "OTP Email",
    })
    return {"verified": True, "dsr_id": dsr_id}


# ── Processing ────────────────────────────────────────────────────────────

@frappe.whitelist()
def process_access_request(dsr_id: str) -> dict:
    """Generate access report for the user and mark DSR as completed."""
    dsr = frappe.get_doc("Data Subject Request", dsr_id)
    _assert_verified(dsr)

    from dpdp_compliance.access_report import generate_access_report_direct
    report = generate_access_report_direct(dsr.user)

    # Attach report to DSR
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"access_report_{dsr_id}.json",
        "is_private": 1,
        "content": frappe.as_json(report, indent=2).encode(),
        "attached_to_doctype": "Data Subject Request",
        "attached_to_name": dsr_id,
    })
    file_doc.save(ignore_permissions=True)

    _close_dsr(dsr, f"Access report generated. Download: {file_doc.file_url}")
    return {"status": "Completed", "report_url": file_doc.file_url}


@frappe.whitelist()
def process_erasure_request(dsr_id: str, dry_run: bool = False) -> dict:
    """Execute erasure/anonymization. Always checks retention first."""
    dsr = frappe.get_doc("Data Subject Request", dsr_id)
    _assert_verified(dsr)

    from dpdp_compliance.erasure import execute_erasure
    result = execute_erasure(dsr.user, dry_run=bool(dry_run))

    if not dry_run:
        if result["status"] == "Success":
            _close_dsr(dsr, f"Data anonymized across: {', '.join(result['anonymized'])}")
        else:
            frappe.db.set_value("Data Subject Request", dsr_id, {
                "status": "Rejected",
                "rejection_reason": result.get("reason", "Retention policy blocks erasure."),
            })

    return result


def _assert_verified(dsr):
    if not dsr.identity_verified:
        frappe.throw("Identity verification is required before processing this request.")
    if dsr.request_type not in ["Access", "Correction", "Erasure", "Nomination", "Grievance"]:
        frappe.throw(f"Unknown request type: {dsr.request_type}")


def _close_dsr(dsr, notes: str):
    frappe.db.set_value("Data Subject Request", dsr.name, {
        "status": "Completed",
        "resolution_notes": notes,
    })


# ── SLA Monitoring ────────────────────────────────────────────────────────

def check_sla_breaches():
    """Scheduled daily: Alert DPO of DSRs approaching SLA."""
    warning_threshold = add_days(now_datetime(), 1)
    nearing = frappe.get_all(
        "Data Subject Request",
        filters={
            "status": ("not in", ["Completed", "Rejected"]),
            "sla_deadline": ("<", warning_threshold),
            "docstatus": ("!=", 1),
        },
        fields=["name", "user", "request_type", "sla_deadline", "hours_until_breach"],
    )
    if nearing:
        dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")
        frappe.sendmail(
            recipients=[dpo_email],
            subject=f"⚠️ {len(nearing)} DSR(s) Near SLA Deadline",
            template="dsr_sla_alert",
            args={"requests": nearing},
        )

    # Overdue DSRs (already past deadline)
    overdue = frappe.get_all(
        "Data Subject Request",
        filters={
            "status": ("not in", ["Completed", "Rejected"]),
            "sla_deadline": ("<", now_datetime()),
            "docstatus": ("!=", 1),
        },
        fields=["name", "user", "request_type"],
    )
    if overdue:
        dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")
        frappe.sendmail(
            recipients=[dpo_email],
            subject=f"🔴 OVERDUE: {len(overdue)} DSR(s) Past SLA Deadline — Legal Risk",
            message=f"The following DSRs are overdue: {[r.name for r in overdue]}",
            now=True,
        )
```

---

## Anonymization Engine (`erasure.py`)

```python
# dpdp_compliance/erasure.py
import frappe
from frappe.utils import now_datetime, random_string, today, add_days

# ── Anonymization Map ─────────────────────────────────────────────────────
# Extend this dict with any custom DocTypes that hold personal data.
ANONYMIZATION_MAP: dict[str, dict[str, callable]] = {
    "User": {
        "first_name": lambda _: "Anonymized",
        "last_name": lambda _: random_string(10),
        "email": lambda _: f"del-{random_string(8)}@anonymized.invalid",
        "phone": lambda _: "",
        "mobile_no": lambda _: "",
        "birth_date": lambda _: None,
        "user_image": lambda _: "",
    },
    "Customer": {
        "customer_name": lambda _: f"Anonymized-{random_string(6)}",
        "email_id": lambda _: f"del-{random_string(8)}@anonymized.invalid",
        "mobile_no": lambda _: "",
        "tax_id": lambda _: "",
    },
    "Contact": {
        "first_name": lambda _: "Anonymized",
        "last_name": lambda _: random_string(6),
        "email_id": lambda _: f"del-{random_string(8)}@anonymized.invalid",
        "phone": lambda _: "",
        "mobile_no": lambda _: "",
    },
    "Employee": {
        "first_name": lambda _: "Anonymized",
        "last_name": lambda _: random_string(6),
        "personal_email": lambda _: f"del-{random_string(8)}@anonymized.invalid",
        "cell_number": lambda _: "",
        "date_of_birth": lambda _: None,
        "pan_number": lambda _: "",
        "aadhaar_no": lambda _: "",
        "bank_account_no": lambda _: "",
    },
}


def check_retention_blocks(user_email: str) -> list[dict]:
    """
    Returns list of DocType records that block erasure due to retention policies.
    """
    policies = frappe.get_all(
        "Retention Policy",
        filters={"override_erasure": 1},
        fields=["doctype_name", "retention_days", "date_field", "legal_basis"],
    )
    blocks = []
    customer = frappe.get_value("Customer", {"email_id": user_email})

    for policy in policies:
        cutoff = add_days(today(), -policy.retention_days)
        try:
            filters: dict = {policy.date_field: (">", cutoff)}
            if policy.doctype_name == "Sales Invoice" and customer:
                filters["customer"] = customer
            elif policy.doctype_name == "Employee":
                filters["personal_email"] = user_email
            else:
                continue  # Can't match without a user link

            count = frappe.db.count(policy.doctype_name, filters)
            if count:
                retain_until = add_days(today(), policy.retention_days)
                blocks.append({
                    "doctype": policy.doctype_name,
                    "count": count,
                    "legal_basis": policy.legal_basis,
                    "retain_until": str(retain_until),
                    "reason": f"{count} {policy.doctype_name} record(s) must be retained until {retain_until}.",
                })
        except Exception as e:
            frappe.log_error(f"Retention check error for {policy.doctype_name}: {e}")

    return blocks


def execute_erasure(user_id: str, dry_run: bool = False) -> dict:
    """
    Main erasure function. Anonymizes data rather than hard-deleting
    to preserve referential integrity in ERPNext.

    NEVER use frappe.delete_doc() for personal data — it breaks foreign keys.
    """
    user_email = frappe.get_value("User", user_id, "email")
    if not user_email:
        return {"status": "Failed", "reason": f"User not found: {user_id}"}

    # Step 1: Retention check
    blocks = check_retention_blocks(user_email)
    if blocks:
        return {
            "status": "Blocked",
            "reason": "Mandatory retention policy prevents full erasure.",
            "blocks": blocks,
        }

    if dry_run:
        return {
            "status": "DryRun",
            "would_anonymize": list(ANONYMIZATION_MAP.keys()),
            "blocks": [],
        }

    anonymized = []

    # Step 2: Anonymize each DocType
    for doctype, field_map in ANONYMIZATION_MAP.items():
        records = _find_user_records(doctype, user_id, user_email)
        for record_name in records:
            try:
                doc = frappe.get_doc(doctype, record_name)
                for field, transform in field_map.items():
                    if hasattr(doc, field):
                        setattr(doc, field, transform(user_id))
                doc.flags.ignore_validate = True
                doc.flags.ignore_permissions = True
                doc.save()
                anonymized.append(f"{doctype}:{record_name}")
            except Exception as e:
                frappe.log_error(f"Anonymization error {doctype}:{record_name}: {e}")

    if "User" in [a.split(":")[0] for a in anonymized]:
        # Disable account
        frappe.db.set_value("User", user_id, "enabled", 0)

    # Step 3: Withdraw all active consents
    from dpdp_compliance.consent import create_consent_log
    active_consents = frappe.get_all(
        "Consent Log",
        filters={"user": user_id, "status": "Granted", "docstatus": 1},
        fields=["purpose"],
    )
    for consent in active_consents:
        create_consent_log(
            user=user_id,
            purpose_id=consent.purpose,
            status="Withdrawn",
            notice_version_id=None,
            channel="System",
        )

    # Step 4: Audit log
    frappe.get_doc({
        "doctype": "Data Erasure Log",
        "user": user_id,
        "executed_by": frappe.session.user,
        "executed_on": now_datetime(),
        "anonymized_records": frappe.as_json(anonymized),
    }).insert(ignore_permissions=True)

    return {
        "status": "Success",
        "anonymized": anonymized,
        "message": f"Anonymized {len(anonymized)} records.",
    }


def _find_user_records(doctype: str, user_id: str, user_email: str) -> list[str]:
    """Find all records in a DocType that belong to this user."""
    found = []
    # Try user field
    if frappe.get_meta(doctype).get_field("user"):
        found += [r.name for r in frappe.get_all(doctype, filters={"user": user_id})]
    # Try email fields
    for field in ["email", "email_id", "personal_email"]:
        if frappe.get_meta(doctype).get_field(field):
            found += [r.name for r in frappe.get_all(doctype, filters={field: user_email})]
    return list(set(found))
```

---

## Access Report

```python
# dpdp_compliance/access_report.py
import frappe
from frappe.utils import now_datetime

def generate_access_report_direct(user: str) -> dict:
    user_doc = frappe.get_doc("User", user)
    user_email = user_doc.email

    return {
        "generated_at": str(now_datetime()),
        "data_principal": user,
        "profile": {
            "name": user_doc.full_name,
            "email": user_doc.email,
            "phone": user_doc.phone,
            "joined": str(user_doc.creation),
        },
        "consents": frappe.get_all(
            "Consent Log",
            filters={"user": user, "docstatus": 1},
            fields=["purpose", "status", "timestamp", "expiry_date"],
            order_by="timestamp asc",
        ),
        "orders": frappe.get_all(
            "Sales Order",
            filters={"contact_email": user_email},
            fields=["name", "transaction_date", "grand_total"],
        ),
        "data_shared_with": frappe.get_all(
            "Data Processor",
            filters={"is_active": 1},
            fields=["processor_name", "purpose", "country"],
        ),
        "open_requests": frappe.get_all(
            "Data Subject Request",
            filters={"user": user, "docstatus": ("!=", 1)},
            fields=["name", "request_type", "status", "received_on"],
        ),
    }
```

---

## Go-Live Checklist

- [ ] `Retention Policy` entries for all financial DocTypes (Sales Invoice = 2920 days)
- [ ] `Data Subject Request` SLA timer hook wired in `hooks.py`
- [ ] OTP expiry is 10 minutes (Redis TTL = 600 seconds)
- [ ] `execute_erasure()` tested against customer with open invoices (should return "Blocked")
- [ ] DPO email alert fires when DSR approaches SLA breach (test with `check_sla_breaches()`)
- [ ] `Data Erasure Log` DocType exists for audit trail
- [ ] All API endpoints are `@frappe.whitelist()` (not `allow_guest=True`)
- [ ] Anonymization tested: no referential integrity errors after run
