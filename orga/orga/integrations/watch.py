# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Watch integration — keeps Orga Task.actual_hours in sync with Watch Entry.

Registered via doc_events in hooks.py. Only fires when Watch is installed
and the Watch Entry has an orga_task custom field set.
"""

import frappe


def on_watch_entry_update(doc, method):
    _update_task_actual_hours(doc)


def on_watch_entry_delete(doc, method):
    _update_task_actual_hours(doc)


def _update_task_actual_hours(doc):
    """Recalculate actual_hours on Orga Task when a linked Watch Entry changes."""
    task = doc.get("orga_task")
    if not task:
        return
    if not frappe.db.exists("Orga Task", task):
        return

    total = frappe.db.sql(
        """SELECT COALESCE(SUM(duration_hours), 0)
           FROM `tabWatch Entry`
           WHERE orga_task = %s AND is_running = 0""",
        task,
    )[0][0]
    frappe.db.set_value("Orga Task", task, "actual_hours", total)
