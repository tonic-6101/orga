# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days


def create_test_project():
    """Helper to create a test project"""
    project = frappe.get_doc({
        "doctype": "Orga Project",
        "project_name": f"API Test Project {frappe.generate_hash(length=6)}",
        "status": "Active",
        "project_type": "Internal",
        "start_date": nowdate(),
        "end_date": add_days(nowdate(), 90),
        "project_manager": "Administrator"
    })
    project.insert()
    return project


class TestProjectAPI(FrappeTestCase):
    def test_get_projects(self):
        """Test get_projects API"""
        from orga.orga.api.project import get_projects

        project = create_test_project()
        result = get_projects()

        self.assertIn("projects", result)
        self.assertIn("total", result)
        self.assertIsInstance(result["projects"], list)
        self.assertGreater(result["total"], 0)

    def test_get_projects_with_filter(self):
        """Test get_projects API with status filter"""
        from orga.orga.api.project import get_projects

        project = create_test_project()
        result = get_projects(status="Active")

        self.assertIn("projects", result)
        for proj in result["projects"]:
            self.assertEqual(proj["status"], "Active")

    def test_get_project(self):
        """Test get_project API"""
        from orga.orga.api.project import get_project

        project = create_test_project()
        result = get_project(project.name)

        self.assertIn("project", result)
        self.assertEqual(result["project"]["name"], project.name)

    def test_get_project_stats(self):
        """Test get_project_stats API"""
        from orga.orga.api.project import get_project_stats

        project = create_test_project()
        result = get_project_stats(project.name)

        self.assertIn("tasks", result)
        self.assertIn("milestones", result)
        self.assertIn("total", result["tasks"])


class TestTaskAPI(FrappeTestCase):
    def test_get_tasks(self):
        """Test get_tasks API"""
        from orga.orga.api.task import get_tasks

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "API Test Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        result = get_tasks()

        self.assertIn("tasks", result)
        self.assertIn("total", result)
        self.assertIsInstance(result["tasks"], list)

    def test_get_tasks_by_project(self):
        """Test get_tasks API filtered by project"""
        from orga.orga.api.task import get_tasks

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Project Filter Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        result = get_tasks(project=project.name)

        self.assertIn("tasks", result)
        for t in result["tasks"]:
            self.assertEqual(t["project"], project.name)

    def test_get_task(self):
        """Test get_task API"""
        from orga.orga.api.task import get_task

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Get Task Test",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        result = get_task(task.name)

        # API returns task dict directly
        self.assertEqual(result["name"], task.name)
        self.assertEqual(result["subject"], "Get Task Test")

    def test_update_task_status(self):
        """Test update_task_status API"""
        from orga.orga.api.task import update_task_status

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Status Update Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium"
        })
        task.insert()

        result = update_task_status(task.name, "In Progress")

        # API returns task dict directly
        self.assertEqual(result["status"], "In Progress")

    def test_get_tasks_by_status(self):
        """Test get_tasks_by_status API"""
        from orga.orga.api.task import get_tasks_by_status

        project = create_test_project()
        result = get_tasks_by_status(project.name)

        self.assertIn("Open", result)
        self.assertIn("In Progress", result)
        self.assertIn("Completed", result)

    def test_get_my_tasks(self):
        """Test get_my_tasks API returns dict with tasks key"""
        from orga.orga.api.task import get_my_tasks

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "My Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium",
            "assigned_to": frappe.session.user
        })
        task.insert()

        result = get_my_tasks()

        self.assertIsInstance(result, dict)
        self.assertIn("tasks", result)
        self.assertIn("total", result)
        self.assertIsInstance(result["tasks"], list)
        self.assertGreater(result["total"], 0)

    def test_get_my_tasks_my_projects_scope(self):
        """Test get_my_tasks with my_projects scope returns tasks from managed projects"""
        from orga.orga.api.task import get_my_tasks

        project = create_test_project()
        # create_test_project sets project_manager to Administrator
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Unassigned Project Task",
            "project": project.name,
            "status": "Open",
            "priority": "Medium",
        })
        task.insert()

        result = get_my_tasks(scope="my_projects")

        self.assertIsInstance(result, dict)
        self.assertIn("tasks", result)
        task_names = [t["name"] for t in result["tasks"]]
        self.assertIn(task.name, task_names)

    def test_get_my_tasks_all_scope(self):
        """Test get_my_tasks with all scope (Administrator only)"""
        from orga.orga.api.task import get_my_tasks

        project = create_test_project()
        task = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": "Any Task for All Scope",
            "project": project.name,
            "status": "Open",
            "priority": "Low",
        })
        task.insert()

        # Running as Administrator in tests
        result = get_my_tasks(scope="all")

        self.assertIsInstance(result, dict)
        self.assertIn("tasks", result)
        task_names = [t["name"] for t in result["tasks"]]
        self.assertIn(task.name, task_names)


class TestDashboardAPI(FrappeTestCase):
    def test_get_stats(self):
        """Test get_stats API"""
        from orga.orga.api.dashboard import get_stats

        project = create_test_project()
        result = get_stats()

        self.assertIn("projects", result)
        self.assertIn("tasks", result)
        self.assertIn("milestones", result)

    def test_get_recent_activity(self):
        """Test get_recent_activity API"""
        from orga.orga.api.dashboard import get_recent_activity

        result = get_recent_activity()
        self.assertIsInstance(result, list)

    def test_get_overdue_tasks(self):
        """Test get_overdue_tasks API"""
        from orga.orga.api.dashboard import get_overdue_tasks

        result = get_overdue_tasks()
        # Result is a list directly
        self.assertIsInstance(result, list)

    def test_get_upcoming_milestones(self):
        """Test get_upcoming_milestones API"""
        from orga.orga.api.dashboard import get_upcoming_milestones

        result = get_upcoming_milestones()
        # Result is a list directly
        self.assertIsInstance(result, list)

    def test_get_project_summary(self):
        """Test get_project_summary API"""
        from orga.orga.api.dashboard import get_project_summary

        project = create_test_project()
        result = get_project_summary()

        # Result is a list of project summaries
        self.assertIsInstance(result, list)

    def test_get_workload_by_user(self):
        """Test get_workload_by_user API"""
        from orga.orga.api.dashboard import get_workload_by_user

        result = get_workload_by_user()
        self.assertIsInstance(result, list)
