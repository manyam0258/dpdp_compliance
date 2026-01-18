# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate
from dpdp_compliance.utils.security_hooks import encrypt_fields, decrypt_fields


class DataSubjectRequest(Document):
    def before_save(self):
        # Auto-calculate SLA Deadline
        if self.request_date:
            # Default SLA: 30 Days (Section 11)
            self.sla_deadline = add_days(self.request_date, 30)

        # Encrypt Sensitive Fields
        encrypt_fields(self, None)

    def onload(self):
        # Decrypt Sensitive Fields
        decrypt_fields(self, None)
