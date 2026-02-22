# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Reports API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.reports.get_project_summary_report',
        args: {}
    })
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, nowdate


@frappe.whitelist()
def get_project_summary_report(date_from=None, date_to=None):
    """
    Generate project summary report.

    Args:
        date_from: Optional start date filter
        date_to: Optional end date filter

    Returns:
        dict: Report data with summary and project details
    """
    filters = {}

    projects = frappe.get_all(
        "Orga Project",
        filters=filters,
        fields=[
            "name", "project_name", "project_code", "status", "progress",
            "health_status", "start_date", "end_date",
            "budget", "spent", "project_manager"
        ],
        order_by="project_name"
    )

    summary = {
        "total_projects": len(projects),
        "by_status": {},
        "by_health": {},
        "total_budget": 0,
        "total_spent": 0,
        "avg_progress": 0
    }

    for project in projects:
        # Count by status
        status = project.status
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # Count by health
        health = project.health_status or "Unknown"
        summary["by_health"][health] = summary["by_health"].get(health, 0) + 1

        # Sum financials
        summary["total_budget"] += project.budget or 0
        summary["total_spent"] += project.spent or 0
        summary["avg_progress"] += project.progress or 0

        # Get manager name
        if project.get("project_manager"):
            project["project_manager_name"] = frappe.db.get_value(
                "User", project["project_manager"], "full_name"
            )

    if projects:
        summary["avg_progress"] = round(summary["avg_progress"] / len(projects), 1)

    return {
        "summary": summary,
        "projects": projects,
        "generated_at": frappe.utils.now()
    }


@frappe.whitelist()
def get_resource_utilization_report(date_from=None, date_to=None, department=None):
    """
    Generate resource utilization report.

    Args:
        date_from: Period start date (default: 30 days ago)
        date_to: Period end date (default: today)
        department: Optional department filter

    Returns:
        dict: Report data with resource utilization
    """
    if not date_from:
        date_from = add_days(today(), -30)
    if not date_to:
        date_to = today()

    filters = {"status": "Active"}
    if department:
        filters["department"] = department

    resources = frappe.get_all(
        "Orga Resource",
        filters=filters,
        fields=["name", "resource_name", "email", "weekly_capacity", "department"]
    )

    result = []
    for resource in resources:
        assignments = frappe.get_all(
            "Orga Assignment",
            filters={
                "resource": resource.name,
                "status": ["in", ["Assigned", "In Progress"]],
            },
            fields=["allocated_hours", "actual_hours", "task", "project"]
        )

        allocated = sum(a.allocated_hours or 0 for a in assignments)
        actual = sum(a.actual_hours or 0 for a in assignments)
        capacity = resource.weekly_capacity or 40

        utilization = round((allocated / capacity) * 100, 1) if capacity else 0

        # Determine status
        if utilization > 100:
            status = "overallocated"
        elif utilization > 80:
            status = "busy"
        else:
            status = "available"

        result.append({
            "resource": resource.name,
            "resource_name": resource.resource_name,
            "email": resource.email,
            "department": resource.department,
            "weekly_capacity": capacity,
            "allocated_hours": allocated,
            "actual_hours": actual,
            "utilization_percent": utilization,
            "assignment_count": len(assignments),
            "status": status
        })

    result.sort(key=lambda x: x["utilization_percent"], reverse=True)

    return {
        "resources": result,
        "date_range": {"from": str(date_from), "to": str(date_to)},
        "summary": {
            "total_resources": len(result),
            "overallocated": sum(1 for r in result if r["status"] == "overallocated"),
            "busy": sum(1 for r in result if r["status"] == "busy"),
            "available": sum(1 for r in result if r["status"] == "available")
        },
        "generated_at": frappe.utils.now()
    }


@frappe.whitelist()
def get_task_completion_report(project=None, date_from=None, date_to=None):
    """
    Generate task completion report.

    Args:
        project: Optional project filter
        date_from: Period start date (default: 30 days ago)
        date_to: Period end date (default: today)

    Returns:
        dict: Report data with task completion statistics
    """
    if not date_from:
        date_from = add_days(today(), -30)
    if not date_to:
        date_to = today()

    filters = {
        "status": "Completed"
    }
    if project:
        filters["project"] = project

    completed_tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=[
            "name", "subject", "project", "assigned_to",
            "priority", "estimated_hours", "actual_hours",
            "due_date", "completed_date"
        ]
    )

    # Filter by completion date range
    completed_tasks = [
        t for t in completed_tasks
        if t.completed_date and
        getdate(date_from) <= getdate(t.completed_date) <= getdate(date_to)
    ]

    total_estimated = sum(t.estimated_hours or 0 for t in completed_tasks)
    total_actual = sum(t.actual_hours or 0 for t in completed_tasks)

    on_time = sum(
        1 for t in completed_tasks
        if t.due_date and t.completed_date and getdate(t.completed_date) <= getdate(t.due_date)
    )
    late = len(completed_tasks) - on_time

    # Group by priority
    by_priority = {}
    for task in completed_tasks:
        priority = task.priority or "Unknown"
        by_priority[priority] = by_priority.get(priority, 0) + 1

    # Group by project
    by_project = {}
    for task in completed_tasks:
        project_name = task.project or "No Project"
        by_project[project_name] = by_project.get(project_name, 0) + 1

    # Enrich with names
    for task in completed_tasks:
        if task.get("assigned_to"):
            task["assigned_to_name"] = frappe.db.get_value(
                "User", task["assigned_to"], "full_name"
            )
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )

    return {
        "tasks": completed_tasks,
        "date_range": {"from": str(date_from), "to": str(date_to)},
        "summary": {
            "total_completed": len(completed_tasks),
            "on_time": on_time,
            "late": late,
            "on_time_rate": round((on_time / len(completed_tasks)) * 100, 1) if completed_tasks else 0,
            "total_estimated_hours": total_estimated,
            "total_actual_hours": total_actual,
            "efficiency": round((total_estimated / total_actual) * 100, 1) if total_actual else 0
        },
        "by_priority": by_priority,
        "by_project": by_project,
        "generated_at": frappe.utils.now()
    }


