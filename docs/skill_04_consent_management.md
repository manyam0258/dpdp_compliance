---
name: dpdp-consent-management
description: >
  Use this skill for building, configuring, or debugging the Consent Management System (CMS)
  module of the dpdp_compliance Frappe v16 app. Triggers include: consent capture, consent
  log (immutable), privacy notice versioning, consent withdrawal, granular purpose management,
  legacy data remediation, consent expiry, or any DocType/hook design for consent in the DPDP
  compliance module. Always use when "consent", "privacy notice", "purpose", "withdrawal",
  "legacy data", "consent log", or "Section 5/6 DPDP" appear in context. Read
  skill_01_frappe_fullstack_core.md first for DocType/hook patterns.
compatibility:
  frappe_version: ">=16.0"
  app: dpdp_compliance
---

# DPDP Consent Management System (CMS)

## Legal Basis: Sections 5 & 6 DPDP Act 2023
- Notice must precede or accompany every consent request (§5)
- Consent must be free, specific, informed, unconditional, unambiguous (§6)
- Withdrawal must be as easy as giving consent (§6(4))
- Legacy data requires fresh notice "as soon as reasonably practicable" (§5(2))

---

## DocType Schemas

### Consent Purpose (Master)
```json
{
  "name": "Consent Purpose",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {"fieldname":"purpose_name","fieldtype":"Data","reqd":1,"unique":1},
    {"fieldname":"description","fieldtype":"Small Text"},
    {"fieldname":"is_mandatory","fieldtype":"Check","default":0,
     "description":"If 1, user cannot opt out. Used for core service purposes."},
    {"fieldname":"validity_days","fieldtype":"Int","default":365},
    {"fieldname":"legal_basis","fieldtype":"Select",
     "options":"Consent\nLegitimate Interest\nLegal Obligation\nVital Interest"},
    {"fieldname":"is_active","fieldtype":"Check","default":1}
  ]
}
```

### Privacy Notice (Master)
```json
{
  "name": "Privacy Notice",
  "is_submittable": 1,
  "track_changes": 1,
  "fields": [
    {"fieldname":"notice_id","fieldtype":"Data","reqd":1,"unique":1},
    {"fieldname":"version","fieldtype":"Data","reqd":1},
    {"fieldname":"language","fieldtype":"Select",
     "options":"English\nHindi\nTamil\nTelugu\nKannada\nMarathi\nBengali\nGujarati","reqd":1},
    {"fieldname":"content_html","fieldtype":"Text Editor","reqd":1},
    {"fieldname":"linked_purposes","fieldtype":"Table",
     "options":"Privacy Notice Consent Purpose"},
    {"fieldname":"effective_date","fieldtype":"Date","reqd":1},
    {"fieldname":"is_active","fieldtype":"Check","default":0},
    {"fieldname":"supersedes","fieldtype":"Link","options":"Privacy Notice"}
  ]
}
```

### Consent Log (Transaction — IMMUTABLE)
```json
{
  "name": "Consent Log",
  "is_submittable": 1,
  "track_changes": 1,
  "allow_import": 0,
  "fields": [
    {"fieldname":"user","fieldtype":"Link","options":"User","reqd":1,"in_list_view":1},
    {"fieldname":"purpose","fieldtype":"Link","options":"Consent Purpose","reqd":1,"in_list_view":1},
    {"fieldname":"status","fieldtype":"Select",
     "options":"Granted\nDenied\nWithdrawn\nExpired","reqd":1,"in_list_view":1},
    {"fieldname":"timestamp","fieldtype":"Datetime","reqd":1,"read_only":1},
    {"fieldname":"ip_address","fieldtype":"Data","read_only":1},
    {"fieldname":"user_agent","fieldtype":"Small Text","read_only":1},
    {"fieldname":"notice_version","fieldtype":"Link","options":"Privacy Notice"},
    {"fieldname":"channel","fieldtype":"Select",
     "options":"Web\nMobile App\nAPI\nSystem\nOffline"},
    {"fieldname":"is_minor","fieldtype":"Check","default":0,"read_only":1},
    {"fieldname":"parent_user","fieldtype":"Link","options":"User"},
    {"fieldname":"verification_token","fieldtype":"Data"},
    {"fieldname":"expiry_date","fieldtype":"Date"}
  ],
  "permissions": [
    {"role":"System Manager","read":1,"create":1,"submit":1,"write":0,"delete":0},
    {"role":"DPO","read":1,"export":1,"write":0,"delete":0},
    {"role":"Guest","read":0}
  ]
}
```

