import frappe
from frappe.utils import now_datetime


def process_signup_consent(doc, method):
    """
    Hook for User.after_insert.
    Checks frappe.flags.dpdp_consent for consent data passed from the frontend.
    Expected format of frappe.flags.dpdp_consent:
    {
            "privacy_notice": "PN-ID",
            "purposes": [
                    {"purpose": "Marketing", "status": "Granted"},
                    {"purpose": "Service", "status": "Granted"}
            ]
    }
    """
    consent_data = frappe.flags.dpdp_consent

    if not consent_data:
        return

    # In a real scenario, we might want to validate the structure strictly

    try:
        artifact = frappe.get_doc(
            {
                "doctype": "Consent Artifact",
                "data_principal": doc.name,
                "privacy_notice_ref": consent_data.get("privacy_notice"),
                "consent_timestamp": now_datetime(),
                "ip_address": frappe.local.request_ip,
                "user_agent": (
                    frappe.request.headers.get("User-Agent")
                    if frappe.request
                    else "Backend"
                ),
                "status": "Active",
                "consented_purposes": consent_data.get("purposes", []),
            }
        )
        artifact.insert(ignore_permissions=True)
        artifact.submit()

        frappe.db.commit()  # Ensure it's saved even if user transaction rolls back (optional, but good for logs)

    except Exception as e:
        frappe.log_error(
            f"Failed to create Consent Artifact for {doc.name}: {str(e)}",
            "DPDP Consent Error",
        )
