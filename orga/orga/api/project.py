# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Project API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.project.get_projects',
        args: { status: 'Active' }
    })
"""

import json
import frappe
from frappe import _
from orga.orga.api.task import _enrich_assigned_to, _enrich_task_resource


def _has_sort_order(doctype: str) -> bool:
    """Check if sort_order column exists in the database table (pre-migration safe)."""
    try:
        return frappe.db.has_column(doctype, "sort_order")
    except Exception:
        return False


def _has_column(doctype: str, column: str) -> bool:
    """Check if a column exists in the database table (pre-migration safe)."""
    try:
        return frappe.db.has_column(doctype, column)
    except Exception:
        return False


@frappe.whitelist()
def get_projects(status=None, project_type=None, project_manager=None, limit=20, offset=0, order_by="modified desc"):
    """
    Get list of projects with optional filters.

    Args:
        status: Filter by project status (Planning, Active, On Hold, Completed, Cancelled)
        project_type: Filter by project type (Internal, Client, Mixed)
        project_manager: Filter by project manager (User)
        limit: Maximum results per page (default 20)
        offset: Pagination offset
        order_by: Sort order (default: modified desc)

    Returns:
        dict: {projects: [...], total: int}
    """
    filters = {}

    if status:
        filters["status"] = status
    if project_type:
        filters["project_type"] = project_type
    if project_manager:
        filters["project_manager"] = project_manager

    # Whitelist allowed sort columns to prevent injection
    allowed_sorts = {
        "modified desc", "modified asc",
        "creation desc", "creation asc",
        "project_name asc", "project_name desc",
        "start_date asc", "start_date desc",
        "end_date asc", "end_date desc",
        "progress desc", "progress asc",
        "status asc", "status desc",
    }
    if order_by not in allowed_sorts:
        order_by = "modified desc"

    projects = frappe.get_all(
        "Orga Project",
        filters=filters,
        fields=[
            "name",
            "project_name",
            "project_code",
            "status",
            "project_type",
            "start_date",
            "end_date",
            "progress",
            "health_status",
            "project_manager",
            "budget",
            "spent",
            "client",
            "modified",
            "creation"
        ],
        order_by=order_by,
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Project", filters)

    # Enrich with task counts
    for project in projects:
        task_filters = {"project": project["name"]}
        project["task_count"] = frappe.db.count("Orga Task", task_filters)
        project["completed_tasks"] = frappe.db.count(
            "Orga Task",
            {**task_filters, "status": "Completed"}
        )
        project["open_tasks"] = frappe.db.count(
            "Orga Task",
            {**task_filters, "status": "Open"}
        )

        # Get project manager full name
        if project.get("project_manager"):
            project["project_manager_name"] = frappe.db.get_value(
                "User",
                project["project_manager"],
                "full_name"
            )

    return {"projects": projects, "total": total}


@frappe.whitelist()
def get_project(name):
    """
    Get single project with tasks and milestones.

    Args:
        name: Project name/ID (project_code)

    Returns:
        dict: {project: {...}, tasks: [...], milestones: [...]}
    """
    if not name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", name):
        frappe.throw(_("Project {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Project", "read", name):
        frappe.throw(_("Not permitted to access this project"), frappe.PermissionError)

    project = frappe.get_doc("Orga Project", name)

    # Get tasks
    task_has_sort = _has_sort_order("Orga Task")
    task_fields = [
        "name", "subject", "description", "status", "priority", "due_date", "start_date",
        "assigned_to", "progress", "estimated_hours", "actual_hours",
        "task_type", "parent_task", "milestone",
        "estimated_cost", "actual_cost", "is_billable", "billing_rate",
        "is_blocked"
    ]
    if task_has_sort:
        task_fields.append("sort_order")
    if _has_column("Orga Task", "task_group"):
        task_fields.append("task_group")
    if _has_column("Orga Task", "depends_on_group"):
        task_fields.append("depends_on_group")
    if _has_column("Orga Task", "task_scheduling_type"):
        task_fields.extend(["task_scheduling_type", "buffer_size", "buffer_consumed"])
    if _has_column("Orga Task", "auto_trail_start"):
        task_fields.append("auto_trail_start")

    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": name},
        fields=task_fields,
        order_by="sort_order asc, start_date asc, due_date asc, priority desc" if task_has_sort else "start_date asc, due_date asc, priority desc"
    )

    # Enrich tasks with assignee names, images, and resource assignments
    for task in tasks:
        _enrich_assigned_to(task)
        _enrich_task_resource(task)

    # Get milestones (sort_order first for user-defined ordering, then due_date)
    ms_has_sort = _has_sort_order("Orga Milestone")
    ms_fields = ["name", "milestone_name", "status", "due_date", "completed_date", "description"]
    if ms_has_sort:
        ms_fields.append("sort_order")

    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": name},
        fields=ms_fields,
        order_by="sort_order asc, due_date asc" if ms_has_sort else "due_date asc"
    )

    # Calculate completion percentage for each milestone from linked tasks
    for milestone in milestones:
        linked_tasks = [t for t in tasks if t.get("milestone") == milestone["name"]]
        milestone["task_count"] = len(linked_tasks)
        if linked_tasks:
            completed = sum(1 for t in linked_tasks if t["status"] == "Completed")
            milestone["completion_percentage"] = round((completed / len(linked_tasks)) * 100)
        else:
            milestone["completion_percentage"] = 0

    # Calculate stats
    stats = {
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks if t["status"] == "Completed"),
        "open_tasks": sum(1 for t in tasks if t["status"] == "Open"),
        "in_progress_tasks": sum(1 for t in tasks if t["status"] == "In Progress"),
        "overdue_tasks": sum(
            1 for t in tasks
            if t["status"] not in ["Completed", "Cancelled"]
            and t.get("due_date")
            and str(t["due_date"]) < frappe.utils.nowdate()
        ),
        "total_milestones": len(milestones),
        "completed_milestones": sum(1 for m in milestones if m["status"] == "Completed"),
    }

    # Get unique team members from task assignments (Users + Resources)
    team_members = []
    seen_users = set()
    seen_resources = set()
    pm = project.project_manager

    # Collect users assigned via assigned_to (User accounts)
    for task in tasks:
        user = task.get("assigned_to")
        if user and user not in seen_users:
            seen_users.add(user)
            user_info = frappe.db.get_value(
                "User",
                user,
                ["full_name", "user_image"],
                as_dict=True
            )
            if user_info:
                team_members.append({
                    "user": user,
                    "full_name": user_info.get("full_name") or user,
                    "user_image": user_info.get("user_image"),
                    "is_manager": user == pm,
                    "source": "user"
                })

    # Also add project manager if not already in team
    if pm and pm not in seen_users:
        pm_info = frappe.db.get_value(
            "User",
            pm,
            ["full_name", "user_image"],
            as_dict=True
        )
        if pm_info:
            team_members.insert(0, {
                "user": pm,
                "full_name": pm_info.get("full_name") or pm,
                "user_image": pm_info.get("user_image"),
                "is_manager": True,
                "source": "user"
            })

    # Collect resources assigned via Orga Assignment (contacts/contractors)
    if frappe.db.exists("DocType", "Orga Assignment"):
        task_names = [t.get("name") for t in tasks if t.get("name")]
        if task_names:
            assignments = frappe.get_all(
                "Orga Assignment",
                filters={"task": ["in", task_names]},
                fields=["resource"],
                group_by="resource"
            )
            for assignment in assignments:
                res_name = assignment.resource
                if res_name and res_name not in seen_resources:
                    seen_resources.add(res_name)
                    res_info = frappe.db.get_value(
                        "Orga Resource",
                        res_name,
                        ["resource_name", "user", "email"],
                        as_dict=True
                    )
                    if res_info:
                        # Skip if this resource's linked user is already in the list
                        if res_info.user and res_info.user in seen_users:
                            continue
                        team_members.append({
                            "user": res_info.user or res_info.email or res_name,
                            "full_name": res_info.resource_name or res_name,
                            "user_image": None,
                            "is_manager": False,
                            "source": "resource"
                        })

    # Get project documents/attachments (all, not just public)
    documents = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Orga Project",
            "attached_to_name": name,
        },
        fields=[
            "name", "file_name", "file_url", "file_size",
            "file_type", "is_private", "creation", "owner"
        ],
        order_by="creation desc"
    )

    # Get task attachments for all tasks in this project
    task_names = [t["name"] for t in tasks]
    task_attachments = []
    if task_names:
        task_attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Orga Task",
                "attached_to_name": ["in", task_names],
            },
            fields=[
                "name", "file_name", "file_url", "file_size",
                "file_type", "is_private", "creation", "owner",
                "attached_to_name"
            ],
            order_by="creation desc"
        )

    return {
        "project": project.as_dict(),
        "tasks": tasks,
        "milestones": milestones,
        "stats": stats,
        "team_members": team_members,
        "documents": documents,
        "task_attachments": task_attachments
    }


@frappe.whitelist()
def create_project(data):
    """
    Create a new project.

    Args:
        data: dict or JSON string with project fields
            Required: project_name, start_date, end_date, project_manager
            Optional: project_code, status, project_type, description, budget, client

    Returns:
        dict: Created project data
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Validate required fields
    required = ["project_name", "start_date", "end_date", "project_manager"]
    for field in required:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    allowed_fields = [
        "project_name", "project_code", "status", "project_type", "description",
        "start_date", "end_date", "actual_start", "actual_end",
        "budget", "client", "project_manager", "health_status",
        "dependency_mode", "auto_schedule_on_completion",
        "auto_trail_start_default"
    ]

    doc_data = {"doctype": "Orga Project"}
    for field in allowed_fields:
        if field in data:
            doc_data[field] = data[field]

    doc = frappe.get_doc(doc_data)
    doc.insert()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def update_project(name, data):
    """
    Update an existing project.

    Args:
        name: Project name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated project data
    """
    if not name:
        frappe.throw(_("Project name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Project", name):
        frappe.throw(_("Project {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Project", name)

    # Update allowed fields
    allowed_fields = [
        "project_name", "status", "project_type", "description",
        "start_date", "end_date", "actual_start", "actual_end",
        "budget", "client", "project_manager", "health_status",
        "dependency_mode", "auto_schedule_on_completion",
        "auto_trail_start_default"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def delete_project(name):
    """
    Delete a project and optionally all associated tasks/milestones.

    Args:
        name: Project name/ID

    Returns:
        dict: {success: True, deleted_tasks: int, deleted_milestones: int}
    """
    if not name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", name):
        frappe.throw(_("Project {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Project", "delete", name):
        frappe.throw(_("Not permitted to delete this project"), frappe.PermissionError)

    # Capture project info before deletion for the activity log
    project_label = frappe.db.get_value("Orga Project", name, "project_name") or name

    # Count and delete associated tasks (use delete_task API for full cleanup)
    tasks = frappe.get_all("Orga Task", filters={"project": name})
    for task in tasks:
        frappe.delete_doc("Orga Task", task.name, force=True)

    # Count and delete associated milestones
    milestones = frappe.get_all("Orga Milestone", filters={"project": name})
    for ms in milestones:
        frappe.delete_doc("Orga Milestone", ms.name, force=True)

    # Clean up other linked records that would block deletion
    for assignment in frappe.get_all("Orga Assignment", filters={"project": name}, pluck="name"):
        frappe.delete_doc("Orga Assignment", assignment, force=True)

    # Clear project reference on time logs and appointments (preserve the records)
    frappe.db.set_value("Orga Time Log", {"project": name}, "project", "", update_modified=False)
    frappe.db.set_value("Orga Appointment", {"project": name}, "project", "", update_modified=False)

    if frappe.db.exists("DocType", "Orga Defect"):
        frappe.db.set_value("Orga Defect", {"project": name}, "project", "", update_modified=False)

    # Delete notifications referencing this project
    if frappe.db.exists("DocType", "Orga Notification"):
        for notif in frappe.get_all("Orga Notification",
            filters={"reference_doctype": "Orga Project", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Notification", notif, force=True)

    # Delete activity comments and reactions referencing this project
    if frappe.db.exists("DocType", "Orga Activity Comment"):
        for comment in frappe.get_all("Orga Activity Comment",
            filters={"reference_doctype": "Orga Project", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Activity Comment", comment, force=True)
    if frappe.db.exists("DocType", "Orga Activity Reaction"):
        for reaction in frappe.get_all("Orga Activity Reaction",
            filters={"reference_doctype": "Orga Project", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Activity Reaction", reaction, force=True)

    # Delete project (force=True to handle any remaining links)
    frappe.delete_doc("Orga Project", name, force=True)

    # Log deletion as a system activity comment so it appears in the activity feed
    try:
        comment = frappe.get_doc({
            "doctype": "Orga Activity Comment",
            "reference_doctype": "Orga Project",
            "reference_name": name,
            "note_type": "System",
            "content": _('Deleted project "{0}" ({1} tasks, {2} milestones)').format(project_label, len(tasks), len(milestones)),
            "user": frappe.session.user,
            "visibility": "Team"
        })
        comment.insert(ignore_permissions=True)
    except Exception:
        # Don't let activity logging failure block deletion
        pass

    frappe.db.commit()

    return {
        "success": True,
        "deleted_tasks": len(tasks),
        "deleted_milestones": len(milestones)
    }


@frappe.whitelist()
def get_project_dependencies(project_name):
    """
    Get all task dependency relationships for a project in one bulk call.

    Args:
        project_name: Project name/ID

    Returns:
        list: [{task: str, depends_on: str, dependency_type: str, lag_days: int}, ...]
    """
    if not project_name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(_("Project {0} not found").format(project_name), frappe.DoesNotExistError)

    # Get all dependencies for tasks in this project in a single query
    dependencies = frappe.db.sql("""
        SELECT
            td.parent AS task,
            td.depends_on,
            td.dependency_type,
            td.lag_days,
            t1.subject AS task_subject,
            t1.status AS task_status,
            t2.subject AS depends_on_subject,
            t2.status AS depends_on_status
        FROM `tabOrga Task Dependency` td
        JOIN `tabOrga Task` t1 ON td.parent = t1.name
        JOIN `tabOrga Task` t2 ON td.depends_on = t2.name
        WHERE t1.project = %s
    """, (project_name,), as_dict=True)

    return dependencies


@frappe.whitelist()
def get_critical_path(project_name):
    """
    Calculate the critical path for a project using the Critical Path Method (CPM).

    Performs forward pass (Early Start/Finish) and backward pass (Late Start/Finish)
    to identify tasks with zero float (slack). These tasks form the critical path —
    any delay on them delays the entire project.

    Args:
        project_name: Project name/ID

    Returns:
        dict: {
            critical_tasks: list of task names on the critical path,
            task_floats: dict mapping task name to float (slack) in days
        }
    """
    if not project_name:
        frappe.throw(_("Project name is required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(_("Project {0} not found").format(project_name), frappe.DoesNotExistError)

    from datetime import datetime, timedelta

    # Load project dates
    project = frappe.get_doc("Orga Project", project_name)
    project_start = project.start_date
    project_end = project.end_date

    if not project_start or not project_end:
        return {"critical_tasks": [], "task_floats": {}}

    # Load all active tasks
    all_tasks = frappe.get_all(
        "Orga Task",
        filters={
            "project": project_name,
            "status": ["not in", ["Completed", "Cancelled"]]
        },
        fields=["name", "start_date", "due_date"]
    )

    if not all_tasks:
        return {"critical_tasks": [], "task_floats": {}}

    # Build task lookup
    task_map = {}
    for t in all_tasks:
        if t.start_date and t.due_date:
            duration = (t.due_date - t.start_date).days + 1
        elif t.start_date:
            duration = 1
        else:
            duration = 1
        task_map[t.name] = {
            "start_date": t.start_date,
            "due_date": t.due_date,
            "duration": max(1, duration)
        }

    task_names = set(task_map.keys())

    # Load dependencies (only FS between active tasks)
    deps = get_project_dependencies(project_name)
    # Build adjacency: predecessors[task] = [(pred_name, lag_days), ...]
    # Build adjacency: successors[pred] = [(task_name, lag_days), ...]
    predecessors = {name: [] for name in task_names}
    successors = {name: [] for name in task_names}
    for dep in deps:
        if dep.get("dependency_type") != "Finish to Start":
            continue
        pred = dep.get("depends_on")
        succ = dep.get("task")
        if pred in task_names and succ in task_names:
            lag = dep.get("lag_days", 0) or 0
            predecessors[succ].append((pred, lag))
            successors[pred].append((succ, lag))

    # Topological sort (Kahn's algorithm)
    in_degree = {name: len(predecessors[name]) for name in task_names}
    queue = [name for name, deg in in_degree.items() if deg == 0]
    topo_order = []

    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for succ, _ in successors.get(node, []):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    # If there's a cycle, include remaining tasks at the end
    remaining = [n for n in task_names if n not in topo_order]
    topo_order.extend(remaining)

    # Convert dates to day offsets from project_start for arithmetic
    def date_to_day(d):
        if not d:
            return 0
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        return (d - project_start).days

    def day_to_date(day_offset):
        return project_start + timedelta(days=day_offset)

    project_end_day = date_to_day(project_end)

    # Forward pass: calculate Early Start (ES) and Early Finish (EF)
    es = {}  # Early Start (day offset)
    ef = {}  # Early Finish (day offset)

    for name in topo_order:
        info = task_map[name]
        if predecessors[name]:
            # ES = max(predecessor EF + lag) for all predecessors
            es[name] = max(
                ef[pred] + lag
                for pred, lag in predecessors[name]
                if pred in ef
            ) if any(pred in ef for pred, _ in predecessors[name]) else date_to_day(info["start_date"])
        else:
            # No predecessors: use task's actual start date
            es[name] = date_to_day(info["start_date"]) if info["start_date"] else 0

        ef[name] = es[name] + info["duration"]

    # Backward pass: calculate Late Finish (LF) and Late Start (LS)
    lf = {}  # Late Finish (day offset)
    ls = {}  # Late Start (day offset)

    for name in reversed(topo_order):
        info = task_map[name]
        if successors[name]:
            # LF = min(successor LS - lag) for all successors
            lf[name] = min(
                ls[succ] - lag
                for succ, lag in successors[name]
                if succ in ls
            ) if any(succ in ls for succ, _ in successors[name]) else project_end_day
        else:
            # No successors: use project end date
            lf[name] = project_end_day

        ls[name] = lf[name] - info["duration"]

    # Calculate float and identify critical path
    task_floats = {}
    critical_tasks = []

    for name in topo_order:
        total_float = ls.get(name, 0) - es.get(name, 0)
        task_floats[name] = total_float
        if total_float <= 0:
            critical_tasks.append(name)

    return {
        "critical_tasks": critical_tasks,
        "task_floats": task_floats
    }


@frappe.whitelist()
def get_project_stats(name=None):
    """
    Get project statistics. If name is provided, get stats for that project.
    Otherwise, get overall stats.

    Args:
        name: Optional project name/ID

    Returns:
        dict: Project statistics
    """
    if name:
        # Single project stats
        if not frappe.db.exists("Orga Project", name):
            frappe.throw(_("Project {0} not found").format(name))

        task_filters = {"project": name}
        milestone_filters = {"project": name}
    else:
        task_filters = {}
        milestone_filters = {}

    today = frappe.utils.nowdate()

    stats = {
        "tasks": {
            "total": frappe.db.count("Orga Task", task_filters),
            "open": frappe.db.count("Orga Task", {**task_filters, "status": "Open"}),
            "in_progress": frappe.db.count("Orga Task", {**task_filters, "status": "In Progress"}),
            "review": frappe.db.count("Orga Task", {**task_filters, "status": "Review"}),
            "completed": frappe.db.count("Orga Task", {**task_filters, "status": "Completed"}),
            "cancelled": frappe.db.count("Orga Task", {**task_filters, "status": "Cancelled"}),
        },
        "milestones": {
            "total": frappe.db.count("Orga Milestone", milestone_filters),
            "upcoming": frappe.db.count("Orga Milestone", {**milestone_filters, "status": "Upcoming"}),
            "in_progress": frappe.db.count("Orga Milestone", {**milestone_filters, "status": "In Progress"}),
            "completed": frappe.db.count("Orga Milestone", {**milestone_filters, "status": "Completed"}),
            "missed": frappe.db.count("Orga Milestone", {**milestone_filters, "status": "Missed"}),
        }
    }

    # Calculate overdue tasks
    overdue_filters = {
        **task_filters,
        "status": ["not in", ["Completed", "Cancelled"]],
        "due_date": ["<", today]
    }
    stats["tasks"]["overdue"] = frappe.db.count("Orga Task", overdue_filters)

    return stats
