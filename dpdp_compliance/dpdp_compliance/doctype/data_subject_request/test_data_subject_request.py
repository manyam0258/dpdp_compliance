# Copyright (c) 2026, manyam surendhranath and Contributors
# See license.txt
# dpdp_compliance/dpdp_compliance/doctype/data_subject_request/test_data_subject_request.py

"""DSR engine unit tests.

Tests cover: DSR creation, SLA deadline calculation, OTP generation/verification,
status transitions, and dev-mode OTP retrieval.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, add_days, time_diff_in_hours

from dpdp_compliance.test_helpers import make_test_user


class TestDataSubjectRequest(IntegrationTestCase):
    def setUp(self):
        self.test_user = make_test_user()

        # Ensure DPDP Settings exists with defaults
        if not frappe.db.get_single_value("DPDP Settings", "dpo_name"):
            settings = frappe.get_doc("DPDP Settings")
            settings.company_name = "Test Corp"
            settings.dpo_name = "Test DPO"
            settings.dpo_email = "dpo@test.com"
            settings.default_sla_days = 30
            settings.save(ignore_permissions=True)

    def tearDown(self):
        # Clean up DSRs for test user
        dsrs = frappe.get_all(
            "Data Subject Request",
            filters={"user": self.test_user.name},
            pluck="name",
        )
        for dsr_name in dsrs:
            try:
                frappe.delete_doc(
                    "Data Subject Request",
                    dsr_name,
                    force=True,
                    ignore_permissions=True,
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

    # === DSR Creation ===

    def test_submit_dsr_creates_document(self):
        """submit_dsr should create a DSR with correct fields."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="I want to see my data.",
        )
        self.assertTrue(dsr_name)
        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertEqual(doc.user, self.test_user.name)
        self.assertEqual(doc.request_type, "Access")
        self.assertEqual(doc.status, "Open")

    def test_dsr_has_sla_deadline(self):
        """DSR should have SLA deadline set from DPDP Settings."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Erasure",
            description="Delete my data.",
        )
        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertIsNotNone(doc.sla_deadline)

    def test_dsr_sla_is_30_days(self):
        """DSR SLA deadline should be 30 days from received_on."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="Access request.",
        )
        doc = frappe.get_doc("Data Subject Request", dsr_name)
        hours_diff = abs(time_diff_in_hours(doc.sla_deadline, doc.received_on))
        # Should be approximately 30 days (720 hours), allow 1 hour tolerance
        self.assertAlmostEqual(hours_diff, 720, delta=1)

    # === OTP ===

    def test_dsr_generates_otp(self):
        """DSR creation should generate and store an OTP token."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="I need my data.",
        )
        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertTrue(doc.otp_token, "OTP token should be set")

    def test_dsr_otp_cached_in_dev_mode(self):
        """In developer mode, OTP should be cached in Redis."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="Test OTP cache.",
        )
        cached_otp = frappe.cache.get_value(f"dpdp_dsr_otp:{dsr_name}")
        self.assertIsNotNone(cached_otp, "OTP should be cached in dev mode")
        self.assertEqual(len(str(cached_otp)), 6, "OTP should be 6 digits")

    def test_verify_dsr_otp_success(self):
        """Correct OTP should verify identity and advance status."""
        from dpdp_compliance.dsr import submit_dsr, verify_dsr_otp

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="Verify me.",
        )
        otp = frappe.cache.get_value(f"dpdp_dsr_otp:{dsr_name}")

        result = verify_dsr_otp(dsr_name=dsr_name, otp=str(otp))
        self.assertTrue(result["success"])

        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertEqual(doc.status, "ID Verified")
        self.assertTrue(doc.identity_verified)
        self.assertEqual(doc.verification_method, "OTP")

    def test_verify_dsr_otp_failure(self):
        """Wrong OTP should raise an error."""
        from dpdp_compliance.dsr import submit_dsr, verify_dsr_otp

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="Bad OTP test.",
        )
        with self.assertRaises(frappe.ValidationError):
            verify_dsr_otp(dsr_name=dsr_name, otp="000000")

    # === Nomination ===

    def test_dsr_nomination_stores_nominee_details(self):
        """Nomination DSR should store nominee name, email, relationship."""
        from dpdp_compliance.dsr import submit_dsr

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Nomination",
            description="Nominate my spouse.",
            nominee_name="Jane Doe",
            nominee_email="jane@example.com",
            nominee_relationship="Spouse",
        )
        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertEqual(doc.nominee_name, "Jane Doe")
        self.assertEqual(doc.nominee_email, "jane@example.com")
        self.assertEqual(doc.nominee_relationship, "Spouse")

    # === SLA Calculator ===

    def test_calculate_sla_hours_updates_field(self):
        """Hourly SLA calculator should update hours_until_breach."""
        from dpdp_compliance.dsr import submit_dsr, calculate_sla_hours

        dsr_name = submit_dsr(
            user=self.test_user.name,
            request_type="Access",
            description="SLA test.",
        )

        calculate_sla_hours()

        doc = frappe.get_doc("Data Subject Request", dsr_name)
        self.assertIsNotNone(doc.hours_until_breach)
        self.assertGreater(doc.hours_until_breach, 0)
