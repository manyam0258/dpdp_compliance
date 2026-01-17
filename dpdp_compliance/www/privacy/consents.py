import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/privacy/consents"
        raise frappe.Redirect

    context.consents = frappe.get_all(
        "Consent Artifact",
        filters={"data_principal": frappe.session.user},
        fields=[
            "name",
            "privacy_notice_ref",
            "consent_timestamp",
            "status",
            "artifact_hash",
        ],
        order_by="consent_timestamp desc",
    )
    context.title = "My Consents"
