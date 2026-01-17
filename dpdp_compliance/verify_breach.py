import frappe
from frappe.utils import now_datetime, add_to_date, get_datetime


def test_breach_flow():
    print(">>> Starting Breach Flow Verification")

    now = now_datetime()

    breach = frappe.get_doc(
        {
            "doctype": "Personal Data Breach",
            "title": "Test Breach",
            "incident_time": now,
            "discovery_time": now,
            "status": "Open",
            "nature_of_breach": "Test",
        }
    ).insert(ignore_permissions=True)

    # Check Deadline (72 hours)
    expected_deadline = add_to_date(now, hours=72)

    # Convert to string for comparison if needed, or rely on internal comparison
    # Frappe datetimes are strings usually when fetched unless converted
    # But `add_to_date` returns datetime object or string.
    # Let's trust they are comparable.

    print(f"Discovery: {breach.discovery_time}")
    print(f"Deadline:  {breach.reporting_deadline}")

    # Basic delta check
    deadline_dt = get_datetime(breach.reporting_deadline)
    discovery_dt = get_datetime(breach.discovery_time)

    diff_hours = (deadline_dt - discovery_dt).total_seconds() / 3600

    if 71.9 < diff_hours < 72.1:
        print(f"[PASS] Reporting Deadline is ~72 hours ({diff_hours})")
    else:
        print(f"[FAIL] Reporting Deadline Incorrect: {diff_hours} hours")

    print(">>> Verification Complete")
