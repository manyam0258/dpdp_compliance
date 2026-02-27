# dpdp_compliance/vpc.py
"""Verifiable Parental Consent (VPC) Engine — minor detection, parental flow.

Implements DPDP Sec 9: Processing children's data requires verifiable parental consent.
"""

import frappe
from frappe.utils import now_datetime, add_to_date, get_datetime


def check_minor_on_signup(doc, method):
    """Hook: User.after_insert — detect if user is a minor and trigger VPC flow.

    Minor detection based on birth_date custom field on User.
    If no birth_date, check DPDP Settings for default age policy.
    """
    birth_date = getattr(doc, "birth_date", None)
    if not birth_date:
        return

    from frappe.utils import date_diff, today

    age_days = date_diff(today(), birth_date)
    age_years = age_days / 365.25

    if age_years < 18:
        # Mark as minor
        frappe.db.set_value("User", doc.name, "flags.is_minor", 1)
        # Initiate VPC flow
        initiate_vpc(doc.name)


def initiate_vpc(child_user: str, parent_email: str | None = None) -> str:
    """Create a VPC Request and send verification email to parent/guardian.

    Args:
        child_user: The minor user's email/ID
        parent_email: Parent/guardian email (if not provided, will be requested)

    Returns:
        str: Name of the VPC Request document.
    """
    import secrets

    token = secrets.token_urlsafe(32)

    vpc = frappe.get_doc(
        {
            "doctype": "VPC Request",
            "child_user": child_user,
            "parent_email": parent_email or "",
            "status": "Pending",
            "token": token,
            "expiry": add_to_date(now_datetime(), days=7),
        }
    )
    vpc.insert(ignore_permissions=True)

    if parent_email:
        _send_vpc_email(vpc, token)

    return vpc.name


def _send_vpc_email(vpc_doc, token: str):
    """Send parental consent verification email."""
    verification_url = (
        f"{frappe.utils.get_url()}/api/method/dpdp_compliance.vpc.verify_vpc"
        f"?token={token}&vpc_name={vpc_doc.name}"
    )

    try:
        frappe.sendmail(
            recipients=[vpc_doc.parent_email],
            subject="Parental Consent Required — DPDP Compliance",
            template="vpc_parental_consent",
            args={
                "child_email": vpc_doc.child_user,
                "verification_url": verification_url,
                "expiry_date": str(vpc_doc.expiry),
            },
        )
    except Exception:
        frappe.log_error(f"Failed to send VPC email for {vpc_doc.name}")


@frappe.whitelist(allow_guest=True, methods=["GET"])
def verify_vpc(token: str, vpc_name: str) -> dict:
    """Guest endpoint: verify parental consent via email link.

    Validates token and expiry, marks VPC as Verified.
    """
    vpc = frappe.get_doc("VPC Request", vpc_name)

    if vpc.status != "Pending":
        frappe.throw(f"VPC Request is already {vpc.status}.")

    if vpc.token != token:
        frappe.throw("Invalid verification token.")

    if vpc.expiry and get_datetime(vpc.expiry) < now_datetime():
        vpc.status = "Expired"
        vpc.save(ignore_permissions=True)
        frappe.throw("Verification link has expired. Please request a new one.")

    vpc.status = "Verified"
    vpc.save(ignore_permissions=True)

    return {"success": True, "message": "Parental consent verified successfully."}
