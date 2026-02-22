# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Dashboard API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.dashboard.get_stats'
    })
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, add_days, get_first_day, get_last_day


@frappe.whitelist()
def get_stats():
    """
    Get dashboard statistics.

    Returns:
        dict: Dashboard stats for projects, tasks, and milestones
    """
    today = getdate(nowdate())
    week_ago = add_days(today, -7)
    week_ahead = add_days(today, 7)

    # Project counts
    total_projects = frappe.db.count("Orga Project")
    projects_by_status = {
        "planning": frappe.db.count("Orga Project", {"status": "Planning"}),
        "active": frappe.db.count("Orga Project", {"status": "Active"}),
        "on_hold": frappe.db.count("Orga Project", {"status": "On Hold"}),
        "completed": frappe.db.count("Orga Project", {"status": "Completed"}),
        "cancelled": frappe.db.count("Orga Project", {"status": "Cancelled"}),
    }

    # Task counts
    total_tasks = frappe.db.count("Orga Task")
    tasks_by_status = {
        "open": frappe.db.count("Orga Task", {"status": "Open"}),
        "in_progress": frappe.db.count("Orga Task", {"status": "In Progress"}),
        "review": frappe.db.count("Orga Task", {"status": "Review"}),
        "completed": frappe.db.count("Orga Task", {"status": "Completed"}),
        "cancelled": frappe.db.count("Orga Task", {"status": "Cancelled"}),
    }

    # Tasks by priority
    tasks_by_priority = {
        "urgent": frappe.db.count("Orga Task", {
            "priority": "Urgent",
            "status": ["not in", ["Completed", "Cancelled"]]
        }),
        "high": frappe.db.count("Orga Task", {
            "priority": "High",
            "status": ["not in", ["Completed", "Cancelled"]]
        }),
        "medium": frappe.db.count("Orga Task", {
            "priority": "Medium",
            "status": ["not in", ["Completed", "Cancelled"]]
        }),
        "low": frappe.db.count("Orga Task", {
            "priority": "Low",
            "status": ["not in", ["Completed", "Cancelled"]]
        }),
    }

    # Overdue tasks
    overdue_tasks = frappe.db.count(
        "Orga Task",
        {
            "status": ["not in", ["Completed", "Cancelled"]],
            "due_date": ["<", today]
        }
    )

    # Tasks due this week
    tasks_due_week = frappe.db.count(
        "Orga Task",
        {
            "status": ["not in", ["Completed", "Cancelled"]],
            "due_date": ["between", [today, week_ahead]]
        }
    )

    # Completed this week
    completed_this_week = frappe.db.count(
        "Orga Task",
        {
            "status": "Completed",
            "completed_date": [">=", week_ago]
        }
    )

    # Milestones
    total_milestones = frappe.db.count("Orga Milestone")
    milestones_by_status = {
        "upcoming": frappe.db.count("Orga Milestone", {"status": "Upcoming"}),
        "in_progress": frappe.db.count("Orga Milestone", {"status": "In Progress"}),
        "completed": frappe.db.count("Orga Milestone", {"status": "Completed"}),
        "missed": frappe.db.count("Orga Milestone", {"status": "Missed"}),
    }

    # Upcoming milestones (next 14 days)
    upcoming_milestones = frappe.db.count(
        "Orga Milestone",
        {
            "status": ["in", ["Upcoming", "In Progress"]],
            "due_date": ["between", [today, add_days(today, 14)]]
        }
    )

    return {
        "projects": {
            "total": total_projects,
            "by_status": projects_by_status
        },
        "tasks": {
            "total": total_tasks,
            "by_status": tasks_by_status,
            "by_priority": tasks_by_priority,
            "overdue": overdue_tasks,
            "due_this_week": tasks_due_week,
            "completed_this_week": completed_this_week
        },
        "milestones": {
            "total": total_milestones,
            "by_status": milestones_by_status,
            "upcoming": upcoming_milestones
        }
    }


