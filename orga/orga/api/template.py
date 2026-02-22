# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Project Template API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.template.get_templates',
        args: { category: 'Engineering' }
    })
"""

import json
import frappe
from frappe import _
from frappe.utils import getdate, date_diff, add_days


_ALLOWED_ROLES = ("System Manager", "Orga Manager")


def _check_template_write_permission():
    """Ensure user has permission for template write operations."""
    roles = frappe.get_roles()
    if not any(role in roles for role in _ALLOWED_ROLES):
        frappe.throw(_("Not permitted to manage project templates"), frappe.PermissionError)


@frappe.whitelist()
def get_templates(category=None, limit=50, offset=0):
    """
    Get list of project templates with optional filters.

    Args:
        category: Filter by category
        limit: Maximum results (default 50)
        offset: Pagination offset

    Returns:
        dict: {templates: [...], total: int}
    """
    filters = {}
    if category:
        filters["category"] = category

    templates = frappe.get_all(
        "Orga Project Template",
        filters=filters,
        fields=[
            "name",
            "template_name",
            "category",
            "project_type",
            "description",
            "source_project",
            "task_count",
            "milestone_count",
            "dependency_count",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=int(limit),
        limit_start=int(offset),
    )

    total = frappe.db.count("Orga Project Template", filters)

    # Enrich with source project name
    for tpl in templates:
        if tpl.get("source_project"):
            tpl["source_project_name"] = frappe.db.get_value(
                "Orga Project", tpl["source_project"], "project_name"
            )

    return {"templates": templates, "total": total}


@frappe.whitelist()
def get_template(name):
    """
    Get single template with parsed template_data.

    Args:
        name: Template name/ID

    Returns:
        dict: Template data with parsed template_data
    """
    if not name:
        frappe.throw(_("Template name is required"))

    if not frappe.db.exists("Orga Project Template", name):
        frappe.throw(
            _("Template {0} not found").format(name), frappe.DoesNotExistError
        )

    tpl = frappe.get_doc("Orga Project Template", name)

    template_data = None
    if tpl.template_data:
        try:
            template_data = (
                json.loads(tpl.template_data)
                if isinstance(tpl.template_data, str)
                else tpl.template_data
            )
        except (json.JSONDecodeError, TypeError):
            template_data = {"tasks": [], "milestones": []}

    result = {
        "name": tpl.name,
        "template_name": tpl.template_name,
        "category": tpl.category,
        "project_type": tpl.project_type,
        "description": tpl.description,
        "source_project": tpl.source_project,
        "task_count": tpl.task_count,
        "milestone_count": tpl.milestone_count,
        "dependency_count": tpl.dependency_count,
        "template_data": template_data,
        "modified": str(tpl.modified),
    }

    if tpl.source_project:
        result["source_project_name"] = frappe.db.get_value(
            "Orga Project", tpl.source_project, "project_name"
        )

    return result


@frappe.whitelist()
def create_template_from_project(
    project_name, template_name, description=None, category="General"
):
    """
    Extract tasks/milestones/dependencies from a project and save as template.

    Computes relative date offsets from the earliest date found (day 0).

    Args:
        project_name: Source project name/ID
        template_name: Name for the new template
        description: Optional description
        category: Template category

    Returns:
        dict: Created template summary
    """
    _check_template_write_permission()

    if not project_name or not template_name:
        frappe.throw(_("Project name and template name are required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(
            _("Project {0} not found").format(project_name),
            frappe.DoesNotExistError,
        )

    project = frappe.get_doc("Orga Project", project_name)

    # Load all tasks for this project
    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": project_name},
        fields=[
            "name",
            "subject",
            "description",
            "priority",
            "estimated_hours",
            "sort_order",
            "start_date",
            "due_date",
            "milestone",
        ],
        order_by="sort_order asc, creation asc",
    )

    # Load all milestones for this project
    milestones = frappe.get_all(
        "Orga Milestone",
        filters={"project": project_name},
        fields=[
            "name",
            "milestone_name",
            "description",
            "due_date",
            "sort_order",
        ],
        order_by="sort_order asc, creation asc",
    )

    # Find earliest date across all items (day 0)
    all_dates = []
    for t in tasks:
        if t.start_date:
            all_dates.append(getdate(t.start_date))
        if t.due_date:
            all_dates.append(getdate(t.due_date))
    for m in milestones:
        if m.due_date:
            all_dates.append(getdate(m.due_date))

    # Fall back to project start_date or today
    if all_dates:
        day0 = min(all_dates)
    elif project.start_date:
        day0 = getdate(project.start_date)
    else:
        day0 = getdate(frappe.utils.today())

    # Build task name → ref_id mapping
    task_name_to_ref = {}
    for idx, t in enumerate(tasks):
        task_name_to_ref[t.name] = f"T{idx}"

    # Build milestone name → ref_id mapping
    milestone_name_to_ref = {}
    for idx, m in enumerate(milestones):
        milestone_name_to_ref[m.name] = f"M{idx}"

    # Build template tasks
    template_tasks = []
    for t in tasks:
        ref_id = task_name_to_ref[t.name]

        # Compute relative offsets
        if t.start_date:
            start_offset = date_diff(getdate(t.start_date), day0)
        else:
            start_offset = 0

        if t.start_date and t.due_date:
            duration = date_diff(getdate(t.due_date), getdate(t.start_date))
        elif t.due_date:
            duration = date_diff(getdate(t.due_date), day0) - start_offset
        else:
            duration = 0

        # Load checklist items
        checklist_items = []
        task_doc = frappe.get_doc("Orga Task", t.name)
        if task_doc.checklist:
            for item in task_doc.checklist:
                checklist_items.append(item.title)

        # Load dependencies
        dependencies = []
        if task_doc.depends_on:
            for dep in task_doc.depends_on:
                predecessor_ref = task_name_to_ref.get(dep.depends_on)
                if predecessor_ref:
                    # Convert full dependency type to short form
                    dep_type_map = {
                        "Finish to Start": "FS",
                        "Start to Start": "SS",
                        "Finish to Finish": "FF",
                        "Start to Finish": "SF",
                    }
                    dependencies.append(
                        {
                            "predecessor_ref": predecessor_ref,
                            "type": dep_type_map.get(
                                dep.dependency_type, "FS"
                            ),
                            "lag_days": dep.lag_days or 0,
                        }
                    )

        # Build milestone_ref
        milestone_ref = None
        if t.milestone and t.milestone in milestone_name_to_ref:
            milestone_ref = milestone_name_to_ref[t.milestone]

        template_tasks.append(
            {
                "ref_id": ref_id,
                "subject": t.subject,
                "description": t.description or "",
                "priority": t.priority or "Medium",
                "estimated_hours": t.estimated_hours or 0,
                "sort_order": t.sort_order or 0,
                "start_offset_days": start_offset,
                "duration_days": max(duration, 0),
                "checklist": checklist_items,
                "milestone_ref": milestone_ref,
                "dependencies": dependencies,
            }
        )

    # Build template milestones
    template_milestones = []
    for m in milestones:
        if m.due_date:
            offset = date_diff(getdate(m.due_date), day0)
        else:
            offset = 0

        template_milestones.append(
            {
                "ref_id": milestone_name_to_ref[m.name],
                "milestone_name": m.milestone_name,
                "description": m.description or "",
                "offset_days": offset,
                "sort_order": m.sort_order or 0,
            }
        )

    template_data = {"tasks": template_tasks, "milestones": template_milestones}

    # Create the template DocType
    tpl = frappe.get_doc(
        {
            "doctype": "Orga Project Template",
            "template_name": template_name,
            "description": description or "",
            "category": category,
            "project_type": project.project_type or "Internal",
            "source_project": project_name,
            "template_data": json.dumps(template_data),
        }
    )
    tpl.insert()
    frappe.db.commit()

    return {
        "name": tpl.name,
        "template_name": tpl.template_name,
        "task_count": tpl.task_count,
        "milestone_count": tpl.milestone_count,
        "dependency_count": tpl.dependency_count,
    }


@frappe.whitelist()
def update_template(name, data):
    """
    Update template metadata (name, description, category).

    Args:
        name: Template name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: {name, modified}
    """
    _check_template_write_permission()

    if not name:
        frappe.throw(_("Template name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Project Template", name):
        frappe.throw(
            _("Template {0} not found").format(name), frappe.DoesNotExistError
        )

    tpl = frappe.get_doc("Orga Project Template", name)

    allowed_fields = ["template_name", "description", "category", "project_type"]
    for field, value in data.items():
        if field in allowed_fields:
            setattr(tpl, field, value)

    tpl.save()
    frappe.db.commit()

    return {"name": tpl.name, "modified": str(tpl.modified)}


@frappe.whitelist()
def delete_template(name):
    """
    Delete a template.

    Args:
        name: Template name/ID

    Returns:
        dict: {success: True}
    """
    _check_template_write_permission()

    if not name:
        frappe.throw(_("Template name is required"))

    if not frappe.db.exists("Orga Project Template", name):
        frappe.throw(
            _("Template {0} not found").format(name), frappe.DoesNotExistError
        )

    frappe.delete_doc("Orga Project Template", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def apply_template(project_name, template_name):
    """
    Create tasks, milestones, and dependencies in a project from a template.

    Uses relative date offsets applied to the project's start_date.

    Args:
        project_name: Target project name/ID
        template_name: Template name/ID to apply

    Returns:
        dict: {tasks_created, milestones_created, dependencies_created}
    """
    _check_template_write_permission()

    if not project_name or not template_name:
        frappe.throw(_("Project name and template name are required"))

    if not frappe.db.exists("Orga Project", project_name):
        frappe.throw(
            _("Project {0} not found").format(project_name),
            frappe.DoesNotExistError,
        )

    if not frappe.db.exists("Orga Project Template", template_name):
        frappe.throw(
            _("Template {0} not found").format(template_name),
            frappe.DoesNotExistError,
        )

    project = frappe.get_doc("Orga Project", project_name)
    tpl = frappe.get_doc("Orga Project Template", template_name)

    if not tpl.template_data:
        frappe.throw(_("Template has no data"))

    data = (
        json.loads(tpl.template_data)
        if isinstance(tpl.template_data, str)
        else tpl.template_data
    )

    project_start = getdate(project.start_date) if project.start_date else getdate(frappe.utils.today())

    tasks = data.get("tasks", [])
    milestones_data = data.get("milestones", [])

    # Phase 1: Create milestones and build mapping
    milestone_mapping = {}  # ref_id → actual milestone name
    milestones_created = 0

    for m in milestones_data:
        due_date = str(add_days(project_start, m.get("offset_days", 0)))

        milestone_doc = frappe.get_doc(
            {
                "doctype": "Orga Milestone",
                "milestone_name": m["milestone_name"],
                "description": m.get("description", ""),
                "project": project_name,
                "due_date": due_date,
                "status": "Upcoming",
                "sort_order": m.get("sort_order", 0),
            }
        )
        milestone_doc.insert()
        milestone_mapping[m["ref_id"]] = milestone_doc.name
        milestones_created += 1

    # Phase 2: Create tasks and build mapping
    name_mapping = {}  # ref_id → actual task name
    tasks_created = 0

    for t in tasks:
        start_offset = t.get("start_offset_days", 0)
        duration = t.get("duration_days", 0)

        has_dates = start_offset > 0 or duration > 0 or t.get("start_offset_days") is not None
        if has_dates:
            start_date = str(add_days(project_start, start_offset))
            due_date = str(add_days(project_start, start_offset + duration)) if duration else start_date
        else:
            start_date = None
            due_date = None

        # Resolve milestone ref
        milestone_name = None
        if t.get("milestone_ref") and t["milestone_ref"] in milestone_mapping:
            milestone_name = milestone_mapping[t["milestone_ref"]]

        task_doc = frappe.get_doc(
            {
                "doctype": "Orga Task",
                "subject": t["subject"],
                "description": t.get("description", ""),
                "project": project_name,
                "priority": t.get("priority", "Medium"),
                "estimated_hours": t.get("estimated_hours", 0),
                "sort_order": t.get("sort_order", 0),
                "start_date": start_date,
                "due_date": due_date,
                "milestone": milestone_name,
                "status": "Open",
            }
        )

        # Add checklist items
        for checklist_title in t.get("checklist", []):
            task_doc.append("checklist", {"title": checklist_title})

        task_doc.insert()
        name_mapping[t["ref_id"]] = task_doc.name
        tasks_created += 1

    # Phase 3: Create dependencies using name_mapping
    dependencies_created = 0

    for t in tasks:
        task_name = name_mapping.get(t["ref_id"])
        if not task_name:
            continue

        deps = t.get("dependencies", [])
        if not deps:
            continue

        task_doc = frappe.get_doc("Orga Task", task_name)

        for dep in deps:
            predecessor_name = name_mapping.get(dep["predecessor_ref"])
            if not predecessor_name:
                continue

            # Convert short form to full dependency type
            type_map = {
                "FS": "Finish to Start",
                "SS": "Start to Start",
                "FF": "Finish to Finish",
                "SF": "Start to Finish",
            }

            task_doc.append(
                "depends_on",
                {
                    "depends_on": predecessor_name,
                    "dependency_type": type_map.get(dep.get("type", "FS"), "Finish to Start"),
                    "lag_days": dep.get("lag_days", 0),
                },
            )
            dependencies_created += 1

        if deps:
            task_doc.save()

    frappe.db.commit()

    return {
        "tasks_created": tasks_created,
        "milestones_created": milestones_created,
        "dependencies_created": dependencies_created,
    }


@frappe.whitelist()
def export_template(name):
    """
    Export a template as a JSON object suitable for download.

    Args:
        name: Template name/ID

    Returns:
        dict: Full template data for export
    """
    if not name:
        frappe.throw(_("Template name is required"))

    if not frappe.db.exists("Orga Project Template", name):
        frappe.throw(
            _("Template {0} not found").format(name), frappe.DoesNotExistError
        )

    tpl = frappe.get_doc("Orga Project Template", name)

    template_data = None
    if tpl.template_data:
        try:
            template_data = (
                json.loads(tpl.template_data)
                if isinstance(tpl.template_data, str)
                else tpl.template_data
            )
        except (json.JSONDecodeError, TypeError):
            template_data = {"tasks": [], "milestones": []}

    return {
        "version": "1.0",
        "template_name": tpl.template_name,
        "description": tpl.description or "",
        "category": tpl.category,
        "project_type": tpl.project_type,
        "task_count": tpl.task_count,
        "milestone_count": tpl.milestone_count,
        "dependency_count": tpl.dependency_count,
        "template_data": template_data,
    }


@frappe.whitelist()
def import_template(data):
    """
    Import a template from JSON data.

    Args:
        data: dict or JSON string of the exported template

    Returns:
        dict: Created template summary
    """
    _check_template_write_permission()

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid JSON data"))

    if not data.get("template_name"):
        frappe.throw(_("Template name is required in import data"))

    if not data.get("template_data"):
        frappe.throw(_("Template data is required in import data"))

    tpl = frappe.get_doc(
        {
            "doctype": "Orga Project Template",
            "template_name": data["template_name"],
            "description": data.get("description", ""),
            "category": data.get("category", "General"),
            "project_type": data.get("project_type", "Internal"),
            "template_data": json.dumps(data["template_data"])
            if isinstance(data["template_data"], dict)
            else data["template_data"],
        }
    )
    tpl.insert()
    frappe.db.commit()

    return {
        "name": tpl.name,
        "template_name": tpl.template_name,
        "task_count": tpl.task_count,
        "milestone_count": tpl.milestone_count,
        "dependency_count": tpl.dependency_count,
    }
