# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Time Log API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.timelog.get_time_logs',
        args: { task: 'TASK-00001' }
    })
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_seconds, today


VALID_CONTEXTS = ("task", "event", "project", "standalone")


@frappe.whitelist()
def get_time_logs(task=None, project=None, user=None, event=None,
                  tracking_context=None, limit=50, offset=0):
    """
    Get time logs with optional filters.

    Args:
        task: Filter by task
        project: Filter by project
        user: Filter by user
        event: Filter by event
        tracking_context: Filter by tracking context
        limit: Maximum results (default 50)
        offset: Pagination offset

    Returns:
        dict: {logs: [...], total: int}
    """
    filters = {"is_running": 0}
    if task:
        filters["task"] = task
    if project:
        filters["project"] = project
    if user:
        filters["user"] = user
    if event:
        filters["event"] = event
    if tracking_context:
        filters["tracking_context"] = tracking_context

    logs = frappe.get_all(
        "Orga Time Log",
        filters=filters,
        fields=[
            "name", "tracking_context", "task", "event", "project", "user",
            "log_date", "from_time", "to_time", "hours", "description",
            "billable", "is_running", "timer_started_at"
        ],
        order_by="log_date desc, modified desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Time Log", filters)

    # Enrich with display names
    for log in logs:
        if log.get("task"):
            log["task_subject"] = frappe.db.get_value("Orga Task", log["task"], "subject")
        if log.get("event"):
            log["event_subject"] = frappe.db.get_value("Orga Appointment", log["event"], "subject")
        if log.get("project"):
            log["project_name"] = frappe.db.get_value("Orga Project", log["project"], "project_name")
        log["user_name"] = frappe.db.get_value("User", log["user"], "full_name")

    return {"logs": logs, "total": total}


@frappe.whitelist()
def get_time_log(name):
    """
    Get a single time log.

    Args:
        name: Time log name/ID

    Returns:
        dict: Time log data
    """
    if not name:
        frappe.throw(_("Time log name is required"))

    if not frappe.db.exists("Orga Time Log", name):
        frappe.throw(_("Time log {0} not found").format(name), frappe.DoesNotExistError)

    log = frappe.get_doc("Orga Time Log", name)
    log_dict = log.as_dict()

    # Enrich with names
    if log.task:
        log_dict["task_subject"] = frappe.db.get_value("Orga Task", log.task, "subject")
    if log.event:
        log_dict["event_subject"] = frappe.db.get_value("Orga Appointment", log.event, "subject")
    log_dict["user_name"] = frappe.db.get_value("User", log.user, "full_name")
    if log.project:
        log_dict["project_name"] = frappe.db.get_value("Orga Project", log.project, "project_name")

    return log_dict


