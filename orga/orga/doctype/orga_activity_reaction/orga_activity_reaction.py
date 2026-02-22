# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Orga Activity Reaction DocType Controller

Handles quick reactions on activity items (acknowledge, celebrate, seen, flag).
Ensures unique reactions per user per activity per type.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaActivityReaction(Document):
    def validate(self):
        self.validate_reference()
        self.validate_unique_reaction()

    def validate_reference(self):
        """Ensure referenced document exists."""
        if not frappe.db.exists(self.reference_doctype, self.reference_name):
            frappe.throw(
                _("{0} {1} not found").format(self.reference_doctype, self.reference_name),
                frappe.DoesNotExistError
            )

    def validate_unique_reaction(self):
        """Ensure one reaction type per user per activity."""
        existing = frappe.db.exists("Orga Activity Reaction", {
            "reference_doctype": self.reference_doctype,
            "reference_name": self.reference_name,
            "user": self.user,
            "reaction_type": self.reaction_type,
            "name": ["!=", self.name or ""]
        })
        if existing:
            frappe.throw(_("You have already reacted with '{0}'").format(self.reaction_type))

    def before_insert(self):
        """Set user before insert if not set."""
        if not self.user:
            self.user = frappe.session.user

    def after_insert(self):
        """Notify activity owner if flagged."""
        if self.reaction_type == "flag":
            self.notify_flag()

    def notify_flag(self):
        """Send notification when activity is flagged."""
        # Get activity owner
        try:
            owner = frappe.db.get_value(
                self.reference_doctype,
                self.reference_name,
                "owner"
            )
            if owner and owner != self.user:
                frappe.publish_realtime(
                    "orga_activity_flagged",
                    {
                        "from_user": self.user,
                        "from_user_fullname": frappe.db.get_value(
                            "User", self.user, "full_name"
                        ),
                        "reference_doctype": self.reference_doctype,
                        "reference_name": self.reference_name
                    },
                    user=owner
                )
        except Exception:
            # Silently fail notification - don't break the reaction
            pass

    def on_trash(self):
        """Only allow user to delete their own reactions."""
        if self.user != frappe.session.user:
            if "System Manager" not in frappe.get_roles():
                frappe.throw(
                    _("You can only delete your own reactions"),
                    frappe.PermissionError
                )
