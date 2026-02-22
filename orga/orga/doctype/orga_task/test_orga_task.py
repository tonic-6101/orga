# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days, getdate


def create_test_project():
    """Helper to create a test project"""
    project = frappe.get_doc({
        "doctype": "Orga Project",
        "project_name": f"Task Test Project {frappe.generate_hash(length=6)}",
        "status": "Active",
        "project_type": "Internal",
        "start_date": nowdate(),
        "end_date": add_days(nowdate(), 90),
        "project_manager": "Administrator"
    })
    project.insert()
    return project


class TestOrgaTask(FrappeTestCase):
    def test_task_creation(self):
        """Test basic task creation"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Test Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        self.assertTrue(task.name)
        self.assertTrue(task.name.startswith("TASK-"))
        self.assertEqual(task.status, "Open")

    def test_task_default_values(self):
        """Test that default values are set correctly"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Default Values Task",
            "project": project.name
        })
        task.insert()

        self.assertEqual(task.status, "Open")
        self.assertEqual(task.priority, "Medium")
        self.assertEqual(task.progress, 0)

    def test_task_date_validation(self):
        """Test that due_date cannot be before start_date"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Invalid Dates Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium",
            "start_date": nowdate(),
            "due_date": add_days(nowdate(), -5)  # Due before start
        })

        self.assertRaises(frappe.ValidationError, task.insert)

    def test_completed_date_auto_set(self):
        """Test that completed_date is auto-set when status changes to Completed"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Completion Date Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        self.assertIsNone(task.completed_date)

        task.status = "Completed"
        task.save()

        self.assertIsNotNone(task.completed_date)

    def test_completed_date_cleared_on_reopen(self):
        """Test that completed_date is cleared when task is reopened"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Reopen Task",
            "project": project.name,
            "status": "Completed",
            "priority": "Medium"
        })
        task.insert()

        self.assertIsNotNone(task.completed_date)

        task.status = "Open"
        task.save()

        self.assertIsNone(task.completed_date)

    def test_circular_parent_task_prevention(self):
        """Test that circular parent task references are prevented"""
        project = create_test_project()

        task1 = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Parent Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task1.insert()

        task2 = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Child Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium",
            "parent_task": task1.name
        })
        task2.insert()

        # Try to make task1 a child of task2 (circular)
        task1.parent_task = task2.name
        self.assertRaises(frappe.ValidationError, task1.save)

    def test_self_reference_prevention(self):
        """Test that task cannot be its own parent"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Self Reference Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        task.parent_task = task.name
        self.assertRaises(frappe.ValidationError, task.save)

    def test_task_priority_values(self):
        """Test valid priority values"""
        project = create_test_project()
        for priority in ["Low", "Medium", "High", "Urgent"]:
            task = frappe.get_doc({
                "doctype": "Orga Task",
                "subject": f"Priority {priority} Task",
                "project": project.name,
                "status": "Open",
                "priority": priority
            })
            task.insert()
            self.assertEqual(task.priority, priority)

    def test_task_status_values(self):
        """Test valid status values"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Status Test Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        for status in ["In Progress", "Review", "Completed", "Cancelled"]:
            task.status = status
            task.save()
            self.assertEqual(task.status, status)

    def test_task_assignment(self):
        """Test task assignment to user"""
        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Assigned Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium",
            "assigned_to": "Administrator"
        })
        task.insert()

        self.assertEqual(task.assigned_to, "Administrator")
