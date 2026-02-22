# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Defect API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.defect.get_defects',
        args: { contact: 'RES-00001' }
    })
"""

import json
import frappe
from frappe import _


@frappe.whitelist()
def get_defects(contact=None, project=None, status=None, severity=None, limit=50, offset=0):
    """
    Get list of defects with optional filters.

    Args:
        contact: Filter by contact (Orga Resource name)
        project: Filter by project (Orga Project name)
        status: Filter by status (Open, In Progress, Resolved, Closed)
        severity: Filter by severity (Low, Medium, High, Critical)
        limit: Max results (default 50)
        offset: Pagination offset

    Returns:
        dict: {defects: [...], total: int}
    """
    filters = {}
    if contact:
        filters["contact"] = contact
    if project:
        filters["project"] = project
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity

    defects = frappe.get_all(
        "Orga Defect",
        filters=filters,
        fields=[
            "name", "title", "contact", "project", "task",
            "defect_type", "severity", "status",
            "reported_date", "resolved_date", "reported_by",
            "cost_estimate", "actual_cost",
            "modified", "creation"
        ],
        order_by="reported_date desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Defect", filters)

    # Enrich with names
    for defect in defects:
        if defect.get("contact"):
            defect["contact_name"] = frappe.db.get_value(
                "Orga Resource", defect["contact"], "resource_name"
            )
        if defect.get("project"):
            defect["project_name"] = frappe.db.get_value(
                "Orga Project", defect["project"], "project_name"
            )
        if defect.get("task"):
            defect["task_subject"] = frappe.db.get_value(
                "Orga Task", defect["task"], "subject"
            )
        if defect.get("reported_by"):
            defect["reported_by_name"] = frappe.db.get_value(
                "User", defect["reported_by"], "full_name"
            )

    return {"defects": defects, "total": total}


@frappe.whitelist()
def get_defect(name):
    """
    Get single defect with full details.

    Args:
        name: Defect name/ID

    Returns:
        dict: Defect data with enriched names
    """
    if not name:
        frappe.throw(_("Defect name is required"))

    if not frappe.db.exists("Orga Defect", name):
        frappe.throw(_("Defect {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Defect", name)
    defect = doc.as_dict()

    # Enrich with names
    if defect.get("contact"):
        defect["contact_name"] = frappe.db.get_value(
            "Orga Resource", defect["contact"], "resource_name"
        )
    if defect.get("project"):
        defect["project_name"] = frappe.db.get_value(
            "Orga Project", defect["project"], "project_name"
        )
    if defect.get("task"):
        defect["task_subject"] = frappe.db.get_value(
            "Orga Task", defect["task"], "subject"
        )
    if defect.get("reported_by"):
        defect["reported_by_name"] = frappe.db.get_value(
            "User", defect["reported_by"], "full_name"
        )

    return defect


@frappe.whitelist()
def create_defect(data):
    """
    Create a new defect.

    Args:
        data: dict or JSON string with defect fields
            Required: title, contact, defect_type, severity

    Returns:
        dict: Created defect data
    """
    if isinstance(data, str):
        data = json.loads(data)

    required = ["title", "contact"]
    for field in required:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    allowed_fields = [
        "title", "contact", "defect_type", "severity", "status",
        "project", "task", "description", "resolution_notes",
        "cost_estimate", "actual_cost", "resolved_date"
    ]

    doc_data = {"doctype": "Orga Defect"}
    for field in allowed_fields:
        if field in data:
            doc_data[field] = data[field]

    doc = frappe.get_doc(doc_data)
    doc.insert()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def update_defect(name, data):
    """
    Update an existing defect.

    Args:
        name: Defect name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated defect data
    """
    if not name:
        frappe.throw(_("Defect name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Defect", name):
        frappe.throw(_("Defect {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Defect", name)

    allowed_fields = [
        "title", "defect_type", "severity", "status",
        "project", "task", "description", "resolution_notes",
        "cost_estimate", "actual_cost", "resolved_date"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return doc.as_dict()


@frappe.whitelist()
def delete_defect(name):
    """
    Delete a defect.

    Args:
        name: Defect name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Defect name is required"))

    if not frappe.db.exists("Orga Defect", name):
        frappe.throw(_("Defect {0} not found").format(name), frappe.DoesNotExistError)

    if not frappe.has_permission("Orga Defect", "delete", name):
        frappe.throw(_("Not permitted to delete this defect"), frappe.PermissionError)

    frappe.delete_doc("Orga Defect", name)
    frappe.db.commit()

    return {"success": True}
