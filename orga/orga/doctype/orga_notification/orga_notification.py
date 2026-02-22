# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Orga Notification DocType controller.

Manages in-app notifications for users with read/unread tracking.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class OrgaNotification(Document):
    def validate(self):
        self.validate_recipient()

    def validate_recipient(self):
        """Ensure recipient is a valid user."""
        if self.recipient and not frappe.db.exists("User", self.recipient):
            frappe.throw(_("Recipient {0} is not a valid user").format(self.recipient))

    def mark_as_read(self):
        """Mark this notification as read."""
        if not self.is_read:
            self.is_read = 1
            self.read_at = now_datetime()
            self.db_update()

    def mark_as_unread(self):
        """Mark this notification as unread."""
        if self.is_read:
            self.is_read = 0
            self.read_at = None
            self.db_update()


# ============================================
# Utility Functions for Creating Notifications
# ============================================

def create_notification(
    notification_type: str,
    subject: str,
    recipient: str,
    message: str = None,
    reference_doctype: str = None,
    reference_name: str = None,
    from_user: str = None
) -> "OrgaNotification":
    """
    Create a new notification.

    Args:
        notification_type: Type of notification (Assignment, Mention, etc.)
        subject: Notification subject line
        recipient: User to notify
        message: Optional detailed message
        reference_doctype: Related DocType
        reference_name: Related document name
        from_user: User who triggered the notification

    Returns:
        Created Orga Notification document
    """
    notification = frappe.get_doc({
        "doctype": "Orga Notification",
        "notification_type": notification_type,
        "subject": subject,
        "message": message,
        "recipient": recipient,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "from_user": from_user or frappe.session.user
    })
    notification.insert(ignore_permissions=True)
    return notification


def notify_assignment(task, assigned_to: str):
    """
    Create notification when user is assigned to a task.

    Args:
        task: Orga Task document
        assigned_to: User being assigned
    """
    if assigned_to == frappe.session.user:
        return  # Don't notify self

    create_notification(
        notification_type="Assignment",
        subject=_("You have been assigned to: {0}").format(task.subject),
        recipient=assigned_to,
        message=_("You have been assigned to task '{0}' in project '{1}'.").format(
            task.subject,
            task.project
        ),
        reference_doctype="Orga Task",
        reference_name=task.name
    )


def notify_status_change(doc, old_status: str, new_status: str):
    """
    Notify document owner when status changes.

    Args:
        doc: Document with status change
        old_status: Previous status
        new_status: New status
    """
    if doc.owner == frappe.session.user:
        return  # Don't notify self

    create_notification(
        notification_type="Status Change",
        subject=_("{0} status changed to {1}").format(doc.doctype.replace("Orga ", ""), new_status),
        recipient=doc.owner,
        message=_("The status of '{0}' was changed from {1} to {2}.").format(
            doc.name,
            old_status,
            new_status
        ),
        reference_doctype=doc.doctype,
        reference_name=doc.name
    )


def notify_mention(doc, mentioned_user: str, comment: str):
    """
    Notify when user is mentioned in a comment.

    Args:
        doc: Parent document where mention occurred
        mentioned_user: User who was mentioned
        comment: Comment text containing the mention
    """
    if mentioned_user == frappe.session.user:
        return  # Don't notify self

    # Truncate long comments
    truncated = comment[:200] + ("..." if len(comment) > 200 else "")

    create_notification(
        notification_type="Mention",
        subject=_("You were mentioned in {0}").format(doc.name),
        recipient=mentioned_user,
        message=truncated,
        reference_doctype=doc.doctype,
        reference_name=doc.name
    )


def notify_deadline(task, days_until_due: int):
    """
    Notify about upcoming task deadline.

    Args:
        task: Orga Task document
        days_until_due: Days until task is due (0 = today)
    """
    # Determine recipient: assigned user or owner
    recipient = task.assigned_to or task.owner
    if not recipient:
        return

    if days_until_due == 0:
        subject = _("Task due today: {0}").format(task.subject)
    elif days_until_due == 1:
        subject = _("Task due tomorrow: {0}").format(task.subject)
    else:
        subject = _("Task due in {0} days: {1}").format(days_until_due, task.subject)

    create_notification(
        notification_type="Deadline",
        subject=subject,
        recipient=recipient,
        message=_("Task '{0}' is due on {1}.").format(task.subject, task.due_date),
        reference_doctype="Orga Task",
        reference_name=task.name,
        from_user=None  # System notification
    )


def get_unread_count(user: str = None) -> int:
    """
    Get unread notification count for a user.

    Args:
        user: User to check (defaults to current user)

    Returns:
        Number of unread notifications
    """
    user = user or frappe.session.user
    return frappe.db.count(
        "Orga Notification",
        filters={"recipient": user, "is_read": 0}
    )