@frappe.whitelist()
def create_time_log(hours, task=None, event=None, project=None,
                    tracking_context="task", description=None,
                    from_time=None, log_date=None, billable=1):
    """
    Create a time log entry.

    Args:
        hours: Hours logged
        task: Task name/ID (required when context=task)
        event: Event name/ID (required when context=event)
        project: Project name/ID (required when context=project)
        tracking_context: One of task/event/project/standalone
        description: Optional description
        from_time: Optional start time (defaults to now)
        log_date: Optional date (defaults to today)
        billable: Whether billable (default 1)

    Returns:
        dict: Created time log data
    """
    if tracking_context not in VALID_CONTEXTS:
        frappe.throw(_("Invalid tracking context: {0}").format(tracking_context))

    if tracking_context == "task" and not task:
        frappe.throw(_("Task is required for task context"))
    if tracking_context == "event" and not event:
        frappe.throw(_("Event is required for event context"))
    if tracking_context == "project" and not project:
        frappe.throw(_("Project is required for project context"))

    doc = frappe.get_doc({
        "doctype": "Orga Time Log",
        "tracking_context": tracking_context,
        "task": task,
        "event": event,
        "project": project,
        "user": frappe.session.user,
        "log_date": log_date or today(),
        "from_time": from_time or None,
        "hours": float(hours),
        "description": description,
        "billable": int(billable)
    })
    if from_time:
        doc.flags.explicit_times = True
    doc.insert()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def update_time_log(name, hours=None, description=None, from_time=None, to_time=None):
    """
    Update a time log entry.

    Args:
        name: Time log name/ID
        hours: New hours value
        description: New description
        from_time: New start time
        to_time: New end time

    Returns:
        dict: Updated time log data
    """
    if not name:
        frappe.throw(_("Time log name is required"))

    if not frappe.db.exists("Orga Time Log", name):
        frappe.throw(_("Time log {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Time Log", name)

    if hours is not None:
        doc.hours = float(hours)
    if description is not None:
        doc.description = description
    if from_time is not None:
        doc.from_time = from_time
    if to_time is not None:
        doc.to_time = to_time

    doc.save()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def delete_time_log(name):
    """
    Delete a time log entry.

    Args:
        name: Time log name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Time log name is required"))

    if not frappe.db.exists("Orga Time Log", name):
        frappe.throw(_("Time log {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Time Log", "delete", name):
        frappe.throw(_("Not permitted to delete this time log"), frappe.PermissionError)

    frappe.delete_doc("Orga Time Log", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_time_summary(project=None, user=None, task=None, event=None,
                     tracking_context=None, group_by=None):
    """
    Get time summary statistics.

    Args:
        project: Filter by project
        user: Filter by user
        task: Filter by task
        event: Filter by event
        tracking_context: Filter by tracking context
        group_by: Group results by field (project/task/event/tracking_context)

    Returns:
        dict: Summary with total_hours, log_count, and optional grouped data
    """
    filters = ["is_running = 0"]
    values = {}

    if project:
        filters.append("project = %(project)s")
        values["project"] = project
    if user:
        filters.append("user = %(user)s")
        values["user"] = user
    if task:
        filters.append("task = %(task)s")
        values["task"] = task
    if event:
        filters.append("event = %(event)s")
        values["event"] = event
    if tracking_context:
        filters.append("tracking_context = %(tracking_context)s")
        values["tracking_context"] = tracking_context

    where_clause = " AND ".join(filters)

    # where_clause is built from hardcoded strings above (not user input),
    # and all dynamic values use %(name)s parameterization via the values dict.
    result = frappe.db.sql(
        "SELECT COALESCE(SUM(hours), 0) as total_hours, COUNT(*) as log_count"
        " FROM `tabOrga Time Log`"
        " WHERE {where_clause}".format(where_clause=where_clause),
        values,
        as_dict=True,
    )[0]

    VALID_GROUP_BY = {"project", "task", "event", "tracking_context"}
    if group_by and group_by in VALID_GROUP_BY:
        # group_by is validated against the strict whitelist above,
        # so interpolating it into the column position is safe.
        grouped = frappe.db.sql(
            "SELECT `{col}` as group_key,"
            " COALESCE(SUM(hours), 0) as total_hours,"
            " COUNT(*) as log_count"
            " FROM `tabOrga Time Log`"
            " WHERE {where_clause} AND `{col}` IS NOT NULL AND `{col}` != ''"
            " GROUP BY `{col}`"
            " ORDER BY total_hours DESC".format(
                col=group_by, where_clause=where_clause
            ),
            values,
            as_dict=True,
        )
        result["grouped"] = grouped

    return result


@frappe.whitelist()
def get_my_time_logs(limit=20):
    """
    Get current user's time logs.

    Args:
        limit: Maximum results (default 20)

    Returns:
        dict: {logs: [...], total: int}
    """
    return get_time_logs(user=frappe.session.user, limit=limit)


# ============================================
# Timer Endpoints
# ============================================


@frappe.whitelist()
def start_timer(tracking_context="standalone", task=None, event=None,
                project=None, description=None):
    """
    Start a new timer. Stops any existing running timer for the user.

    Args:
        tracking_context: One of task/event/project/standalone
        task: Task name (required when context=task)
        event: Event name (required when context=event)
        project: Project name (required when context=project)
        description: Optional work description

    Returns:
        dict: The created running time log
    """
    if tracking_context not in VALID_CONTEXTS:
        frappe.throw(_("Invalid tracking context: {0}").format(tracking_context))

    if tracking_context == "task" and not task:
        frappe.throw(_("Task is required for task context"))
    if tracking_context == "event" and not event:
        frappe.throw(_("Event is required for event context"))
    if tracking_context == "project" and not project:
        frappe.throw(_("Project is required for project context"))

    now = now_datetime()

    doc = frappe.get_doc({
        "doctype": "Orga Time Log",
        "tracking_context": tracking_context,
        "task": task,
        "event": event,
        "project": project,
        "user": frappe.session.user,
        "log_date": today(),
        "hours": 0,
        "is_running": 1,
        "timer_started_at": now,
        "description": description
    })
    doc.insert()
    frappe.db.commit()

    result = doc.as_dict()
    _enrich_timer(result)
    return result


@frappe.whitelist()
def stop_timer(name=None):
    """
    Stop the current user's running timer.

    Args:
        name: Optional specific timer name. If not provided, stops the active timer.

    Returns:
        dict: The completed time log with calculated hours
    """
    if name:
        if not frappe.db.exists("Orga Time Log", name):
            frappe.throw(_("Time log {0} not found").format(name), frappe.DoesNotExistError)
        doc = frappe.get_doc("Orga Time Log", name)
    else:
        running = frappe.get_all(
            "Orga Time Log",
            filters={"user": frappe.session.user, "is_running": 1},
            fields=["name"],
            limit=1
        )
        if not running:
            frappe.throw(_("No active timer found"))
        doc = frappe.get_doc("Orga Time Log", running[0].name)

    if not doc.is_running:
        frappe.throw(_("Timer is not running"))

    now = now_datetime()
    hours = 0
    if doc.timer_started_at:
        seconds = time_diff_in_seconds(now, doc.timer_started_at)
        hours = max(round(seconds / 3600, 4), 0)
    # Ensure at least a minimal value when timer actually ran
    if hours == 0 and doc.timer_started_at:
        hours = 0.01

    doc.is_running = 0
    doc.hours = hours
    doc.save()
    frappe.db.commit()

    result = doc.as_dict()
    _enrich_timer(result)
    return result


@frappe.whitelist()
def get_active_timer():
    """
    Get the current user's running timer, if any.

    Returns:
        dict or None: The running time log with enriched context, or None
    """
    running = frappe.get_all(
        "Orga Time Log",
        filters={"user": frappe.session.user, "is_running": 1},
        fields=[
            "name", "tracking_context", "task", "event", "project",
            "user", "description", "is_running", "timer_started_at",
            "log_date", "billable"
        ],
        limit=1
    )

    if not running:
        return None

    timer = running[0]
    _enrich_timer(timer)
    return timer


@frappe.whitelist()
def discard_timer(name=None):
    """
    Discard (delete) the current user's running timer without saving.

    Args:
        name: Optional specific timer name.

    Returns:
        dict: {success: True}
    """
    if name:
        if not frappe.db.exists("Orga Time Log", name):
            frappe.throw(_("Time log {0} not found").format(name), frappe.DoesNotExistError)
        doc = frappe.get_doc("Orga Time Log", name)
    else:
        running = frappe.get_all(
            "Orga Time Log",
            filters={"user": frappe.session.user, "is_running": 1},
            fields=["name"],
            limit=1
        )
        if not running:
            frappe.throw(_("No active timer found"))
        doc = frappe.get_doc("Orga Time Log", running[0].name)

    if not doc.is_running:
        frappe.throw(_("Timer is not running"))

    frappe.delete_doc("Orga Time Log", doc.name, force=True)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_today_summary():
    """
    Get today's time tracking summary for the current user.

    Returns:
        dict: {total_hours, log_count, logs: [...], active_timer: {...} or None}
    """
    user = frappe.session.user
    date = today()

    logs = frappe.get_all(
        "Orga Time Log",
        filters={
            "user": user,
            "log_date": date,
            "is_running": 0
        },
        fields=[
            "name", "tracking_context", "task", "event", "project",
            "hours", "description", "from_time", "to_time"
        ],
        order_by="modified desc"
    )

    total_hours = sum(log.hours or 0 for log in logs)

    # Enrich logs
    for log in logs:
        if log.get("task"):
            log["task_subject"] = frappe.db.get_value("Orga Task", log["task"], "subject")
        if log.get("event"):
            log["event_subject"] = frappe.db.get_value("Orga Appointment", log["event"], "subject")
        if log.get("project"):
            log["project_name"] = frappe.db.get_value("Orga Project", log["project"], "project_name")

    active_timer = get_active_timer()

    return {
        "total_hours": round(total_hours, 2),
        "log_count": len(logs),
        "logs": logs,
        "active_timer": active_timer
    }


def _enrich_timer(timer):
    """Add display names to a timer dict."""
    if timer.get("task"):
        timer["task_subject"] = frappe.db.get_value("Orga Task", timer["task"], "subject")
    if timer.get("event"):
        timer["event_subject"] = frappe.db.get_value("Orga Appointment", timer["event"], "subject")
    if timer.get("project"):
        timer["project_name"] = frappe.db.get_value("Orga Project", timer["project"], "project_name")
    timer["user_name"] = frappe.db.get_value("User", timer.get("user") or frappe.session.user, "full_name")
