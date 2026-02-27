---
name: frappe-fullstack-core
description: >
  Use this skill for any Frappe v16 full-stack development task — creating apps, DocTypes,
  server scripts, client scripts, REST APIs, hooks, scheduled jobs, permissions, web forms,
  print formats, or bench operations. Always use this skill when the user mentions "Frappe",
  "ERPNext", "DocType", "bench", "hooks.py", "server script", "client script", "whitelist",
  "frappe.call", "frappe.db", "scheduler", "custom app", "install app", or any Frappe-specific
  development concept. This is the foundational skill for the entire dpdp_compliance app
  development — use it before and alongside all other DPDP module skills.
compatibility:
  frappe_version: ">=16.0"
  python: ">=3.10"
  node: ">=18"
---

# Frappe v16 Full-Stack Core Development Skill

## Purpose
Complete reference for building production-grade custom Frappe apps on v16. Covers the full
stack: DocType design, Python backend, JavaScript frontend, REST APIs, hooks, permissions,
scheduled jobs, and bench operations — all in the context of the `dpdp_compliance` app.

---

## 1. App Bootstrapping

```bash
# Create the custom app
cd /path/to/frappe-bench
bench new-app dpdp_compliance
# Prompts: App Title, Description, Publisher, Email, Icon, Color, License

# Install on site
bench --site your-site.local install-app dpdp_compliance

# Development mode (auto-reload)
bench start  # Starts all services including Redis, Celery workers

# Build JS/CSS assets
bench build --app dpdp_compliance

# After Python changes (hooks, DocType)
bench --site your-site.local migrate  # Runs DB migrations
```

### App Directory Structure
```
dpdp_compliance/
├── dpdp_compliance/              # Python package
│   ├── __init__.py
│   ├── hooks.py                  # ← ALL event bindings here
│   ├── modules.txt               # e.g. "DPDP Compliance"
│   ├── patches.txt               # DB migration patches
│   ├── doctype/
│   │   └── consent_log/
│   │       ├── consent_log.json  # DocType schema
│   │       ├── consent_log.py    # Controller
│   │       └── consent_log.js   # Client script
│   ├── api.py                    # @frappe.whitelist endpoints
│   ├── consent.py
│   ├── breach.py
│   └── ...
├── public/
│   ├── js/                       # Bundled JS (via hooks.py)
│   └── css/
├── www/                          # Web pages (no auth by default)
│   ├── dpdp-portal.py
│   └── dpdp-portal.html
└── setup.py
```

---

## 2. DocType Design Patterns

### DocType JSON Schema (consent_log.json)
```json
{
  "name": "Consent Log",
  "module": "DPDP Compliance",
  "doctype": "DocType",
  "is_submittable": 1,
  "track_changes": 1,
  "allow_import": 0,
  "fields": [
    {
      "fieldname": "user",
      "fieldtype": "Link",
      "options": "User",
      "label": "User",
      "reqd": 1,
      "in_list_view": 1
    },
    {
      "fieldname": "status",
      "fieldtype": "Select",
      "options": "Granted\nDenied\nWithdrawn\nExpired",
      "label": "Status",
      "reqd": 1,
      "in_list_view": 1
    },
    {
      "fieldname": "timestamp",
      "fieldtype": "Datetime",
      "label": "Timestamp",
      "reqd": 1,
      "read_only": 1
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1,
      "write": 0,
      "delete": 0,
      "submit": 1,
      "cancel": 0,
      "create": 1
    },
    {
      "role": "DPO",
      "read": 1,
      "write": 0,
      "delete": 0,
      "export": 1
    }
  ]
}
```

### DocType Controller (consent_log.py)
```python
import frappe
from frappe.model.document import Document

class ConsentLog(Document):

    def before_insert(self):
        """Auto-populate audit fields."""
        self.timestamp = frappe.utils.now_datetime()
        self.ip_address = frappe.local.request_ip
        self.user_agent = frappe.get_request_header("User-Agent")

    def validate(self):
        """Business rule validation."""
        if not self.purpose:
            frappe.throw("Consent Purpose is required.", frappe.MandatoryError)

    def before_submit(self):
        """Pre-submit checks — immutability guard."""
        if self.status not in ["Granted", "Denied", "Withdrawn", "Expired"]:
            frappe.throw("Invalid status for submission.")

    def on_submit(self):
        """Post-submit side effects."""
        if self.status == "Withdrawn":
            self._propagate_withdrawal()

    def _propagate_withdrawal(self):
        """Internal: stop processing for this purpose."""
        frappe.publish_realtime(
            "consent_withdrawn",
            {"user": self.user, "purpose": self.purpose},
        )

    def on_trash(self):
        """Prevent deletion — Consent Logs are immutable evidence."""
        frappe.throw(
            "Consent Logs cannot be deleted. They are legal evidence.",
            frappe.PermissionError,
        )
```

