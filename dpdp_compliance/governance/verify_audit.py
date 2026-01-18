import frappe
import time


def verify_audit_trail():
    print(">>> Starting Audit Trail Verification")

    # 1. Create or Get Consent Purpose with Track Changes
    # Ensure Track Changes is enabled in JSON first (Did this in Phase 3?)
    # Wait, I only enabled it on DSR, Breach, and Consent Artifact.
    # I should also enable it on 'Consent Purpose' for RoPA auditing.

    if not frappe.db.get_value("DocType", "Consent Purpose", "track_changes"):
        print("[FAIL] Track Changes NOT enabled on Consent Purpose")
        return

    doc = frappe.get_doc(
        {
            "doctype": "Consent Purpose",
            "purpose_name": "Audit Test Purpose",
            "description": "Initial Description",
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()

    # 2. Modify Document
    doc.description = "Updated Description for Audit"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # 3. Check for Version Log
    version = frappe.get_all(
        "Version", filters={"docname": doc.name, "ref_doctype": "Consent Purpose"}
    )

    if version:
        print(f"[PASS] Version Log Found: {version[0].name}")
    else:
        print("[FAIL] No Version Log found")

    print(">>> Verification Complete")