---

## Core Engine (`consent.py`)

```python
# dpdp_compliance/consent.py
import frappe
from frappe.utils import now_datetime, add_days, getdate, today


def create_consent_log(
    user: str,
    purpose_id: str,
    status: str,
    notice_version_id: str | None,
    channel: str = "Web",
    is_minor: bool = False,
    parent_user: str | None = None,
    token: str | None = None,
) -> str:
    """
    Creates and SUBMITS an immutable Consent Log entry.
    This is the only sanctioned way to record consent state changes.
    Returns the Consent Log document name.
    """
    purpose = frappe.get_cached_doc("Consent Purpose", purpose_id)
    expiry_date = None
    if status == "Granted":
        expiry_date = add_days(today(), purpose.validity_days or 365)

    log = frappe.get_doc({
        "doctype": "Consent Log",
        "user": user,
        "purpose": purpose_id,
        "status": status,
        "timestamp": now_datetime(),
        "ip_address": getattr(frappe.local, "request_ip", None),
        "user_agent": (
            frappe.get_request_header("User-Agent") if frappe.local.request else None
        ),
        "notice_version": notice_version_id,
        "channel": channel,
        "is_minor": 1 if is_minor else 0,
        "parent_user": parent_user,
        "verification_token": token,
        "expiry_date": expiry_date,
    })
    log.insert(ignore_permissions=True)
    log.submit()
    return log.name


def get_active_consent(user: str, purpose_id: str) -> bool:
    """
    Returns True if the user has a current, non-expired Granted consent
    for the given purpose. This is the consent gate — call before any processing.
    """
    logs = frappe.get_all(
        "Consent Log",
        filters={"user": user, "purpose": purpose_id, "docstatus": 1},
        fields=["name", "status", "expiry_date"],
        order_by="timestamp desc",
        limit=1,
    )
    if not logs:
        return False

    latest = logs[0]
    if latest.status != "Granted":
        return False

    if latest.expiry_date and getdate(latest.expiry_date) < getdate(today()):
        # Auto-mark as expired
        frappe.db.set_value("Consent Log", latest.name, "status", "Expired")
        return False

    return True


def process_signup_consent(doc, method):
    """
    Hook: User.after_insert
    Processes consent payload from frappe.flags.dpdp_consent
    """
    consent_data: list[dict] = frappe.flags.get("dpdp_consent") or []
    is_minor: bool = getattr(doc, "is_minor", False)
    parent_user: str | None = getattr(doc, "guardian_email", None)
    token: str | None = frappe.flags.get("parental_consent_token")

    if is_minor and not token:
        frappe.throw(
            "Verifiable Parental Consent (VPC) is mandatory for users under 18.",
            title="Parental Consent Required",
        )

    # Mandatory purposes must always be recorded even if no payload
    mandatory_purposes = frappe.get_all(
        "Consent Purpose",
        filters={"is_mandatory": 1, "is_active": 1},
        fields=["name"],
    )

    active_notice = frappe.get_all(
        "Privacy Notice",
        filters={"is_active": 1, "language": "English", "docstatus": 1},
        fields=["name"],
        limit=1,
    )
    notice_id = active_notice[0].name if active_notice else None

    # Record mandatory purposes as Granted regardless
    provided_ids = {item["purpose_id"] for item in consent_data}
    for p in mandatory_purposes:
        if p.name not in provided_ids:
            create_consent_log(
                user=doc.name,
                purpose_id=p.name,
                status="Granted",
                notice_version_id=notice_id,
                channel="Web",
                is_minor=is_minor,
                parent_user=parent_user,
                token=token if is_minor else None,
            )

    # Record optional purposes from payload
    for item in consent_data:
        create_consent_log(
            user=doc.name,
            purpose_id=item["purpose_id"],
            status=item.get("status", "Granted"),
            notice_version_id=notice_id,
            channel="Web",
            is_minor=is_minor,
            parent_user=parent_user,
            token=token if is_minor else None,
        )


def expire_stale_consents():
    """Scheduled daily: auto-expire consents past their expiry_date."""
    expired = frappe.get_all(
        "Consent Log",
        filters={
            "status": "Granted",
            "docstatus": 1,
            "expiry_date": ("<", today()),
        },
        fields=["name"],
        limit=5000,
    )
    for log in expired:
        frappe.db.set_value("Consent Log", log.name, "status", "Expired")

    if expired:
        frappe.log_error(f"Auto-expired {len(expired)} consent logs.", "Consent Expiry")


def send_legacy_consent_reminders():
    """Scheduled weekly: email users with no consent record."""
    commencement = frappe.db.get_single_value("DPDP Settings", "act_commencement_date")
    if not commencement:
        return

    all_users = frappe.get_all(
        "User",
        filters={"enabled": 1, "creation": ("<", commencement)},
        fields=["name", "email", "full_name"],
    )

    for user in all_users:
        has_any_consent = frappe.db.count(
            "Consent Log", {"user": user.name, "docstatus": 1}
        )
        if not has_any_consent:
            frappe.sendmail(
                recipients=[user.email],
                subject="Action Required: Update Your Privacy Preferences",
                template="legacy_consent_reminder",
                args={"user_name": user.full_name},
                now=False,  # Queue it
            )
```

