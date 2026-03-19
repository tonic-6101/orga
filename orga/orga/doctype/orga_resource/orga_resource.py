# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaResource(Document):
    def validate(self):
        self.validate_user_uniqueness()
        self.set_full_name_from_user()
        self.auto_link_contact()

    def validate_user_uniqueness(self):
        """Ensure each user is linked to only one resource"""
        if self.user:
            existing = frappe.db.get_value(
                "Orga Resource",
                {"user": self.user, "name": ("!=", self.name)},
                "name"
            )
            if existing:
                frappe.throw(
                    _("User {0} is already linked to resource {1}").format(
                        self.user, existing
                    )
                )

    def set_full_name_from_user(self):
        """Auto-fill resource name from user if not set"""
        if self.user and not self.resource_name:
            self.resource_name = frappe.db.get_value("User", self.user, "full_name")

    def auto_link_contact(self):
        """Auto-link to a Frappe Contact if not already linked.

        If ``user`` is set but ``contact`` is empty, search for an existing
        Contact whose email matches the user's email.  If no match, create a
        new Contact and mark it as shared (``dock_shared = 1``) so the team
        can see it in Dock People.
        """
        if self.contact:
            return

        if not self.user:
            return

        user_email = frappe.db.get_value("User", self.user, "email")
        if not user_email:
            return

        # Try to find existing Contact by email
        existing = frappe.db.get_value(
            "Contact Email",
            {"email_id": user_email, "parenttype": "Contact"},
            "parent",
        )
        if existing:
            self.contact = existing
            return

        # Create a new Contact
        user_doc = frappe.get_doc("User", self.user)
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": user_doc.first_name or self.resource_name,
            "last_name": user_doc.last_name or "",
            "designation": frappe.db.get_value("Employee", self.employee, "designation") if self.employee else None,
            "company_name": frappe.db.get_value("Employee", self.employee, "company") if self.employee else None,
        })
        contact.append("email_ids", {"email_id": user_email, "is_primary": 1})
        if user_doc.mobile_no:
            contact.append("phone_nos", {"phone": user_doc.mobile_no, "is_primary_mobile_no": 1})
        if user_doc.phone:
            contact.append("phone_nos", {"phone": user_doc.phone, "is_primary_phone": 1})

        # Set dock_shared if the custom field exists
        if frappe.db.exists("Custom Field", {"dt": "Contact", "fieldname": "dock_shared"}):
            contact.dock_shared = 1

        contact.insert(ignore_permissions=True)
        self.contact = contact.name

    def get_current_workload(self, start_date=None, end_date=None):
        """
        Calculate current workload from assignments.

        Returns:
            dict: {allocated_hours, assignment_count, utilization_percent}
        """
        from frappe.utils import today, add_days

        if not start_date:
            start_date = today()
        if not end_date:
            end_date = add_days(start_date, 7)

        # Check if Orga Assignment table exists before querying
        if not frappe.db.table_exists("tabOrga Assignment"):
            return {
                "allocated_hours": 0,
                "assignment_count": 0,
                "utilization_percent": 0
            }

        assignments = frappe.get_all(
            "Orga Assignment",
            filters={
                "resource": self.name,
                "status": ["in", ["Assigned", "In Progress"]],
                "start_date": ["<=", end_date],
                "end_date": [">=", start_date]
            },
            fields=["allocated_hours"]
        )

        allocated = sum(a.allocated_hours or 0 for a in assignments)
        utilization = (allocated / self.weekly_capacity * 100) if self.weekly_capacity else 0

        return {
            "allocated_hours": allocated,
            "assignment_count": len(assignments),
            "utilization_percent": round(utilization, 1)
        }
