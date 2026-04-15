# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Task Template API endpoints for Orga.

Task templates are lightweight reusable task lists (distinct from project templates
which capture full project structures with milestones and dependencies).

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.task_template.get_templates',
        args: { category: 'Seasonal' }
    })
"""

import json

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today


@frappe.whitelist()
def get_templates(category=None):
    """
    Return task templates grouped by system vs custom.

    Args:
        category: Optional filter by category

    Returns:
        dict: {system: [...], custom: [...]}
    """
    filters = {}
    if category:
        filters["category"] = category

    templates = frappe.get_all(
        "Orga Task Template",
        filters=filters,
        fields=[
            "name", "template_name", "category", "description",
            "is_system_template", "modified",
        ],
        order_by="template_name asc",
    )

    # Enrich with task count
    for tpl in templates:
        tpl["task_count"] = frappe.db.count(
            "Orga Task Template Item", {"parent": tpl["name"]}
        )

    system = [t for t in templates if t.get("is_system_template")]
    custom = [t for t in templates if not t.get("is_system_template")]

    return {"system": system, "custom": custom}


@frappe.whitelist()
def get_template_preview(template, start_date=None):
    """
    Preview tasks that would be created from a template.

    Args:
        template: Template name/ID
        start_date: Base date for offset calculation (defaults to today)

    Returns:
        dict: {template_name: str, tasks: [...]}
    """
    if not template:
        frappe.throw(_("Template name is required"))

    if not frappe.db.exists("Orga Task Template", template):
        frappe.throw(_("Template {0} not found").format(template), frappe.DoesNotExistError)

    tpl = frappe.get_doc("Orga Task Template", template)
    base_date = getdate(start_date) if start_date else getdate(today())

    tasks = []
    for item in tpl.tasks:
        scheduled_date = str(add_days(base_date, item.days_offset or 0))
        tasks.append({
            "subject": item.subject,
            "task_type": item.task_type,
            "priority": item.priority or "Medium",
            "scheduled_date": scheduled_date,
            "days_offset": item.days_offset or 0,
            "estimated_hours": item.estimated_hours or 0,
            "notes": item.notes,
        })

    return {"template_name": tpl.template_name, "tasks": tasks}


@frappe.whitelist(methods=["POST"])
def spawn_template(template, project=None, start_date=None):
    """
    Create Orga Tasks from a task template.

    Each template item becomes a separate Orga Task. If a project is provided,
    tasks are linked to it; otherwise they are standalone tasks.

    Args:
        template: Template name/ID
        project: Optional Orga Project to link tasks to
        start_date: Base date for offset calculation (defaults to today)

    Returns:
        dict: {created: [task_names], count: int}
    """
    if not template:
        frappe.throw(_("Template name is required"))

    if isinstance(template, str) and template.startswith("{"):
        template = json.loads(template).get("template", template)

    if not frappe.db.exists("Orga Task Template", template):
        frappe.throw(_("Template {0} not found").format(template), frappe.DoesNotExistError)

    if project and not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project), frappe.DoesNotExistError)

    tpl = frappe.get_doc("Orga Task Template", template)
    base_date = getdate(start_date) if start_date else getdate(today())

    created = []
    for item in tpl.tasks:
        task_date = str(add_days(base_date, item.days_offset or 0))
        task_doc = frappe.get_doc({
            "doctype": "Orga Task",
            "subject": item.subject,
            "description": item.notes or "",
            "priority": item.priority or "Medium",
            "start_date": task_date,
            "due_date": task_date,
            "estimated_hours": item.estimated_hours or 0,
            "project": project,
            "assigned_to": frappe.session.user,
            "status": "Open",
        })
        task_doc.insert()
        created.append(task_doc.name)

    frappe.db.commit()

    return {"created": created, "count": len(created)}


@frappe.whitelist(methods=["POST"])
def duplicate_template(template):
    """
    Create an editable copy of a template.

    Args:
        template: Template name/ID to copy

    Returns:
        dict: {name: new_template_name}
    """
    if not template:
        frappe.throw(_("Template name is required"))

    if not frappe.db.exists("Orga Task Template", template):
        frappe.throw(_("Template {0} not found").format(template), frappe.DoesNotExistError)

    source = frappe.get_doc("Orga Task Template", template)
    new_tpl = frappe.copy_doc(source)
    new_tpl.template_name = _("{0} (Copy)").format(source.template_name)
    new_tpl.is_system_template = 0
    new_tpl.insert()
    frappe.db.commit()

    return {"name": new_tpl.name}
