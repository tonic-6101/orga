# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Milestone API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.milestone.create_milestone',
        args: { data: '{"milestone_name": "Phase 1", "project": "ORG-2026-0001"}' }
    })
"""

import json
import frappe
from frappe import _


def _has_sort_order() -> bool:
    """Check if sort_order column exists on Orga Milestone (pre-migration safe)."""
    try:
        return frappe.db.has_column("Orga Milestone", "sort_order")
    except Exception:
        return False


@frappe.whitelist()
def get_milestones(project, status=None, limit=50, offset=0):
    """
    Get milestones for a project.

    Args:
        project: Project name/ID
        status: Optional status filter (Upcoming, In Progress, Completed, Missed)
        limit: Maximum results (default 50)
        offset: Pagination offset

    Returns:
        dict: {milestones: [...], total: int}
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    filters = {"project": project}
    if status:
        filters["status"] = status

    has_sort = _has_sort_order()
    ms_fields = [
        "name", "milestone_name", "status", "due_date",
        "completed_date", "description", "completion_criteria", "modified"
    ]
    if has_sort:
        ms_fields.append("sort_order")

    milestones = frappe.get_all(
        "Orga Milestone",
        filters=filters,
        fields=ms_fields,
        order_by="sort_order asc, due_date asc" if has_sort else "due_date asc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Milestone", filters)

    # Calculate completion percentage for each milestone
    for milestone in milestones:
        milestone["completion_percentage"] = _calculate_milestone_completion(milestone["name"])
        milestone["task_count"] = frappe.db.count(
            "Orga Task",
            {"milestone": milestone["name"]}
        )

    return {"milestones": milestones, "total": total}


@frappe.whitelist()
def get_milestone(name):
    """
    Get single milestone with full details.

    Args:
        name: Milestone name/ID

    Returns:
        dict: Milestone data with linked tasks
    """
    if not name:
        frappe.throw(_("Milestone name is required"))

    if not frappe.db.exists("Orga Milestone", name):
        frappe.throw(_("Milestone {0} not found").format(name), frappe.DoesNotExistError)

    milestone = frappe.get_doc("Orga Milestone", name)
    milestone_dict = milestone.as_dict()

    # Add completion percentage
    milestone_dict["completion_percentage"] = _calculate_milestone_completion(name)

    # Add linked tasks
    milestone_dict["tasks"] = frappe.get_all(
        "Orga Task",
        filters={"milestone": name},
        fields=["name", "subject", "status", "priority", "assigned_to", "due_date"]
    )

    return milestone_dict


@frappe.whitelist()
def create_milestone(data):
    """
    Create a new milestone.

    Args:
        data: dict or JSON string with milestone fields
            Required: milestone_name, project
            Optional: due_date, description, status, completion_criteria

    Returns:
        dict: Created milestone data
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Validate required fields
    required = ["milestone_name", "project"]
    for field in required:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    # Validate project exists
    if not frappe.db.exists("Orga Project", data["project"]):
        frappe.throw(_("Project {0} not found").format(data["project"]))

    # Set default status if not provided
    if not data.get("status"):
        data["status"] = "Upcoming"

    allowed_fields = [
        "milestone_name", "project", "description", "status", "due_date",
        "completion_criteria", "sort_order"
    ]

    doc_data = {"doctype": "Orga Milestone"}
    for field in allowed_fields:
        if field in data:
            doc_data[field] = data[field]

    doc = frappe.get_doc(doc_data)
    doc.insert()
    frappe.db.commit()

    return {
        "name": doc.name,
        "milestone_name": doc.milestone_name,
        "status": doc.status,
        "due_date": doc.due_date,
        "project": doc.project
    }


@frappe.whitelist()
def update_milestone(name, data):
    """
    Update milestone fields.

    Args:
        name: Milestone name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated milestone data
    """
    if not name:
        frappe.throw(_("Milestone name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Milestone", name):
        frappe.throw(_("Milestone {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Milestone", name)

    # Update allowed fields
    allowed_fields = [
        "milestone_name", "description", "status", "due_date",
        "completion_criteria", "sort_order"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    result = doc.as_dict()
    result["completion_percentage"] = _calculate_milestone_completion(doc.name)
    return result


@frappe.whitelist()
def delete_milestone(name):
    """
    Delete a milestone.

    Args:
        name: Milestone name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Milestone name is required"))

    if not frappe.db.exists("Orga Milestone", name):
        frappe.throw(_("Milestone {0} not found").format(name), frappe.DoesNotExistError)

    # Unlink tasks from this milestone
    linked_tasks = frappe.db.count("Orga Task", {"milestone": name})
    if linked_tasks > 0:
        frappe.db.set_value("Orga Task", {"milestone": name}, "milestone", None)

    frappe.delete_doc("Orga Milestone", name)
    frappe.db.commit()

    return {"success": True, "unlinked_tasks": linked_tasks}


