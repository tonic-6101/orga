# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Notification API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.notification.get_my_notifications'
    })
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def get_my_notifications(limit=50, offset=0, unread_only=False):
    """
    Get notifications for current user.

    Args:
        limit: Maximum results (default 50)
        offset: Pagination offset
        unread_only: Only return unread notifications

    Returns:
        dict: {notifications: [...], total: int, unread_count: int}
    """
    filters = {"recipient": frappe.session.user}

    if unread_only in (True, "true", "1", 1):
        filters["is_read"] = 0

    notifications = frappe.get_all(
        "Orga Notification",
        filters=filters,
        fields=[
            "name",
            "notification_type",
            "subject",
            "message",
            "is_read",
            "read_at",
            "reference_doctype",
            "reference_name",
            "from_user",
            "creation"
        ],
        order_by="creation desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    # Enrich with sender name
    for n in notifications:
        if n.get("from_user"):
            n["from_user_name"] = frappe.db.get_value("User", n["from_user"], "full_name")
        else:
            n["from_user_name"] = "System"

    total = frappe.db.count("Orga Notification", {"recipient": frappe.session.user})
    unread_count = frappe.db.count(
        "Orga Notification",
        {"recipient": frappe.session.user, "is_read": 0}
    )

    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count
    }


@frappe.whitelist()
def get_unread_count():
    """
    Get unread notification count for current user.

    Returns:
        int: Number of unread notifications
    """
    return frappe.db.count(
        "Orga Notification",
        {"recipient": frappe.session.user, "is_read": 0}
    )


@frappe.whitelist()
def mark_as_read(name):
    """
    Mark a notification as read.

    Args:
        name: Notification name

    Returns:
        dict: {success: True}
    """
    if not frappe.db.exists("Orga Notification", name):
        frappe.throw(_("Notification not found"))

    notification = frappe.get_doc("Orga Notification", name)

    # Permission check
    if notification.recipient != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    notification.is_read = 1
    notification.read_at = now_datetime()
    notification.save(ignore_permissions=True)

    return {"success": True}


@frappe.whitelist()
def mark_as_unread(name):
    """
    Mark a notification as unread.

    Args:
        name: Notification name

    Returns:
        dict: {success: True}
    """
    if not frappe.db.exists("Orga Notification", name):
        frappe.throw(_("Notification not found"))

    notification = frappe.get_doc("Orga Notification", name)

    # Permission check
    if notification.recipient != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    notification.is_read = 0
    notification.read_at = None
    notification.save(ignore_permissions=True)

    return {"success": True}


@frappe.whitelist()
def mark_all_as_read():
    """
    Mark all notifications as read for current user.

    Returns:
        dict: {success: True, count: int}
    """
    count = frappe.db.sql("""
        UPDATE `tabOrga Notification`
        SET is_read = 1, read_at = %s
        WHERE recipient = %s AND is_read = 0
    """, (now_datetime(), frappe.session.user))

    frappe.db.commit()

    return {"success": True, "count": frappe.db.rowcount or 0}


@frappe.whitelist()
def delete_notification(name):
    """
    Delete a notification.

    Args:
        name: Notification name

    Returns:
        dict: {success: True}
    """
    if not frappe.db.exists("Orga Notification", name):
        frappe.throw(_("Notification not found"))

    notification = frappe.get_doc("Orga Notification", name)

    # Permission check
    if notification.recipient != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    notification.delete()

    return {"success": True}


@frappe.whitelist()
def delete_all_read():
    """
    Delete all read notifications for current user.

    Returns:
        dict: {success: True, count: int}
    """
    notifications = frappe.get_all(
        "Orga Notification",
        filters={"recipient": frappe.session.user, "is_read": 1},
        pluck="name"
    )

    for name in notifications:
        frappe.delete_doc("Orga Notification", name, ignore_permissions=True)

    return {"success": True, "count": len(notifications)}


@frappe.whitelist()
def get_notification(name):
    """
    Get a single notification.

    Args:
        name: Notification name

    Returns:
        dict: Notification data
    """
    if not frappe.db.exists("Orga Notification", name):
        frappe.throw(_("Notification not found"))

    notification = frappe.get_doc("Orga Notification", name)

    # Permission check
    if notification.recipient != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    result = notification.as_dict()

    # Add sender name
    if notification.from_user:
        result["from_user_name"] = frappe.db.get_value("User", notification.from_user, "full_name")
    else:
        result["from_user_name"] = "System"

    return result


# ============================================
# Internal API for creating notifications
# ============================================

@frappe.whitelist(allow_guest=False)
def create_notification(
    notification_type,
    subject,
    recipient,
    message=None,
    reference_doctype=None,
    reference_name=None
):
    """
    Create a new notification (internal API).

    Args:
        notification_type: Type of notification
        subject: Notification subject
        recipient: User to notify
        message: Optional message body
        reference_doctype: Related DocType
        reference_name: Related document name

    Returns:
        dict: {name: notification name}
    """
    # Import from controller to use the utility function
    from orga.orga.doctype.orga_notification.orga_notification import create_notification as _create

    notification = _create(
        notification_type=notification_type,
        subject=subject,
        recipient=recipient,
        message=message,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        from_user=frappe.session.user
    )

    return {"name": notification.name}
