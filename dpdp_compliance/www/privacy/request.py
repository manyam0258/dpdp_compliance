import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/privacy/request"
        raise frappe.Redirect

    context.title = "New Data Request"
