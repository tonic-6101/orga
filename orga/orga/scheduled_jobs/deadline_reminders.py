# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Scheduled job for deadline reminder notifications.

Runs daily to check for tasks with upcoming deadlines and sends reminder
notifications to assigned users or task owners.
"""

import frappe
from frappe import _
from frappe.utils import add_days, today, getdate


def send_deadline_reminders():
    """
    Check for tasks with upcoming deadlines and send reminders.

    Runs daily. Sends reminders for:
    - Tasks due today (0 days)
    - Tasks due tomorrow (1 day)
    - Tasks due in 3 days (configurable)

    Skips tasks that are already completed or cancelled.
    """
    from orga.orga.doctype.orga_notification.orga_notification import notify_deadline

    # Default reminder days: today, tomorrow, 3 days out
    reminder_days = [0, 1, 3]

    # Check if custom reminder days are configured in settings
    if frappe.db.exists("DocType", "Orga Settings"):
        settings = frappe.get_single("Orga Settings")
        if hasattr(settings, "deadline_reminder_days") and settings.deadline_reminder_days:
            try:
                reminder_days = [int(d.strip()) for d in settings.deadline_reminder_days.split(",")]
            except (ValueError, AttributeError):
                pass  # Use defaults

    for days in reminder_days:
        target_date = add_days(today(), days)

        # Find tasks due on target date that aren't complete
        tasks = frappe.get_all(
            "Orga Task",
            filters={
                "due_date": target_date,
                "status": ["not in", ["Completed", "Cancelled"]]
            },
            fields=["name", "subject", "due_date", "assigned_to", "owner", "project"]
        )

        for task_data in tasks:
            # Check if we've already sent a reminder for this task today
            existing_reminder = frappe.db.exists(
                "Orga Notification",
                {
                    "notification_type": "Deadline",
                    "reference_doctype": "Orga Task",
                    "reference_name": task_data.name,
                    "creation": [">=", today()]
                }
            )

            if existing_reminder:
                continue  # Skip, already notified today

            # Create a minimal task object for the notification function
            class TaskProxy:
                def __init__(self, data):
                    self.name = data.name
                    self.subject = data.subject
                    self.due_date = data.due_date
                    self.assigned_to = data.assigned_to
                    self.owner = data.owner
                    self.project = data.project

            task = TaskProxy(task_data)
            notify_deadline(task, days)

    frappe.db.commit()


def cleanup_old_notifications():
    """
    Remove old read notifications to keep the database clean.

    Runs weekly. Deletes notifications that:
    - Are older than 30 days
    - Have been read

    Keeps unread notifications regardless of age.
    """
    from frappe.utils import add_days, today

    cutoff_date = add_days(today(), -30)

    old_notifications = frappe.get_all(
        "Orga Notification",
        filters={
            "is_read": 1,
            "creation": ["<", cutoff_date]
        },
        pluck="name"
    )

    for name in old_notifications:
        try:
            frappe.delete_doc("Orga Notification", name, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to clean notification {name}: {e}", "Orga Notification Cleanup")

    frappe.db.commit()

    if old_notifications:
        frappe.log_error(
            title="Notification Cleanup",
            message=f"Deleted {len(old_notifications)} old notifications"
        )
