import frappe

no_cache = 1


def get_context(context):
    """Serve the Doppio SPA shell for the Data Principal Portal."""
    csrf_token = frappe.sessions.get_csrf_token()
    context.csrf_token = csrf_token
    context.no_cache = 1
