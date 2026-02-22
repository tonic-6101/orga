# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days


class TestOrgaProject(FrappeTestCase):
    def test_project_creation(self):
        """Test basic project creation"""
        project = frappe.get_doc({
            "doctype": "Orga Project",
            "project_name": "Test Project",
            "status": "Planning",
            "project_type": "Internal",
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), 30),
            "project_manager": "Administrator"
        })
        project.insert()

        self.assertTrue(project.name)
        self.assertTrue(project.project_code.startswith("ORG-"))
        self.assertEqual(project.status, "Planning")

    def test_project_code_auto_generation(self):
        """Test that project_code is auto-generated if not provided"""
        project = frappe.get_doc({
            "doctype": "Orga Project",
            "project_name": "Auto Code Project",
            "status": "Planning",
            "project_type": "Internal",
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), 30),
            "project_manager": "Administrator"
        })
        project.insert()

        self.assertTrue(project.project_code)
        self.assertRegex(project.project_code, r"ORG-\d{4}-\d{4}")

    def test_date_validation(self):
        """Test that end_date cannot be before start_date"""
        project = frappe.get_doc({
            "doctype": "Orga Project",
            "project_name": "Invalid Dates Project",
            "status": "Planning",
            "project_type": "Internal",
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), -10),  # End before start
            "project_manager": "Administrator"
        })

        self.assertRaises(frappe.ValidationError, project.insert)

    def test_project_with_custom_code(self):
        """Test project creation with custom project code"""
        custom_code = f"CUSTOM-{frappe.generate_hash(length=6).upper()}"
        project = frappe.get_doc({
            "doctype": "Orga Project",
            "project_name": "Custom Code Project",
            "project_code": custom_code,
            "status": "Planning",
            "project_type": "Client",
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), 60),
            "project_manager": "Administrator"
        })
        project.insert()

        self.assertEqual(project.project_code, custom_code)

    def test_project_status_transitions(self):
        """Test valid project status values"""
        project = frappe.get_doc({
            "doctype": "Orga Project",
            "project_name": "Status Test Project",
            "status": "Planning",
            "project_type": "Internal",
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), 30),
            "project_manager": "Administrator"
        })
        project.insert()

        # Test valid status transitions
        for status in ["Active", "On Hold", "Completed", "Cancelled"]:
            project.status = status
            project.save()
            self.assertEqual(project.status, status)
