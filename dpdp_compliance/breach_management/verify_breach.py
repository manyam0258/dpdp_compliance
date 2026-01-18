import frappe
from frappe.utils import now_datetime
from frappe.utils import now_datetime


def test_breach_notification():
    print(">>> Starting Breach Notification Verification")

    # 0. Setup Dummy Email Account to avoid OutgoingEmailError
    if not frappe.db.exists("Email Account", "DPDP Tester"):
        frappe.get_doc(
            {
                "doctype": "Email Account",
                "email_account_name": "DPDP Tester",
                "email_id": "test@example.com",
                "default_outgoing": 1,
                "enable_outgoing": 0,
                "enable_incoming": 0,
                "smtp_server": "localhost",
            }
        ).insert(ignore_permissions=True)
        # Force enable outgoing to bypass SMTP check
        frappe.db.set_value("Email Account", "DPDP Tester", "enable_outgoing", 1)
        frappe.db.set_value("Email Account", "DPDP Tester", "default_outgoing", 1)
        print("Created Dummy Email Account (Forced Enabled)")

    # 1. Create a Test Breach (Open)
    breach = frappe.get_doc(
        {
            "doctype": "Personal Data Breach",
            "title": "Test Security Incident 2026",
            "status": "Open",
            "incident_time": now_datetime(),
            "discovery_time": now_datetime(),
            "description": "Unauthorized access to testing server reported.",
            "affected_principals": 100,
        }
    ).insert(ignore_permissions=True)
    print(f"Created Breach: {breach.name} (Status: Open)")

    # 2. Confirm Breach to trigger Hook
    print("Updating status to 'Confirmed'...")
    breach.status = "Confirmed"
    breach.save(ignore_permissions=True)

    # 3. Verify Email Queue
    # We check if an email with subject containing the breach name exists in Email Queue
    email_queue = frappe.get_all(
        "Email Queue",
        filters={"message": ["like", f"%{breach.name}%"]},
        fields=["name", "status", "message", "sender"],
        order_by="creation desc",
        limit=1,
    )

    if email_queue:
        print(f"[PASS] Email Notification queued: {email_queue[0].name}")
        print(f"Subject/Body Match: {breach.name}")
    else:
        print("[FAIL] No Email Notification found in Queue.")

    print(">>> Verification Complete")
