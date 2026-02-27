# dpdp_compliance/dsr.py
"""Data Subject Request (DSR) Engine — OTP verification, SLA management.

Implements DPDP Sec 11–14: Right to Access, Correction, Erasure, Nomination, Grievance.
"""

import frappe
from frappe.utils import now_datetime, add_days, time_diff_in_hours, get_datetime


def submit_dsr(
    user: str,
    request_type: str,
    description: str,
    nominee_name: str | None = None,
    nominee_email: str | None = None,
    nominee_relationship: str | None = None,
) -> str:
    """Create a new Data Subject Request and send OTP for identity verification.

    Returns:
        str: Name of the created DSR document.
    """
    # Get SLA days from DPDP Settings
    sla_days = frappe.db.get_single_value("DPDP Settings", "default_sla_days") or 30

    dsr = frappe.get_doc(
        {
            "doctype": "Data Subject Request",
            "user": user,
            "request_type": request_type,
            "description": description,
            "status": "Open",
            "received_on": now_datetime(),
            "sla_deadline": add_days(now_datetime(), sla_days),
        }
    )

    # Add nomination details if applicable
    if request_type == "Nomination":
        dsr.nominee_name = nominee_name
        dsr.nominee_email = nominee_email
        dsr.nominee_relationship = nominee_relationship

    dsr.insert(ignore_permissions=True)

    # Send OTP for identity verification
    _send_otp(dsr)

    return dsr.name


def _send_otp(dsr_doc) -> str:
    """Generate and send OTP to the data principal for identity verification.

    In dev mode, OTP is logged and stored on the DSR for test retrieval.
    """
    import secrets

    otp = f"{secrets.randbelow(900000) + 100000}"  # 6-digit OTP
    dsr_doc.otp_token = frappe.utils.password.encrypt(otp)
    dsr_doc.save(ignore_permissions=True)

    user_email = frappe.db.get_value("User", dsr_doc.user, "email")

    # In dev mode, log OTP for test purposes (skill_07 pattern)
    if frappe.conf.developer_mode:
        frappe.logger().info(f"DPDP DSR OTP for {dsr_doc.name}: {otp}")
        frappe.cache.set_value(f"dpdp_dsr_otp:{dsr_doc.name}", otp, expires_in_sec=300)
    else:
        try:
            frappe.sendmail(
                recipients=[user_email],
                subject=f"OTP for Identity Verification - {dsr_doc.name}",
                template="dsr_otp_verification",
                args={
                    "otp": otp,
                    "dsr_name": dsr_doc.name,
                    "request_type": dsr_doc.request_type,
                    "valid_minutes": 5,
                },
            )
        except Exception:
            frappe.log_error(f"Failed to send OTP for DSR {dsr_doc.name}")

    return otp


@frappe.whitelist(methods=["POST"])
def verify_dsr_otp(dsr_name: str, otp: str) -> dict:
    """Verify the OTP submitted by the data principal.

    After successful verification, DSR moves to 'ID Verified' status.
    """
    dsr = frappe.get_doc("Data Subject Request", dsr_name)

    if dsr.identity_verified:
        return {"success": True, "message": "Already verified."}

    if not dsr.otp_token:
        frappe.throw("No OTP was generated for this request.")

    stored_otp = frappe.utils.password.decrypt(dsr.otp_token)

    if str(otp).strip() != str(stored_otp).strip():
        frappe.throw("Invalid OTP. Please try again.")

    dsr.identity_verified = 1
    dsr.verification_method = "OTP"
    dsr.status = "ID Verified"
    dsr.save(ignore_permissions=True)

    return {"success": True, "message": "Identity verified successfully."}


def calculate_sla_hours():
    """Scheduled hourly: calculate remaining SLA hours for all open DSRs.

    Updates hours_until_breach field for dashboard visibility.
    """
    open_dsrs = frappe.get_all(
        "Data Subject Request",
        filters={"status": ["in", ["Open", "ID Verified", "Processing"]]},
        fields=["name", "sla_deadline"],
    )

    for dsr in open_dsrs:
        if dsr.sla_deadline:
            hours = time_diff_in_hours(
                get_datetime(dsr.sla_deadline),
                now_datetime(),
            )
            frappe.db.set_value(
                "Data Subject Request",
                dsr.name,
                "hours_until_breach",
                max(0, round(hours, 1)),
                update_modified=False,
            )

    if open_dsrs:
        frappe.db.commit()