@frappe.whitelist()
def get_recent_activity(limit=20):
    """
    Get recent activity across projects.

    Args:
        limit: Maximum items to return (default 20)

    Returns:
        list: Recent activity items
    """
    activity = []

    # Get recent task updates
    tasks = frappe.get_all(
        "Orga Task",
        fields=["name", "subject", "status", "project", "modified", "modified_by"],
        order_by="modified desc",
        limit_page_length=int(limit)
    )

    for task in tasks:
        project_name = None
        if task.project:
            project_name = frappe.db.get_value("Orga Project", task.project, "project_name")

        user_info = frappe.db.get_value("User", task.modified_by, ["full_name", "user_image"], as_dict=True) or {}

        # Get comment count for this task
        comment_count = _get_activity_comment_count("Orga Task", task.name)

        # Get reaction data for this task
        reaction_data = _get_activity_reaction_summary("Orga Task", task.name)

        activity.append({
            "type": "task",
            "action": "updated",
            "name": task.name,
            "title": task.subject,
            "status": task.status,
            "project": task.project,
            "project_name": project_name,
            "timestamp": task.modified,
            "user": task.modified_by,
            "user_name": user_info.get("full_name"),
            "user_image": user_info.get("user_image"),
            "reference_doctype": "Orga Task",
            "reference_name": task.name,
            "comment_count": comment_count,
            "reaction_counts": reaction_data.get("counts", {}),
            "user_reactions": reaction_data.get("user_reactions", [])
        })

    # Get recent milestone updates
    milestones = frappe.get_all(
        "Orga Milestone",
        fields=["name", "milestone_name", "status", "project", "modified", "modified_by"],
        order_by="modified desc",
        limit_page_length=int(limit) // 2
    )

    for ms in milestones:
        project_name = None
        if ms.project:
            project_name = frappe.db.get_value("Orga Project", ms.project, "project_name")

        user_info = frappe.db.get_value("User", ms.modified_by, ["full_name", "user_image"], as_dict=True) or {}

        # Get comment count for this milestone
        comment_count = _get_activity_comment_count("Orga Milestone", ms.name)

        # Get reaction data for this milestone
        reaction_data = _get_activity_reaction_summary("Orga Milestone", ms.name)

        activity.append({
            "type": "milestone",
            "action": "updated",
            "name": ms.name,
            "title": ms.milestone_name,
            "status": ms.status,
            "project": ms.project,
            "project_name": project_name,
            "timestamp": ms.modified,
            "user": ms.modified_by,
            "user_name": user_info.get("full_name"),
            "user_image": user_info.get("user_image"),
            "reference_doctype": "Orga Milestone",
            "reference_name": ms.name,
            "comment_count": comment_count,
            "reaction_counts": reaction_data.get("counts", {}),
            "user_reactions": reaction_data.get("user_reactions", [])
        })

    # Get recent appointment updates
    appointments = frappe.get_all(
        "Orga Appointment",
        fields=["name", "title", "event_type", "status", "project", "start_datetime", "end_datetime", "location", "modified", "modified_by", "creation"],
        order_by="modified desc",
        limit_page_length=int(limit) // 2
    )

    for appt in appointments:
        project_name = None
        if appt.project:
            project_name = frappe.db.get_value("Orga Project", appt.project, "project_name")

        user_info = frappe.db.get_value("User", appt.modified_by, ["full_name", "user_image"], as_dict=True) or {}

        # Determine action based on timing
        action = "updated"
        if appt.creation and appt.modified:
            # If created within last few seconds of modified, it's a new appointment
            from frappe.utils import time_diff_in_seconds, get_datetime
            diff = time_diff_in_seconds(appt.modified, appt.creation)
            if diff < 5:
                action = "created"

        # Get comment count for this appointment
        comment_count = _get_activity_comment_count("Orga Appointment", appt.name)

        # Get reaction data for this appointment
        reaction_data = _get_activity_reaction_summary("Orga Appointment", appt.name)

        # Get RSVP info for this appointment
        rsvp_info = _get_appointment_rsvp_info(appt.name)

        activity.append({
            "type": "appointment",
            "action": action,
            "name": appt.name,
            "title": appt.title,
            "status": appt.status or appt.event_type,
            "project": appt.project,
            "project_name": project_name,
            "timestamp": appt.modified,
            "user": appt.modified_by,
            "user_name": user_info.get("full_name"),
            "user_image": user_info.get("user_image"),
            "reference_doctype": "Orga Appointment",
            "reference_name": appt.name,
            "event_type": appt.event_type,
            "start_datetime": str(appt.start_datetime) if appt.start_datetime else None,
            "end_datetime": str(appt.end_datetime) if appt.end_datetime else None,
            "location": appt.location,
            "comment_count": comment_count,
            "reaction_counts": reaction_data.get("counts", {}),
            "user_reactions": reaction_data.get("user_reactions", []),
            # RSVP info
            "is_attendee": rsvp_info.get("is_attendee", False),
            "user_rsvp_status": rsvp_info.get("user_rsvp_status"),
            "attendee_stats": rsvp_info.get("attendee_stats", {}),
            "attendees": rsvp_info.get("attendees", [])
        })

    # Get system events (project deletions, etc.)
    if frappe.db.exists("DocType", "Orga Activity Comment"):
        system_comments = frappe.get_all(
            "Orga Activity Comment",
            filters={"note_type": "System"},
            fields=["name", "reference_doctype", "reference_name", "content", "user", "creation"],
            order_by="creation desc",
            limit_page_length=int(limit) // 2
        )

        for sc in system_comments:
            user_info = frappe.db.get_value(
                "User", sc.user, ["full_name", "user_image"], as_dict=True
            ) or {}

            # Determine type from reference_doctype
            event_type = "project" if sc.reference_doctype == "Orga Project" else "task"

            activity.append({
                "type": event_type,
                "action": "deleted",
                "name": sc.name,
                "title": sc.content,
                "status": "Deleted",
                "project": None,
                "project_name": None,
                "timestamp": sc.creation,
                "user": sc.user,
                "user_name": user_info.get("full_name"),
                "user_image": user_info.get("user_image"),
                "comment_count": 0,
                "reaction_counts": {},
                "user_reactions": [],
                "is_system_event": True,
                "reference_doctype": sc.reference_doctype,
                "reference_name": sc.reference_name
            })

    # Sort by timestamp and limit
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    return activity[:int(limit)]


