import frappe
from dpdp_compliance.api import withdraw_consent, create_dsr, get_active_notice


def test_portal_flow():
    print(">>> Starting Portal API Verification")

    # 1. Simulate Login
    if not frappe.db.exists("User", "test_user_portal@example.com"):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": "test_user_portal@example.com",
                "first_name": "Portal",
                "last_name": "Tester",
            }
        ).insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", "test_user_portal@example.com")

    frappe.set_user(user.name)

    # 2. Test Get Notice
    notice = get_active_notice("English")
    if notice and notice.get("version"):
        print(f"[PASS] Active Notice Fetched: {notice.get('name')}")
    else:
        print("[FAIL] Active Notice Not Found (Ensure one is active)")

    # 3. Create Dummy Consent for Withdrawal
    # Ensure privacy notice ref is valid
    pn_ref = notice.get("name") if notice else "PN-VERIFY-001"
    if not frappe.db.exists("Privacy Notice", pn_ref):
        # Create it if it doesn't exist to prevent error
        frappe.get_doc(
            {
                "doctype": "Privacy Notice",
                "notice_id": pn_ref,
                "version": "1.0",
                "language": "English",
                "is_active": 1,
                "content_html": "Dummy content",
                "linked_purposes": [],
            }
        ).insert(ignore_permissions=True)

    artifact = frappe.get_doc(
        {
            "doctype": "Consent Artifact",
            "data_principal": user.name,
            "privacy_notice_ref": pn_ref,
            "consent_timestamp": frappe.utils.now(),
            "status": "Active",
        }
    ).insert(ignore_permissions=True)

    # 4. Test Withdraw API
    try:
        res = withdraw_consent(artifact.name)
        frappe.db.commit()
        refetched = frappe.get_doc("Consent Artifact", artifact.name)
        if refetched.status == "Withdrawn":
            print(f"[PASS] Consent Withdrawal API Success: {res.get('message')}")
        else:
            print(f"[FAIL] Consent Status not updated. Got: {refetched.status}")
    except Exception as e:
        print(f"[FAIL] Withdrawal API Error: {str(e)}")

    # 5. Test DSR API
    try:
        res_dsr = create_dsr("Erasure", "Delete me via Portal")
        dsr_name = res_dsr.get("name")
        if frappe.db.exists("Data Subject Request", dsr_name):
            print(f"[PASS] DSR Creation API Success: {dsr_name}")
        else:
            print("[FAIL] DSR Document not created")
    except Exception as e:
        print(f"[FAIL] DSR API Error: {str(e)}")

    print(">>> Verification Complete")
