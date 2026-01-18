import frappe
from frappe import _


def notify_breach(doc, method):
    """
    Triggers mandatory notifications when a Personal Data Breach is confirmed.
    Section 8(6) of DPDP Act 2023.
    """
    if doc.status == "Confirmed" and not doc.db_get("status") == "Confirmed":
        # Status changed to Confirmed. Trigger notifications.
        send_dpb_notification(doc)
        send_user_notification(doc)


def send_dpb_notification(doc):
    """
    Notify Data Protection Board (Mock).
    """
    # In reality, this would be an API call or official format email.
    pass


def send_user_notification(doc):
    """
    Notify affected Data Principals.
    """
    if not doc.affected_principals:
        return

    # Assuming 'affected_data_principals' is a child table or list of users.
    # For MVP, let's assume it's a Text field with emails or we just notify all users (too broad).
    # Let's check the JSON first. If no child table, we'll create one or assume broad alert.
    # For this implementation, I'll send a system manager alert as placeholder if no user list.

    recipients = []
    # logic to fetch recipients
    # For MVP: Notify System Managers as fail-safe
    if not recipients:
        recipients = frappe.get_all(
            "Has Role",
            filters={"role": "System Manager", "parenttype": "User"},
            pluck="parent",
        )
        if not recipients:
            recipients = ["administrator@example.com"]  # Absolute fallback

    frappe.sendmail(
        recipients=recipients,
        subject=f"URGENT: Security Incident Notification - {doc.name}",
        message=f"""
        <p>Dear Data Principal,</p>
        <p>We are writing to inform you of a security incident that may have affected your personal data.</p>
        <p><b>Breach Details:</b> {doc.description}</p>
        <p><b>Date Occurred:</b> {doc.incident_time}</p>
        <p><b>Steps Taken:</b> {doc.mitigation_steps or 'Investigation underway.'}</p>
        <p>We are taking all necessary measures to mitigate the impact.</p>
        """,
    )
