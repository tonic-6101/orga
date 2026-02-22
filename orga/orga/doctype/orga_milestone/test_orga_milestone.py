# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days


def create_test_project():
    """Helper to create a test project"""
    project = frappe.get_doc({
        "doctype": "Orga Project",
        "project_name": f"Milestone Test Project {frappe.generate_hash(length=6)}",
        "status": "Active",
        "project_type": "Internal",
        "start_date": nowdate(),
        "end_date": add_days(nowdate(), 90),
        "project_manager": "Administrator"
    })
    project.insert()
    return project


class TestOrgaMilestone(FrappeTestCase):
    def test_milestone_creation(self):
        """Test basic milestone creation"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Test Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        self.assertTrue(milestone.name)
        self.assertTrue(milestone.name.startswith("MS-"))
        self.assertEqual(milestone.status, "Upcoming")

    def test_milestone_default_status(self):
        """Test that default status is Upcoming"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Default Status Milestone",
            "project": project.name,
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        self.assertEqual(milestone.status, "Upcoming")

    def test_completed_date_auto_set(self):
        """Test that completed_date is auto-set when status changes to Completed"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Completion Date Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        self.assertIsNone(milestone.completed_date)

        milestone.status = "Completed"
        milestone.save()

        self.assertIsNotNone(milestone.completed_date)

    def test_completed_date_cleared_on_status_change(self):
        """Test that completed_date is cleared when status changes from Completed"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Reopen Milestone",
            "project": project.name,
            "status": "Completed",
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        self.assertIsNotNone(milestone.completed_date)

        milestone.status = "In Progress"
        milestone.save()

        self.assertIsNone(milestone.completed_date)

    def test_missed_status_auto_set(self):
        """Test that overdue milestones are marked as Missed"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Overdue Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), -5)  # Past due
        })
        milestone.insert()

        # The validate method should set status to Missed
        self.assertEqual(milestone.status, "Missed")

    def test_completed_milestone_not_marked_missed(self):
        """Test that completed milestones are not marked as Missed"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Completed Past Milestone",
            "project": project.name,
            "status": "Completed",
            "due_date": add_days(nowdate(), -5)  # Past due but completed
        })
        milestone.insert()

        # Should stay Completed, not Missed
        self.assertEqual(milestone.status, "Completed")

    def test_milestone_status_values(self):
        """Test valid status values"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Status Test Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        for status in ["In Progress", "Completed", "Missed"]:
            milestone.status = status
            milestone.save()
            self.assertEqual(milestone.status, status)

    def test_milestone_with_description(self):
        """Test milestone with description and completion criteria"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Detailed Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), 30),
            "description": "<p>This is a detailed milestone</p>",
            "completion_criteria": "All tasks must be completed"
        })
        milestone.insert()

        self.assertEqual(milestone.description, "<p>This is a detailed milestone</p>")
        self.assertEqual(milestone.completion_criteria, "All tasks must be completed")

    def test_milestone_linked_to_project(self):
        """Test that milestone is properly linked to project"""
        project = create_test_project()
        milestone = frappe.get_doc({
            "doctype": "Orga Milestone",
            "milestone_name": "Linked Milestone",
            "project": project.name,
            "status": "Upcoming",
            "due_date": add_days(nowdate(), 30)
        })
        milestone.insert()

        self.assertEqual(milestone.project, project.name)

        # Verify we can get milestones for a project
        milestones = frappe.get_all(
            "Orga Milestone",
            filters={"project": project.name},
            fields=["name"]
        )
        self.assertGreater(len(milestones), 0)
