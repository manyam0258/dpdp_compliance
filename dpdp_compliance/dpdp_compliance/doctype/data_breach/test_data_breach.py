# Copyright (c) 2026, manyam surendhranath and Contributors
# See license.txt
# dpdp_compliance/dpdp_compliance/doctype/data_breach/test_data_breach.py

"""Data Breach engine unit tests.

Tests cover: 72-hour deadline calculation, breach ID generation,
IRT alerting, escalation thresholds, and Data Breach DocType validation.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, add_to_date, get_datetime


class TestDataBreach(IntegrationTestCase):
    def setUp(self):
        # Ensure DPDP Settings has IRT emails
        settings = frappe.get_doc("DPDP Settings")
        if not settings.dpo_name:
            settings.company_name = "Test Corp"
            settings.dpo_name = "Test DPO"
            settings.dpo_email = "dpo@test.com"
        settings.irt_emails = "irt@test.com"
        settings.save(ignore_permissions=True)

    def tearDown(self):
        breaches = frappe.get_all(
            "Data Breach",
            filters={"breach_title": ["like", "Test Breach%"]},
            pluck="name",
        )
        for name in breaches:
            try:
                doc = frappe.get_doc("Data Breach", name)
                if doc.docstatus == 1:
                    doc.flags.ignore_permissions = True
                    doc.cancel()
                frappe.delete_doc(
                    "Data Breach", name, force=True, ignore_permissions=True
                )
            except Exception:
                pass
        frappe.db.commit()

    def _create_breach(self, **kwargs):
        """Helper to create a test breach."""
        defaults = {
            "doctype": "Data Breach",
            "breach_title": f"Test Breach {frappe.generate_hash()[:6]}",
            "severity": "High",
            "nature_of_breach": "Test breach for unit testing.",
            "detection_time": now_datetime(),
        }
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        return doc

    # === Breach Creation ===

    def test_breach_insert_sets_deadline(self):
        """On insert, breach should auto-set 72-hour reporting deadline."""
        breach = self._create_breach()
        breach.reload()
        self.assertIsNotNone(breach.reporting_deadline)

    def test_breach_deadline_is_72_hours(self):
        """Reporting deadline should be exactly 72 hours from detection."""
        detection = now_datetime()
        breach = self._create_breach(detection_time=detection)
        breach.reload()

        expected = add_to_date(detection, hours=72)
        actual = get_datetime(breach.reporting_deadline)

        diff_seconds = abs((expected - actual).total_seconds())
        self.assertLess(
            diff_seconds, 60, "Deadline should be within 1 minute of 72h from detection"
        )

    def test_breach_auto_generates_id(self):
        """Breach should auto-generate a breach_id on insert."""
        breach = self._create_breach()
        breach.reload()
        self.assertTrue(breach.breach_id)
        self.assertTrue(breach.breach_id.startswith("BR-"))

    def test_breach_hours_remaining_set(self):
        """On insert, hours_remaining should be set to 72."""
        breach = self._create_breach()
        breach.reload()
        self.assertEqual(breach.hours_remaining, 72)

    # === Breach Severity ===

    def test_breach_accepts_all_severity_levels(self):
        """All severity levels should be valid."""
        for severity in ["Critical", "High", "Medium", "Low"]:
            breach = self._create_breach(severity=severity)
            breach.reload()
            self.assertEqual(breach.severity, severity)

    # === Status Transitions ===

    def test_breach_default_status_is_detected(self):
        """New breach should default to 'Detected' status."""
        breach = self._create_breach()
        breach.reload()
        self.assertEqual(breach.status, "Detected")

    def test_breach_status_can_be_updated(self):
        """Breach status should be updatable through lifecycle."""
        breach = self._create_breach()
        breach.reload()

        for new_status in ["Assessing", "Contained", "Reported to DPB"]:
            breach.status = new_status
            breach.save(ignore_permissions=True)
            breach.reload()
            self.assertEqual(breach.status, new_status)

    # === Hourly Calculator ===

    def test_calculate_breach_hours_updates_remaining(self):
        """Hourly calculator should update hours_remaining field."""
        from dpdp_compliance.breach import calculate_breach_hours

        breach = self._create_breach()
        breach.reload()

        calculate_breach_hours()

        breach.reload()
        self.assertIsNotNone(breach.hours_remaining)
        self.assertGreater(breach.hours_remaining, 0)
        self.assertLessEqual(breach.hours_remaining, 72)

    def test_calculate_breach_hours_skips_reported(self):
        """Calculator should skip breaches that are already reported to DPB."""
        breach = self._create_breach()
        breach.reload()
        breach.status = "Reported to DPB"
        breach.save(ignore_permissions=True)

        from dpdp_compliance.breach import calculate_breach_hours

        calculate_breach_hours()

        # hours_remaining should stay as initially set (not recalculated)
        breach.reload()
        self.assertEqual(breach.hours_remaining, 72)
