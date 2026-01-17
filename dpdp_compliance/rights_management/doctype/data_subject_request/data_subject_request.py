# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class DataSubjectRequest(Document):
    def before_insert(self):
        if not self.request_date:
            self.request_date = getdate()

        # Standard SLA for DSR is often 30 days internal target, though law says 'reasonable'.
        # Setting 30 days as default.
        self.sla_deadline = add_days(self.request_date, 30)
