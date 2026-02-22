# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class OrgaMilestone(Document):
    def validate(self):
        self.validate_due_date()

    def validate_due_date(self):
        """Warn if due date is in the past for new milestones"""
        if self.is_new() and self.due_date:
            if getdate(self.due_date) < getdate(nowdate()):
                frappe.msgprint(
                    _("Due date is in the past"),
                    indicator="orange",
                    alert=True
                )

    def before_save(self):
        self.set_completed_date()
        self.check_missed_status()

    def set_completed_date(self):
        """Auto-set completed date when status changes to Completed"""
        if self.status == "Completed" and not self.completed_date:
            self.completed_date = nowdate()
        elif self.status != "Completed" and self.completed_date:
            self.completed_date = None

    def check_missed_status(self):
        """Auto-set status to Missed if past due and not completed"""
        if self.due_date and self.status not in ["Completed", "Missed"]:
            if getdate(self.due_date) < getdate(nowdate()):
                self.status = "Missed"
                frappe.msgprint(
                    _("Milestone marked as Missed (past due date)"),
                    indicator="red",
                    alert=True
                )

    def get_linked_tasks(self):
        """Get all tasks linked to this milestone"""
        if not frappe.db.exists("DocType", "Orga Task"):
            return []

        return frappe.get_all(
            "Orga Task",
            filters={"milestone": self.name},
            fields=["name", "subject", "status", "assigned_to"]
        )

    def get_completion_percentage(self):
        """Calculate completion based on linked tasks"""
        tasks = self.get_linked_tasks()
        if not tasks:
            return 0

        completed = sum(1 for t in tasks if t.status == "Completed")
        return round((completed / len(tasks)) * 100, 2)
