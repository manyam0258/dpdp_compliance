# Copyright (c) 2025, Antigravity and contributors
# For license information, please see license.txt

import frappe
import hashlib
import json
from frappe.model.document import Document


class ConsentArtifact(Document):
    def before_insert(self):
        self.generate_hash()

    def generate_hash(self):
        # Create a hash of critical fields to ensure tamper-proofing
        data_to_hash = {
            "user": self.data_principal,
            "notice": self.privacy_notice_ref,
            "timestamp": str(self.consent_timestamp),
            "purposes": [p.purpose for p in self.consented_purposes],
        }
        self.artifact_hash = hashlib.sha256(
            json.dumps(data_to_hash, sort_keys=True).encode()
        ).hexdigest()

    def validate(self):
        # Ensure referenced Privacy Notice is active (if this is new consent)
        if self.is_new():
            notice = frappe.get_doc("Privacy Notice", self.privacy_notice_ref)
            if not notice.is_active:
                frappe.throw(
                    f"Privacy Notice {self.privacy_notice_ref} is not active. Cannot grant consent."
                )

    def on_submit(self):
        pass

    def on_cancel(self):
        frappe.throw("Consent Artifacts cannot be cancelled. Use Withdrawal workflow.")

    def on_trash(self):
        frappe.throw(
            "Consent Artifacts cannot be deleted. They are immutable legal records."
        )