---

## 3. hooks.py — The Event Bus

```python
# dpdp_compliance/hooks.py

app_name = "dpdp_compliance"
app_title = "DPDP Compliance"
app_publisher = "Your Org"
app_description = "DPDP Act 2023 Compliance for Frappe/ERPNext"
app_version = "1.0.0"

# ── DocType Event Hooks ──────────────────────────────────────────────────────
doc_events = {
    "User": {
        "after_insert":   "dpdp_compliance.consent.process_signup_consent",
        "before_save":    "dpdp_compliance.vpc.detect_minor_on_save",
        "on_trash":       "dpdp_compliance.governance.log_user_deletion_attempt",
    },
    "Consent Log": {
        "before_insert":  "dpdp_compliance.validations.validate_consent_log",
        "on_trash":       "dpdp_compliance.validations.block_consent_log_deletion",
    },
    "Data Breach": {
        "after_insert":   "dpdp_compliance.breach.on_breach_creation",
        "on_update":      "dpdp_compliance.breach.check_status_transition",
    },
    "Data Subject Request": {
        "before_insert":  "dpdp_compliance.dsr.set_sla_deadline",
        "on_update":      "dpdp_compliance.dsr.on_status_change",
    },
}

# ── Scheduled Jobs ───────────────────────────────────────────────────────────
scheduler_events = {
    "hourly": [
        "dpdp_compliance.breach.check_breach_deadlines",
    ],
    "daily": [
        "dpdp_compliance.consent.expire_stale_consents",
        "dpdp_compliance.retention.run_retention_engine",
        "dpdp_compliance.dsr.check_sla_breaches",
    ],
    "weekly": [
        "dpdp_compliance.consent.send_legacy_consent_reminders",
        "dpdp_compliance.governance.audit_unmapped_fields",
    ],
}

# ── Permission Query Hooks (Row-Level Security) ──────────────────────────────
permission_query_conditions = {
    "Consent Log": "dpdp_compliance.permissions.consent_log_query",
    "Data Breach":  "dpdp_compliance.permissions.breach_dpo_only_query",
}

# ── Website Routes ───────────────────────────────────────────────────────────
website_route_rules = [
    {"from_route": "/dpdp-portal", "to_route": "dpdp-portal"},
    {"from_route": "/vpc-consent",  "to_route": "vpc-consent"},
    {"from_route": "/vpc-callback", "to_route": "vpc-callback"},
]

# ── JS/CSS Asset Bundles ─────────────────────────────────────────────────────
app_include_js = [
    "/assets/dpdp_compliance/js/consent_modal.js",
    "/assets/dpdp_compliance/js/minor_protection.js",
]

# ── After Install ────────────────────────────────────────────────────────────
after_install = "dpdp_compliance.setup.after_install"
after_migrate = "dpdp_compliance.setup.after_migrate"
```

---

## 4. REST API Patterns

### Whitelisted API Methods
```python
# dpdp_compliance/api.py
import frappe

# ── Public API (no auth required) ───────────────────────────────────────────
@frappe.whitelist(allow_guest=True)
def get_active_notice(language="English"):
    """Returns the active Privacy Notice for a given language."""
    notices = frappe.get_all(
        "Privacy Notice",
        filters={"is_active": 1, "language": language, "docstatus": 1},
        fields=["name", "content_html", "version", "notice_id"],
        limit=1,
    )
    if not notices:
        return None
    notice = notices[0]
    # Enrich with linked purposes
    purposes = frappe.get_all(
        "Privacy Notice Consent Purpose",  # Child table
        filters={"parent": notice.name},
        fields=["consent_purpose as name"],
    )
    enriched = []
    for p in purposes:
        cp = frappe.get_cached_doc("Consent Purpose", p.name)
        enriched.append({
            "name": cp.name,
            "purpose_name": cp.purpose_name,
            "description": cp.description,
            "is_mandatory": cp.is_mandatory,
        })
    notice["purposes"] = enriched
    return notice


# ── Authenticated API ────────────────────────────────────────────────────────
@frappe.whitelist()
def withdraw_consent(purpose_id: str) -> dict:
    """Data Principal withdraws consent. Requires active session."""
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required.", frappe.AuthenticationError)

    from dpdp_compliance.consent import create_consent_log, get_active_consent
    if not get_active_consent(user, purpose_id):
        frappe.throw(f"No active consent found for purpose: {purpose_id}")

    log_name = create_consent_log(
        user=user,
        purpose_id=purpose_id,
        status="Withdrawn",
        notice_version_id=None,
        channel="Web",
    )
    return {"success": True, "log": log_name}


# ── File Download API ────────────────────────────────────────────────────────
@frappe.whitelist()
def download_my_data():
    """Generates a JSON data export for the logged-in user (Right to Access)."""
    user = frappe.session.user
    from dpdp_compliance.access_report import generate_access_report_direct
    report = generate_access_report_direct(user)

    frappe.response.filename = f"my_data_{frappe.utils.today()}.json"
    frappe.response.filecontent = frappe.as_json(report, indent=2)
    frappe.response.type = "download"
```

