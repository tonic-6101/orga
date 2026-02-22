# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Portal API Module

Provides API endpoints for the Vue-based client portal.
All endpoints require authentication as a client with portal access.
"""

import frappe
from frappe import _
from frappe.utils import getdate, today, date_diff


def _get_current_client() -> dict:
    """
    Get the Orga Client record for the current user.

    Returns:
        dict: Client record

    Raises:
        frappe.PermissionError: If user is not a valid portal client
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to access the client portal"), frappe.PermissionError)

    client = frappe.db.get_value(
        "Orga Client",
        {
            "user": frappe.session.user,
            "portal_enabled": 1,
            "status": "Active"
        },
        ["name", "client_name", "company", "email", "phone"],
        as_dict=True
    )

    if not client:
        frappe.throw(
            _("You do not have access to the client portal. Please contact support."),
            frappe.PermissionError
        )

    return client


def _get_status_color(status: str) -> str:
    """Get color class for project status."""
    colors = {
        "Planning": "blue",
        "Active": "green",
        "On Hold": "orange",
        "Completed": "gray",
        "Cancelled": "red"
    }
    return colors.get(status, "gray")


def _get_health_color(health: str) -> str:
    """Get color class for health status."""
    colors = {
        "Green": "green",
        "Yellow": "yellow",
        "Red": "red",
        "Unknown": "gray"
    }
    return colors.get(health, "gray")


def _get_milestone_status_color(status: str) -> str:
    """Get color class for milestone status."""
    colors = {
        "Upcoming": "blue",
        "Completed": "green",
        "Missed": "red"
    }
    return colors.get(status, "gray")