@frappe.whitelist()
def get_activity_since(since_timestamp: str, limit: int = 20) -> dict:
    """
    Return activities newer than since_timestamp. Lightweight delta fetch
    for live polling on the Activity page.

    Args:
        since_timestamp: ISO timestamp string — only return items modified after this
        limit: Maximum items to return (default 20)

    Returns:
        dict: { items: [...], count: int, latest_timestamp: str }
    """
    from frappe.utils import get_datetime

    since_dt = get_datetime(since_timestamp)
    limit = int(limit)
    items = []

    # --- Batch-fetch recent tasks ---
    tasks = frappe.get_all(
        "Orga Task",
        filters={"modified": [">", since_dt]},
        fields=["name", "subject", "status", "project", "modified", "modified_by"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for t in tasks:
        items.append({
            "type": "task",
            "action": "updated",
            "name": t.name,
            "title": t.subject,
            "status": t.status,
            "project": t.project,
            "timestamp": t.modified,
            "user": t.modified_by,
            "reference_doctype": "Orga Task",
            "reference_name": t.name,
        })

    # --- Batch-fetch recent milestones ---
    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"modified": [">", since_dt]},
        fields=["name", "milestone_name", "status", "project", "modified", "modified_by"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for ms in milestones:
        items.append({
            "type": "milestone",
            "action": "updated",
            "name": ms.name,
            "title": ms.milestone_name,
            "status": ms.status,
            "project": ms.project,
            "timestamp": ms.modified,
            "user": ms.modified_by,
            "reference_doctype": "Orga Milestone",
            "reference_name": ms.name,
        })

    # --- Batch-fetch recent appointments ---
    appointments = frappe.get_all(
        "Orga Appointment",
        filters={"modified": [">", since_dt]},
        fields=["name", "title", "event_type", "status", "project",
                "start_datetime", "end_datetime", "location",
                "modified", "modified_by", "creation"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for appt in appointments:
        action = "updated"
        if appt.creation and appt.modified:
            from frappe.utils import time_diff_in_seconds
            if time_diff_in_seconds(appt.modified, appt.creation) < 5:
                action = "created"

        items.append({
            "type": "appointment",
            "action": action,
            "name": appt.name,
            "title": appt.title,
            "status": appt.status or appt.event_type,
            "project": appt.project,
            "timestamp": appt.modified,
            "user": appt.modified_by,
            "reference_doctype": "Orga Appointment",
            "reference_name": appt.name,
            "event_type": appt.event_type,
            "start_datetime": str(appt.start_datetime) if appt.start_datetime else None,
            "end_datetime": str(appt.end_datetime) if appt.end_datetime else None,
            "location": appt.location,
        })

    # Sort all items together and cap at limit
    items.sort(key=lambda x: x["timestamp"], reverse=True)
    items = items[:limit]

    if not items:
        return {"items": [], "count": 0, "latest_timestamp": since_timestamp}

    # --- Batch user-info loading (single query for all unique users) ---
    unique_users = list({i["user"] for i in items if i.get("user")})
    user_info_map: dict = {}
    if unique_users:
        user_rows = frappe.get_all(
            "User",
            filters={"name": ["in", unique_users]},
            fields=["name", "full_name", "user_image"],
        )
        user_info_map = {u["name"]: u for u in user_rows}

    # --- Batch project-name loading ---
    unique_projects = list({i["project"] for i in items if i.get("project")})
    project_name_map: dict = {}
    if unique_projects:
        project_rows = frappe.get_all(
            "Orga Project",
            filters={"name": ["in", unique_projects]},
            fields=["name", "project_name"],
        )
        project_name_map = {p["name"]: p["project_name"] for p in project_rows}

    # Enrich items
    for item in items:
        ui = user_info_map.get(item.get("user"), {})
        item["user_name"] = ui.get("full_name")
        item["user_image"] = ui.get("user_image")
        item["project_name"] = project_name_map.get(item.get("project"))
        # Defaults for fields the full endpoint provides
        item.setdefault("comment_count", 0)
        item.setdefault("reaction_counts", {})
        item.setdefault("user_reactions", [])

    latest_ts = str(items[0]["timestamp"]) if items else since_timestamp

    return {
        "items": items,
        "count": len(items),
        "latest_timestamp": latest_ts,
    }


@frappe.whitelist()
def get_my_tasks(status=None, limit=10):
    """
    Get tasks assigned to current user.

    Args:
        status: Optional status filter
        limit: Maximum items (default 10)

    Returns:
        list: User's tasks
    """
    user = frappe.session.user

    filters = {"assigned_to": user}

    if status:
        filters["status"] = status
    else:
        filters["status"] = ["not in", ["Completed", "Cancelled"]]

    tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=[
            "name", "subject", "status", "priority",
            "due_date", "project", "progress"
        ],
        order_by="due_date asc, priority desc",
        limit_page_length=int(limit)
    )

    # Enrich with project names
    for task in tasks:
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )

        # Check if overdue
        if task.get("due_date"):
            task["is_overdue"] = getdate(task["due_date"]) < getdate(nowdate())
        else:
            task["is_overdue"] = False

    return tasks


@frappe.whitelist()
def get_overdue_tasks(limit=20):
    """
    Get overdue tasks.

    Args:
        limit: Maximum items (default 20)

    Returns:
        list: Overdue tasks
    """
    today = getdate(nowdate())

    tasks = frappe.get_all(
        "Orga Task",
        filters={
            "status": ["not in", ["Completed", "Cancelled"]],
            "due_date": ["<", today]
        },
        fields=[
            "name", "subject", "status", "priority",
            "due_date", "project", "assigned_to"
        ],
        order_by="due_date asc",
        limit_page_length=int(limit)
    )

    # Enrich with names and days overdue
    for task in tasks:
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )
        if task.get("assigned_to"):
            task["assigned_to_name"] = frappe.db.get_value(
                "User", task["assigned_to"], "full_name"
            )

        # Calculate days overdue
        task["days_overdue"] = (today - getdate(task["due_date"])).days

    return tasks


@frappe.whitelist()
def get_upcoming_milestones(days=14, limit=10):
    """
    Get upcoming milestones.

    Args:
        days: Number of days to look ahead (default 14)
        limit: Maximum items (default 10)

    Returns:
        list: Upcoming milestones
    """
    today = getdate(nowdate())
    end_date = add_days(today, int(days))

    milestones = frappe.get_all(
        "Orga Milestone",
        filters={
            "status": ["in", ["Upcoming", "In Progress"]],
            "due_date": ["between", [today, end_date]]
        },
        fields=[
            "name", "milestone_name", "status",
            "due_date", "project"
        ],
        order_by="due_date asc",
        limit_page_length=int(limit)
    )

    # Enrich with project names and days until due
    for ms in milestones:
        if ms.get("project"):
            ms["project_name"] = frappe.db.get_value(
                "Orga Project", ms["project"], "project_name"
            )

        # Calculate days until due
        ms["days_until_due"] = (getdate(ms["due_date"]) - today).days

    return milestones


@frappe.whitelist()
def get_project_summary():
    """
    Get summary of all projects with progress.

    Returns:
        list: Projects with stats
    """
    projects = frappe.get_all(
        "Orga Project",
        filters={"status": ["in", ["Planning", "Active", "On Hold"]]},
        fields=[
            "name", "project_name", "project_code", "status",
            "progress", "health_status", "start_date", "end_date",
            "project_manager"
        ],
        order_by="status asc, end_date asc"
    )

    today = getdate(nowdate())

    for project in projects:
        # Get task counts
        project["task_count"] = frappe.db.count(
            "Orga Task", {"project": project["name"]}
        )
        project["completed_tasks"] = frappe.db.count(
            "Orga Task", {"project": project["name"], "status": "Completed"}
        )
        project["overdue_tasks"] = frappe.db.count(
            "Orga Task",
            {
                "project": project["name"],
                "status": ["not in", ["Completed", "Cancelled"]],
                "due_date": ["<", today]
            }
        )

        # Get manager name
        if project.get("project_manager"):
            project["project_manager_name"] = frappe.db.get_value(
                "User", project["project_manager"], "full_name"
            )

        # Calculate days remaining
        if project.get("end_date"):
            days_remaining = (getdate(project["end_date"]) - today).days
            project["days_remaining"] = days_remaining
            project["is_overdue"] = days_remaining < 0
        else:
            project["days_remaining"] = None
            project["is_overdue"] = False

    return projects


@frappe.whitelist()
def get_workload_by_user(project=None):
    """
    Get task distribution by user.

    Args:
        project: Optional project filter

    Returns:
        list: Users with task counts
    """
    filters = {"status": ["not in", ["Completed", "Cancelled"]]}
    if project:
        filters["project"] = project

    # Get all active tasks with assignees
    tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=["assigned_to", "priority"]
    )

    # Group by user
    workload = {}
    for task in tasks:
        user = task.get("assigned_to")
        if not user:
            user = "Unassigned"

        if user not in workload:
            workload[user] = {
                "user": user,
                "total": 0,
                "urgent": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

        workload[user]["total"] += 1
        priority = task.get("priority", "Medium").lower()
        if priority in workload[user]:
            workload[user][priority] += 1

    # Convert to list and add user names
    result = list(workload.values())
    for item in result:
        if item["user"] != "Unassigned":
            item["user_name"] = frappe.db.get_value(
                "User", item["user"], "full_name"
            )
        else:
            item["user_name"] = "Unassigned"

    # Sort by total tasks descending
    result.sort(key=lambda x: x["total"], reverse=True)

    return result


@frappe.whitelist()
def get_project_health(project_name):
    """
    Get detailed health information for a project.

    Args:
        project_name: Name of the project

    Returns:
        dict: Health score, status, factors, and recommendations
    """
    if not project_name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(_("Project {0} not found").format(project_name), frappe.DoesNotExistError)

    from orga.orga.services.health_calculator import HealthCalculator
    calculator = HealthCalculator()
    return calculator.calculate_project_health(project_name)


@frappe.whitelist()
def get_health_overview():
    """
    Get health overview across all active projects.

    Returns:
        dict: Health summary and at-risk projects
    """
    projects = frappe.get_all(
        "Orga Project",
        filters={"status": ["in", ["Planning", "Active"]]},
        fields=["name", "project_name", "project_code", "health_status", "progress"]
    )

    summary = {
        "green": 0,
        "yellow": 0,
        "red": 0,
        "unknown": 0
    }

    at_risk = []

    for project in projects:
        status = (project.health_status or "Unknown").lower()
        if status in summary:
            summary[status] += 1
        else:
            summary["unknown"] += 1

        # Collect at-risk projects (Yellow or Red)
        if status in ["yellow", "red"]:
            at_risk.append({
                "name": project.name,
                "project_name": project.project_name,
                "project_code": project.project_code,
                "health_status": project.health_status,
                "progress": project.progress
            })

    # Sort at-risk by severity (Red first)
    at_risk.sort(key=lambda x: 0 if x["health_status"] == "Red" else 1)

    return {
        "summary": summary,
        "total": len(projects),
        "at_risk": at_risk,
        "at_risk_count": len(at_risk)
    }


@frappe.whitelist()
def recalculate_project_health(project_name):
    """
    Force recalculation of health for a single project.

    Args:
        project_name: Name of the project

    Returns:
        dict: Updated health information
    """
    if not project_name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(_("Project {0} not found").format(project_name), frappe.DoesNotExistError)

    from orga.orga.services.health_calculator import update_project_health
    return update_project_health(project_name)


def _get_activity_comment_count(doctype: str, docname: str) -> int:
    """
    Get the count of activity comments for a document.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        int: Number of comments (including replies)
    """
    try:
        return frappe.db.count(
            "Orga Activity Comment",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname
            }
        )
    except Exception:
        # Return 0 if table doesn't exist yet
        return 0