@frappe.whitelist()
def reorder_milestones(project, milestone_id, new_index):
    """
    Reorder milestones within a project by updating sort_order values.

    This is used by the Gantt chart drag-and-drop row reordering feature.
    Milestones with sort_order=0 are sorted by due_date by default.
    After reordering, affected milestones get explicit sort_order values.

    Args:
        project: Project name/ID
        milestone_id: Milestone being moved
        new_index: Target position (0-based index in the milestone list)

    Returns:
        dict: {success: True, updated_milestones: list of updated milestone IDs}
    """
    if not project:
        frappe.throw(_("Project is required"))

    if not milestone_id:
        frappe.throw(_("Milestone ID is required"))

    if new_index is None:
        frappe.throw(_("New index is required"))

    new_index = int(new_index)

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    if not frappe.db.exists("Orga Milestone", milestone_id):
        frappe.throw(_("Milestone {0} not found").format(milestone_id))

    # Check if sort_order column exists (migration may not have run yet)
    has_sort = _has_sort_order()
    if not has_sort:
        return {"success": False, "reason": "migration_required", "updated_milestones": []}

    # Get all milestones for the project ordered by current sort_order, then by date
    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": project},
        fields=["name", "sort_order", "due_date"],
        order_by="sort_order asc, due_date asc, creation asc"
    )

    if not milestones:
        return {"success": True, "updated_milestones": []}

    # Find current index of the milestone being moved
    milestone_names = [m.name for m in milestones]
    if milestone_id not in milestone_names:
        frappe.throw(_("Milestone {0} not in project {1}").format(milestone_id, project))

    current_index = milestone_names.index(milestone_id)

    # Clamp new_index to valid range
    new_index = max(0, min(new_index, len(milestones) - 1))

    # If position unchanged, do nothing
    if current_index == new_index:
        return {"success": True, "updated_milestones": []}

    # Remove milestone from current position and insert at new position
    milestone_names.pop(current_index)
    milestone_names.insert(new_index, milestone_id)

    # Update sort_order for all milestones (1-based to distinguish from default 0)
    updated_milestones = []
    try:
        for idx, name in enumerate(milestone_names):
            frappe.db.set_value(
                "Orga Milestone",
                name,
                "sort_order",
                idx + 1,  # 1-based so 0 means "not explicitly ordered"
                update_modified=False
            )
            updated_milestones.append(name)

        frappe.db.commit()

        return {
            "success": True,
            "updated_milestones": updated_milestones,
            "new_order": milestone_names
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(_("Failed to reorder milestones: {0}").format(str(e)))


def _calculate_milestone_completion(milestone_name):
    """Calculate completion percentage based on linked tasks."""
    tasks = frappe.get_all(
        "Orga Task",
        filters={"milestone": milestone_name},
        fields=["status"]
    )

    if not tasks:
        return 0

    completed = sum(1 for t in tasks if t.status == "Completed")
    return round((completed / len(tasks)) * 100)
