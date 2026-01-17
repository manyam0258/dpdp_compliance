import frappe
from frappe.utils import getdate, add_days


def test_rights_flow():
    print(">>> Starting Rights Flow Verification")

    # Setup Data Principal
    if not frappe.db.exists("User", "test_rights@example.com"):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": "test_rights@example.com",
                "first_name": "Rights",
                "last_name": "Tester",
            }
        ).insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", "test_rights@example.com")

    # 1. Test DSR SLA
    dsr = frappe.get_doc(
        {
            "doctype": "Data Subject Request",
            "data_principal": user.name,
            "request_type": "Access",
            "description": "I want my data",
        }
    ).insert(ignore_permissions=True)

    expected_dsr_sla = add_days(getdate(), 30)
    if dsr.sla_deadline == expected_dsr_sla:
        print(f"[PASS] DSR SLA Deadline Correct: {dsr.sla_deadline}")
    else:
        print(
            f"[FAIL] DSR SLA Mismatch. Expected {expected_dsr_sla}, Got {dsr.sla_deadline}"
        )

    # 2. Test Grievance SLA
    ticket = frappe.get_doc(
        {
            "doctype": "Grievance Ticket",
            "data_principal": user.name,
            "category": "Processing Issue",
            "description": "Unfair processing",
        }
    ).insert(ignore_permissions=True)

    expected_grv_sla = add_days(getdate(), 90)
    if ticket.resolution_deadline == expected_grv_sla:
        print(
            f"[PASS] Grievance Resolution Deadline Correct: {ticket.resolution_deadline}"
        )
    else:
        print(
            f"[FAIL] Grievance SLA Mismatch. Expected {expected_grv_sla}, Got {ticket.resolution_deadline}"
        )

    print(">>> Verification Complete")
