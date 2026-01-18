import frappe
from frappe import _
from frappe.utils import now
from frappe.model.rename_doc import rename_doc


def process_erasure_queue():
    """
    Scheduled Job: Processes all DSRs with status 'Pending Erasure'.
    Anonymizes the linked User and marks DSR as Resolved.
    """
    erasure_requests = frappe.get_all(
        "Data Subject Request",
        filters={"request_type": "Erasure", "status": "Pending Erasure"},
        fields=["name", "data_principal"],
    )

    if not erasure_requests:
        return

    for req in erasure_requests:
        try:
            anonymize_user(req.data_principal)

            # Update DSR Status
            frappe.db.set_value("Data Subject Request", req.name, "status", "Resolved")
            frappe.db.commit()  # Commit per user to avoid partial failure blocks

        except Exception as e:
            frappe.log_error(
                f"Failed to process Erasure for DSR {req.name}: {str(e)}",
                "DPDP Erasure Job",
            )


def anonymize_user(user_name):
    """
    Anonymizes PII for the given User.
    """
    if not user_name or user_name in ["Administrator", "Guest"]:
        return

    user_doc = frappe.get_doc("User", user_name)

    # Anonymization format: anon_{random_hash}@example.com?
    # Or simpler: anon_{USER_ID}@deleted.user
    # We must ensure uniqueness if Email is unique.

    anon_id = f"anon_{frappe.generate_hash(length=8)}"
    anon_email = f"{anon_id}@deleted.local"

    user_doc.first_name = "Anonymous"
    user_doc.last_name = "User"
    user_doc.email = anon_email
    user_doc.username = anon_id
    user_doc.phone = ""
    user_doc.mobile_no = ""
    user_doc.bio = "This user account has been anonymized via DPDP Right to Erasure."

    # Disable the user
    user_doc.enabled = 0

    user_doc.save(ignore_permissions=True)

    # Also anonymize the name (ID) if possible?
    # In Frappe, renaming User is possible but expensive.
    # For now, we anonymize PII fields. The 'name' (ID) might adhere to email or random.
    # If the ID was the email, we should rename it.
    if "@" in user_doc.name:
        try:
            rename_doc("User", user_name, anon_email, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(
                f"Failed to rename User {user_name} during anonymization",
                "DPDP Erasure",
            )
