# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Orga Activity Comment DocType Controller

Handles inline comments on activity items with threading support.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaActivityComment(Document):
    def validate(self):
        self.validate_reference()
        self.validate_parent_comment()

    def validate_reference(self):
        """Ensure referenced document exists and user has access.

        System notes (e.g. deletion events) skip this check because the
        referenced document may no longer exist.
        """
        if self.note_type == "System":
            return

        if not frappe.db.exists(self.reference_doctype, self.reference_name):
            frappe.throw(
                _("{0} {1} not found").format(self.reference_doctype, self.reference_name),
                frappe.DoesNotExistError
            )

        if not frappe.has_permission(self.reference_doctype, "read", self.reference_name):
            frappe.throw(_("Not permitted to comment on this document"), frappe.PermissionError)

    def validate_parent_comment(self):
        """Ensure parent comment exists and belongs to same reference."""
        if self.parent_comment:
            parent = frappe.db.get_value(
                "Orga Activity Comment",
                self.parent_comment,
                ["reference_doctype", "reference_name"],
                as_dict=True
            )
            if not parent:
                frappe.throw(_("Parent comment not found"), frappe.DoesNotExistError)

            if (parent.reference_doctype != self.reference_doctype or
                    parent.reference_name != self.reference_name):
                frappe.throw(_("Parent comment must belong to the same document"))

    def before_insert(self):
        """Set user before insert if not set."""
        if not self.user:
            self.user = frappe.session.user

    def after_insert(self):
        """Notify mentioned users."""
        self.notify_mentions()

    def notify_mentions(self):
        """Send realtime notifications to mentioned users."""
        for mention in self.mentions:
            if mention.user != frappe.session.user:
                frappe.publish_realtime(
                    "orga_mention_notification",
                    {
                        "from_user": frappe.session.user,
                        "from_user_fullname": frappe.db.get_value(
                            "User", frappe.session.user, "full_name"
                        ),
                        "reference_doctype": self.reference_doctype,
                        "reference_name": self.reference_name,
                        "comment": self.name,
                        "content_preview": self.content[:100] if self.content else ""
                    },
                    user=mention.user
                )

    def on_trash(self):
        """Only allow author or admin to delete."""
        if self.user != frappe.session.user:
            if "System Manager" not in frappe.get_roles():
                frappe.throw(
                    _("Only the comment author or administrators can delete comments"),
                    frappe.PermissionError
                )

        # Delete child replies
        replies = frappe.get_all(
            "Orga Activity Comment",
            filters={"parent_comment": self.name},
            pluck="name"
        )
        for reply in replies:
            frappe.delete_doc("Orga Activity Comment", reply, ignore_permissions=True)
