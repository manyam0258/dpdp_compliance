# Copyright (c) 2026, manyam surendhranath and Contributors
# See license.txt
# dpdp_compliance/dpdp_compliance/doctype/consent_log/test_consent_log.py

"""Comprehensive consent engine unit tests.

Tests cover: consent log creation, immutability, active consent gate,
withdrawal flow, expiry, and Privacy Notice validation.
"""

import frappe
from frappe.tests import IntegrationTestCase

from dpdp_compliance.consent import create_consent_log, get_active_consent
from dpdp_compliance.test_helpers import (
    make_test_user,
    make_test_purpose,
    make_test_notice,
)


class TestConsentLog(IntegrationTestCase):
    def setUp(self):
        self.test_user = make_test_user()
        self.test_purpose = make_test_purpose()
        self.test_purpose_mandatory = make_test_purpose(
            name_suffix=f"mandatory-{frappe.generate_hash()[:4]}",
            is_mandatory=1,
        )

    def tearDown(self):
        # Clean up consent logs for this user
        logs = frappe.get_all(
            "Consent Log",
            filters={"user": self.test_user.name},
            pluck="name",
        )
        for log_name in logs:
            try:
                doc = frappe.get_doc("Consent Log", log_name)
                if doc.docstatus == 1:
                    doc.flags.ignore_permissions = True
                    doc.cancel()
                frappe.delete_doc(
                    "Consent Log", log_name, force=True, ignore_permissions=True
                )
            except Exception:
                pass

        # Clean up purposes
        for purpose in [self.test_purpose, self.test_purpose_mandatory]:
            try:
                purpose.reload()
                if purpose.docstatus == 1:
                    purpose.flags.ignore_permissions = True
                    purpose.cancel()
                frappe.delete_doc(
                    "Consent Purpose", purpose.name, force=True, ignore_permissions=True
                )
            except Exception:
                pass

        # Clean up user
        try:
            frappe.delete_doc(
                "User", self.test_user.name, force=True, ignore_permissions=True
            )
        except Exception:
            pass

        frappe.db.commit()

    # === Consent Log Creation ===

    def test_create_consent_log_returns_name(self):
        """create_consent_log should return a valid document name."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        self.assertTrue(log_name)
        self.assertTrue(frappe.db.exists("Consent Log", log_name))

    def test_consent_log_is_auto_submitted(self):
        """Consent logs should be auto-submitted (docstatus=1)."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        doc = frappe.get_doc("Consent Log", log_name)
        self.assertEqual(doc.docstatus, 1, "Consent Log must be Submitted")
        self.assertEqual(doc.status, "Granted")

    def test_consent_log_stores_metadata(self):
        """Consent log should store IP, user agent, channel, and timestamp."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
            channel="API",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )
        doc = frappe.get_doc("Consent Log", log_name)
        self.assertEqual(doc.channel, "API")
        self.assertEqual(doc.ip_address, "192.168.1.1")
        self.assertEqual(doc.user_agent, "TestAgent/1.0")
        self.assertIsNotNone(doc.timestamp)

    def test_consent_log_calculates_expiry(self):
        """Granted consent should have expiry_date based on purpose validity_days."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        doc = frappe.get_doc("Consent Log", log_name)
        self.assertIsNotNone(doc.expiry_date)

    def test_withdrawn_consent_has_no_expiry(self):
        """Withdrawn consent log should not set an expiry date."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Withdrawn",
        )
        doc = frappe.get_doc("Consent Log", log_name)
        self.assertIsNone(doc.expiry_date)

    # === Immutability Guards ===

    def test_consent_log_cannot_be_edited_after_submit(self):
        """Submitted Consent Log should block save attempts (immutability)."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        doc = frappe.get_doc("Consent Log", log_name)
        with self.assertRaises(frappe.UpdateAfterSubmitError):
            doc.status = "Withdrawn"
            doc.save()

    def test_consent_log_cannot_be_deleted(self):
        """Consent Log should not be deletable (legal evidence)."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("Consent Log", log_name)

    # === Active Consent Gate ===

    def test_get_active_consent_true_when_granted(self):
        """Active consent gate should return True after granting."""
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        self.assertTrue(get_active_consent(self.test_user.name, self.test_purpose.name))

    def test_get_active_consent_false_when_no_log(self):
        """Active consent gate should return False when no logs exist."""
        self.assertFalse(
            get_active_consent(self.test_user.name, self.test_purpose.name)
        )

    def test_get_active_consent_false_after_withdrawal(self):
        """Active consent gate should return False after withdrawal."""
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Withdrawn",
        )
        self.assertFalse(
            get_active_consent(self.test_user.name, self.test_purpose.name)
        )

    def test_get_active_consent_false_after_denial(self):
        """Active consent gate should return False after denial."""
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Denied",
        )
        self.assertFalse(
            get_active_consent(self.test_user.name, self.test_purpose.name)
        )

    def test_consent_re_grant_after_withdrawal(self):
        """Re-granting consent after withdrawal should return True."""
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Withdrawn",
        )
        create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        self.assertTrue(get_active_consent(self.test_user.name, self.test_purpose.name))

    # === Expiry ===

    def test_expired_consent_returns_false(self):
        """Consent with past expiry date should return False from active gate."""
        log_name = create_consent_log(
            user=self.test_user.name,
            purpose_id=self.test_purpose.name,
            status="Granted",
        )
        # Manually backdate expiry to yesterday
        frappe.db.set_value(
            "Consent Log",
            log_name,
            "expiry_date",
            frappe.utils.add_days(frappe.utils.today(), -1),
            update_modified=False,
        )
        frappe.db.commit()
        self.assertFalse(
            get_active_consent(self.test_user.name, self.test_purpose.name)
        )
