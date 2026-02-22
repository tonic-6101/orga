# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Task API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.task.get_tasks',
        args: { project: 'ORG-2026-0001' }
    })
"""

import json
import frappe
from frappe import _
from frappe.utils import now_datetime


def _has_sort_order() -> bool:
    """Check if sort_order column exists on Orga Task (pre-migration safe)."""
    try:
        return frappe.db.has_column("Orga Task", "sort_order")
    except Exception:
        return False


def _has_task_group() -> bool:
    """Check if task_group column exists on Orga Task (pre-migration safe)."""
    try:
        return frappe.db.has_column("Orga Task", "task_group")
    except Exception:
        return False


def _has_depends_on_group() -> bool:
    """Check if depends_on_group column exists on Orga Task (pre-migration safe)."""
    try:
        return frappe.db.has_column("Orga Task", "depends_on_group")
    except Exception:
        return False


def _has_auto_trail_start() -> bool:
    """Check if auto_trail_start column exists on Orga Task (pre-migration safe)."""
    try:
        return frappe.db.has_column("Orga Task", "auto_trail_start")
    except Exception:
        return False


def _enrich_assigned_to(task):
    """Add assigned_to_name and assigned_to_image from User doctype."""
    if task.get("assigned_to"):
        user_info = frappe.db.get_value(
            "User", task["assigned_to"], ["full_name", "user_image"], as_dict=True
        )
        if user_info:
            task["assigned_to_name"] = user_info.get("full_name") or task["assigned_to"]
            task["assigned_to_image"] = user_info.get("user_image") or ""
        else:
            task["assigned_to_name"] = task["assigned_to"]
            task["assigned_to_image"] = ""
    else:
        task.setdefault("assigned_to_name", "")
        task.setdefault("assigned_to_image", "")


def _enrich_task_resource(task):
    """Add assigned resource info from Orga Assignment if one exists."""
    if not frappe.db.exists("DocType", "Orga Assignment"):
        task["assigned_resource"] = ""
        task["assigned_resource_name"] = ""
        return

    assignment = frappe.db.get_value(
        "Orga Assignment",
        {"task": task.get("name")},
        ["resource", "name"],
        as_dict=True,
        order_by="creation desc"
    )
    if assignment:
        resource_name = frappe.db.get_value(
            "Orga Resource", assignment.resource, "resource_name"
        )
        task["assigned_resource"] = assignment.resource
        task["assigned_resource_name"] = resource_name or ""
        # If task has no assigned_to but has a resource assignment, use resource name
        if not task.get("assigned_to_name") and resource_name:
            task["assigned_to_name"] = resource_name
    else:
        task["assigned_resource"] = ""
        task["assigned_resource_name"] = ""


def _get_resource_assigned_task_names(user):
    """Get task names assigned to user via Orga Assignment (resource-based).

    Looks up Orga Resources linked to the user, then finds active Orga Assignments
    for those resources, returning the associated task names.
    """
    if not frappe.db.exists("DocType", "Orga Assignment"):
        return []

    # Find resources linked to this user
    resources = frappe.get_all(
        "Orga Resource",
        filters={"user": user},
        pluck="name"
    )
    if not resources:
        return []

    # Find active assignments for those resources
    return frappe.get_all(
        "Orga Assignment",
        filters={
            "resource": ["in", resources],
            "status": ["in", ["Assigned", "In Progress"]],
        },
        pluck="task"
    )


@frappe.whitelist()
def get_tasks(
    project=None,
    status=None,
    priority=None,
    assigned_to=None,
    milestone=None,
    task_type=None,
    task_group=None,
    limit=100,
    offset=0
):
    """
    Get tasks with optional filters.

    Args:
        project: Filter by project
        status: Filter by status (Open, In Progress, Review, Completed, Cancelled)
        priority: Filter by priority (Low, Medium, High, Urgent)
        assigned_to: Filter by assignee (User)
        milestone: Filter by milestone
        task_type: Filter by type (Task, Bug, Feature, Research, Meeting)
        task_group: Filter by task group name
        limit: Maximum results (default 100)
        offset: Pagination offset

    Returns:
        dict: {tasks: [...], total: int}
    """
    filters = {}

    if project:
        filters["project"] = project
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if milestone:
        filters["milestone"] = milestone
    if task_type:
        filters["task_type"] = task_type
    has_task_group = _has_task_group()
    if task_group and has_task_group:
        filters["task_group"] = task_group

    fields = [
        "name",
        "subject",
        "status",
        "priority",
        "due_date",
        "start_date",
        "completed_date",
        "assigned_to",
        "project",
        "progress",
        "estimated_hours",
        "actual_hours",
        "task_type",
        "parent_task",
        "milestone",
        "is_blocked",
        "sort_order",
        "modified"
    ]
    if has_task_group:
        fields.append("task_group")
    if _has_depends_on_group():
        fields.append("depends_on_group")

    tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=fields,
        order_by="sort_order asc, due_date asc, priority desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Task", filters)

    # Enrich with names
    for task in tasks:
        _enrich_assigned_to(task)
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )
        if task.get("milestone"):
            task["milestone_name"] = frappe.db.get_value(
                "Orga Milestone", task["milestone"], "milestone_name"
            )
        _enrich_task_resource(task)

    return {"tasks": tasks, "total": total}


@frappe.whitelist()
def get_task(name):
    """
    Get single task with full details.

    Args:
        name: Task name/ID

    Returns:
        dict: Task data with project and milestone info
    """
    if not name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", name):
        frappe.throw(_("Task {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Task", "read", name):
        frappe.throw(_("Not permitted to access this task"), frappe.PermissionError)

    task = frappe.get_doc("Orga Task", name)
    task_dict = task.as_dict()

    # Enrich with related info
    _enrich_assigned_to(task_dict)

    if task.project:
        task_dict["project_name"] = frappe.db.get_value(
            "Orga Project", task.project, "project_name"
        )

    if task.milestone:
        task_dict["milestone_name"] = frappe.db.get_value(
            "Orga Milestone", task.milestone, "milestone_name"
        )

    _enrich_task_resource(task_dict)

    # Get subtasks
    subtasks = frappe.get_all(
        "Orga Task",
        filters={"parent_task": name},
        fields=["name", "subject", "status", "priority", "assigned_to", "due_date"]
    )
    task_dict["subtasks"] = subtasks

    return task_dict


@frappe.whitelist()
def create_task(data):
    """
    Create a new task.

    Args:
        data: dict or JSON string with task fields
            Required: subject, project
            Optional: status, priority, description, due_date, assigned_to, etc.

    Returns:
        dict: Created task data
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Validate required fields
    required = ["subject", "project"]
    for field in required:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    # Validate project exists
    if not frappe.db.exists("Orga Project", data["project"]):
        frappe.throw(_("Project {0} not found").format(data["project"]))

    # Only allow known task fields (prevents unexpected fields from causing errors)
    allowed_fields = [
        "subject", "project", "description", "status", "priority",
        "start_date", "due_date", "assigned_to", "task_type",
        "milestone", "parent_task", "estimated_hours",
        "estimated_cost", "actual_cost", "is_billable", "billing_rate",
        "sort_order",
    ]
    if _has_task_group():
        allowed_fields.append("task_group")
    if _has_depends_on_group():
        allowed_fields.append("depends_on_group")
    if _has_auto_trail_start():
        allowed_fields.append("auto_trail_start")

    task_data = {"doctype": "Orga Task"}
    for field in allowed_fields:
        if field in data and data[field] is not None:
            task_data[field] = data[field]

    # Apply project-level auto_trail_start default if not explicitly set
    if "auto_trail_start" not in data and _has_auto_trail_start():
        try:
            if frappe.db.has_column("Orga Project", "auto_trail_start_default"):
                proj_default = frappe.db.get_value(
                    "Orga Project", data["project"], "auto_trail_start_default"
                )
                if proj_default:
                    task_data["auto_trail_start"] = 1
        except Exception as e:
            frappe.log_error(f"Auto trail start default check failed: {e}", "Orga Task Create")

    doc = frappe.get_doc(task_data)
    doc.insert()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def update_task(name, data):
    """
    Update task fields.

    Args:
        name: Task name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated task data
    """
    if not name:
        frappe.throw(_("Task name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Task", name):
        frappe.throw(_("Task {0} not found").format(name), frappe.DoesNotExistError)

    # Use db_set for individual field updates to avoid schema mismatch
    # (doc.save() writes ALL DocType fields, which fails if task_group column
    # doesn't exist yet because bench migrate hasn't been run)
    allowed_fields = [
        "subject", "description", "status", "priority", "task_type",
        "start_date", "due_date", "assigned_to", "milestone",
        "estimated_hours", "progress", "parent_task",
        "estimated_cost", "actual_cost", "is_billable", "billing_rate"
    ]
    if _has_task_group():
        allowed_fields.append("task_group")
    if _has_depends_on_group():
        allowed_fields.append("depends_on_group")
    if _has_auto_trail_start():
        allowed_fields.append("auto_trail_start")

    updates = {}
    for field, value in data.items():
        if field in allowed_fields:
            updates[field] = value

    # Hammock tasks: reject manual date changes (dates are auto-calculated)
    if ("start_date" in updates or "due_date" in updates):
        try:
            sched_type = frappe.db.get_value("Orga Task", name, "task_scheduling_type")
            if sched_type == "Hammock":
                frappe.throw(_("Hammock task dates are auto-calculated and cannot be changed manually"))
        except Exception as e:
            frappe.log_error(f"Hammock check failed for {name}: {e}", "Orga Task Update")

    cascade_result = None

    if updates:
        # Validate dates if both are being set or one is changing
        doc = frappe.get_doc("Orga Task", name)
        new_start = updates.get("start_date", doc.start_date)
        new_due = updates.get("due_date", doc.due_date)
        if new_start and new_due:
            from frappe.utils import getdate
            if getdate(new_start) > getdate(new_due):
                frappe.throw(_("Due date cannot be before start date"))

        # Validate group dependency: can't depend on own group
        new_dog = updates.get("depends_on_group")
        current_tg = updates.get("task_group", getattr(doc, "task_group", None))
        if new_dog and current_tg and new_dog == current_tg:
            frappe.throw(_("Task cannot depend on the group it belongs to"))

        # Capture old dates before updating (for cascade calculation)
        old_start_date = str(doc.start_date) if doc.start_date else None
        old_end_date = str(doc.due_date) if doc.due_date else None
        dates_changed = ("start_date" in updates or "due_date" in updates)

        # Apply field updates individually (avoids schema mismatch with
        # doc.save() when task_group column doesn't exist yet)
        for field, value in updates.items():
            frappe.db.set_value("Orga Task", name, field, value, update_modified=True)

        # Handle completed_date auto-set
        if "status" in updates:
            if updates["status"] == "Completed" and not doc.completed_date:
                frappe.db.set_value("Orga Task", name, "completed_date", frappe.utils.nowdate(), update_modified=False)
            elif updates["status"] != "Completed" and doc.completed_date:
                frappe.db.set_value("Orga Task", name, "completed_date", None, update_modified=False)

        # Sync progress with status
        if "status" in updates:
            if updates["status"] == "Completed":
                frappe.db.set_value("Orga Task", name, "progress", 100, update_modified=False)
            elif updates["status"] == "Cancelled":
                frappe.db.set_value("Orga Task", name, "progress", 0, update_modified=False)

        # Recalculate blocked status when depends_on_group changes
        if "depends_on_group" in updates or "status" in updates:
            updated_doc = frappe.get_doc("Orga Task", name)
            updated_doc.update_blocked_status()
            frappe.db.set_value("Orga Task", name, "is_blocked", updated_doc.is_blocked, update_modified=False)

        # When status changes, update dependent tasks' blocked status and
        # send unblock notifications (mirrors on_update hook behavior)
        if "status" in updates:
            try:
                updated_doc = frappe.get_doc("Orga Task", name)
                updated_doc.update_dependent_tasks()
            except Exception as e:
                frappe.log_error(f"Dependent task update failed for {name}: {e}", "Orga Task Update")

        frappe.db.commit()

        # Auto-cascade dependent task dates if dates changed
        if dates_changed and doc.project:
            cascade_result = reschedule_dependents(name, old_start_date, old_end_date)

        # Advance FS successors when predecessor completes (via update_task too)
        if "status" in updates and updates["status"] == "Completed" and doc.project:
            mode = _get_project_dependency_mode(doc.project)
            if mode != "Off":
                _advance_successors_on_completion(name)

        # Trigger project progress/spent/estimated recalculation
        project = doc.project
        if project and frappe.db.exists("Orga Project", project):
            try:
                project_doc = frappe.get_doc("Orga Project", project)
                project_doc.update_progress()
                project_doc.update_spent()
                project_doc.update_estimated_cost()
            except Exception as e:
                # Non-critical: progress will sync on next load
                frappe.log_error(f"Project progress update failed for {project}: {e}", "Orga Task Update")

    doc = frappe.get_doc("Orga Task", name)
    result = doc.as_dict()

    # Include cascade info in response for frontend
    if cascade_result:
        result["_cascade"] = cascade_result

    return result


@frappe.whitelist()
def update_task_status(name, status):
    """
    Quick status update for Kanban operations.

    Args:
        name: Task name/ID
        status: New status (Open, In Progress, Review, Completed, Cancelled)

    Returns:
        dict: Updated task data
    """
    if not name:
        frappe.throw(_("Task name is required"))

    valid_statuses = ["Open", "In Progress", "Review", "Completed", "Cancelled"]
    if status not in valid_statuses:
        frappe.throw(_("Invalid status: {0}. Must be one of: {1}").format(
            status, ", ".join(valid_statuses)
        ))

    if not frappe.db.exists("Orga Task", name):
        frappe.throw(_("Task {0} not found").format(name), frappe.DoesNotExistError)

    # Use doc.save() instead of db.set_value so that on_update hooks fire
    # (update_dependent_tasks, blocked status, unblock notifications, etc.)
    doc = frappe.get_doc("Orga Task", name)
    doc.status = status
    doc.save()
    frappe.db.commit()

    # Advance FS successors when predecessor completes
    # This runs whenever dependency_mode is not "Off" — no separate toggle needed.
    # Successors move to start right after completion (today + lag or their current
    # start, whichever is earlier).
    if status == "Completed" and doc.project:
        mode = _get_project_dependency_mode(doc.project)
        if mode != "Off":
            _advance_successors_on_completion(name)

    doc.reload()
    return doc.as_dict()


def _advance_successors_on_completion(task_name):
    """When a predecessor completes, snap FS successors to the earliest valid start.

    The new start_date for each successor = max(today, completed_task_due_date + 1) + lag.
    This means:
    - If the predecessor finished early, successor starts tomorrow (or today + lag)
    - If the predecessor finished on time, successor starts the day after the due date
    - Duration is always preserved (end date shifts by the same amount as start)

    Skips successors that are Completed/Cancelled or have other incomplete FS predecessors.
    """
    from frappe.utils import getdate, nowdate, add_days
    import datetime

    today = getdate(nowdate())

    # Get the completed task's due_date to calculate the anchor point
    completed_due = frappe.db.get_value("Orga Task", task_name, "due_date")
    anchor = today
    if completed_due:
        # The day after the predecessor ends
        day_after_pred = getdate(completed_due) + datetime.timedelta(days=1)
        # Use whichever is closer to now (logical closest time)
        anchor = max(today, day_after_pred)

    # Find FS successors
    successors = frappe.db.sql("""
        SELECT td.parent, td.lag_days
        FROM `tabOrga Task Dependency` td
        WHERE td.depends_on = %s AND td.dependency_type = 'Finish to Start'
    """, (task_name,), as_dict=True)

    for succ in successors:
        succ_task = frappe.db.get_value(
            "Orga Task", succ.parent,
            ["start_date", "due_date", "status"],
            as_dict=True
        )
        if not succ_task or succ_task.status in ("Completed", "Cancelled"):
            continue

        # Check if ALL FS predecessors of this successor are completed
        # (don't advance if other predecessors are still pending)
        all_preds_done = True
        all_preds = frappe.db.sql("""
            SELECT td.depends_on
            FROM `tabOrga Task Dependency` td
            WHERE td.parent = %s AND td.dependency_type = 'Finish to Start'
        """, (succ.parent,), as_dict=True)

        for pred in all_preds:
            pred_status = frappe.db.get_value("Orga Task", pred.depends_on, "status")
            if pred_status != "Completed":
                all_preds_done = False
                break

        if not all_preds_done:
            continue

        lag = succ.lag_days or 0
        new_start = getdate(add_days(anchor, lag))

        # Only move if the new start is different from current
        if not succ_task.start_date or getdate(succ_task.start_date) == new_start:
            continue

        # Maintain task duration
        if succ_task.start_date and succ_task.due_date:
            duration = (getdate(succ_task.due_date) - getdate(succ_task.start_date)).days
            new_end = add_days(new_start, duration)
            frappe.db.set_value("Orga Task", succ.parent, "due_date", str(new_end), update_modified=True)

        frappe.db.set_value("Orga Task", succ.parent, "start_date", str(new_start), update_modified=True)

    frappe.db.commit()


@frappe.whitelist()
def get_tasks_by_status(project):
    """
    Get tasks grouped by status for Kanban view.

    Args:
        project: Project name/ID

    Returns:
        dict: Tasks grouped by status {Open: [...], In Progress: [...], ...}
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": project},
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "due_date",
            "assigned_to",
            "progress",
            "task_type",
            "estimated_hours",
            "is_blocked"
        ],
        order_by="due_date asc, priority desc"
    )

    # Enrich with assignee names and resource info
    for task in tasks:
        _enrich_assigned_to(task)
        _enrich_task_resource(task)

    # Group by status
    grouped = {
        "Open": [],
        "In Progress": [],
        "Review": [],
        "Completed": [],
        "Cancelled": []
    }

    for task in tasks:
        if task["status"] in grouped:
            grouped[task["status"]].append(task)

    return grouped


@frappe.whitelist()
def get_task_groups(project):
    """
    Get distinct task group names for a project.

    Args:
        project: Project name/ID

    Returns:
        list: Distinct group names sorted alphabetically
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not _has_task_group():
        return []

    result = frappe.db.sql("""
        SELECT DISTINCT task_group
        FROM `tabOrga Task`
        WHERE project = %s AND task_group IS NOT NULL AND task_group != ''
        ORDER BY task_group ASC
    """, project, as_list=True)

    return [row[0] for row in result]


@frappe.whitelist()
def get_group_dependency_status(project, group_name):
    """
    Get completion status of a task group within a project.

    Args:
        project: Project name/ID
        group_name: Task group name to check

    Returns:
        dict: {total: int, completed: int, incomplete: int, is_complete: bool, tasks: [...]}
    """
    if not project or not group_name:
        return {"total": 0, "completed": 0, "incomplete": 0, "is_complete": True, "tasks": []}

    if not _has_task_group():
        return {"total": 0, "completed": 0, "incomplete": 0, "is_complete": True, "tasks": []}

    tasks = frappe.get_all(
        "Orga Task",
        filters={
            "project": project,
            "task_group": group_name
        },
        fields=["name", "subject", "status"]
    )

    completed = sum(1 for t in tasks if t.status in ("Completed", "Cancelled"))

    return {
        "total": len(tasks),
        "completed": completed,
        "incomplete": len(tasks) - completed,
        "is_complete": completed == len(tasks),
        "tasks": tasks
    }


@frappe.whitelist()
def delete_task(name):
    """
    Delete a task.

    Args:
        name: Task name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", name):
        frappe.throw(_("Task {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Task", "delete", name):
        frappe.throw(_("Not permitted to delete this task"), frappe.PermissionError)

    # Check for subtasks
    subtasks = frappe.db.count("Orga Task", {"parent_task": name})
    if subtasks > 0:
        frappe.throw(_("Cannot delete task with {0} subtasks. Delete subtasks first.").format(subtasks))

    # Clean up linked records before deleting

    # Remove dependency rows in OTHER tasks that reference this task
    # (i.e., other tasks that depend on the task being deleted)
    dep_rows = frappe.db.sql("""
        SELECT name, parent FROM `tabOrga Task Dependency`
        WHERE depends_on = %s
    """, (name,), as_dict=True)
    for dep_row in dep_rows:
        frappe.db.delete("Orga Task Dependency", {"name": dep_row.name})
        # Clear cached doc so Frappe doesn't see stale child rows
        frappe.clear_document_cache("Orga Task", dep_row.parent)

    # Delete assignments (meaningless without the task)
    for assignment in frappe.get_all("Orga Assignment", filters={"task": name}, pluck="name"):
        frappe.delete_doc("Orga Assignment", assignment, force=True)

    # Clear task reference on time logs, appointments, defects (preserve the records)
    frappe.db.set_value("Orga Time Log", {"task": name}, "task", "", update_modified=False)
    frappe.db.set_value("Orga Appointment", {"task": name}, "task", "", update_modified=False)
    if frappe.db.exists("DocType", "Orga Defect"):
        frappe.db.set_value("Orga Defect", {"task": name}, "task", "", update_modified=False)

    # Delete notifications referencing this task (Dynamic Link)
    if frappe.db.exists("DocType", "Orga Notification"):
        for notif in frappe.get_all("Orga Notification",
            filters={"reference_doctype": "Orga Task", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Notification", notif, force=True)

    # Delete activity comments and reactions referencing this task
    if frappe.db.exists("DocType", "Orga Activity Comment"):
        for comment in frappe.get_all("Orga Activity Comment",
            filters={"reference_doctype": "Orga Task", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Activity Comment", comment, force=True)
    if frappe.db.exists("DocType", "Orga Activity Reaction"):
        for reaction in frappe.get_all("Orga Activity Reaction",
            filters={"reference_doctype": "Orga Task", "reference_name": name}, pluck="name"):
            frappe.delete_doc("Orga Activity Reaction", reaction, force=True)

    frappe.delete_doc("Orga Task", name, force=True)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_my_tasks(status=None, priority=None, project=None, assigned_to=None, search=None, limit=20, offset=0, include_completed=False, scope="assigned", sort_by="due_date", sort_dir="asc"):
    """
    Get tasks for the current user based on scope.

    Args:
        status: Optional status filter (e.g. "Open", "In Progress")
        priority: Optional priority filter (e.g. "High", "Urgent")
        project: Optional project filter (Orga Project name)
        assigned_to: Optional assigned_to filter (User email)
        search: Optional search string (matches subject via LIKE)
        limit: Maximum results (default 20)
        offset: Pagination offset (default 0)
        include_completed: If True, include Completed/Cancelled tasks when no status filter
        scope: Task scope - "assigned" (default), "my_projects", or "all"
        sort_by: Sort field - "due_date" (default), "subject", "project", "priority", "status"
        sort_dir: Sort direction - "asc" (default) or "desc"

    Returns:
        dict: {tasks: [...], total: int}
    """
    user = frappe.session.user

    # Validate sort parameters (whitelist to prevent SQL injection)
    allowed_sort_fields = {
        "subject": "subject",
        "project": "project",
        "priority": "priority",
        "status": "status",
        "due_date": "due_date",
    }
    if sort_by not in allowed_sort_fields:
        sort_by = "due_date"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"

    # Build order_by clause
    if sort_by == "priority":
        # Use FIELD() for correct semantic ordering: Urgent > High > Medium > Low
        if sort_dir == "desc":
            order_by = "FIELD(priority, 'Urgent', 'High', 'Medium', 'Low') ASC"
        else:
            order_by = "FIELD(priority, 'Urgent', 'High', 'Medium', 'Low') DESC"
    else:
        sort_col = allowed_sort_fields[sort_by]
        order_by = f"{sort_col} {sort_dir}"

    # Validate scope
    if scope not in ("assigned", "my_projects", "all"):
        scope = "assigned"

    # "all" scope requires elevated role
    if scope == "all":
        user_roles = frappe.get_roles(user)
        if "Administrator" not in user_roles and "Orga Manager" not in user_roles:
            frappe.throw(_("Insufficient permissions to view all tasks"), frappe.PermissionError)

    fields = [
        "name",
        "subject",
        "status",
        "priority",
        "start_date",
        "due_date",
        "assigned_to",
        "project",
        "progress",
        "modified"
    ]

    filters = frappe._dict()

    if status:
        filters["status"] = status
    elif not include_completed:
        filters["status"] = ["not in", ["Completed", "Cancelled"]]

    if priority:
        filters["priority"] = priority
    if project:
        filters["project"] = project
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if search:
        filters["subject"] = ["like", f"%{search}%"]

    if scope == "assigned":
        # Collect all task names belonging to the user (direct + resource-based)
        # then use a simple IN filter — avoids or_filters which can be unreliable
        direct_assigned = frappe.get_all(
            "Orga Task",
            filters={"assigned_to": user},
            pluck="name"
        )
        resource_assigned = _get_resource_assigned_task_names(user)
        my_task_names = list(set(direct_assigned + resource_assigned))
        if not my_task_names:
            return {"tasks": [], "total": 0}
        filters["name"] = ["in", my_task_names]

    elif scope == "my_projects":
        # Tasks from projects where user is project_manager
        my_projects = frappe.get_all(
            "Orga Project",
            filters={"project_manager": user},
            pluck="name"
        )
        if not my_projects:
            return {"tasks": [], "total": 0}
        # If a specific project filter was passed, intersect with managed projects
        if project and project in my_projects:
            filters["project"] = project
        elif project and project not in my_projects:
            return {"tasks": [], "total": 0}
        else:
            filters["project"] = ["in", my_projects]

    # scope == "all": no additional filters needed

    tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=fields,
        order_by=order_by,
        limit_page_length=int(limit),
        limit_start=int(offset),
    )

    total = frappe.db.count("Orga Task", filters)

    # Enrich with project names and assignee names
    for task in tasks:
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )
        _enrich_assigned_to(task)

    return {"tasks": tasks, "total": total}


@frappe.whitelist()
def bulk_update_status(tasks, status):
    """
    Update status for multiple tasks.

    Args:
        tasks: List of task names or JSON string
        status: New status

    Returns:
        dict: {success: True, updated: int}
    """
    if isinstance(tasks, str):
        tasks = json.loads(tasks)

    valid_statuses = ["Open", "In Progress", "Review", "Completed", "Cancelled"]
    if status not in valid_statuses:
        frappe.throw(_("Invalid status: {0}").format(status))

    updated = 0
    for task_name in tasks:
        if frappe.db.exists("Orga Task", task_name):
            if not frappe.has_permission("Orga Task", "write", task_name):
                frappe.throw(
                    _("Not permitted to update task {0}").format(task_name),
                    frappe.PermissionError
                )
            frappe.db.set_value("Orga Task", task_name, "status", status, update_modified=True)
            updated += 1

    frappe.db.commit()

    return {"success": True, "updated": updated}


# ============================================================================
# CHECKLIST OPERATIONS
# ============================================================================

@frappe.whitelist()
def get_task_checklist(task_name):
    """
    Get all checklist items for a task.

    Args:
        task_name: Task name/ID

    Returns:
        list: Checklist items with completion status
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    task = frappe.get_doc("Orga Task", task_name)
    checklist = []

    for item in task.checklist:
        checklist.append({
            "name": item.name,
            "title": item.title,
            "is_completed": item.is_completed,
            "completed_by": item.completed_by,
            "completed_by_name": frappe.db.get_value("User", item.completed_by, "full_name") if item.completed_by else None,
            "completed_on": item.completed_on
        })

    return checklist


@frappe.whitelist()
def add_checklist_item(task_name, title):
    """
    Add a new checklist item to a task.

    Args:
        task_name: Task name/ID
        title: Checklist item title

    Returns:
        dict: Created checklist item data
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not title:
        frappe.throw(_("Checklist item title is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    # Get current count for idx
    existing_count = frappe.db.count("Orga Task Checklist", {"parent": task_name})

    item = frappe.get_doc({
        "doctype": "Orga Task Checklist",
        "parent": task_name,
        "parenttype": "Orga Task",
        "parentfield": "checklist",
        "idx": existing_count + 1,
        "title": title,
        "is_completed": 0
    })
    item.insert()
    frappe.db.commit()

    return {
        "name": item.name,
        "title": item.title,
        "is_completed": item.is_completed,
        "completed_by": item.completed_by,
        "completed_on": getattr(item, "completed_on", None)
    }


@frappe.whitelist()
def toggle_checklist_item(task_name, item_name):
    """
    Toggle completion status of a checklist item.

    Args:
        task_name: Task name/ID
        item_name: Checklist item name/ID

    Returns:
        dict: Updated checklist item data
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not item_name:
        frappe.throw(_("Checklist item name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    # Get the checklist item directly
    if not frappe.db.exists("Orga Task Checklist", item_name):
        frappe.throw(_("Checklist item {0} not found in task").format(item_name))

    item = frappe.get_doc("Orga Task Checklist", item_name)
    if item.parent != task_name:
        frappe.throw(_("Checklist item {0} not found in task").format(item_name))

    # Toggle completion using db_set to avoid parent save
    new_completed = not item.is_completed
    if new_completed:
        frappe.db.set_value("Orga Task Checklist", item_name, {
            "is_completed": 1,
            "completed_by": frappe.session.user,
            "completed_on": now_datetime()
        })
    else:
        frappe.db.set_value("Orga Task Checklist", item_name, {
            "is_completed": 0,
            "completed_by": None,
            "completed_on": None
        })
    frappe.db.commit()

    # Return updated item
    item.reload()
    return {
        "name": item.name,
        "title": item.title,
        "is_completed": item.is_completed,
        "completed_by": item.completed_by,
        "completed_by_name": frappe.db.get_value("User", item.completed_by, "full_name") if item.completed_by else None,
        "completed_on": item.completed_on
    }


@frappe.whitelist()
def delete_checklist_item(task_name, item_name):
    """
    Delete a checklist item from a task.

    Args:
        task_name: Task name/ID
        item_name: Checklist item name/ID

    Returns:
        dict: {success: True}
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not item_name:
        frappe.throw(_("Checklist item name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Task Checklist", item_name):
        frappe.throw(_("Checklist item {0} not found in task").format(item_name))

    item = frappe.get_doc("Orga Task Checklist", item_name)
    if item.parent != task_name:
        frappe.throw(_("Checklist item {0} not found in task").format(item_name))

    frappe.delete_doc("Orga Task Checklist", item_name, force=True)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def promote_checklist_to_task(task_name, item_name):
    """
    Promote a checklist item to a full Orga Task.

    Creates a new task from the checklist item's title, inheriting the parent
    task's project and priority, then removes the checklist item.

    Args:
        task_name: Parent task name/ID
        item_name: Checklist item name/ID

    Returns:
        dict: {name: str, subject: str} of the newly created task
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not item_name:
        frappe.throw(_("Checklist item name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Task Checklist", item_name):
        frappe.throw(_("Checklist item {0} not found").format(item_name))

    item = frappe.get_doc("Orga Task Checklist", item_name)
    if item.parent != task_name:
        frappe.throw(_("Checklist item {0} not found in task").format(item_name))

    parent_task = frappe.get_doc("Orga Task", task_name)

    # Create new task from checklist item
    new_task = frappe.get_doc({
        "doctype": "Orga Task",
        "subject": item.title,
        "project": parent_task.project,
        "status": "Open",
        "priority": parent_task.priority or "Medium",
        "milestone": parent_task.milestone,
        "parent_task": task_name,
    })
    new_task.insert()

    # Remove the checklist item
    frappe.delete_doc("Orga Task Checklist", item_name, force=True)
    frappe.db.commit()

    return {"name": new_task.name, "subject": new_task.subject}


# ============================================================================
# COMMENT OPERATIONS
# ============================================================================

@frappe.whitelist()
def get_task_comments(task_name):
    """
    Get all comments for a task.

    Args:
        task_name: Task name/ID

    Returns:
        list: Comments with user info, ordered by time descending
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    task = frappe.get_doc("Orga Task", task_name)
    comments = []

    for item in task.comments:
        comments.append({
            "name": item.name,
            "content": item.content,
            "comment_by": item.comment_by,
            "comment_by_name": frappe.db.get_value("User", item.comment_by, "full_name") if item.comment_by else None,
            "comment_time": item.comment_time
        })

    # Sort by time descending (most recent first)
    comments.sort(key=lambda x: x["comment_time"] or "", reverse=True)
    return comments


@frappe.whitelist()
def add_task_comment(task_name, content):
    """
    Add a comment to a task.

    Args:
        task_name: Task name/ID
        content: Comment text

    Returns:
        dict: Created comment data
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not content or not content.strip():
        frappe.throw(_("Comment content is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    # Get current count for idx
    existing_count = frappe.db.count("Orga Task Comment", {"parent": task_name})

    item = frappe.get_doc({
        "doctype": "Orga Task Comment",
        "parent": task_name,
        "parenttype": "Orga Task",
        "parentfield": "comments",
        "idx": existing_count + 1,
        "content": content.strip(),
        "comment_by": frappe.session.user,
        "comment_time": now_datetime()
    })
    item.insert()
    frappe.db.commit()

    return {
        "name": item.name,
        "content": item.content,
        "comment_by": item.comment_by,
        "comment_by_name": frappe.db.get_value("User", item.comment_by, "full_name") if item.comment_by else None,
        "comment_time": item.comment_time
    }


@frappe.whitelist()
def delete_task_comment(task_name, comment_name):
    """
    Delete a comment from a task.

    Args:
        task_name: Task name/ID
        comment_name: Comment name/ID

    Returns:
        dict: {success: True}
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Task Comment", comment_name):
        frappe.throw(_("Comment {0} not found in task").format(comment_name))

    item = frappe.get_doc("Orga Task Comment", comment_name)
    if item.parent != task_name:
        frappe.throw(_("Comment {0} not found in task").format(comment_name))

    # Only allow deletion by comment author or managers
    if item.comment_by != frappe.session.user and "Orga Manager" not in frappe.get_roles():
        frappe.throw(_("You can only delete your own comments"), frappe.PermissionError)

    frappe.delete_doc("Orga Task Comment", comment_name, force=True)
    frappe.db.commit()
    return {"success": True}


# ============================================================================
# DEPENDENCY OPERATIONS
# ============================================================================

@frappe.whitelist()
def get_task_dependencies(task_name):
    """
    Get dependencies for a task.

    Args:
        task_name: Task name/ID

    Returns:
        dict: {predecessors: [...], successors: [...], is_blocked: bool}
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    task = frappe.get_doc("Orga Task", task_name)

    # Map full dependency type names to short codes for frontend
    type_short = {
        "Finish to Start": "FS",
        "Start to Start": "SS",
        "Finish to Finish": "FF",
        "Start to Finish": "SF",
    }

    # Tasks this depends on (predecessors)
    predecessors = []
    for dep in (task.depends_on or []):
        dep_task = frappe.db.get_value(
            "Orga Task", dep.depends_on,
            ["subject", "status"], as_dict=True
        )
        if dep_task:
            predecessors.append({
                "name": dep.name,
                "depends_on": dep.depends_on,
                "depends_on_subject": dep_task.subject,
                "depends_on_status": dep_task.status,
                "dependency_type": type_short.get(dep.dependency_type, "FS"),
                "lag_days": dep.lag_days
            })

    # Tasks that depend on this (successors)
    successors = frappe.db.sql("""
        SELECT td.parent AS name, td.parent AS task, t.subject AS task_subject,
               t.status AS task_status, td.dependency_type
        FROM `tabOrga Task Dependency` td
        JOIN `tabOrga Task` t ON td.parent = t.name
        WHERE td.depends_on = %s
    """, (task_name,), as_dict=True)

    for s in successors:
        s["dependency_type"] = type_short.get(s.get("dependency_type", ""), "FS")

    return {
        "predecessors": predecessors,
        "successors": successors,
        "is_blocked": task.is_blocked
    }


@frappe.whitelist()
def add_task_dependency(task_name, depends_on, dependency_type="Finish to Start", lag_days=0):
    """
    Add a dependency to a task.

    Args:
        task_name: Task name/ID
        depends_on: Task that this depends on
        dependency_type: Type of dependency
        lag_days: Lag in days

    Returns:
        dict: Updated dependencies
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not depends_on:
        frappe.throw(_("Depends on task is required"))

    if task_name == depends_on:
        frappe.throw(_("Task cannot depend on itself"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Task", depends_on):
        frappe.throw(_("Dependency task {0} not found").format(depends_on), frappe.DoesNotExistError)

    # Check if dependency already exists
    existing = frappe.db.exists("Orga Task Dependency", {
        "parent": task_name,
        "depends_on": depends_on
    })
    if existing:
        frappe.throw(_("Dependency already exists"))

    # Get current count for idx
    existing_count = frappe.db.count("Orga Task Dependency", {"parent": task_name})

    item = frappe.get_doc({
        "doctype": "Orga Task Dependency",
        "parent": task_name,
        "parenttype": "Orga Task",
        "parentfield": "depends_on",
        "idx": existing_count + 1,
        "depends_on": depends_on,
        "dependency_type": dependency_type,
        "lag_days": int(lag_days)
    })
    item.insert()
    frappe.db.commit()

    return get_task_dependencies(task_name)


@frappe.whitelist()
def remove_task_dependency(task_name=None, dependency_name=None, depends_on=None):
    """
    Remove a dependency from a task.

    Args:
        task_name: Task name/ID (optional if dependency_name provided)
        dependency_name: Child table row name (preferred)
        depends_on: Task to remove from dependencies (legacy, used if dependency_name not provided)

    Returns:
        dict: Updated dependencies
    """
    # Resolve task_name from dependency_name if not provided
    if dependency_name and not task_name:
        task_name = frappe.db.get_value("Orga Task Dependency", dependency_name, "parent")

    if not task_name:
        frappe.throw(_("Task name is required"))

    if not dependency_name and not depends_on:
        frappe.throw(_("Either dependency_name or depends_on is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if dependency_name:
        if frappe.db.exists("Orga Task Dependency", dependency_name):
            frappe.delete_doc("Orga Task Dependency", dependency_name, force=True)
    else:
        # Find by depends_on field
        dep_name = frappe.db.get_value("Orga Task Dependency", {
            "parent": task_name,
            "depends_on": depends_on
        })
        if dep_name:
            frappe.delete_doc("Orga Task Dependency", dep_name, force=True)

    frappe.db.commit()

    return get_task_dependencies(task_name)


@frappe.whitelist()
def update_task_dependency(dependency_name, dependency_type=None, lag_days=None):
    """
    Update an existing task dependency (type and/or lag days).

    Args:
        dependency_name: Child table row name (Orga Task Dependency)
        dependency_type: New dependency type (full form)
        lag_days: New lag days value

    Returns:
        dict: Updated dependencies for the parent task
    """
    if not dependency_name:
        frappe.throw(_("Dependency name is required"))

    task_name = frappe.db.get_value("Orga Task Dependency", dependency_name, "parent")
    if not task_name:
        frappe.throw(_("Dependency {0} not found").format(dependency_name), frappe.DoesNotExistError)

    updates = {}
    if dependency_type is not None:
        updates["dependency_type"] = dependency_type
    if lag_days is not None:
        updates["lag_days"] = int(lag_days)

    if updates:
        frappe.db.set_value("Orga Task Dependency", dependency_name, updates)
        frappe.db.commit()

    return get_task_dependencies(task_name)


# ============================================================================
# CASCADE OPERATIONS (Gantt Date Propagation)
# ============================================================================

@frappe.whitelist()
def preview_cascade(task_name, new_start_date=None, new_end_date=None):
    """
    Preview the cascade effect of date changes on dependent tasks.

    This endpoint calculates how changing a task's dates will affect all
    dependent tasks in the dependency chain, without making any changes.

    Args:
        task_name: Task being modified
        new_start_date: New start date (YYYY-MM-DD format)
        new_end_date: New end date (YYYY-MM-DD format)

    Returns:
        dict: {
            affected_tasks: list of tasks with calculated new dates,
            total_affected: number of affected tasks
        }
    """
    from frappe.utils import getdate, add_days

    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not new_start_date and not new_end_date:
        return {"affected_tasks": [], "total_affected": 0}

    task = frappe.get_doc("Orga Task", task_name)

    # Calculate date shift based on which date changed
    shift_days = 0
    if new_end_date and task.due_date:
        old_end = getdate(task.due_date)
        new_end = getdate(new_end_date)
        shift_days = (new_end - old_end).days
    elif new_start_date and task.start_date:
        old_start = getdate(task.start_date)
        new_start = getdate(new_start_date)
        shift_days = (new_start - old_start).days

    if shift_days == 0:
        return {"affected_tasks": [], "total_affected": 0}

    # Find all dependent tasks recursively
    affected = []
    visited = set()

    def find_dependents(t_name, shift, depth=0):
        # Prevent infinite loops (max depth of 100)
        if depth > 100:
            frappe.log_error(f"Cascade depth exceeded for task {t_name}")
            return

        # Find all tasks that depend on this task
        deps = frappe.db.sql("""
            SELECT td.parent, td.dependency_type, td.lag_days
            FROM `tabOrga Task Dependency` td
            WHERE td.depends_on = %s
        """, (t_name,), as_dict=True)

        for dep in deps:
            if dep.parent in visited:
                continue
            visited.add(dep.parent)

            dep_task = frappe.db.get_value(
                "Orga Task", dep.parent,
                ["name", "subject", "start_date", "due_date", "status"],
                as_dict=True
            )

            if not dep_task:
                continue

            # Calculate effective shift including lag
            lag_days = dep.lag_days or 0
            effective_shift = shift  # Lag affects when task can start, not the shift amount

            # Calculate new dates
            new_start = None
            new_end = None

            if dep_task.start_date:
                new_start = str(add_days(getdate(dep_task.start_date), effective_shift))
            if dep_task.due_date:
                new_end = str(add_days(getdate(dep_task.due_date), effective_shift))

            affected.append({
                "task_id": dep_task.name,
                "task_name": dep_task.subject,
                "status": dep_task.status,
                "field": "start_date",
                "old_value": str(dep_task.start_date) if dep_task.start_date else None,
                "new_value": new_start,
                "old_end_date": str(dep_task.due_date) if dep_task.due_date else None,
                "new_end_date": new_end,
                "days_shift": effective_shift,
                "dependency_type": dep.dependency_type,
                "lag_days": lag_days
            })

            # Recursively find dependents of this task
            find_dependents(dep.parent, effective_shift, depth + 1)

    find_dependents(task_name, shift_days)

    return {
        "affected_tasks": affected,
        "total_affected": len(affected)
    }


@frappe.whitelist()
def apply_cascade(task_name, new_start_date=None, new_end_date=None, changes=None):
    """
    Apply cascade date changes atomically.

    Updates the original task and all dependent tasks in a single transaction.

    Args:
        task_name: Original task being modified
        new_start_date: New start date for original task
        new_end_date: New end date for original task
        changes: JSON string of changes from preview_cascade (optional)
                 If not provided, will be calculated from preview_cascade

    Returns:
        dict: {success: True, updated_tasks: list of updated task names}
    """
    from frappe.utils import getdate, add_days

    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    # Get cascade changes
    if changes:
        if isinstance(changes, str):
            changes_list = json.loads(changes)
        else:
            changes_list = changes
    else:
        # Calculate cascade if not provided
        preview = preview_cascade(task_name, new_start_date, new_end_date)
        changes_list = preview.get("affected_tasks", [])

    updated_tasks = []

    try:
        # Update the original task first (use db_set to avoid schema mismatch)
        if new_start_date:
            frappe.db.set_value("Orga Task", task_name, "start_date", new_start_date, update_modified=True)
        if new_end_date:
            frappe.db.set_value("Orga Task", task_name, "due_date", new_end_date, update_modified=True)
        updated_tasks.append(task_name)

        # Update all dependent tasks
        for change in changes_list:
            tid = change["task_id"]
            if change.get("new_value"):
                frappe.db.set_value("Orga Task", tid, "start_date", change["new_value"], update_modified=True)
            if change.get("new_end_date"):
                frappe.db.set_value("Orga Task", tid, "due_date", change["new_end_date"], update_modified=True)
            updated_tasks.append(tid)

        frappe.db.commit()

        return {
            "success": True,
            "updated_tasks": updated_tasks,
            "total_updated": len(updated_tasks)
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Cascade apply failed: {str(e)}")
        frappe.throw(_("Failed to apply cascade changes: {0}").format(str(e)))


def _get_project_dependency_mode(project_name):
    """Get the dependency mode for a project. Returns 'Flexible' if not set."""
    if not project_name or not frappe.db.exists("Orga Project", project_name):
        return "Flexible"
    try:
        if not frappe.db.has_column("Orga Project", "dependency_mode"):
            return "Flexible"
        mode = frappe.db.get_value("Orga Project", project_name, "dependency_mode")
        return mode or "Flexible"
    except Exception as e:
        frappe.log_error(f"Dependency mode check failed for {project_name}: {e}", "Orga Task")
        return "Flexible"


def _get_project_auto_schedule_on_completion(project_name):
    """Check if auto-schedule on completion is enabled for a project."""
    if not project_name or not frappe.db.exists("Orga Project", project_name):
        return False
    try:
        if not frappe.db.has_column("Orga Project", "auto_schedule_on_completion"):
            return False
        return bool(frappe.db.get_value("Orga Project", project_name, "auto_schedule_on_completion"))
    except Exception as e:
        frappe.log_error(f"Auto schedule check failed for {project_name}: {e}", "Orga Task")
        return False


@frappe.whitelist()
def reschedule_dependents(task_name, old_start_date=None, old_end_date=None):
    """
    Reschedule dependent tasks after a task's dates change.

    Calculates the date shift and propagates it to all successor tasks
    in the dependency chain. Respects the project's dependency_mode setting.

    Args:
        task_name: Task whose dates changed
        old_start_date: Previous start date (YYYY-MM-DD)
        old_end_date: Previous end date (YYYY-MM-DD)

    Returns:
        dict: {success: bool, updated_tasks: list, total_updated: int, mode: str}
    """
    from frappe.utils import getdate

    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    task = frappe.get_doc("Orga Task", task_name)
    mode = _get_project_dependency_mode(task.project)

    if mode == "Off":
        return {"success": True, "updated_tasks": [], "total_updated": 0, "mode": "Off"}

    # Calculate new dates from current task state
    new_start_date = str(task.start_date) if task.start_date else None
    new_end_date = str(task.due_date) if task.due_date else None

    # Use preview_cascade to calculate affected tasks
    preview = preview_cascade(task_name, new_start_date, new_end_date)
    affected = preview.get("affected_tasks", [])

    if not affected:
        return {"success": True, "updated_tasks": [], "total_updated": 0, "mode": mode}

    if mode == "Flexible":
        # In Flexible mode, return preview for frontend confirmation
        return {
            "success": True,
            "mode": "Flexible",
            "cascade_preview": affected,
            "total_affected": len(affected),
            "updated_tasks": []
        }

    # Strict mode: apply cascade automatically
    updated_tasks = []
    try:
        for change in affected:
            tid = change["task_id"]
            if change.get("new_value"):
                frappe.db.set_value("Orga Task", tid, "start_date", change["new_value"], update_modified=True)
            if change.get("new_end_date"):
                frappe.db.set_value("Orga Task", tid, "due_date", change["new_end_date"], update_modified=True)
            updated_tasks.append(tid)

        # Recalculate blocked status for all affected tasks
        for tid in updated_tasks:
            t = frappe.get_doc("Orga Task", tid)
            t.update_blocked_status()
            frappe.db.set_value("Orga Task", tid, "is_blocked", t.is_blocked, update_modified=False)

        frappe.db.commit()

        return {
            "success": True,
            "mode": "Strict",
            "updated_tasks": updated_tasks,
            "total_updated": len(updated_tasks)
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Reschedule dependents failed: {str(e)}")
        frappe.throw(_("Failed to reschedule dependent tasks: {0}").format(str(e)))


@frappe.whitelist()
def check_circular_dependency(task_name, depends_on):
    """
    Check if adding a dependency would create a circular reference.

    Args:
        task_name: Task that would have the dependency
        depends_on: Task that would be the dependency target

    Returns:
        dict: {has_circular: bool, cycle_path: list if circular}
    """
    if not task_name or not depends_on:
        frappe.throw(_("Both task_name and depends_on are required"))

    if task_name == depends_on:
        return {
            "has_circular": True,
            "cycle_path": [task_name, depends_on],
            "message": _("Task cannot depend on itself")
        }

    # Check if depends_on eventually depends on task_name
    visited = set()
    path = []

    def check_deps(current_task, target_task):
        if current_task in visited:
            return False
        visited.add(current_task)
        path.append(current_task)

        # Get tasks that current_task depends on
        deps = frappe.get_all(
            "Orga Task Dependency",
            filters={"parent": current_task},
            fields=["depends_on"]
        )

        for dep in deps:
            if dep.depends_on == target_task:
                path.append(target_task)
                return True
            if check_deps(dep.depends_on, target_task):
                return True

        path.pop()
        return False

    # Check if depends_on has any path back to task_name
    has_circular = check_deps(depends_on, task_name)

    if has_circular:
        return {
            "has_circular": True,
            "cycle_path": path,
            "message": _("Adding this dependency would create a circular reference: {0}").format(
                " → ".join(path)
            )
        }

    return {
        "has_circular": False,
        "cycle_path": [],
        "message": None
    }


@frappe.whitelist()
def get_gantt_tasks(project):
    """
    Get tasks formatted for Gantt chart display.

    Returns tasks with dependency info, budget info, and blocked status.

    Args:
        project: Project name/ID

    Returns:
        list: Tasks with Gantt-specific fields
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    # Get all tasks for the project
    # Order by sort_order first (if set), then by dates
    gantt_fields = [
        "name",
        "subject",
        "description",
        "status",
        "priority",
        "start_date",
        "due_date",
        "completed_date",
        "assigned_to",
        "progress",
        "estimated_hours",
        "actual_hours",
        "parent_task",
        "is_blocked",
        "sort_order"
    ]
    if _has_task_group():
        gantt_fields.append("task_group")
    if _has_depends_on_group():
        gantt_fields.append("depends_on_group")

    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": project},
        fields=gantt_fields,
        order_by="sort_order asc, start_date asc, due_date asc"
    )

    # Get project budget info
    project_doc = frappe.db.get_value(
        "Orga Project", project,
        ["budget", "spent"],
        as_dict=True
    )

    # Enrich each task
    for task in tasks:
        # Add assignee name and image
        _enrich_assigned_to(task)
        _enrich_task_resource(task)

        # Calculate duration
        if task.start_date and task.due_date:
            from frappe.utils import date_diff
            task["duration"] = date_diff(task.due_date, task.start_date)
        else:
            task["duration"] = None

        # Get dependencies (tasks this depends on)
        deps = frappe.db.sql("""
            SELECT td.depends_on, t.subject, t.status, td.dependency_type, td.lag_days
            FROM `tabOrga Task Dependency` td
            JOIN `tabOrga Task` t ON td.depends_on = t.name
            WHERE td.parent = %s
        """, (task.name,), as_dict=True)

        task["dependencies_info"] = [{
            "task_id": d.depends_on,
            "task_name": d.subject,
            "status": d.status,
            "type": _convert_dependency_type(d.dependency_type),
            "lag": d.lag_days or 0
        } for d in deps]

        # Get dependents (tasks that depend on this)
        dependents = frappe.db.sql("""
            SELECT td.parent, t.subject, t.status, td.dependency_type, td.lag_days
            FROM `tabOrga Task Dependency` td
            JOIN `tabOrga Task` t ON td.parent = t.name
            WHERE td.depends_on = %s
        """, (task.name,), as_dict=True)

        task["dependents_info"] = [{
            "task_id": d.parent,
            "task_name": d.subject,
            "status": d.status,
            "type": _convert_dependency_type(d.dependency_type),
            "lag": d.lag_days or 0
        } for d in dependents]

        # Budget allocation (simplified - could be enhanced)
        task["budget"] = None
        task["spent"] = None
        if project_doc and project_doc.budget:
            # Distribute budget proportionally by estimated hours
            pass  # TODO: Implement budget distribution logic

    return tasks


def _convert_dependency_type(dep_type):
    """Convert long dependency type name to short code."""
    mapping = {
        "Finish to Start": "FS",
        "Start to Start": "SS",
        "Finish to Finish": "FF",
        "Start to Finish": "SF"
    }
    return mapping.get(dep_type, "FS")


@frappe.whitelist()
def reorder_tasks(project, task_id, new_index):
    """
    Reorder tasks within a project by updating sort_order values.

    This is used by the Gantt chart drag-and-drop row reordering feature.
    Tasks with sort_order=0 are sorted by start_date/due_date by default.
    After reordering, affected tasks get explicit sort_order values.

    Args:
        project: Project name/ID
        task_id: Task being moved
        new_index: Target position (0-based index in the task list)

    Returns:
        dict: {success: True, updated_tasks: list of updated task IDs}
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not task_id:
        frappe.throw(_("Task ID is required"))

    if new_index is None:
        frappe.throw(_("New index is required"))

    new_index = int(new_index)

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    if not frappe.has_permission("Orga Project", "write", project):
        frappe.throw(_("Not permitted to modify project {0}").format(project), frappe.PermissionError)

    if not frappe.db.exists("Orga Task", task_id):
        frappe.throw(_("Task {0} not found").format(task_id))

    # Check if sort_order column exists (migration may not have run yet)
    if not _has_sort_order():
        return {"success": False, "reason": "migration_required", "updated_tasks": []}

    # Get all tasks for the project ordered by current sort_order, then by date
    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": project},
        fields=["name", "sort_order", "start_date", "due_date"],
        order_by="sort_order asc, start_date asc, due_date asc, creation asc"
    )

    if not tasks:
        return {"success": True, "updated_tasks": []}

    # Find current index of the task being moved
    task_names = [t.name for t in tasks]
    if task_id not in task_names:
        frappe.throw(_("Task {0} not in project {1}").format(task_id, project))

    current_index = task_names.index(task_id)

    # Clamp new_index to valid range
    new_index = max(0, min(new_index, len(tasks) - 1))

    # If position unchanged, do nothing
    if current_index == new_index:
        return {"success": True, "updated_tasks": []}

    # Remove task from current position and insert at new position
    task_names.pop(current_index)
    task_names.insert(new_index, task_id)

    # Update sort_order for all tasks (1-based to distinguish from default 0)
    updated_tasks = []
    try:
        for idx, name in enumerate(task_names):
            frappe.db.set_value(
                "Orga Task",
                name,
                "sort_order",
                idx + 1,  # 1-based so 0 means "not explicitly ordered"
                update_modified=False
            )
            updated_tasks.append(name)

        frappe.db.commit()

        return {
            "success": True,
            "updated_tasks": updated_tasks,
            "new_order": task_names
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Task reorder failed: {str(e)}")
        frappe.throw(_("Failed to reorder tasks: {0}").format(str(e)))


@frappe.whitelist()
def batch_update_task_dates(updates):
    """
    Update dates for multiple tasks in a single transaction.

    Args:
        updates: JSON string or list of {task_id, start_date, end_date}

    Returns:
        dict: {success: True, updated: int, failed: list}
    """
    if isinstance(updates, str):
        updates = json.loads(updates)

    if not updates:
        return {"success": True, "updated": 0, "failed": []}

    updated = 0
    failed = []

    try:
        for update in updates:
            task_id = update.get("task_id")
            start_date = update.get("start_date")
            end_date = update.get("end_date") or update.get("due_date")

            if not task_id:
                failed.append({"task_id": None, "error": "Missing task_id"})
                continue

            if not frappe.db.exists("Orga Task", task_id):
                failed.append({"task_id": task_id, "error": "Task not found"})
                continue

            if not frappe.has_permission("Orga Task", "write", task_id):
                failed.append({"task_id": task_id, "error": "Permission denied"})
                continue

            if start_date:
                frappe.db.set_value("Orga Task", task_id, "start_date", start_date, update_modified=True)
            if end_date:
                frappe.db.set_value("Orga Task", task_id, "due_date", end_date, update_modified=True)
            updated += 1

        frappe.db.commit()

        return {
            "success": len(failed) == 0,
            "updated": updated,
            "failed": failed
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Batch update failed: {str(e)}")
        frappe.throw(_("Failed to update tasks: {0}").format(str(e)))


# ============================================================================
# ATTACHMENT OPERATIONS
# ============================================================================

@frappe.whitelist()
def get_task_attachments(task_name):
    """
    Get all file attachments for a task.

    Uses Frappe's built-in File DocType with attached_to_doctype/attached_to_name.

    Args:
        task_name: Task name/ID

    Returns:
        list: File records with name, file_name, file_url, file_size, file_type,
              is_private, creation, owner
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    attachments = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Orga Task",
            "attached_to_name": task_name,
        },
        fields=[
            "name", "file_name", "file_url", "file_size",
            "file_type", "is_private", "creation", "owner"
        ],
        order_by="creation desc"
    )

    return attachments


@frappe.whitelist()
def delete_task_attachment(task_name, file_name):
    """
    Delete a file attachment from a task.

    Verifies the File record belongs to the specified task before deleting.

    Args:
        task_name: Task name/ID
        file_name: File DocType name (not the filename string)

    Returns:
        dict: {success: True}
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    if not file_name:
        frappe.throw(_("File name is required"))

    if not frappe.db.exists("Orga Task", task_name):
        frappe.throw(_("Task {0} not found").format(task_name), frappe.DoesNotExistError)

    if not frappe.db.exists("File", file_name):
        frappe.throw(_("File {0} not found").format(file_name), frappe.DoesNotExistError)

    # Verify the file belongs to this task
    file_doc = frappe.get_doc("File", file_name)
    if file_doc.attached_to_doctype != "Orga Task" or file_doc.attached_to_name != task_name:
        frappe.throw(_("File does not belong to this task"), frappe.PermissionError)

    frappe.delete_doc("File", file_name)
    frappe.db.commit()

    return {"success": True}