@frappe.whitelist()
def get_budget_tracking_report():
    """
    Generate budget tracking report.

    Returns:
        dict: Report data with budget tracking details
    """
    filters = {"budget": [">", 0]}

    projects = frappe.get_all(
        "Orga Project",
        filters=filters,
        fields=[
            "name", "project_name", "project_code", "status", "progress",
            "budget", "spent", "start_date", "end_date"
        ],
        order_by="budget desc"
    )

    result = []
    total_budget = 0
    total_spent = 0

    for project in projects:
        budget = project.budget or 0
        spent = project.spent or 0
        remaining = budget - spent
        utilization = round((spent / budget) * 100, 1) if budget else 0

        progress = project.progress or 0

        # Determine budget status based on progress vs spend
        if utilization > progress + 10:
            budget_status = "over"
        elif utilization < progress - 10:
            budget_status = "under"
        else:
            budget_status = "on_track"

        result.append({
            "name": project.name,
            "project_name": project.project_name,
            "project_code": project.project_code,
            "status": project.status,
            "progress": progress,
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "utilization_percent": utilization,
            "budget_status": budget_status,
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None
        })

        total_budget += budget
        total_spent += spent

    return {
        "projects": result,
        "summary": {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_budget - total_spent,
            "overall_utilization": round((total_spent / total_budget) * 100, 1) if total_budget else 0,
            "projects_over_budget": sum(1 for p in result if p["budget_status"] == "over"),
            "projects_on_track": sum(1 for p in result if p["budget_status"] == "on_track"),
            "projects_under_budget": sum(1 for p in result if p["budget_status"] == "under")
        },
        "generated_at": frappe.utils.now()
    }


@frappe.whitelist()
def get_milestone_report(days_ahead=30):
    """
    Generate milestone tracking report.

    Args:
        days_ahead: Days to look ahead for upcoming milestones (default: 30)

    Returns:
        dict: Report data with milestone tracking
    """
    today_date = getdate(today())
    future_date = add_days(today_date, int(days_ahead))

    project_ids = frappe.get_all(
        "Orga Project",
        pluck="name"
    )

    if not project_ids:
        return {
            "milestones": [],
            "summary": {
                "total": 0,
                "completed": 0,
                "upcoming": 0,
                "overdue": 0,
                "missed": 0
            },
            "generated_at": frappe.utils.now()
        }

    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": ["in", project_ids]},
        fields=[
            "name", "milestone_name", "status", "due_date",
            "project", "description"
        ],
        order_by="due_date asc"
    )

    # Enrich with project names and calculate status details
    for ms in milestones:
        if ms.get("project"):
            ms["project_name"] = frappe.db.get_value(
                "Orga Project", ms["project"], "project_name"
            )

        # Calculate days until/past due
        if ms.get("due_date"):
            days_diff = (getdate(ms["due_date"]) - today_date).days
            ms["days_until_due"] = days_diff
            ms["is_overdue"] = days_diff < 0 and ms["status"] not in ["Completed", "Missed"]

    # Categorize
    completed = [m for m in milestones if m["status"] == "Completed"]
    upcoming = [m for m in milestones if m["status"] in ["Upcoming", "In Progress"] and m.get("due_date") and getdate(m["due_date"]) <= future_date]
    overdue = [m for m in milestones if m.get("is_overdue")]
    missed = [m for m in milestones if m["status"] == "Missed"]

    return {
        "milestones": milestones,
        "upcoming": upcoming,
        "overdue": overdue,
        "summary": {
            "total": len(milestones),
            "completed": len(completed),
            "upcoming": len(upcoming),
            "overdue": len(overdue),
            "missed": len(missed),
            "completion_rate": round((len(completed) / len(milestones)) * 100, 1) if milestones else 0
        },
        "generated_at": frappe.utils.now()
    }