@frappe.whitelist()
def get_portal_dashboard() -> dict:
    """
    Get client portal dashboard data.

    Returns:
        dict: {
            client: client record,
            projects: list of projects with enriched data,
            stats: summary statistics
        }
    """
    client = _get_current_client()

    # Update last login timestamp
    frappe.db.set_value("Orga Client", client.name, "last_login", frappe.utils.now_datetime())
    frappe.db.commit()

    # Get client's projects
    projects = frappe.get_all(
        "Orga Project",
        filters={"client": client.name},
        fields=[
            "name", "project_name", "description", "status",
            "progress", "start_date", "end_date", "health_status"
        ],
        order_by="creation desc"
    )

    # Enrich each project with task counts and upcoming milestones
    for project in projects:
        # Task counts
        task_counts = frappe.db.sql("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM `tabOrga Task`
            WHERE project = %s
        """, project.name, as_dict=True)[0]

        project.task_count = task_counts.total or 0
        project.completed_tasks = task_counts.completed or 0

        # Upcoming milestone
        upcoming_milestone = frappe.db.get_value(
            "Orga Milestone",
            {
                "project": project.name,
                "status": ["!=", "Completed"]
            },
            ["milestone_name", "due_date"],
            as_dict=True,
            order_by="due_date asc"
        )
        project.upcoming_milestone = upcoming_milestone

        # Status colors
        project.status_color = _get_status_color(project.status)
        project.health_color = _get_health_color(project.health_status)

    # Calculate summary stats
    total = len(projects)
    active = sum(1 for p in projects if p.status in ["Active", "Planning"])
    completed = sum(1 for p in projects if p.status == "Completed")
    on_hold = sum(1 for p in projects if p.status == "On Hold")

    total_tasks = sum(p.task_count for p in projects)
    completed_tasks = sum(p.completed_tasks for p in projects)

    stats = {
        "total_projects": total,
        "active_projects": active,
        "completed_projects": completed,
        "on_hold_projects": on_hold,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overall_progress": round(
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
        )
    }

    return {
        "client": client,
        "projects": projects,
        "stats": stats
    }


@frappe.whitelist()
def get_portal_project(project_name: str) -> dict:
    """
    Get detailed project info for portal view.

    Args:
        project_name: Project document name (e.g., ORG-2026-0001)

    Returns:
        dict: {
            project: project record with computed fields,
            milestones: list of milestones,
            task_summary: task counts by status,
            recent_activity: list of recent activity items
        }

    Raises:
        frappe.PermissionError: If client doesn't have access to the project
    """
    client = _get_current_client()

    # Get project and verify client access
    project = frappe.db.get_value(
        "Orga Project",
        {
            "name": project_name,
            "client": client.name
        },
        [
            "name", "project_name", "description", "status",
            "progress", "start_date", "end_date", "health_status",
            "budget", "spent", "project_manager"
        ],
        as_dict=True
    )

    if not project:
        frappe.throw(
            _("Project not found or you do not have access"),
            frappe.PermissionError
        )

    # Enrich project data
    if project.project_manager:
        project.manager_name = frappe.db.get_value(
            "User", project.project_manager, "full_name"
        )

    project.status_color = _get_status_color(project.status)
    project.health_color = _get_health_color(project.health_status)

    # Calculate days remaining/overdue
    if project.end_date:
        days = date_diff(project.end_date, today())
        project.days_remaining = days if days >= 0 else 0
        project.days_overdue = abs(days) if days < 0 else 0
    else:
        project.days_remaining = None
        project.days_overdue = None

    # Budget utilization
    if project.budget and project.budget > 0:
        project.budget_utilization = round((project.spent or 0) / project.budget * 100, 1)
    else:
        project.budget_utilization = 0

    # Get milestones
    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": project_name},
        fields=[
            "name", "milestone_name", "description", "status",
            "due_date", "completion_date"
        ],
        order_by="due_date asc"
    )

    for milestone in milestones:
        milestone.status_color = _get_milestone_status_color(milestone.status)

        # Check if overdue
        milestone.is_overdue = False
        if milestone.status != "Completed" and milestone.due_date:
            if getdate(milestone.due_date) < getdate(today()):
                milestone.is_overdue = True

    # Get task summary
    task_summary_raw = frappe.db.sql("""
        SELECT
            status,
            COUNT(*) as count
        FROM `tabOrga Task`
        WHERE project = %s
        GROUP BY status
    """, project_name, as_dict=True)

    task_summary = {
        "Open": 0,
        "Working": 0,
        "Pending Review": 0,
        "Completed": 0,
        "Cancelled": 0,
        "total": 0
    }

    for row in task_summary_raw:
        task_summary[row.status] = row.count
        task_summary["total"] += row.count

    # Get recent activity (limited view for clients)
    recent_activity = _get_project_activity(project_name, limit=10)

    return {
        "project": project,
        "milestones": milestones,
        "task_summary": task_summary,
        "recent_activity": recent_activity
    }


def _get_project_activity(project_name: str, limit: int = 10) -> list:
    """
    Get recent activity for a project (client-appropriate view).

    Only shows milestone events and completed tasks, not internal comments
    or other sensitive information.

    Defensive check: verifies that the project belongs to the current client
    even though callers should already validate this.
    """
    # Defensive: verify the calling client owns this project
    try:
        client = _get_current_client()
        project_client = frappe.db.get_value("Orga Project", project_name, "client")
        if project_client != client.name:
            frappe.throw(_("Not permitted"), frappe.PermissionError)
    except frappe.PermissionError:
        raise
    except Exception:
        # If client detection fails (e.g. called from internal context), allow
        pass

    activities = []

    # Milestone events
    milestone_activities = frappe.db.sql("""
        SELECT
            'milestone' as type,
            milestone_name as title,
            CASE
                WHEN status = 'Completed' THEN 'completed'
                ELSE 'updated'
            END as action,
            COALESCE(completion_date, modified) as timestamp
        FROM `tabOrga Milestone`
        WHERE project = %s
        ORDER BY modified DESC
        LIMIT %s
    """, (project_name, limit), as_dict=True)

    activities.extend(milestone_activities)

    # Task completions (only completed tasks visible to clients)
    task_activities = frappe.db.sql("""
        SELECT
            'task' as type,
            subject as title,
            'completed' as action,
            modified as timestamp
        FROM `tabOrga Task`
        WHERE project = %s AND status = 'Completed'
        ORDER BY modified DESC
        LIMIT %s
    """, (project_name, limit), as_dict=True)

    activities.extend(task_activities)

    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.timestamp or "", reverse=True)
    return activities[:limit]


@frappe.whitelist()
def get_client_projects() -> list:
    """
    Get list of projects for the current client.

    Returns:
        list: Project records with basic info
    """
    client = _get_current_client()

    projects = frappe.get_all(
        "Orga Project",
        filters={"client": client.name},
        fields=["name", "project_name", "status", "progress"],
        order_by="project_name asc"
    )

    return projects


@frappe.whitelist()
def submit_support_request(subject: str, message: str, project: str = None) -> dict:
    """
    Submit a support request from the client portal.

    Creates a Communication document for tracking and optionally
    sends an email to the support team.

    Args:
        subject: Request subject line
        message: Request message body
        project: Optional project reference

    Returns:
        dict: {success: True, communication: document name}

    Raises:
        frappe.ValidationError: If subject or message is empty
    """
    client = _get_current_client()

    if not subject or not subject.strip():
        frappe.throw(_("Subject is required"), frappe.ValidationError)

    if not message or not message.strip():
        frappe.throw(_("Message is required"), frappe.ValidationError)

    # Validate project belongs to client (if provided)
    if project:
        project_client = frappe.db.get_value("Orga Project", project, "client")
        if project_client != client.name:
            frappe.throw(
                _("Invalid project reference"),
                frappe.ValidationError
            )

    # Build communication content
    content = f"""
<p><strong>From:</strong> {client.client_name} ({client.email})</p>
<p><strong>Company:</strong> {client.company or 'N/A'}</p>
{"<p><strong>Project:</strong> " + project + "</p>" if project else ""}
<hr>
<p>{frappe.utils.escape_html(message)}</p>
"""

    # Create Communication document
    communication = frappe.get_doc({
        "doctype": "Communication",
        "communication_type": "Communication",
        "communication_medium": "Email",
        "subject": f"[Portal Support] {subject.strip()}",
        "content": content,
        "sender": client.email,
        "sender_full_name": client.client_name,
        "reference_doctype": "Orga Project" if project else "Orga Client",
        "reference_name": project if project else client.name,
        "status": "Open"
    })
    communication.insert(ignore_permissions=True)

    # Optionally send email to support
    support_email = frappe.db.get_single_value("Orga Settings", "support_email")
    if support_email:
        try:
            frappe.sendmail(
                recipients=[support_email],
                subject=f"[Portal Support] {subject.strip()}",
                message=content,
                reference_doctype="Communication",
                reference_name=communication.name,
                reply_to=client.email
            )
        except Exception as e:
            # Log but don't fail the request
            frappe.log_error(f"Failed to send support email: {e}", "Portal Support Email Error")

    frappe.db.commit()

    return {
        "success": True,
        "communication": communication.name,
        "message": _("Your support request has been submitted successfully.")
    }
