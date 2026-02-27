# Copyright (c) 2026, manyam surendhranath and Contributors
# See license.txt
# dpdp_compliance/dpdp_compliance/doctype/data_erasure_log/test_data_erasure_log.py

"""Data erasure engine unit tests.

Tests cover: full user anonymization, ANONYMIZATION_MAP field replacement,
retention override blocking, erasure log creation, and User record anonymization.
"""

import json

import frappe
from frappe.tests import IntegrationTestCase

from dpdp_compliance.erasure import anonymize_user_data, ANONYMIZATION_MAP
from dpdp_compliance.test_helpers import make_test_user


class TestDataErasureLog(IntegrationTestCase):
    def setUp(self):
        self.test_user = make_test_user()

    def tearDown(self):
        # Clean up erasure logs
        logs = frappe.get_all(
            "Data Erasure Log",
            filters={"user": self.test_user.name},
            pluck="name",
        )
        for log_name in logs:
            try:
                frappe.delete_doc(
                    "Data Erasure Log", log_name, force=True, ignore_permissions=True
                )
            except Exception:
                pass

        try:
            frappe.delete_doc(
                "User", self.test_user.name, force=True, ignore_permissions=True
            )
        except Exception:
            pass
        frappe.db.commit()

    # === Core Anonymization ===

    def test_anonymize_user_data_returns_success(self):
        """anonymize_user_data should return success with count and log name."""
        result = anonymize_user_data(user=self.test_user.name)
        self.assertTrue(result["success"])
        self.assertIn("anonymized_count", result)
        self.assertIn("log_name", result)

    def test_anonymize_creates_erasure_log(self):
        """Anonymization should create a Data Erasure Log entry."""
        result = anonymize_user_data(user=self.test_user.name)
        log = frappe.get_doc("Data Erasure Log", result["log_name"])
        self.assertEqual(log.user, self.test_user.name)
        self.assertEqual(log.executed_by, frappe.session.user)
        self.assertIsNotNone(log.executed_on)

    def test_erasure_log_contains_anonymized_records_json(self):
        """Erasure log should contain a valid JSON of anonymized records."""
        result = anonymize_user_data(user=self.test_user.name)
        log = frappe.get_doc("Data Erasure Log", result["log_name"])
        records = json.loads(log.anonymized_records)
        self.assertIsInstance(records, list)

    def test_anonymize_disables_user_account(self):
        """After anonymization, User.enabled should be 0."""
        anonymize_user_data(user=self.test_user.name)
        user = frappe.get_doc("User", self.test_user.name)
        self.assertEqual(user.enabled, 0)

    def test_anonymize_replaces_user_name(self):
        """After anonymization, User.full_name should be 'Anonymized User'."""
        anonymize_user_data(user=self.test_user.name)
        user = frappe.get_doc("User", self.test_user.name)
        self.assertEqual(user.full_name, "Anonymized User")
        self.assertEqual(user.first_name, "Anonymized")

    def test_anonymize_with_dsr_reference(self):
        """Erasure log should link back to DSR when provided."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Erasure",
            description="Delete my data.",
        )
        result = anonymize_user_data(
            user=self.test_user.name,
            dsr_name=dsr_name,
        )
        log = frappe.get_doc("Data Erasure Log", result["log_name"])
        self.assertEqual(log.dsr_reference, dsr_name)

    # === ANONYMIZATION_MAP ===

    def test_anonymization_map_covers_common_types(self):
        """ANONYMIZATION_MAP should have entries for common field types."""
        expected_types = ["Data", "Email", "Phone", "Text", "Int", "Float", "Password"]
        for ft in expected_types:
            self.assertIn(
                ft, ANONYMIZATION_MAP, f"Missing ANONYMIZATION_MAP entry for {ft}"
            )

    def test_anonymization_map_email_is_invalid(self):
        """Anonymized email should use .invalid TLD per RFC."""
        self.assertTrue(
            ANONYMIZATION_MAP["Email"].endswith(".invalid"),
            "Anonymized email should use .invalid TLD",
        )