---

## API Endpoints

```python
# In dpdp_compliance/api.py

@frappe.whitelist()
def get_my_consents() -> list[dict]:
    """Returns all consent logs for the logged-in user."""
    user = frappe.session.user
    logs = frappe.get_all(
        "Consent Log",
        filters={"user": user, "docstatus": 1},
        fields=["name", "purpose", "status", "timestamp", "expiry_date", "channel"],
        order_by="timestamp desc",
    )
    # Enrich with purpose names
    for log in logs:
        log["purpose_name"] = frappe.get_cached_value(
            "Consent Purpose", log.purpose, "purpose_name"
        )
        log["is_mandatory"] = frappe.get_cached_value(
            "Consent Purpose", log.purpose, "is_mandatory"
        )
    return logs


@frappe.whitelist()
def withdraw_consent(purpose_id: str) -> dict:
    """Withdraw consent for a specific purpose. Ease = as easy as giving."""
    user = frappe.session.user

    if not get_active_consent(user, purpose_id):
        frappe.throw(f"No active consent found for: {purpose_id}")

    purpose = frappe.get_cached_doc("Consent Purpose", purpose_id)
    if purpose.is_mandatory:
        frappe.throw(
            "This consent is required for the core service and cannot be withdrawn. "
            "You may close your account to stop all processing."
        )

    log_name = create_consent_log(
        user=user,
        purpose_id=purpose_id,
        status="Withdrawn",
        notice_version_id=None,
        channel="Web",
    )
    _apply_withdrawal_effects(user, purpose_id)
    return {"success": True, "log": log_name, "message": "Consent withdrawn."}


def _apply_withdrawal_effects(user: str, purpose_id: str):
    """Side effects when consent is withdrawn."""
    purpose_name = frappe.get_cached_value(
        "Consent Purpose", purpose_id, "purpose_name"
    ) or ""

    if "marketing" in purpose_name.lower():
        # Unsubscribe from email groups
        user_email = frappe.get_value("User", user, "email")
        frappe.db.set_value(
            "Email Group Member",
            {"email": user_email},
            "unsubscribed",
            1,
        )

    # Publish realtime event for any active sessions
    frappe.publish_realtime(
        "consent_withdrawn",
        {"user": user, "purpose": purpose_id},
        user=user,
    )
```

