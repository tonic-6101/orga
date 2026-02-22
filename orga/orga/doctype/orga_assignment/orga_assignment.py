# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaAssignment(Document):
    def validate(self):
        self.validate_dates()
        self.validate_duplicate_assignment()
        self.check_resource_availability()

    def validate_dates(self):
        """Ensure end_date >= start_date"""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                frappe.throw(_("End Date cannot be before Start Date"))

    def validate_duplicate_assignment(self):
        """Prevent duplicate task-resource assignments"""
        existing = frappe.db.get_value(
            "Orga Assignment",
            {
                "task": self.task,
                "resource": self.resource,
                "status": ["not in", ["Completed", "Cancelled"]],
                "name": ("!=", self.name)
            },
            "name"
        )
        if existing:
            frappe.throw(
                _("Resource {0} is already assigned to this task ({1})").format(
                    self.resource, existing
                )
            )

    def check_resource_availability(self):
        """Warn if resource is overallocated (soft warning, not blocking)"""
        if not self.resource or not self.allocated_hours:
            return

        resource = frappe.get_doc("Orga Resource", self.resource)
        if resource.status != "Active":
            frappe.msgprint(
                _("Warning: Resource {0} status is {1}").format(
                    resource.resource_name, resource.status
                ),
                alert=True
            )

    def on_update(self):
        self.update_task_assigned_to()

    def on_trash(self):
        self.update_task_assigned_to()

    def update_task_assigned_to(self):
        """Update task's assigned_to field based on assignments"""
        if self.task:
            # Get first active assignment's resource user
            assignment = frappe.db.get_value(
                "Orga Assignment",
                {
                    "task": self.task,
                    "status": ["in", ["Assigned", "In Progress"]]
                },
                ["resource"],
                order_by="creation asc"
            )

            if assignment:
                user = frappe.db.get_value("Orga Resource", assignment, "user")
                if user:
                    frappe.db.set_value("Orga Task", self.task, "assigned_to", user)
            else:
                frappe.db.set_value("Orga Task", self.task, "assigned_to", None)