### Calling APIs from Client JS
```javascript
// Standard frappe.call — auto-includes CSRF token (X-Frappe-CSRF-Token header)
frappe.call({
    method: "dpdp_compliance.api.get_active_notice",
    args: { language: "English" },
    callback: function(r) {
        if (r.message) {
            console.log(r.message);
        }
    },
    error: function(r) {
        frappe.msgprint("Error: " + r.message);
    }
});

// For custom fetch (e.g., in Doppio/Vue) — CSRF MUST be handled manually:
// See skill_doppio_frontend.md for the full pattern
```

---

## 5. Client Scripts (DocType JS)

```javascript
// dpdp_compliance/doctype/data_subject_request/data_subject_request.js
frappe.ui.form.on("Data Subject Request", {

    refresh: function(frm) {
        // Show custom action buttons based on state
        if (frm.doc.status === "ID Verified" && !frm.doc.docstatus) {
            frm.add_custom_button("Process Request", function() {
                frappe.confirm(
                    "Are you sure you want to process this request? This action may anonymize data.",
                    function() {
                        frm.call("process_request").then(() => {
                            frm.reload_doc();
                        });
                    }
                );
            }, "Actions").addClass("btn-primary");
        }

        // SLA countdown indicator
        if (frm.doc.sla_deadline && frm.doc.status !== "Completed") {
            const deadline = moment(frm.doc.sla_deadline);
            const now = moment();
            const hoursLeft = deadline.diff(now, "hours");

            const indicator = hoursLeft < 24
                ? `<span class="indicator red">⚠️ ${hoursLeft}h until SLA breach</span>`
                : `<span class="indicator green">${hoursLeft}h remaining</span>`;

            frm.set_intro(indicator, hoursLeft < 24 ? "red" : "green");
        }
    },

    request_type: function(frm) {
        // Show/hide fields based on request type
        frm.toggle_display("nominee_name", frm.doc.request_type === "Nomination");
        frm.toggle_display("nominee_contact", frm.doc.request_type === "Nomination");
    },
});
```

---

## 6. Frappe Permission Patterns

```python
# dpdp_compliance/permissions.py

def consent_log_query(user):
    """Row-level: DPO sees all; users see only their own."""
    if "DPO" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(user):
        return ""  # No filter = all records
    return f"`tabConsent Log`.`user` = '{frappe.db.escape(user)}'"


def breach_dpo_only_query(user):
    """Only DPO and System Manager can see Data Breach records."""
    roles = frappe.get_roles(user)
    if "DPO" in roles or "System Manager" in roles:
        return ""
    return "1=0"  # No records for others


# Custom Role Setup (run in setup.py)
def create_dpdp_roles():
    for role_name in ["DPO", "Data Privacy Officer", "DPDP Admin"]:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert()
```

---

## 7. Frappe DB Patterns (frappe.db)

```python
# ── Read ─────────────────────────────────────────────────────────────────────
# Single value
email = frappe.get_value("User", "admin@example.com", "email")

# Multiple fields
user = frappe.get_value("User", user_id, ["email", "full_name", "phone"], as_dict=True)

# List query with filters
records = frappe.get_all(
    "Consent Log",
    filters={"user": user_id, "status": "Granted", "docstatus": 1},
    fields=["name", "purpose", "timestamp", "expiry_date"],
    order_by="timestamp desc",
    limit=50,
)

# Raw SQL (use sparingly; always parameterize)
result = frappe.db.sql(
    """SELECT user, COUNT(*) as cnt FROM `tabConsent Log`
       WHERE status = %s AND docstatus = 1 GROUP BY user""",
    ("Granted",),
    as_dict=True,
)

# ── Write ─────────────────────────────────────────────────────────────────────
# Direct field update (no hooks fired)
frappe.db.set_value("User", user_id, "vpc_status", "Verified")

# Bulk update
frappe.db.set_value(
    "Consent Log",
    {"user": user_id, "status": "Granted"},  # filter
    {"status": "Expired"},                    # values
)

# ── Document API (hooks fired) ────────────────────────────────────────────────
doc = frappe.get_doc("Data Subject Request", dsr_id)
doc.status = "Processing"
doc.save(ignore_permissions=True)

# Insert new document
new_log = frappe.get_doc({
    "doctype": "Consent Log",
    "user": user_id,
    "purpose": purpose_id,
    "status": "Granted",
})
new_log.insert(ignore_permissions=True)
new_log.submit()

# ── Transactions ──────────────────────────────────────────────────────────────
# Frappe auto-wraps each request in a DB transaction.
# For explicit control:
frappe.db.begin()
try:
    # ... operations ...
    frappe.db.commit()
except Exception:
    frappe.db.rollback()
    raise
```

