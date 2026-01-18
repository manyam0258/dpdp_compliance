import frappe


def test_encryption_hook():
    print(">>> Starting Encryption Hook Verification")

    secret_text = "My Secret PII 9876543210"

    # 1. Create Doc
    dsr = frappe.get_doc(
        {
            "doctype": "Data Subject Request",
            "data_principal": (
                frappe.session.user
                if frappe.session.user != "Guest"
                else "Administrator"
            ),
            "request_type": "Access",
            "description": secret_text,
            "status": "Open",
        }
    ).insert(ignore_permissions=True)

    doc_name = dsr.name
    print(f"Created DSR: {doc_name}")

    # 2. Check DB (Raw SQL) -> Should be Encrypted
    raw_desc = frappe.db.sql(
        f"SELECT description FROM `tabData Subject Request` WHERE name='{doc_name}'"
    )[0][0]
    print(f"Raw DB Value: {raw_desc}")

    if raw_desc != secret_text and raw_desc.startswith("gAAAA"):
        print("[PASS] Field is ENCRYPTED in Database.")
    else:
        print(f"[FAIL] Field is NOT Encrypted in Database. Got: {raw_desc}")

    # 3. Check ORM (get_doc) -> Should be Decrypted
    # Clear cache to force reload from DB
    frappe.clear_document_cache("Data Subject Request", doc_name)

    loaded_doc = frappe.get_doc("Data Subject Request", doc_name)
    # Manually trigger onload to see if it works
    loaded_doc.run_method("onload")

    print(f"Loaded Value: {loaded_doc.description}")

    if loaded_doc.description == secret_text:
        print("[PASS] Field is DECRYPTED on Load.")
    else:
        print(f"[FAIL] Field is NOT Decrypted on Load. Got: {loaded_doc.description}")

    print(">>> Verification Complete")
