# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Assignment API endpoints for Orga.
"""

import json
import frappe
from frappe import _


@frappe.whitelist()
def get_assignments(task=None, resource=None, project=None, status=None, limit=100, offset=0):
    """
    Get assignments with optional filters.

    Args:
        task: Filter by task
        resource: Filter by resource
        project: Filter by project
        status: Filter by status
        limit: Max results
        offset: Pagination offset

    Returns:
        dict: {assignments: [...], total: int}
    """
    filters = {}
    if task:
        filters["task"] = task
    if resource:
        filters["resource"] = resource
    if project:
        filters["project"] = project
    if status:
        filters["status"] = status

    assignments = frappe.get_all(
        "Orga Assignment",
        filters=filters,
        fields=[
            "name", "task", "resource", "project", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="start_date desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Assignment", filters)

    # Enrich with names
    for assignment in assignments:
        assignment["task_subject"] = frappe.db.get_value(
            "Orga Task", assignment["task"], "subject"
        )
        assignment["resource_name"] = frappe.db.get_value(
            "Orga Resource", assignment["resource"], "resource_name"
        )
        if assignment["project"]:
            assignment["project_name"] = frappe.db.get_value(
                "Orga Project", assignment["project"], "project_name"
            )

    return {
        "assignments": assignments,
        "total": total
    }


@frappe.whitelist()
def get_assignment(name):
    """
    Get single assignment details.

    Args:
        name: Assignment name/ID

    Returns:
        dict: Assignment data
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Assignment", name)
    assignment = doc.as_dict()

    # Enrich
    assignment["task_subject"] = frappe.db.get_value(
        "Orga Task", assignment["task"], "subject"
    )
    assignment["resource_name"] = frappe.db.get_value(
        "Orga Resource", assignment["resource"], "resource_name"
    )
    if assignment["project"]:
        assignment["project_name"] = frappe.db.get_value(
            "Orga Project", assignment["project"], "project_name"
        )

    return assignment


@frappe.whitelist()
def create_assignment(task, resource, allocated_hours=None, start_date=None, end_date=None, role=None):
    """
    Create a task assignment.

    Args:
        task: Task name/ID
        resource: Resource name/ID
        allocated_hours: Hours to allocate
        start_date: Assignment start
        end_date: Assignment end
        role: Role on this task

    Returns:
        dict: Created assignment
    """
    if not task or not resource:
        frappe.throw(_("Task and resource are required"))

    if not frappe.db.exists("Orga Task", task):
        frappe.throw(_("Task {0} not found").format(task), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Resource", resource):
        frappe.throw(_("Resource {0} not found").format(resource), frappe.DoesNotExistError)

    doc = frappe.get_doc({
        "doctype": "Orga Assignment",
        "task": task,
        "resource": resource,
        "allocated_hours": float(allocated_hours) if allocated_hours else None,
        "start_date": start_date,
        "end_date": end_date,
        "role": role,
        "status": "Assigned"
    })
    doc.insert()
    frappe.db.commit()

    return get_assignment(doc.name)


@frappe.whitelist()
def update_assignment(name, data):
    """
    Update an assignment.

    Args:
        name: Assignment name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated assignment
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Assignment", name)

    allowed_fields = [
        "status", "role", "start_date", "end_date",
        "allocated_hours", "notes"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return get_assignment(doc.name)


@frappe.whitelist()
def delete_assignment(name):
    """
    Delete an assignment.

    Args:
        name: Assignment name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    frappe.delete_doc("Orga Assignment", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_task_assignments(task_name):
    """
    Get all assignments for a task.

    Args:
        task_name: Task name/ID

    Returns:
        list: Assignments with resource details
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    assignments = frappe.get_all(
        "Orga Assignment",
        filters={"task": task_name},
        fields=[
            "name", "resource", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="creation asc"
    )

    for assignment in assignments:
        resource = frappe.get_doc("Orga Resource", assignment["resource"])
        assignment["resource_name"] = resource.resource_name
        assignment["resource_email"] = resource.email
        assignment["resource_status"] = resource.status

        # Get initials
        name_parts = resource.resource_name.split()
        if len(name_parts) >= 2:
            assignment["initials"] = (name_parts[0][0] + name_parts[-1][0]).upper()
        else:
            assignment["initials"] = resource.resource_name[:2].upper()

    return assignments


@frappe.whitelist()
def get_resource_assignments(resource_name, status=None, include_completed=False):
    """
    Get all assignments for a resource.

    Args:
        resource_name: Resource name/ID
        status: Filter by status
        include_completed: Include completed assignments

    Returns:
        list: Assignments with task details
    """
    if not resource_name:
        frappe.throw(_("Resource name is required"))

    filters = {"resource": resource_name}

    if status:
        filters["status"] = status
    elif not include_completed:
        filters["status"] = ["in", ["Assigned", "In Progress"]]

    assignments = frappe.get_all(
        "Orga Assignment",
        filters=filters,
        fields=[
            "name", "task", "project", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="start_date asc"
    )

    for assignment in assignments:
        task = frappe.db.get_value(
            "Orga Task",
            assignment["task"],
            ["subject", "status", "priority", "due_date"],
            as_dict=True
        )
        assignment["task_subject"] = task.subject if task else None
        assignment["task_status"] = task.status if task else None
        assignment["task_priority"] = task.priority if task else None
        assignment["task_due_date"] = task.due_date if task else None

        if assignment["project"]:
            assignment["project_name"] = frappe.db.get_value(
                "Orga Project", assignment["project"], "project_name"
            )

    return assignments
