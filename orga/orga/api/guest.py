# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Guest Portal API Module

Provides read-only project data for the Dock Guest Portal.
All endpoints use allow_guest=True and validate the Dock guest token.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today, date_diff


def _validate_guest_token(token: str) -> dict:
    """
    Validate a Dock guest token and return the session data.

    Args:
        token: The guest session token (dgs_* prefix)

    Returns:
        dict with session data if valid

    Raises:
        frappe.PermissionError if token is invalid, expired, or revoked
    """
    if not token or not isinstance(token, str):
        frappe.throw(_("Invalid guest token"), frappe.PermissionError)

    if "dock" not in frappe.get_installed_apps():
        frappe.throw(_("Guest portal is not available"), frappe.PermissionError)

    from dock.api.guest import validate_token
    result = validate_token(token)

    if not result.get("valid"):
        reason = result.get("reason", "not_found")
        if reason == "expired":
            frappe.throw(_("This link has expired"), frappe.PermissionError)
        elif reason == "revoked":
            frappe.throw(_("This link has been deactivated"), frappe.PermissionError)
        else:
            frappe.throw(_("Invalid guest link"), frappe.PermissionError)

    return result


@frappe.whitelist(allow_guest=True)
def get_project_status(project_name: str, token: str) -> dict:
    """
    Get read-only project status for the Dock Guest Portal.

    Validates the guest token, then returns a curated subset of project data:
    progress, status, milestones, task summary. No internal details exposed.

    Args:
        project_name: Orga Project document name
        token: Dock guest session token

    Returns:
        dict with project status data for guest view
    """
    session = _validate_guest_token(token)

    # Verify the token is for this specific project
    if session.get("source_doctype") != "Orga Project" or session.get("source_name") != project_name:
        frappe.throw(_("Access denied"), frappe.PermissionError)

    # Get project (limited fields only — no budget, no internal notes)
    project = frappe.db.get_value(
        "Orga Project",
        project_name,
        [
            "name", "project_name", "status", "progress",
            "start_date", "end_date", "health_status", "description",
        ],
        as_dict=True,
    )

    if not project:
        frappe.throw(_("Project not found"), frappe.DoesNotExistError)

    # Days remaining / overdue
    if project.end_date:
        days = date_diff(project.end_date, today())
        project["days_remaining"] = days if days >= 0 else 0
        project["days_overdue"] = abs(days) if days < 0 else 0
    else:
        project["days_remaining"] = None
        project["days_overdue"] = None

    # Task summary (counts only — no individual task details)
    task_rows = frappe.db.sql(
        """
        SELECT status, COUNT(*) as count
        FROM `tabOrga Task`
        WHERE project = %s
        GROUP BY status
        """,
        project_name,
        as_dict=True,
    )
    task_summary = {"Open": 0, "In Progress": 0, "Review": 0, "Completed": 0, "total": 0}
    for row in task_rows:
        task_summary[row.status] = row.count
        task_summary["total"] += row.count

    # Milestones (name, status, due date — no internal descriptions)
    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": project_name},
        fields=["milestone_name", "status", "due_date", "completion_date"],
        order_by="due_date asc",
    )
    for m in milestones:
        m["is_overdue"] = (
            m.status != "Completed"
            and m.due_date
            and getdate(m.due_date) < getdate(today())
        )

    # Recent completions (last 5 completed tasks — subject only)
    recent_completions = frappe.get_all(
        "Orga Task",
        filters={"project": project_name, "status": "Completed"},
        fields=["subject", "modified"],
        order_by="modified desc",
        limit=5,
    )

    return {
        "project": {
            "name": project.name,
            "project_name": project.project_name,
            "status": project.status,
            "progress": project.progress or 0,
            "health_status": project.health_status,
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None,
            "days_remaining": project.get("days_remaining"),
            "days_overdue": project.get("days_overdue"),
        },
        "task_summary": task_summary,
        "milestones": milestones,
        "recent_completions": recent_completions,
    }