---

## Validations

```python
# dpdp_compliance/validations.py

def validate_consent_log(doc, method):
    """Prevent modification of submitted consent logs."""
    if not doc.is_new():
        frappe.throw("Consent Logs are immutable. Cannot modify after creation.")


def block_consent_log_deletion(doc, method):
    frappe.throw(
        "Deletion of Consent Logs is not permitted. "
        "They are legal evidence of consent.",
        frappe.PermissionError,
    )


def validate_privacy_notice(doc, method):
    """Ensure only one active notice per language."""
    if doc.is_active and doc.docstatus == 1:
        existing = frappe.get_all(
            "Privacy Notice",
            filters={
                "is_active": 1,
                "language": doc.language,
                "name": ("!=", doc.name),
                "docstatus": 1,
            },
            limit=1,
        )
        if existing:
            frappe.throw(
                f"Active Privacy Notice for {doc.language} already exists: "
                f"{existing[0].name}. Deactivate it first."
            )
```

---

## Consent Capture — Frontend JS (for Frappe web pages)

```javascript
// public/js/consent_modal.js — Injected via hooks.py app_include_js
frappe.ready(function () {
  if (!window.location.pathname.includes("/signup")) return;

  frappe.call({
    method: "dpdp_compliance.api.get_active_notice",
    args: { language: frappe.boot?.lang || "English" },
    callback: function (r) {
      if (!r.message) return;
      _renderConsentModal(r.message);
    },
  });

  function _renderConsentModal(notice) {
    const purposes = notice.purposes
      .map(
        (p) => `
        <div class="form-check mb-2">
          <input class="form-check-input dpdp-consent-cb" type="checkbox"
                 id="p_${p.name}" data-purpose="${p.name}"
                 ${p.is_mandatory ? "checked disabled" : ""}>
          <label class="form-check-label" for="p_${p.name}">
            <strong>${p.purpose_name}</strong>
            ${p.is_mandatory ? '<span class="badge bg-secondary">Required</span>' : ""}
            <div class="text-muted small">${p.description || ""}</div>
          </label>
        </div>`
      )
      .join("");

    const dialog = new frappe.ui.Dialog({
      title: "Your Privacy Preferences",
      fields: [
        {
          fieldtype: "HTML",
          options: `
            <div class="dpdp-notice-content mb-3" style="max-height:200px;overflow-y:auto">
              ${notice.content_html}
            </div>
            <hr/>
            <h6>What you are agreeing to:</h6>
            ${purposes}
          `,
        },
      ],
      primary_action_label: "I Agree & Continue",
      primary_action: function () {
        const consents = [];
        document.querySelectorAll(".dpdp-consent-cb").forEach((cb) => {
          consents.push({
            purpose_id: cb.dataset.purpose,
            status: cb.checked ? "Granted" : "Denied",
          });
        });
        // Store for backend hook to pick up
        frappe.flags.dpdp_consent = consents;
        dialog.hide();
        // Allow form submission to proceed
        document.querySelector("[data-action='signup']")?.click();
      },
    });
    dialog.show();
    // Intercept the original signup submit
    document
      .querySelector("[data-action='signup']")
      ?.addEventListener("click", function (e) {
        if (!frappe.flags.dpdp_consent) {
          e.preventDefault();
          e.stopPropagation();
          dialog.show();
        }
      }, { once: false });
  }
});
```

---

## Go-Live Checklist

- [ ] At least one `Consent Purpose` with `is_mandatory = 1` (Core Service)
- [ ] Active `Privacy Notice` submitted in English + Hindi minimum
- [ ] `Consent Log` permissions: no Write/Delete for any role after Submit
- [ ] `after_insert` hook on `User` registered in `hooks.py`
- [ ] Consent modal JS loaded on signup page
- [ ] Daily scheduler for `expire_stale_consents` running
- [ ] Weekly scheduler for `send_legacy_consent_reminders` running
- [ ] Legacy users (pre-commencement) identified and remediation email queued
- [ ] `validate_privacy_notice` enforces one active notice per language
