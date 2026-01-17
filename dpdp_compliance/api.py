import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def withdraw_consent(artifact_name):
    """
    Withdraws a specific consent artifact.
    """
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(
            _("You must be logged in to withdraw consent."), frappe.PermissionError
        )

    artifact = frappe.get_doc("Consent Artifact", artifact_name)

    # Security Check: Ensure the artifact belongs to the logged-in user
    if artifact.data_principal != frappe.session.user:
        frappe.throw(
            _("Unauthorized to withdraw this consent."), frappe.PermissionError
        )

    if artifact.status == "Withdrawn":
        frappe.throw(_("Consent is already withdrawn."))

    artifact.status = "Withdrawn"
    artifact.withdrawal_timestamp = now_datetime()
    artifact.save(ignore_permissions=True)

    return {"status": "success", "message": _("Consent withdrawn successfully.")}


@frappe.whitelist()
def create_dsr(request_type, description):
    """
    Creates a Data Subject Request.
    """
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(
            _("You must be logged in to submit a request."), frappe.PermissionError
        )

    dsr = frappe.get_doc(
        {
            "doctype": "Data Subject Request",
            "data_principal": frappe.session.user,
            "request_type": request_type,
            "description": description,
            "status": "Open",
            "request_date": now_datetime(),
        }
    )

    dsr.insert(ignore_permissions=True)

    return {
        "status": "success",
        "message": _("Request submitted successfully."),
        "name": dsr.name,
    }


@frappe.whitelist()
def get_active_notice(language="English"):
    """
    Fetches the currently active Privacy Notice for the given language.
    """
    notice = frappe.db.get_value(
        "Privacy Notice",
        {"is_active": 1, "language": language},
        ["name", "content_html", "version"],
        as_dict=True,
    )
    return notice
