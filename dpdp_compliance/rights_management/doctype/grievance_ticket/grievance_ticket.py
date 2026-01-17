# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class GrievanceTicket(Document):
    def before_insert(self):
        if not self.raised_on:
            self.raised_on = getdate()

        # Rule 14(3): Reasonable period not exceeding 90 days
        self.resolution_deadline = add_days(self.raised_on, 90)
