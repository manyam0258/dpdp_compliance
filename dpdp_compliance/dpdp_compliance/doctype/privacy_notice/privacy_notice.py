# Copyright (c) 2026, manyam surendhranath and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PrivacyNotice(Document):
    def before_insert(self):
        """Auto-generate notice_id."""
        import secrets

        self.notice_id = f"PN-{frappe.utils.now_datetime().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

    def validate(self):
        """Ensure only one active notice per language."""
        if self.is_active:
            existing = frappe.db.exists(
                "Privacy Notice",
                {
                    "is_active": 1,
                    "language": self.language or "en",
                    "name": ("!=", self.name),
                    "docstatus": ("!=", 2),
                },
            )
            if existing:
                frappe.throw(
                    f"Another active Privacy Notice already exists for language "
                    f"'{self.language}': {existing}. Deactivate it first."
                )
