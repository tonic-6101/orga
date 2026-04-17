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
        """Prevent duplicate task-contact assignments.

        Identity is Contact (new Owner + Collaborators model). `resource` is an
        optional capacity-enrichment pointer and may be null — don't key on it.
        """
        if not self.contact:
            return
        existing = frappe.db.get_value(
            "Orga Assignment",
            {
                "task": self.task,
                "contact": self.contact,
                "status": ["not in", ["Completed", "Cancelled"]],
                "name": ("!=", self.name),
            },
            "name",
        )
        if existing:
            frappe.throw(
                _("{0} is already assigned to this task ({1})").format(
                    self.contact, existing
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