def _get_activity_reaction_summary(doctype: str, docname: str) -> dict:
    """
    Get a summary of reactions for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: {counts: {type: count}, user_reactions: [types]}
    """
    try:
        reactions = frappe.get_all(
            "Orga Activity Reaction",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname
            },
            fields=["reaction_type", "user"]
        )

        counts = {}
        user_reactions = []

        for r in reactions:
            rtype = r["reaction_type"]
            counts[rtype] = counts.get(rtype, 0) + 1
            if r["user"] == frappe.session.user:
                user_reactions.append(rtype)

        return {
            "counts": counts,
            "user_reactions": user_reactions
        }
    except Exception:
        # Return empty if table doesn't exist yet
        return {"counts": {}, "user_reactions": []}


def _get_appointment_rsvp_info(appointment_name: str) -> dict:
    """
    Get RSVP info for an appointment (for activity card display).

    Args:
        appointment_name: Appointment document name

    Returns:
        dict: {is_attendee, user_rsvp_status, attendee_stats, attendees}
    """
    try:
        doc = frappe.get_doc("Orga Appointment", appointment_name)

        # Find current user's status
        is_attendee = False
        user_rsvp_status = None

        attendees = []
        stats = {"total": 0, "accepted": 0, "declined": 0, "tentative": 0, "pending": 0}

        for att in doc.attendees:
            stats["total"] += 1
            status_key = (att.rsvp_status or "Pending").lower()
            if status_key in stats:
                stats[status_key] += 1

            # Check if current user is this attendee
            if att.user == frappe.session.user:
                is_attendee = True
                user_rsvp_status = att.rsvp_status
            elif att.resource:
                resource_user = frappe.db.get_value("Orga Resource", att.resource, "user")
                if resource_user == frappe.session.user:
                    is_attendee = True
                    user_rsvp_status = att.rsvp_status

            # Get attendee display info
            name = att.resource_name
            user_image = None

            if att.user:
                user_info = frappe.db.get_value(
                    "User", att.user, ["full_name", "user_image"], as_dict=True
                )
                if user_info:
                    name = user_info.get("full_name") or name
                    user_image = user_info.get("user_image")
            elif att.resource:
                resource_info = frappe.db.get_value(
                    "Orga Resource", att.resource, ["resource_name", "user"], as_dict=True
                )
                if resource_info:
                    name = resource_info.get("resource_name") or name
                    if resource_info.get("user"):
                        user_image = frappe.db.get_value("User", resource_info["user"], "user_image")

            attendees.append({
                "name": name,
                "user_image": user_image,
                "rsvp_status": att.rsvp_status or "Pending"
            })

        return {
            "is_attendee": is_attendee,
            "user_rsvp_status": user_rsvp_status,
            "attendee_stats": stats,
            "attendees": attendees
        }
    except Exception:
        return {
            "is_attendee": False,
            "user_rsvp_status": None,
            "attendee_stats": {"total": 0, "accepted": 0, "declined": 0, "tentative": 0, "pending": 0},
            "attendees": []
        }
