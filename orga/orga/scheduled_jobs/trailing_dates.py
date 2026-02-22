# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.utils import nowdate, getdate, add_days


def update_trailing_start_dates():
    """Daily job: trail start_date for Open tasks with auto_trail_start enabled.

    For each qualifying task whose start_date has fallen into the past,
    shift both start_date and due_date forward to today while preserving
    the original task duration.
    """
    today = nowdate()

    try:
        has_col = frappe.db.has_column("Orga Task", "auto_trail_start")
    except Exception:
        has_col = False
    if not has_col:
        return

    tasks = frappe.get_all(
        "Orga Task",
        filters={
            "auto_trail_start": 1,
            "status": "Open",
            "progress": 0,
            "start_date": ["<", today],
        },
        fields=["name", "start_date", "due_date"],
    )

    for task in tasks:
        old_start = getdate(task.start_date)
        shift = (getdate(today) - old_start).days
        frappe.db.set_value(
            "Orga Task", task.name, "start_date", today, update_modified=True
        )
        if task.due_date:
            new_due = add_days(task.due_date, shift)
            frappe.db.set_value(
                "Orga Task", task.name, "due_date", str(new_due), update_modified=True
            )

    if tasks:
        frappe.db.commit()
