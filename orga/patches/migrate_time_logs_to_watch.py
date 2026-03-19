# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Migrate Orga Time Log records to Watch Entry.

Run: bench --site <site> run-patch orga.patches.migrate_time_logs_to_watch

Safe to run multiple times — skips records where migrated_to_watch=1.
Requires Watch to be installed and Orga context custom fields to exist.
"""

import frappe
from frappe.utils import cint


def execute():
    if "watch" not in frappe.get_installed_apps():
        print("Watch app not installed — skipping migration.")
        return

    if not frappe.db.exists("DocType", "Orga Time Log"):
        print("Orga Time Log DocType not found — nothing to migrate.")
        return

    # Add tracking column if missing
    if not frappe.db.has_column("Orga Time Log", "migrated_to_watch"):
        frappe.db.sql_ddl(
            "ALTER TABLE `tabOrga Time Log` ADD COLUMN `migrated_to_watch` INT(1) NOT NULL DEFAULT 0"
        )

    # Ensure custom fields exist
    from orga.install import setup_watch_custom_fields
    setup_watch_custom_fields()

    logs = frappe.get_all(
        "Orga Time Log",
        filters={"migrated_to_watch": 0},
        fields=["*"],
        order_by="log_date asc",
        limit_page_length=0,
    )

    if not logs:
        print("No Orga Time Log records to migrate.")
        return

    migrated = 0
    skipped = 0

    for log in logs:
        try:
            entry = frappe.new_doc("Watch Entry")
            entry.date = log.log_date
            entry.user = log.user
            entry.start_time = log.from_time
            entry.end_time = log.to_time
            entry.duration_hours = log.hours or 0
            entry.description = log.description
            entry.is_running = cint(log.is_running)
            entry.timer_started_at = log.timer_started_at
            entry.entry_type = "billable" if cint(log.billable) else "non-billable"
            entry.entry_status = "draft"

            # Orga context fields (custom fields on Watch Entry)
            entry.orga_tracking_context = log.tracking_context
            entry.orga_task = log.task
            entry.orga_event = log.event
            entry.orga_project = log.project

            # ERPNext link
            if log.erpnext_timesheet:
                entry.erpnext_timesheet = str(log.erpnext_timesheet)
                entry.erpnext_synced = 1

            entry.insert(ignore_permissions=True)

            frappe.db.set_value(
                "Orga Time Log", log.name,
                "migrated_to_watch", 1,
                update_modified=False,
            )

            migrated += 1
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Failed to migrate Orga Time Log {log.name}"
            )
            skipped += 1

    frappe.db.commit()
    print(f"Migrated {migrated} time logs to Watch Entry. Skipped {skipped}.")
