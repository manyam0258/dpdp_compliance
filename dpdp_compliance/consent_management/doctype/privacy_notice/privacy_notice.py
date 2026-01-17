# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PrivacyNotice(Document):
    def validate(self):
        if self.is_active:
            # Ensure only one active notice per language
            active_notices = frappe.get_all(
                "Privacy Notice",
                filters={
                    "is_active": 1,
                    "language": self.language,
                    "name": ["!=", self.name],
                },
                fields=["name"],
            )
            if active_notices:
                frappe.throw(
                    f"Another active Privacy Notice ({active_notices[0].name}) already exists for language {self.language}. Please deactivate it first."
                )
