# dpdp_compliance/breach.py
"""Breach Response Engine — 72-hour deadline tracking, DPB notification, IRT alerts.

Implements DPDP Sec 8(6): Mandatory breach reporting within 72 hours.
"""

import frappe
from frappe.utils import (
    now_datetime,
    add_to_date,
    time_diff_in_hours,
    get_datetime,
)


BREACH_DEADLINE_HOURS = 72


def on_breach_insert(doc, method):
    """Hook: Data Breach.after_insert — set 72h deadline and alert IRT."""
    import secrets

    # Auto-generate breach ID
    doc.breach_id = (
        f"BR-{now_datetime().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    )

    # Set 72-hour reporting deadline from detection_time
    detection = get_datetime(doc.detection_time)
    doc.reporting_deadline = add_to_date(detection, hours=BREACH_DEADLINE_HOURS)
    doc.hours_remaining = BREACH_DEADLINE_HOURS

    doc.save(ignore_permissions=True)

    # Alert IRT immediately
    _send_irt_alert(doc)


def _send_irt_alert(breach_doc):
    """Send immediate email alert to Incident Response Team."""
    irt_emails_str = frappe.db.get_single_value("DPDP Settings", "irt_emails")
    if not irt_emails_str:
        frappe.log_error(
            "No IRT emails configured in DPDP Settings", "Breach Alert Failed"
        )
        return

    irt_emails = [e.strip() for e in irt_emails_str.split(",") if e.strip()]

    try:
        frappe.sendmail(
            recipients=irt_emails,
            subject=f"🚨 DATA BREACH DETECTED — {breach_doc.breach_title} [{breach_doc.severity}]",
            template="breach_irt_alert",
            args={
                "breach_id": breach_doc.breach_id,
                "breach_title": breach_doc.breach_title,
                "severity": breach_doc.severity,
                "detection_time": str(breach_doc.detection_time),
                "reporting_deadline": str(breach_doc.reporting_deadline),
                "nature_of_breach": breach_doc.nature_of_breach,
                "affected_users_count": breach_doc.affected_users_count or "Unknown",
            },
        )
    except Exception:
        frappe.log_error(f"Failed to send IRT alert for breach {breach_doc.name}")


def calculate_breach_hours():
    """Scheduled hourly: update hours_remaining for active breaches.

    Sends escalation alerts at 48h, 24h, and 6h marks.
    """
    active_breaches = frappe.get_all(
        "Data Breach",
        filters={"status": ["not in", ["Reported to DPB", "Closed"]]},
        fields=[
            "name",
            "breach_id",
            "breach_title",
            "reporting_deadline",
            "severity",
            "hours_remaining",
        ],
    )

    for breach in active_breaches:
        if breach.reporting_deadline:
            hours = time_diff_in_hours(
                get_datetime(breach.reporting_deadline),
                now_datetime(),
            )
            previous_hours = breach.hours_remaining or BREACH_DEADLINE_HOURS

            frappe.db.set_value(
                "Data Breach",
                breach.name,
                "hours_remaining",
                max(0, round(hours, 1)),
                update_modified=False,
            )

            # Escalation alerts at thresholds
            for threshold in [48, 24, 6]:
                if previous_hours > threshold >= hours:
                    _send_escalation_alert(breach, threshold)

    if active_breaches:
        frappe.db.commit()


def _send_escalation_alert(breach, hours_threshold):
    """Send escalation emails at critical time thresholds."""
    dpo_email = frappe.db.get_single_value("DPDP Settings", "dpo_email")
    if not dpo_email:
        return

    try:
        frappe.sendmail(
            recipients=[dpo_email],
            subject=f"⏰ BREACH ESCALATION — {hours_threshold}h remaining — {breach.breach_title}",
            message=f"""
            <h3>Breach Deadline Escalation</h3>
            <p><strong>Breach:</strong> {breach.breach_id} — {breach.breach_title}</p>
            <p><strong>Severity:</strong> {breach.severity}</p>
            <p><strong>Hours Remaining:</strong> {hours_threshold}h</p>
            <p><strong>Deadline:</strong> {breach.reporting_deadline}</p>
            <p>Immediate action required to file DPB report within the 72-hour statutory window.</p>
            """,
        )
    except Exception:
        frappe.log_error(f"Failed to send escalation alert for {breach.name}")
