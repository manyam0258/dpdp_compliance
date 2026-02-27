# dpdp_compliance/consent.py
"""Consent Management Engine — core functions for DPDP Sec 5 & 6 compliance."""

import frappe
from frappe.utils import now_datetime, add_days, today, getdate


def create_consent_log(
    user: str,
    purpose_id: str,
    status: str,
    notice_version_id: str | None = None,
    channel: str = "Web",
    is_minor: bool = False,
    parent_user: str | None = None,
    token: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Create and auto-submit an immutable consent log entry.

    Returns:
        str: Name of the created Consent Log document.
    """
    # Calculate expiry based on purpose validity_days
    expiry_date = None
    validity = frappe.db.get_value("Consent Purpose", purpose_id, "validity_days")
    if validity and status == "Granted":
        expiry_date = add_days(today(), int(validity))

    log = frappe.get_doc(
        {
            "doctype": "Consent Log",
            "user": user,
            "purpose": purpose_id,
            "status": status,
            "timestamp": now_datetime(),
            "expiry_date": expiry_date,
            "notice_version": notice_version_id,
            "channel": channel,
            "ip_address": ip_address
            or (
                getattr(frappe.local, "request", None).remote_addr
                if getattr(frappe.local, "request", None)
                else None
            ),
            "user_agent": user_agent
            or (
                getattr(frappe.local, "request", None).headers.get("User-Agent", "")[
                    :500
                ]
                if getattr(frappe.local, "request", None)
                else None
            ),
            "is_minor": 1 if is_minor else 0,
            "parent_user": parent_user,
            "verification_token": token,
        }
    )
    log.insert(ignore_permissions=True)
    log.submit()

    return log.name


def get_active_consent(user: str, purpose_id: str) -> bool:
    """Check if user has an active (non-expired, non-withdrawn) consent for a purpose.

    This is the consent gate — call before any data processing.
    """
    latest = frappe.db.sql(
        """
        SELECT status, expiry_date
        FROM `tabConsent Log`
        WHERE user = %s AND purpose = %s AND docstatus = 1
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (user, purpose_id),
        as_dict=True,
    )

    if not latest:
        return False

    log = latest[0]

    # Check if withdrawn or denied
    if log.status in ("Withdrawn", "Denied"):
        return False

    # Check if expired
    if log.status == "Granted" and log.expiry_date:
        if getdate(log.expiry_date) < getdate(today()):
            return False

    return log.status == "Granted"


def process_signup_consent(doc, method):
    """Hook: User.after_insert — create consent logs for signup consents.

    Called when consent_modal_enabled is True in DPDP Settings.
    The consent choices are passed via doc.flags.dpdp_consents.
    """
    if not frappe.db.get_single_value("DPDP Settings", "consent_modal_enabled"):
        return

    consents = getattr(doc.flags, "dpdp_consents", None)
    if not consents:
        return

    # Get the active privacy notice
    notice = frappe.db.get_value(
        "Privacy Notice",
        {"is_active": 1, "docstatus": 1},
        "name",
    )

    for consent in consents:
        create_consent_log(
            user=doc.name,
            purpose_id=consent.get("purpose_id"),
            status="Granted" if consent.get("accepted") else "Denied",
            notice_version_id=notice,
            channel="Web",
        )


def expire_stale_consents():
    """Scheduled daily: mark expired consents and create Expired log entries."""
    expired_logs = frappe.db.sql(
        """
        SELECT cl.user, cl.purpose, cl.name
        FROM `tabConsent Log` cl
        INNER JOIN (
            SELECT user, purpose, MAX(timestamp) as max_ts
            FROM `tabConsent Log`
            WHERE docstatus = 1
            GROUP BY user, purpose
        ) latest ON cl.user = latest.user
            AND cl.purpose = latest.purpose
            AND cl.timestamp = latest.max_ts
        WHERE cl.status = 'Granted'
          AND cl.expiry_date IS NOT NULL
          AND cl.expiry_date < %s
          AND cl.docstatus = 1
        """,
        (today(),),
        as_dict=True,
    )

    for log in expired_logs:
        create_consent_log(
            user=log.user,
            purpose_id=log.purpose,
            status="Expired",
            channel="System",
        )

    if expired_logs:
        frappe.logger().info(f"DPDP: Expired {len(expired_logs)} stale consents")


def send_legacy_consent_reminders():
    """Scheduled weekly: send consent reminders for users without consent records.

    DPDP Sec 5(2): Legacy data requires fresh notice 'as soon as reasonably practicable'.
    """
    # Get users who have no consent logs at all
    users_without_consent = frappe.db.sql(
        """
        SELECT u.name, u.email, u.full_name
        FROM `tabUser` u
        WHERE u.enabled = 1
          AND u.name != 'Guest'
          AND u.name != 'Administrator'
          AND u.user_type = 'Website User'
          AND u.name NOT IN (
              SELECT DISTINCT user FROM `tabConsent Log` WHERE docstatus = 1
          )
        LIMIT 100
        """,
        as_dict=True,
    )

    if not users_without_consent:
        return

    dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")
    portal_url = frappe.utils.get_url()

    for user in users_without_consent:
        try:
            frappe.sendmail(
                recipients=[user.email],
                subject="Action Required: Review Your Privacy Preferences",
                template="legacy_consent_reminder",
                args={
                    "full_name": user.full_name or user.email,
                    "portal_url": f"{portal_url}/dpdp-portal/privacy-choices",
                    "dpo_email": dpo_email,
                },
            )
        except Exception:
            frappe.log_error(f"Failed to send consent reminder to {user.email}")
