import frappe
from dpdp_compliance.api import get_active_notice


def get_context(context):
    context.active_notice = get_active_notice()
    context.title = "Privacy Portal"
