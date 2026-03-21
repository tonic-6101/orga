# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Settings API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.settings.get_settings'
    })
"""

import json
import frappe
from frappe import _


@frappe.whitelist()
def get_settings():
    """
    Get Orga Settings.

    Returns:
        dict: Settings document fields
    """
    settings = frappe.get_single("Orga Settings")
    return settings.as_dict()


@frappe.whitelist()
def update_settings(data):
    """
    Update Orga Settings.

    Args:
        data: dict or JSON string with settings fields

    Returns:
        dict: Updated settings
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Check permission
    if not frappe.has_permission("Orga Settings", "write"):
        frappe.throw(_("Not permitted to update settings"), frappe.PermissionError)

    settings = frappe.get_single("Orga Settings")

    # Allowed fields that can be updated via the standard Document.save() path
    allowed_fields = [
        "default_task_status",
        "default_project_status",
        "project_code_prefix",
        "default_priority",
        "auto_calculate_progress",
        "auto_set_missed_milestones",
        "enable_time_tracking",
        "default_capacity_hours",
        "notify_on_task_assignment",
        "notify_on_status_change",
        "notify_on_due_date",
        "due_date_reminder_days"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(settings, field, value)

    settings.save()
    frappe.db.commit()

    return settings.as_dict()


@frappe.whitelist()
def get_update_info():
    """
    Get cached version update information.

    Returns:
        dict: Update info including current_version, latest_version,
              update_available, release_url, release_notes, checked_at.
              Returns empty dict if no data available.
    """
    from orga.orga.services.version_checker import check_for_updates

    result = check_for_updates(force=False)
    return result or {}


@frappe.whitelist()
def check_updates_now():
    """
    Force a fresh check for updates (bypasses cache).

    Only Orga Manager and System Manager can trigger this.

    Returns:
        dict: Fresh update info
    """
    if not (frappe.has_permission("Orga Settings", "write")
            or "System Manager" in frappe.get_roles()):
        frappe.throw(_("Not permitted to check for updates"), frappe.PermissionError)

    from orga.orga.services.version_checker import check_for_updates

    result = check_for_updates(force=True)
    return result or {}
