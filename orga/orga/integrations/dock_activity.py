# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic
#
# Custom activity renderers for Dock Activity Feed (#40).
# Registered via dock_activity_renderers hook in hooks.py.
# Each renderer receives a Version doc and returns a rich summary dict.

import frappe


def render_task(version_doc, comment_doc=None):
    """Custom renderer for Orga Task activity."""
    try:
        task = frappe.get_doc("Orga Task", version_doc.docname)
        project_name = ""
        if task.project:
            project_name = frappe.db.get_value(
                "Orga Project", task.project, "project_name"
            ) or task.project

        return {
            "summary": f"{frappe.utils.get_fullname(version_doc.owner)} updated task: {task.subject}",
            "detail": f"Status: {task.status}" + (f" | Priority: {task.priority}" if task.priority else ""),
            "badges": _get_priority_badge(task.get("priority")),
            "context": {
                "project": project_name,
                "project_route": f"/orga/projects/{task.project}" if task.project else None,
            },
        }
    except Exception:
        return None


def render_appointment(version_doc, comment_doc=None):
    """Custom renderer for Orga Appointment activity."""
    try:
        appt = frappe.get_doc("Orga Appointment", version_doc.docname)
        return {
            "summary": f"{frappe.utils.get_fullname(version_doc.owner)} updated appointment: {appt.subject}",
            "detail": f"Type: {appt.appointment_type}" if appt.get("appointment_type") else "",
            "badges": [],
            "context": {
                "event_type": appt.get("appointment_type"),
            },
        }
    except Exception:
        return None


def render_milestone(version_doc, comment_doc=None):
    """Custom renderer for Orga Milestone activity."""
    try:
        ms = frappe.get_doc("Orga Milestone", version_doc.docname)
        project_name = ""
        if ms.project:
            project_name = frappe.db.get_value(
                "Orga Project", ms.project, "project_name"
            ) or ms.project

        return {
            "summary": f"{frappe.utils.get_fullname(version_doc.owner)} updated milestone: {ms.milestone_name}",
            "detail": f"Status: {ms.status}" + (f" | Progress: {ms.progress}%" if ms.get("progress") else ""),
            "badges": [],
            "context": {
                "project": project_name,
                "project_route": f"/orga/projects/{ms.project}" if ms.project else None,
            },
        }
    except Exception:
        return None


def _get_priority_badge(priority):
    """Return a badge list based on task priority."""
    if not priority:
        return []
    colors = {
        "Urgent": "red",
        "High": "orange",
        "Medium": "yellow",
        "Low": "gray",
    }
    color = colors.get(priority, "gray")
    return [{"label": priority, "color": color}]
