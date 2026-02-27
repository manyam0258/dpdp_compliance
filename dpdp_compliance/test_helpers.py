# dpdp_compliance/test_helpers.py
"""Test helpers for DPDP Compliance — dev-mode only utilities.

Used by both unit tests and Playwright E2E tests for OTP retrieval.
"""

import frappe


@frappe.whitelist()
def get_test_otp(dsr_id: str) -> str:
    """TEST-ONLY: Retrieve OTP from Redis cache for automated testing.

    Only available in developer_mode. Must be disabled in production.
    """
    if not frappe.conf.get("developer_mode"):
        frappe.throw("This endpoint is only available in developer mode.")

    otp = frappe.cache.get_value(f"dpdp_dsr_otp:{dsr_id}")
    if not otp:
        frappe.throw(f"No OTP found for DSR {dsr_id}")
    return otp


def make_test_user(email=None):
    """Create a test user for DPDP tests. Returns the User doc."""
    email = email or f"test-dpdp-{frappe.generate_hash()[:6]}@example.com"

    if frappe.db.exists("User", email):
        return frappe.get_doc("User", email)

    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": "Test",
            "last_name": "DPDPUser",
            "user_type": "Website User",
            "send_welcome_email": 0,
        }
    )
    user.insert(ignore_permissions=True)
    return user


def make_test_purpose(name_suffix=None, is_mandatory=0, validity_days=365):
    """Create and submit a test Consent Purpose. Returns the doc."""
    suffix = name_suffix or frappe.generate_hash()[:6]
    purpose = frappe.get_doc(
        {
            "doctype": "Consent Purpose",
            "purpose_name": f"Test Purpose {suffix}",
            "description": f"Test consent purpose {suffix}",
            "is_mandatory": is_mandatory,
            "is_active": 1,
            "validity_days": validity_days,
            "lawful_basis": "Consent",
        }
    )
    purpose.insert(ignore_permissions=True)
    purpose.submit()
    return purpose


def make_test_notice(purposes=None, version="1.0"):
    """Create and submit a test Privacy Notice. Returns the doc."""
    notice = frappe.get_doc(
        {
            "doctype": "Privacy Notice",
            "version": version,
            "effective_date": frappe.utils.today(),
            "is_active": 1,
            "language": "en",
            "content_html": "<p>Test privacy notice content.</p>",
            "purposes": [{"consent_purpose": p.name} for p in (purposes or [])],
        }
    )
    notice.insert(ignore_permissions=True)
    notice.submit()
    return notice


def cleanup_test_data(*docs):
    """Delete test documents in reverse order, ignoring errors."""
    for doc in reversed(docs):
        try:
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(
                doc.doctype, doc.name, force=True, ignore_permissions=True
            )
        except Exception:
            pass
    frappe.db.commit()
