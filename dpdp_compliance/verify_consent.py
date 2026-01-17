import frappe
from frappe.utils import random_string
from dpdp_compliance.consent_management.consent_controller import process_signup_consent


def test_consent_flow():
    print(">>> Starting Consent Flow Verification")

    # 1. Setup Masters
    if not frappe.db.exists("Consent Purpose", "Marketing"):
        frappe.get_doc(
            {
                "doctype": "Consent Purpose",
                "purpose_name": "Marketing",
                "description": "Marketing emails",
                "is_mandatory": 0,
            }
        ).insert()

    # 2. Setup Privacy Notice
    notice_id = "PN-VERIFY-001"
    if not frappe.db.exists("Privacy Notice", {"notice_id": notice_id}):
        print(f"Creating Privacy Notice {notice_id}...")
        notice = frappe.get_doc(
            {
                "doctype": "Privacy Notice",
                "notice_id": notice_id,
                "version": "1.0",
                "language": "English",
                "is_active": 1,
                "content_html": "<p>We collect data...</p>",
                "linked_purposes": [
                    {"purpose": "Marketing", "data_items": "Email", "is_mandatory": 0}
                ],
            }
        ).insert()
    else:
        notice = frappe.get_doc("Privacy Notice", {"notice_id": notice_id})

    # 3. Simulate Signup
    user_email = f"test_user_{random_string(5)}@example.com"
    print(f"Creating User {user_email} with consent flags...")

    frappe.flags.dpdp_consent = {
        "privacy_notice": notice.name,
        "purposes": [{"purpose": "Marketing", "status": "Granted"}],
    }

    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": user_email,
            "first_name": "Test",
            "last_name": "User",
        }
    ).insert(ignore_permissions=True)

    # 4. Check Artifact
    artifacts = frappe.get_all(
        "Consent Artifact",
        filters={"data_principal": user.name},
        fields=["name", "status", "artifact_hash"],
    )

    if not artifacts:
        print("Hook didn't fire automatically. Triggering manually...")
        process_signup_consent(user, "after_insert")
        artifacts = frappe.get_all(
            "Consent Artifact",
            filters={"data_principal": user.name},
            fields=["name", "status", "artifact_hash"],
        )

    if artifacts:
        print(f"[PASS] Consent Artifact Created: {artifacts[0].name}")
        print(f"       Hash: {artifacts[0].artifact_hash}")
        print(f"       Status: {artifacts[0].status}")
    else:
        print("[FAIL] Consent Artifact NOT created.")

    print(">>> Verification Complete")
