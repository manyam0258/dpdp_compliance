# dpdp_compliance/setup.py
"""Post-install and post-migrate hooks for DPDP Compliance app."""

import frappe


DPDP_ROLES = [
    {
        "role_name": "DPO Manager",
        "desk_access": 1,
        "search_bar": 1,
        "notifications": 1,
    },
    {
        "role_name": "DPDP Admin",
        "desk_access": 1,
        "search_bar": 1,
        "notifications": 1,
    },
    {
        "role_name": "Compliance Viewer",
        "desk_access": 1,
        "search_bar": 1,
        "notifications": 0,
    },
]


def after_install():
    """Run after app installation."""
    create_dpdp_roles()
    frappe.db.commit()


def after_migrate():
    """Run after bench migrate."""
    create_dpdp_roles()
    frappe.db.commit()


def create_dpdp_roles():
    """Create DPDP-specific roles if they don't exist."""
    for role_data in DPDP_ROLES:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.get_doc({
                "doctype": "Role",
                **role_data,
            })
            role.insert(ignore_permissions=True)
            frappe.logger().info(f"Created role: {role_data['role_name']}")
