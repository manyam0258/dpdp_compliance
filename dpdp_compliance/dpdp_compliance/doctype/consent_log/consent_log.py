# Copyright (c) 2026, manyam surendhranath and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ConsentLog(Document):
    def before_save(self):
        """Prevent modification of submitted consent logs — immutability guard."""
        if self.docstatus == 1:
            frappe.throw(
                "Consent Log records are immutable after submission. "
                "Create a new log entry instead.",
                frappe.PermissionError,
            )

    def on_trash(self):
        """Prevent deletion of consent logs — legal evidence."""
        frappe.throw(
            "Consent Log records cannot be deleted as they serve as legal evidence "
            "under DPDP Act 2023.",
            frappe.PermissionError,
        )
