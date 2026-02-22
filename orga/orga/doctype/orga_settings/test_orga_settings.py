# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestOrgaSettings(FrappeTestCase):
    def test_settings_exists(self):
        """Test that Orga Settings DocType exists and is accessible"""
        settings = frappe.get_single("Orga Settings")
        self.assertIsNotNone(settings)

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = frappe.get_single("Orga Settings")

        # Check defaults
        self.assertEqual(settings.default_task_status, "Open")
        self.assertEqual(settings.default_project_status, "Planning")
        self.assertEqual(settings.project_code_prefix, "ORG")
        self.assertEqual(settings.default_priority, "Medium")

    def test_feature_defaults(self):
        """Test feature toggle defaults"""
        settings = frappe.get_single("Orga Settings")

        self.assertEqual(settings.auto_calculate_progress, 1)
        self.assertEqual(settings.auto_set_missed_milestones, 1)
        self.assertEqual(settings.enable_time_tracking, 0)
        self.assertEqual(settings.default_capacity_hours, 40)

    def test_notification_defaults(self):
        """Test notification setting defaults"""
        settings = frappe.get_single("Orga Settings")

        self.assertEqual(settings.notify_on_task_assignment, 1)
        self.assertEqual(settings.notify_on_status_change, 0)
        self.assertEqual(settings.notify_on_due_date, 1)
        self.assertEqual(settings.due_date_reminder_days, 1)

    def test_update_settings(self):
        """Test updating settings"""
        settings = frappe.get_single("Orga Settings")

        original_prefix = settings.project_code_prefix

        settings.project_code_prefix = "TEST"
        settings.save()

        # Reload and verify
        settings.reload()
        self.assertEqual(settings.project_code_prefix, "TEST")

        # Restore original
        settings.project_code_prefix = original_prefix
        settings.save()

    def test_get_settings_helper(self):
        """Test get_settings helper function"""
        from orga.orga.doctype.orga_settings.orga_settings import get_settings

        settings = get_settings()
        self.assertIsNotNone(settings)
        self.assertTrue(hasattr(settings, "default_task_status"))

    def test_get_setting_helper(self):
        """Test get_setting helper function"""
        from orga.orga.doctype.orga_settings.orga_settings import get_setting

        value = get_setting("default_priority")
        self.assertEqual(value, "Medium")

        # Test with default
        value = get_setting("nonexistent_field", "default_value")
        self.assertEqual(value, "default_value")
