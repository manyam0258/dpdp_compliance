import frappe
from dpdp_compliance.rights_management.utils import process_erasure_queue


def test_erasure_flow():
    print(">>> Starting Erasure Job Verification")

    email = "delete_me@test.com"
    # Cleanup
    frappe.db.delete("User", {"email": email})
    frappe.db.delete("Data Subject Request", {"data_principal": email})
    frappe.db.commit()

    # 1. Create a Test User
    if not frappe.db.exists("User", email):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "Delete",
                "last_name": "Me",
                "send_welcome_email": 0,
            }
        ).insert(ignore_permissions=True)
        print(f"Created User: {email}")
    else:
        user = frappe.get_doc("User", email)

    # 2. Create DSR with Pending Erasure status
    dsr = frappe.get_doc(
        {
            "doctype": "Data Subject Request",
            "data_principal": email,
            "request_type": "Erasure",
            "status": "Pending Erasure",
            "description": "Please delete me!",
        }
    ).insert(ignore_permissions=True)
    print(f"Created DSR: {dsr.name}")

    # 3. Running Job
    print("Running process_erasure_queue()...")
    process_erasure_queue()

    # 4. Verification
    # Check DSR Status
    dsr.reload()
    if dsr.status == "Resolved":
        print("[PASS] DSR Status updated to Resolved.")
    else:
        print(f"[FAIL] DSR Status is {dsr.status}.")

    # Check User Anonymization
    # Note: Original email `delete_me@test.com` should fail to load if renamed,
    # OR if just details changed, we check fields.
    # My logic attempts rename if "@" in name.

    if not frappe.db.exists("User", email):
        print("[PASS] User record with original email no longer exists (Renamed).")
    else:
        # If rename failed or not triggered, check fields
        chk_user = frappe.get_doc("User", email)
        if (
            chk_user.email.endswith("@deleted.local")
            and chk_user.first_name == "Anonymous"
        ):
            print("[PASS] User fields Anonymized.")
        else:
            print(
                f"[FAIL] User fields NOT Anonymized: {chk_user.email}, {chk_user.first_name}"
            )

    print(">>> Verification Complete")
