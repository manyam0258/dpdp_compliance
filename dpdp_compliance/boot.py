# dpdp_compliance/boot.py
"""Boot session hook — inject DPDP settings into frappe.boot for client-side use."""

import frappe


def boot_session(bootinfo):
    """Add DPDP-specific flags to boot session."""
    try:
        bootinfo.dpdp_consent_modal_enabled = (
            frappe.db.get_single_value("DPDP Settings", "consent_modal_enabled") or 0
        )
    except Exception:
        bootinfo.dpdp_consent_modal_enabled = 0
