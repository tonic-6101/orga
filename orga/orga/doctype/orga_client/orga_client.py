# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class OrgaClient(Document):
    def validate(self):
        self.validate_email_uniqueness()
        self.validate_user()
        self.update_project_count()

    def validate_email_uniqueness(self):
        """Ensure email is unique across clients"""
        if self.email:
            existing = frappe.db.get_value(
                "Orga Client",
                {"email": self.email, "name": ("!=", self.name)},
                "name"
            )
            if existing:
                frappe.throw(
                    _("A client with email {0} already exists: {1}").format(
                        self.email, existing
                    )
                )

    def validate_user(self):
        """Validate linked user has correct role"""
        if self.user:
            # Check if user already linked to another client
            existing = frappe.db.get_value(
                "Orga Client",
                {"user": self.user, "name": ("!=", self.name)},
                "name"
            )
            if existing:
                frappe.throw(
                    _("User {0} is already linked to client {1}").format(
                        self.user, existing
                    )
                )

    def update_project_count(self):
        """Update the count of linked projects"""
        if frappe.db.table_exists("tabOrga Project"):
            count = frappe.db.count(
                "Orga Project",
                {"client": self.name}
            )
            self.project_count = count

    def after_insert(self):
        """Actions after client is created"""
        if self.portal_enabled and not self.user:
            # Optionally auto-create user
            pass

    def on_update(self):
        """Actions after client is updated"""
        if self.user and self.portal_enabled:
            self.ensure_client_role()

    def ensure_client_role(self):
        """Ensure linked user has Orga Client role"""
        if not self.user:
            return

        user_doc = frappe.get_doc("User", self.user)
        has_role = any(r.role == "Orga Client" for r in user_doc.roles)

        if not has_role:
            user_doc.append("roles", {"role": "Orga Client"})
            user_doc.save(ignore_permissions=True)

    def create_portal_user(self, send_welcome_email=True):
        """
        Create a portal user for this client.

        Args:
            send_welcome_email: Whether to send welcome email with login instructions

        Returns:
            str: The created user's email/name
        """
        if self.user:
            frappe.throw(_("Client already has a portal user: {0}").format(self.user))

        if not self.email:
            frappe.throw(_("Email is required to create portal user"))

        # Check if user with this email already exists
        existing_user = frappe.db.exists("User", self.email)
        if existing_user:
            # Link existing user
            self.user = self.email
            self.portal_enabled = 1
            self.status = "Active"
            self.save()
            self.ensure_client_role()
            return self.email

        # Create new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": self.email,
            "first_name": self.client_name.split()[0] if self.client_name else "Client",
            "last_name": " ".join(self.client_name.split()[1:]) if len(self.client_name.split()) > 1 else "",
            "user_type": "Website User",
            "send_welcome_email": send_welcome_email,
            "roles": [{"role": "Orga Client"}]
        })
        user.insert(ignore_permissions=True)

        # Update client record
        self.user = user.name
        self.portal_enabled = 1
        self.status = "Active"
        self.save()

        return user.name

    def update_last_login(self):
        """Update last login timestamp"""
        self.db_set("last_login", now_datetime())

    def get_linked_projects(self, fields=None):
        """
        Get all projects linked to this client.

        Args:
            fields: List of fields to return

        Returns:
            list: List of project dicts
        """
        if not fields:
            fields = ["name", "project_name", "status", "progress", "start_date", "end_date"]

        if not frappe.db.table_exists("tabOrga Project"):
            return []

        return frappe.get_all(
            "Orga Project",
            filters={"client": self.name},
            fields=fields,
            order_by="creation desc"
        )

    def get_linked_milestones(self, project=None):
        """
        Get milestones for client's projects.

        Args:
            project: Optional project filter

        Returns:
            list: List of milestone dicts
        """
        if not frappe.db.table_exists("tabOrga Milestone"):
            return []

        filters = {}
        if project:
            filters["project"] = project
        else:
            # Get all projects for this client
            projects = self.get_linked_projects(fields=["name"])
            if not projects:
                return []
            filters["project"] = ["in", [p.name for p in projects]]

        return frappe.get_all(
            "Orga Milestone",
            filters=filters,
            fields=["name", "milestone_name", "project", "due_date", "status", "completion_date"],
            order_by="due_date asc"
        )
