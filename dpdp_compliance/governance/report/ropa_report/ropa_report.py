import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "purpose",
            "label": _("Purpose of Processing"),
            "fieldtype": "Link",
            "options": "Consent Purpose",
            "width": 200,
        },
        {
            "fieldname": "data_principals",
            "label": _("Categories of Data Principals"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "personal_data",
            "label": _("Categories of Personal Data"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "lawful_basis",
            "label": _("Lawful Basis"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "retention_period",
            "label": _("Retention Period (Days)"),
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "fieldname": "data_processor",
            "label": _("Data Processors"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "security_measures",
            "label": _("Security Measures"),
            "fieldtype": "Data",
            "width": 200,
        },
    ]


def get_data(filters):
    """
    Generates RoPA data by aggregating Consent Purposes and metadata.
    """
    data = []

    # 1. Fetch all defined Purposes
    # Note: Assuming 'Consent Purpose' has fields like 'retention_period'.
    # If not, we use defaults for MVP.
    purposes = frappe.get_all("Consent Purpose", fields=["name", "description"])

    for purpose in purposes:
        row = {
            "purpose": purpose.name,
            "data_principals": "Customers / Site Users",  # Static for now
            "personal_data": "Name, Email, Phone, Bio",  # Derived from typical Schema
            "lawful_basis": "Consent (Section 6)",
            "retention_period": 365,  # Default placeholder
            "data_processor": "N/A (Internal)",
            "security_measures": "Fernet Encryption, Role Based Access",
        }
        data.append(row)

    return data
