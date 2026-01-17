# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date


class PersonalDataBreach(Document):
    def before_insert(self):
        if self.discovery_time:
            # Rule 7: Report within 72 hours of becoming aware
            self.reporting_deadline = add_to_date(self.discovery_time, hours=72)

    def validate(self):
        if self.discovery_time and self.incident_time:
            if self.discovery_time < self.incident_time:
                frappe.throw("Discovery Time cannot be before Incident Time.")

        # Recalculate if changed
        if self.discovery_time:
            self.reporting_deadline = add_to_date(self.discovery_time, hours=72)
