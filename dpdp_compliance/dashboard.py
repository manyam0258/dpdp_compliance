# dpdp_compliance/dashboard.py
"""DPO Dashboard API — aggregated compliance metrics.

Provides the data behind the DPDP Compliance Cockpit workspace.
"""

import frappe
from frappe.utils import today, add_days, getdate


@frappe.whitelist(methods=["GET"])
def get_dashboard_data() -> dict:
    """Return aggregated metrics for the DPO dashboard.

    Requires DPO Manager or System Manager role.
    """
    if not frappe.has_permission("DPDP Settings", ptype="read"):
        frappe.throw(
            "Insufficient permissions for DPO dashboard.", frappe.PermissionError
        )

    data = {}

    # === Consent Metrics ===
    data["consent_stats"] = {
        "total_granted": frappe.db.count(
            "Consent Log", {"status": "Granted", "docstatus": 1}
        ),
        "total_withdrawn": frappe.db.count(
            "Consent Log", {"status": "Withdrawn", "docstatus": 1}
        ),
        "total_expired": frappe.db.count(
            "Consent Log", {"status": "Expired", "docstatus": 1}
        ),
        "total_denied": frappe.db.count(
            "Consent Log", {"status": "Denied", "docstatus": 1}
        ),
    }

    # === DSR Metrics ===
    data["dsr_stats"] = {
        "open": frappe.db.count("Data Subject Request", {"status": "Open"}),
        "processing": frappe.db.count("Data Subject Request", {"status": "Processing"}),
        "completed": frappe.db.count("Data Subject Request", {"status": "Completed"}),
        "rejected": frappe.db.count("Data Subject Request", {"status": "Rejected"}),
        "sla_at_risk": frappe.db.count(
            "Data Subject Request",
            {
                "status": ["in", ["Open", "ID Verified", "Processing"]],
                "hours_until_breach": ["<", 24],
            },
        ),
    }

    # === Breach Metrics ===
    data["breach_stats"] = {
        "active": frappe.db.count(
            "Data Breach", {"status": ["not in", ["Closed", "Reported to DPB"]]}
        ),
        "reported": frappe.db.count("Data Breach", {"status": "Reported to DPB"}),
        "closed": frappe.db.count("Data Breach", {"status": "Closed"}),
        "critical_active": frappe.db.count(
            "Data Breach",
            {
                "severity": "Critical",
                "status": ["not in", ["Closed", "Reported to DPB"]],
            },
        ),
    }

    # === Governance Metrics ===
    data["governance_stats"] = {
        "data_assets_total": frappe.db.count("Data Asset"),
        "sensitive_assets": frappe.db.count(
            "Data Asset", {"classification": "Sensitive Personal Data"}
        ),
        "encrypted_assets": frappe.db.count("Data Asset", {"is_encrypted": 1}),
        "active_policies": frappe.db.count("Retention Policy", {"is_active": 1}),
        "processors_without_dpa": frappe.db.count(
            "Data Processor", {"is_active": 1, "dpa_signed": 0}
        ),
        "erasure_count": frappe.db.count("Data Erasure Log"),
    }

    # === VPC Metrics ===
    data["vpc_stats"] = {
        "pending": frappe.db.count("VPC Request", {"status": "Pending"}),
        "verified": frappe.db.count("VPC Request", {"status": "Verified"}),
    }

    return data
