# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime


class OrgaTask(Document):
    def validate(self):
        self.trail_start_date()
        self.validate_dates()
        self.validate_parent_task()
        self.validate_dependencies()
        self.validate_group_dependency()
        self.update_blocked_status()

    def trail_start_date(self):
        """If auto-trail is enabled and task is untouched, snap start_date to today."""
        if not getattr(self, "auto_trail_start", False):
            return
        if self.status != "Open" or (self.progress or 0) > 0:
            return
        if not self.start_date:
            return

        today = getdate(nowdate())
        if getdate(self.start_date) < today:
            old_start = getdate(self.start_date)
            shift = (today - old_start).days
            self.start_date = today
            if self.due_date:
                self.due_date = getdate(self.due_date) + datetime.timedelta(days=shift)

    def validate_dates(self):
        """Ensure due date is not before start date"""
        if self.due_date and self.start_date:
            if getdate(self.start_date) > getdate(self.due_date):
                frappe.throw(_("Due date cannot be before start date"))

    def validate_parent_task(self):
        """Prevent circular parent-child relationships"""
        if self.parent_task:
            if self.parent_task == self.name:
                frappe.throw(_("Task cannot be its own parent"))

            # Check for circular reference
            parent = self.parent_task
            visited = {self.name}
            while parent:
                if parent in visited:
                    frappe.throw(_("Circular parent-child relationship detected"))
                visited.add(parent)
                parent = frappe.db.get_value("Orga Task", parent, "parent_task")

    def validate_dependencies(self):
        """Prevent circular dependencies"""
        if not self.depends_on:
            return

        for dep in self.depends_on:
            # Check direct circular reference
            if dep.depends_on == self.name:
                frappe.throw(_("Task cannot depend on itself"))

            # Check transitive circular reference
            if self._creates_dependency_cycle(dep.depends_on, set()):
                frappe.throw(_("Circular dependency detected: {0}").format(dep.depends_on))

    def _creates_dependency_cycle(self, task_name, visited):
        """Recursively check for cycles in dependencies"""
        if task_name == self.name:
            return True
        if task_name in visited:
            return False

        visited.add(task_name)

        deps = frappe.get_all(
            "Orga Task Dependency",
            filters={"parent": task_name},
            fields=["depends_on"]
        )

        for dep in deps:
            if self._creates_dependency_cycle(dep.depends_on, visited):
                return True

        return False

    def validate_group_dependency(self):
        """A task cannot depend on its own group"""
        depends_on_group = getattr(self, "depends_on_group", None)
        task_group = getattr(self, "task_group", None)
        if depends_on_group and task_group and depends_on_group == task_group:
            frappe.throw(_("Task cannot depend on the group it belongs to"))

    def update_blocked_status(self):
        """Check if task is blocked by incomplete task or group dependencies"""
        # Check individual task dependencies (Finish to Start)
        for dep in (self.depends_on or []):
            dep_status = frappe.db.get_value("Orga Task", dep.depends_on, "status")
            if dep.dependency_type == "Finish to Start":
                if dep_status != "Completed":
                    self.is_blocked = 1
                    return

        # Check group dependency: blocked until ALL tasks in the named group are Completed
        depends_on_group = getattr(self, "depends_on_group", None)
        if depends_on_group and self.project:
            has_col = False
            try:
                has_col = frappe.db.has_column("Orga Task", "depends_on_group")
            except Exception as e:
                frappe.log_error(f"Column check failed: {e}", "Orga Task Blocked Status")
            if has_col:
                incomplete = frappe.db.count("Orga Task", {
                    "project": self.project,
                    "task_group": depends_on_group,
                    "status": ["not in", ["Completed", "Cancelled"]],
                    "name": ["!=", self.name]
                })
                if incomplete > 0:
                    self.is_blocked = 1
                    return

        self.is_blocked = 0

    def recalculate_hammock_dates(self):
        """Recalculate dates for hammock tasks based on predecessor/successor dates"""
        scheduling_type = getattr(self, "task_scheduling_type", None)
        if scheduling_type != "Hammock":
            return

        # Find latest predecessor end date (FS dependencies)
        pred_end = None
        for dep in (self.depends_on or []):
            if dep.dependency_type == "Finish to Start":
                pred_due = frappe.db.get_value("Orga Task", dep.depends_on, "due_date")
                if pred_due:
                    lag = dep.lag_days or 0
                    candidate = getdate(pred_due) + __import__("datetime").timedelta(days=1 + lag)
                    if pred_end is None or candidate > pred_end:
                        pred_end = candidate

        # Find earliest successor start date (tasks that depend on this one via FS)
        succ_start = None
        successors = frappe.get_all(
            "Orga Task Dependency",
            filters={"depends_on": self.name, "dependency_type": "Finish to Start"},
            fields=["parent", "lag_days"]
        )
        for succ in successors:
            s_start = frappe.db.get_value("Orga Task", succ.parent, "start_date")
            if s_start:
                lag = succ.lag_days or 0
                candidate = getdate(s_start) - __import__("datetime").timedelta(days=1 + lag)
                if succ_start is None or candidate < succ_start:
                    succ_start = candidate

        # Only update if both anchors exist
        if pred_end and succ_start and pred_end <= succ_start:
            if getdate(self.start_date) != pred_end or getdate(self.due_date) != succ_start:
                self.db_set("start_date", pred_end, update_modified=False)
                self.db_set("due_date", succ_start, update_modified=False)

    def calculate_buffer_consumption(self):
        """Calculate buffer consumption percentage based on predecessor delays"""
        scheduling_type = getattr(self, "task_scheduling_type", None)
        if scheduling_type != "Buffer":
            return

        buffer_size = getattr(self, "buffer_size", 0) or 0
        if buffer_size <= 0:
            return

        # Sum delay days from all FS predecessors
        total_delay = 0
        for dep in (self.depends_on or []):
            if dep.dependency_type == "Finish to Start":
                pred = frappe.db.get_value(
                    "Orga Task", dep.depends_on,
                    ["due_date", "start_date"], as_dict=True
                )
                if pred and pred.due_date and pred.start_date:
                    # Compare actual end vs expected end based on task's own duration
                    actual_end = getdate(pred.due_date)
                    # If predecessor is late (due_date > our start_date - lag - 1), count the delay
                    expected_end = getdate(self.start_date) - __import__("datetime").timedelta(days=1 + (dep.lag_days or 0))
                    delay = (actual_end - expected_end).days
                    if delay > 0:
                        total_delay += delay

        consumed = min(100.0, (total_delay / buffer_size) * 100)
        if self.buffer_consumed != consumed:
            self.db_set("buffer_consumed", consumed, update_modified=False)

    def before_save(self):
        self.set_completed_date()
        self.sync_progress_with_status()

    def set_completed_date(self):
        """Auto-set completed date when status changes to Completed"""
        if self.status == "Completed" and not self.completed_date:
            self.completed_date = nowdate()
        elif self.status != "Completed" and self.completed_date:
            self.completed_date = None

    def sync_progress_with_status(self):
        """Keep progress field in sync with task status.
        - Completed → 100%
        - Cancelled → 0%
        - Open (with no manual progress set) → 0%
        """
        if self.status == "Completed":
            self.progress = 100
        elif self.status == "Cancelled":
            self.progress = 0

    def on_update(self):
        self.update_project_progress()
        self.update_project_estimated_cost()
        self.update_project_spent()
        self.touch_project()
        self.update_dependent_tasks()

    def touch_project(self):
        """Update project's modified timestamp when a task changes"""
        if self.project and frappe.db.exists("Orga Project", self.project):
            frappe.db.set_value("Orga Project", self.project, "modified", frappe.utils.now())

    def update_dependent_tasks(self):
        """Update blocked status of tasks that depend on this one (task or group)"""
        updated = set()

        # 1. Tasks with individual dependency on this task
        dependents = frappe.get_all(
            "Orga Task Dependency",
            filters={"depends_on": self.name},
            fields=["parent"]
        )
        for dep in dependents:
            if dep.parent != self.name:
                updated.add(dep.parent)

        # 2. Tasks that depend on this task's group (same project)
        task_group = getattr(self, "task_group", None)
        if task_group and self.project:
            has_col = False
            try:
                has_col = frappe.db.has_column("Orga Task", "depends_on_group")
            except Exception as e:
                frappe.log_error(f"Column check failed: {e}", "Orga Task Dependents")
            if has_col:
                group_dependents = frappe.get_all(
                    "Orga Task",
                    filters={
                        "project": self.project,
                        "depends_on_group": task_group,
                        "name": ["!=", self.name]
                    },
                    fields=["name"]
                )
                for t in group_dependents:
                    updated.add(t.name)

        # Recalculate blocked status for all affected tasks
        for task_name in updated:
            task = frappe.get_doc("Orga Task", task_name)
            old_blocked = task.is_blocked
            task.update_blocked_status()
            if task.is_blocked != old_blocked:
                task.db_set("is_blocked", task.is_blocked, update_modified=False)
                # Notify assignee when task becomes unblocked
                if old_blocked and not task.is_blocked:
                    self._notify_task_unblocked(task)

        # Recalculate hammock/buffer dates for affected tasks
        for task_name in updated:
            try:
                task = frappe.get_doc("Orga Task", task_name)
                task.recalculate_hammock_dates()
                task.calculate_buffer_consumption()
            except Exception as e:
                frappe.log_error(
                    f"Hammock/buffer recalculation failed for {task_name}: {e}",
                    "Orga Task Recalculation"
                )

    def _notify_task_unblocked(self, task):
        """Send notification when a dependent task becomes unblocked"""
        try:
            from orga.orga.doctype.orga_notification.orga_notification import create_notification
            recipient = getattr(task, "assigned_to", None) or task.owner
            create_notification(
                notification_type="System",
                subject=_("Task unblocked: {0}").format(task.subject),
                recipient=recipient,
                message=_('Your task "{0}" is no longer blocked and can now be started.').format(task.subject),
                reference_doctype="Orga Task",
                reference_name=task.name
            )
        except Exception as e:
            # Don't break task updates if notification fails
            frappe.log_error(f"Task unblocked notification failed: {e}", "Orga Task Notification")

    def on_trash(self):
        self.update_project_progress()
        self.update_project_estimated_cost()
        self.update_project_spent()
        self.touch_project()

    def update_project_progress(self):
        """Trigger project progress recalculation"""
        if self.project and frappe.db.exists("Orga Project", self.project):
            project = frappe.get_doc("Orga Project", self.project)
            project.update_progress()

    def update_project_estimated_cost(self):
        """Trigger project estimated cost recalculation from task estimates"""
        if self.project and frappe.db.exists("Orga Project", self.project):
            project = frappe.get_doc("Orga Project", self.project)
            project.update_estimated_cost()

    def update_project_spent(self):
        """Trigger project spent recalculation from task actual costs"""
        if self.project and frappe.db.exists("Orga Project", self.project):
            project = frappe.get_doc("Orga Project", self.project)
            project.update_spent()

    @frappe.whitelist()
    def set_status(self, status):
        """Quick status update method for Kanban operations"""
        valid_statuses = ["Open", "In Progress", "Review", "Completed", "Cancelled"]
        if status not in valid_statuses:
            frappe.throw(_("Invalid status: {0}").format(status))

        self.status = status
        self.save()
        return self.status

    def update_checklist_completion(self, item_name, is_completed):
        """Update a checklist item's completion status"""
        for item in self.checklist:
            if item.name == item_name:
                item.is_completed = is_completed
                if is_completed:
                    item.completed_by = frappe.session.user
                    item.completed_on = now_datetime()
                else:
                    item.completed_by = None
                    item.completed_on = None
                self.save()
                return item
        frappe.throw(_("Checklist item not found"))

    def get_checklist_progress(self):
        """Calculate checklist completion percentage"""
        if not self.checklist:
            return 0
        completed = sum(1 for item in self.checklist if item.is_completed)
        return round((completed / len(self.checklist)) * 100, 2)
