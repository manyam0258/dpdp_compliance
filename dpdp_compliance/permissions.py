# dpdp_compliance/permissions.py
"""Row-level permission queries for DPDP Compliance DocTypes.

Restricts Website Users to only see their own records.
"""

import frappe


def dsr_permission_query(user):
    """Data Subject Request: Users see only their own DSRs (unless DPO/Admin)."""
    if not user:
        user = frappe.session.user

    if _has_elevated_role(user):
        return ""

    return f"(`tabData Subject Request`.user = {frappe.db.escape(user)})"


def consent_log_permission_query(user):
    """Consent Log: Users see only their own consent records (unless DPO/Admin)."""
    if not user:
        user = frappe.session.user

    if _has_elevated_role(user):
        return ""

    return f"(`tabConsent Log`.user = {frappe.db.escape(user)})"


def nominee_permission_query(user):
    """Nominee Record: Users see only their own nominees (unless DPO/Admin)."""
    if not user:
        user = frappe.session.user

    if _has_elevated_role(user):
        return ""

    return f"(`tabNominee Record`.user = {frappe.db.escape(user)})"


def _has_elevated_role(user: str) -> bool:
    """Check if user has DPO Manager, DPDP Admin, or System Manager role."""
    roles = frappe.get_roles(user)
    return bool(
        set(roles) & {"DPO Manager", "DPDP Admin", "System Manager", "Administrator"}
    )
