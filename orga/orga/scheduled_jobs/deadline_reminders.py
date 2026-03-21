# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Scheduled job for deadline reminder notifications.

Runs daily to check for tasks and milestones with upcoming deadlines and
publishes notifications to Dock's bell icon.
"""

import frappe
from frappe import _
from frappe.utils import add_days, today


def send_deadline_reminders():
    """
    Check for tasks and milestones with upcoming deadlines and send reminders.

    Runs daily. Sends reminders for:
    - Tasks due today (0 days)
    - Tasks due tomorrow (1 day)
    - Tasks due in 3 days (configurable)

    Skips tasks that are already completed or cancelled.
    Publishes to Dock bell icon via dock.api.notifications.publish().
    """
    from orga.orga.integrations.dock_notification import publish, _dock_installed

    if not _dock_installed():
        return

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

        # --- Task deadline reminders ---
        tasks = frappe.get_all(
            "Orga Task",
            filters={
                "due_date": target_date,
                "status": ["not in", ["Completed", "Cancelled"]]
            },
            fields=["name", "subject", "due_date", "assigned_to", "owner", "project"]
        )

        for task_data in tasks:
            # Deduplicate: check if Dock already has a reminder for this task today
            existing = frappe.db.exists(
                "Dock Notification",
                {
                    "notification_type": "deadline_reminder",
                    "reference_doctype": "Orga Task",
                    "reference_name": task_data.name,
                    "creation": [">=", today()],
                },
            )
            if existing:
                continue

            recipient = task_data.assigned_to or task_data.owner
            if not recipient:
                continue

            if days == 0:
                subject = _("Task due today: {0}").format(task_data.subject)
            elif days == 1:
                subject = _("Task due tomorrow: {0}").format(task_data.subject)
            else:
                subject = _("Task due in {0} days: {1}").format(days, task_data.subject)

            publish(
                notification_type="deadline_reminder",
                title=subject,
                for_user=recipient,
                message=_("Task '{0}' is due on {1}.").format(task_data.subject, task_data.due_date),
                reference_doctype="Orga Task",
                reference_name=task_data.name,
            )

        # --- Milestone deadline reminders ---
        milestones = frappe.get_all(
            "Orga Milestone",
            filters={
                "due_date": target_date,
                "status": ["not in", ["Completed", "Cancelled"]],
            },
            fields=["name", "milestone_name", "due_date", "project", "owner"],
        )

        for ms in milestones:
            existing = frappe.db.exists(
                "Dock Notification",
                {
                    "notification_type": "milestone_due",
                    "reference_doctype": "Orga Milestone",
                    "reference_name": ms.name,
                    "creation": [">=", today()],
                },
            )
            if existing:
                continue

            project_owner = (
                frappe.db.get_value("Orga Project", ms.project, "owner")
                if ms.project
                else None
            )
            recipient = project_owner or ms.owner
            if not recipient:
                continue

            if days == 0:
                subject = _("Milestone due today: {0}").format(ms.milestone_name)
            elif days == 1:
                subject = _("Milestone due tomorrow: {0}").format(ms.milestone_name)
            else:
                subject = _("Milestone due in {0} days: {1}").format(days, ms.milestone_name)

            publish(
                notification_type="milestone_due",
                title=subject,
                for_user=recipient,
                message=_("Milestone '{0}' is due on {1}.").format(ms.milestone_name, ms.due_date),
                reference_doctype="Orga Milestone",
                reference_name=ms.name,
            )

    frappe.db.commit()
