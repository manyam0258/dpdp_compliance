import frappe
from dpdp_compliance.governance.report.ropa_report.ropa_report import execute


def verify_ropa():
    print(">>> Starting RoPA Report Verification")

    # 1. Ensure Consent Purpose Exists
    if not frappe.get_all("Consent Purpose"):
        print("Creating Dummy Consent Purpose...")
        frappe.get_doc(
            {
                "doctype": "Consent Purpose",
                "purpose_name": "Marketing Analytics",
                "description": "To analyze user behavior for better ad targeting.",
            }
        ).insert(ignore_permissions=True)

    # 2. Run Report Execute
    columns, data = execute()

    # 3. Verify Output
    print(f"Columns: {len(columns)}")
    print(f"Rows: {len(data)}")

    if data:
        print("[PASS] RoPA Data Generated:")
        print(data[0])
    else:
        print("[FAIL] No Data Generated")

    print(">>> Verification Complete")
