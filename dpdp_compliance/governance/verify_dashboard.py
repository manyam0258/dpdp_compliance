import frappe


def verify_dashboard():
    print(">>> Starting DPO Dashboard Verification")

    # 1. Verify Workspace Exists (via File read simulation since we can't fully sync files without bench migrate)
    # Actually, we can check if frappe can load the JSON if we reload the DocType.
    # But since we created files manually, they aren't in DB yet without 'bench migrate'.
    # For verification script, we will simulate loading the file content manually or check if file exists.

    import os

    base_path = frappe.get_app_path("dpdp_compliance", "governance")
    workspace_path = os.path.join(
        base_path, "workspace", "dpdp_governance", "dpdp_governance.json"
    )

    if os.path.exists(workspace_path):
        print(f"[PASS] Workspace File Found: {workspace_path}")
    else:
        print("[FAIL] Workspace File NOT Found")

    # 2. Verify Charts
    chart_paths = [
        ("dsr_by_status", "dashboard_chart"),
        ("consent_trends", "dashboard_chart"),
        ("active_breaches", "number_card"),
    ]

    all_passed = True
    for name, type_folder in chart_paths:
        path = os.path.join(base_path, type_folder, name, f"{name}.json")
        if os.path.exists(path):
            print(f"[PASS] {type_folder} Found: {name}")
        else:
            print(f"[FAIL] {type_folder} NOT Found: {name}")
            all_passed = False

    if all_passed:
        print(">>> Dashboard Structure Verified")
    else:
        print(">>> Dashboard Structure INCOMPLETE")
