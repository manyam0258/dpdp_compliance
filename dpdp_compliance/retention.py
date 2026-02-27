# dpdp_compliance/retention.py
"""Retention Engine — daily scheduler for data lifecycle management.

Implements DPDP Sec 8(7): Data shall not be retained beyond the period necessary.
"""

import frappe
from frappe.utils import today, add_days, getdate, now_datetime


def run_retention_engine():
    """Scheduled daily: check all active Retention Policies and process expired records.

    For each policy:
    1. Find records past the retention date
    2. Based on action_on_expiry: Anonymize, Delete, or Flag for Review
    3. Create Data Erasure Log entries for audit trail
    """
    import json

    policies = frappe.get_all(
        "Retention Policy",
        filters={"is_active": 1},
        fields=[
            "name",
            "policy_name",
            "doctype_name",
            "date_field",
            "retention_days",
            "action_on_expiry",
            "override_erasure",
        ],
    )

    total_processed = 0

    for policy in policies:
        try:
            cutoff_date = add_days(today(), -policy.retention_days)

            # Find expired records
            expired_records = frappe.get_all(
                policy.doctype_name,
                filters={
                    policy.date_field: ["<", cutoff_date],
                },
                fields=["name", policy.date_field],
                limit=500,  # Process in batches
            )

            if not expired_records:
                continue

            action = policy.action_on_expiry or "Anonymize"

            for record in expired_records:
                if action == "Delete":
                    frappe.delete_doc(
                        policy.doctype_name,
                        record.name,
                        ignore_permissions=True,
                        force=True,
                    )
                elif action == "Anonymize":
                    from dpdp_compliance.erasure import _anonymize_record

                    # Get personal data fields for this DocType from Data Assets
                    fields = frappe.get_all(
                        "Data Asset",
                        filters={
                            "doctype_name": policy.doctype_name,
                            "classification": [
                                "in",
                                ["Personal Data", "Sensitive Personal Data"],
                            ],
                        },
                        pluck="field_name",
                    )
                    if fields:
                        _anonymize_record(policy.doctype_name, record.name, fields)
                elif action == "Flag for Review":
                    # Add a comment for DPO review
                    frappe.get_doc(
                        {
                            "doctype": "Comment",
                            "comment_type": "Info",
                            "reference_doctype": policy.doctype_name,
                            "reference_name": record.name,
                            "content": f"⏰ Retention period expired per policy '{policy.policy_name}'. "
                            f"Record is {policy.retention_days} days past retention date. "
                            f"DPO review required.",
                        }
                    ).insert(ignore_permissions=True)

                total_processed += 1

            # Create audit log for this policy run
            frappe.get_doc(
                {
                    "doctype": "Data Erasure Log",
                    "user": "System",
                    "executed_by": "Administrator",
                    "executed_on": now_datetime(),
                    "anonymized_records": json.dumps(
                        {
                            "policy": policy.policy_name,
                            "doctype": policy.doctype_name,
                            "action": action,
                            "records_processed": len(expired_records),
                            "cutoff_date": str(cutoff_date),
                        }
                    ),
                }
            ).insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(
                f"Retention policy '{policy.policy_name}' failed: {e}",
                "DPDP Retention Engine Error",
            )

    if total_processed:
        frappe.logger().info(f"DPDP Retention: processed {total_processed} records")
        frappe.db.commit()
