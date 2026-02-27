# dpdp_compliance/api.py
"""Public API endpoints for the DPDP Compliance app.

All endpoints use @frappe.whitelist() for authenticated access.
Guest endpoints are explicitly marked with allow_guest=True.
"""

import frappe
from frappe.utils import today, getdate


@frappe.whitelist(methods=["GET"])
def get_active_notice(language: str = "en") -> dict | None:
    """Get the current active Privacy Notice for a given language.

    Returns the notice content with linked consent purposes.
    """
    notice = frappe.db.get_value(
        "Privacy Notice",
        {"is_active": 1, "language": language, "docstatus": 1},
        ["name", "notice_id", "version", "effective_date", "content_html"],
        as_dict=True,
    )

    if not notice:
        return None

    # Get linked purposes
    purposes = frappe.get_all(
        "Privacy Notice Consent Purpose",
        filters={"parent": notice.name},
        fields=["consent_purpose", "is_mandatory"],
    )

    # Enrich with purpose details
    enriched_purposes = []
    for p in purposes:
        purpose_doc = frappe.db.get_value(
            "Consent Purpose",
            p.consent_purpose,
            [
                "name",
                "purpose_name",
                "description",
                "is_mandatory",
                "validity_days",
                "lawful_basis",
            ],
            as_dict=True,
        )
        if purpose_doc:
            enriched_purposes.append(purpose_doc)

    notice["purposes"] = enriched_purposes
    return notice


@frappe.whitelist(methods=["GET"])
def get_my_consents() -> list[dict]:
    """Get the current user's consent log entries (latest per purpose)."""
    user = frappe.session.user

    consents = frappe.db.sql(
        """
        SELECT cl.name, cl.purpose, cl.status, cl.timestamp, cl.expiry_date,
               cl.channel, cl.notice_version,
               cp.purpose_name, cp.description, cp.is_mandatory
        FROM `tabConsent Log` cl
        INNER JOIN `tabConsent Purpose` cp ON cl.purpose = cp.name
        INNER JOIN (
            SELECT user, purpose, MAX(timestamp) as max_ts
            FROM `tabConsent Log`
            WHERE docstatus = 1
            GROUP BY user, purpose
        ) latest ON cl.user = latest.user
            AND cl.purpose = latest.purpose
            AND cl.timestamp = latest.max_ts
        WHERE cl.user = %s AND cl.docstatus = 1
        ORDER BY cl.timestamp DESC
        """,
        (user,),
        as_dict=True,
    )

    return consents


@frappe.whitelist(methods=["POST"])
def withdraw_consent(purpose_id: str) -> dict:
    """Withdraw consent for a specific purpose. Creates a new 'Withdrawn' log entry.

    Withdrawal must be as easy as granting consent (DPDP Sec 6(4)).
    """
    from dpdp_compliance.consent import get_active_consent, create_consent_log

    user = frappe.session.user

    if not get_active_consent(user, purpose_id):
        frappe.throw("No active consent found for this purpose.")

    # Check if purpose is mandatory
    is_mandatory = frappe.db.get_value("Consent Purpose", purpose_id, "is_mandatory")
    if is_mandatory:
        frappe.throw(
            "Cannot withdraw consent for mandatory purposes. "
            "Contact the Data Protection Officer for assistance."
        )

    create_consent_log(
        user=user,
        purpose_id=purpose_id,
        status="Withdrawn",
        channel="Web",
    )

    return {"success": True, "message": "Consent withdrawn successfully."}


@frappe.whitelist(methods=["GET"])
def get_my_dsrs() -> list[dict]:
    """Get the current user's Data Subject Requests."""
    user = frappe.session.user

    dsrs = frappe.get_all(
        "Data Subject Request",
        filters={"user": user},
        fields=[
            "name",
            "request_type",
            "description",
            "status",
            "received_on",
            "sla_deadline",
            "identity_verified",
            "resolution_notes",
            "rejection_reason",
        ],
        order_by="received_on desc",
    )

    return dsrs


@frappe.whitelist(methods=["GET"])
def get_my_data_summary() -> dict:
    """Generate a summary of the user's personal data stored in the system.

    Right to Access (DPDP Sec 11).
    """
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    summary = {
        "email": user_doc.email,
        "full_name": user_doc.full_name,
        "user_type": user_doc.user_type,
        "creation": str(user_doc.creation),
        "last_active": str(user_doc.last_active) if user_doc.last_active else None,
    }

    # Count related records
    summary["consent_records"] = frappe.db.count(
        "Consent Log", {"user": user, "docstatus": 1}
    )
    summary["dsr_records"] = frappe.db.count("Data Subject Request", {"user": user})

    # Check if Customer record exists
    customer = frappe.db.get_value("Customer", {"name": user_doc.email}, "name")
    if customer:
        summary["customer_record"] = customer
        summary["order_count"] = frappe.db.count("Sales Order", {"customer": customer})
    else:
        summary["customer_record"] = None
        summary["order_count"] = 0

    # Get data processors this data is shared with
    processors = frappe.get_all(
        "Data Processor",
        filters={"is_active": 1},
        fields=["processor_name", "services"],
    )
    summary["data_shared_with"] = processors

    return summary


@frappe.whitelist(methods=["GET"])
def download_my_data():
    """Download all personal data as JSON (Right to Access + Portability).

    Returns a JSON response with all user data.
    """
    import json

    summary = get_my_data_summary()

    # Add consent details
    summary["consents"] = get_my_consents()

    # Add DSR history
    summary["data_subject_requests"] = get_my_dsrs()

    frappe.response["filename"] = f"my_data_{today()}.json"
    frappe.response["filecontent"] = json.dumps(summary, indent=2, default=str)
    frappe.response["type"] = "download"
