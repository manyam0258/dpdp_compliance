# dpdp_compliance/erasure.py
"""Data Erasure Engine — anonymization and retention-based data cleanup.

Implements DPDP Sec 12(3): Right to Erasure (anonymize rather than hard-delete).
Fields are overwritten with anonymized placeholders while preserving references.
"""

import json

import frappe
from frappe.utils import today, now_datetime


# Anonymization map: field type → replacement value
ANONYMIZATION_MAP = {
    "Data": "***ANONYMIZED***",
    "Small Text": "***ANONYMIZED***",
    "Text": "***ANONYMIZED***",
    "Text Editor": "***ANONYMIZED***",
    "Long Text": "***ANONYMIZED***",
    "Phone": "+00-0000000000",
    "Email": "anonymized@anonymized.invalid",
    "Date": None,  # Set to None
    "Datetime": None,
    "Int": 0,
    "Float": 0.0,
    "Currency": 0.0,
    "Password": "",
}


def anonymize_user_data(user: str, dsr_name: str | None = None) -> dict:
    """Anonymize all personal data for a given user across all tracked Data Assets.

    Does NOT delete records — overwrites PII fields with anonymized values
    while preserving record structure, IDs, and non-personal fields.

    Args:
        user: Email/user ID of the data principal.
        dsr_name: Optional DSR reference for audit trail.

    Returns:
        dict with anonymized_count and log details.
    """
    # Check retention policies — skip records still under legal retention
    retention_overrides = _get_retention_overrides()

    # Get all data assets to build anonymization plan
    data_assets = frappe.get_all(
        "Data Asset",
        filters={
            "classification": ["in", ["Personal Data", "Sensitive Personal Data"]]
        },
        fields=["name", "doctype_name", "field_name"],
    )

    anonymized = []
    total_count = 0

    # Group by DocType
    dt_fields = {}
    for asset in data_assets:
        dt_fields.setdefault(asset.doctype_name, []).append(asset.field_name)

    for doctype_name, fields in dt_fields.items():
        try:
            # Find records belonging to this user
            # Look for user link in standard fields: user, email, owner
            user_records = []

            if frappe.db.has_column(doctype_name, "user"):
                user_records = frappe.get_all(
                    doctype_name,
                    filters={"user": user},
                    fields=["name"],
                )
            elif frappe.db.has_column(doctype_name, "email"):
                user_records = frappe.get_all(
                    doctype_name,
                    filters={"email": user},
                    fields=["name"],
                )
            elif frappe.db.has_column(doctype_name, "owner"):
                user_records = frappe.get_all(
                    doctype_name,
                    filters={"owner": user},
                    fields=["name"],
                )

            if not user_records:
                continue

            # Check retention override
            if doctype_name in retention_overrides:
                continue

            for record in user_records:
                _anonymize_record(doctype_name, record.name, fields)
                anonymized.append(
                    {
                        "doctype": doctype_name,
                        "name": record.name,
                        "fields_anonymized": fields,
                    }
                )
                total_count += 1

        except Exception as e:
            frappe.log_error(
                f"Anonymization failed for {doctype_name}: {e}",
                "DPDP Erasure Error",
            )

    # Anonymize the User record itself
    _anonymize_user_record(user)

    # Create audit log
    log = frappe.get_doc(
        {
            "doctype": "Data Erasure Log",
            "user": user,
            "dsr_reference": dsr_name,
            "executed_by": frappe.session.user,
            "executed_on": now_datetime(),
            "anonymized_records": json.dumps(anonymized, indent=2),
        }
    )
    log.insert(ignore_permissions=True)

    return {
        "success": True,
        "anonymized_count": total_count,
        "log_name": log.name,
    }


def _anonymize_record(doctype_name: str, name: str, fields: list):
    """Anonymize specific fields in a single record."""
    updates = {}
    meta = frappe.get_meta(doctype_name)

    for field_name in fields:
        field = meta.get_field(field_name)
        if field:
            replacement = ANONYMIZATION_MAP.get(field.fieldtype, "***ANONYMIZED***")
            updates[field_name] = replacement

    if updates:
        frappe.db.set_value(
            doctype_name,
            name,
            updates,
            update_modified=False,
        )


def _anonymize_user_record(user: str):
    """Anonymize the User record's personal fields."""
    try:
        frappe.db.set_value(
            "User",
            user,
            {
                "full_name": "Anonymized User",
                "first_name": "Anonymized",
                "last_name": "User",
                "phone": ANONYMIZATION_MAP["Phone"],
                "mobile_no": ANONYMIZATION_MAP["Phone"],
                "bio": ANONYMIZATION_MAP["Text"],
                "location": ANONYMIZATION_MAP["Data"],
                "user_image": None,
                "enabled": 0,
            },
            update_modified=False,
        )
    except Exception as e:
        frappe.log_error(f"Failed to anonymize User record {user}: {e}")


def _get_retention_overrides() -> set:
    """Get DocTypes that are currently under legal retention override."""
    retention_policies = frappe.get_all(
        "Retention Policy",
        filters={"is_active": 1, "override_erasure": 1},
        fields=["doctype_name"],
    )
    return {rp.doctype_name for rp in retention_policies}