---

## 8. Frappe Cache

```python
# frappe.cache() uses Redis
# Set with TTL
frappe.cache().set_value("vpc_token_ABC123", {"user": "x@y.com"}, expires_in_sec=3600)

# Get
data = frappe.cache().get_value("vpc_token_ABC123")

# Delete
frappe.cache().delete_value("vpc_token_ABC123")

# For site-level config (no TTL needed):
frappe.db.get_single_value("DPDP Settings", "dpo_email")  # Cached by Frappe
```

---

## 9. Email & Notifications

```python
# Send email
frappe.sendmail(
    recipients=["dpo@company.com"],
    subject="Breach Alert",
    template="breach_alert",              # templates/email/breach_alert.html
    args={"breach_title": "...", "hours_remaining": 68},
    header=["Data Protection Alert", "red"],
    now=True,                             # Send immediately (not queued)
)

# Queue (default, async via worker)
frappe.sendmail(recipients=[...], subject="...", message="...", now=False)

# Realtime notification (desktop/browser push)
frappe.publish_realtime(
    event="new_breach",
    message={"title": "Breach Detected", "severity": "Critical"},
    user="dpo@company.com",  # Specific user
)

# System notification (bell icon in Frappe)
notification = frappe.get_doc({
    "doctype": "Notification Log",
    "for_user": "dpo@company.com",
    "type": "Alert",
    "subject": "DSR approaching SLA deadline",
    "email_content": "...",
    "document_type": "Data Subject Request",
    "document_name": dsr_id,
})
notification.insert(ignore_permissions=True)
```

---

## 10. Frappe Bench Operations Cheatsheet

```bash
# ── Development ───────────────────────────────────────────────────
bench start                                    # Start all services
bench --site site.local migrate                # Run pending migrations
bench --site site.local clear-cache            # Clear all caches
bench build --app dpdp_compliance              # Rebuild JS/CSS assets
bench --site site.local console                # Python REPL with Frappe context
bench --site site.local execute dpdp_compliance.setup.after_install  # Run function

# ── App Management ────────────────────────────────────────────────
bench get-app dpdp_compliance /path/or/url     # Install from path/git
bench --site site.local install-app dpdp_compliance
bench --site site.local uninstall-app dpdp_compliance
bench update --apps dpdp_compliance            # Pull updates

# ── Database ──────────────────────────────────────────────────────
bench --site site.local backup                 # Backup DB + files
bench --site site.local restore backup.sql.gz  # Restore
bench --site site.local mariadb               # Open MariaDB shell

# ── Scheduler ─────────────────────────────────────────────────────
bench enable-scheduler                          # Enable cron jobs
bench --site site.local run-patch dpdp_compliance.patches.v1.some_patch

# ── Testing ───────────────────────────────────────────────────────
bench --site site.local run-tests --app dpdp_compliance
bench --site site.local run-tests --module dpdp_compliance.tests.test_consent
```

---

## 11. Common Frappe Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `frappe.PermissionError` | Role lacks permission on DocType | Check DocType permissions; use `ignore_permissions=True` in system scripts only |
| `Document not found` | Wrong name or site | Verify with `frappe.db.exists("DocType", name)` first |
| `frappe.DuplicateEntryError` | Unique field violation | Check with `frappe.db.exists()` before insert |
| `Cannot import name X from frappe` | Wrong Frappe version API | Check Frappe v16 changelog; some APIs moved |
| Hook not firing | hooks.py not loaded | Run `bench migrate` + `bench clear-cache` |
| Scheduler not running | Worker not started | `bench start` or check `bench enable-scheduler` |
| JS not updating | Asset cache stale | `bench build --app dpdp_compliance` + hard refresh |
