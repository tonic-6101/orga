# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
ERPNext Integration Module

Provides integration with ERPNext modules:
- Employee linking and sync
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt


# =============================================================================
# ERPNEXT AVAILABILITY CHECK
# =============================================================================

def is_erpnext_installed():
    """Check if ERPNext is installed."""
    return "erpnext" in frappe.get_installed_apps()


def is_employee_doctype_available():
    """Check if Employee DocType exists."""
    return frappe.db.exists("DocType", "Employee")


# =============================================================================
# EMPLOYEE LINKING (Task 7.2.1)
# =============================================================================

@frappe.whitelist()
def get_employees(search_text=None, filters=None, limit=20):
    """
    Get ERPNext employees for linking to Orga Resources.

    Args:
        search_text: Search in employee name or ID
        filters: Additional filters (e.g., {"status": "Active"})
        limit: Maximum results

    Returns:
        list: Employee records with basic info
    """
    if not is_employee_doctype_available():
        return {"success": False, "message": _("Employee DocType not available")}

    query_filters = filters or {}

    if search_text:
        query_filters["employee_name"] = ["like", f"%{search_text}%"]

    employees = frappe.get_all(
        "Employee",
        filters=query_filters,
        fields=[
            "name", "employee_name", "status", "department",
            "designation", "user_id", "company_email", "personal_email",
            "cell_number", "image"
        ],
        limit_page_length=int(limit),
        order_by="employee_name asc"
    )

    # Mark which are already linked
    linked_employees = frappe.get_all(
        "Orga Resource",
        filters={"employee": ["is", "set"]},
        fields=["employee"]
    )
    linked_set = {e.employee for e in linked_employees}

    for emp in employees:
        emp["already_linked"] = emp.name in linked_set

    return {"success": True, "employees": employees}


@frappe.whitelist()
def get_employee_details(employee_name):
    """
    Get full employee details for auto-populating resource.

    Args:
        employee_name: Employee ID

    Returns:
        dict: Employee details mapped to Orga Resource fields
    """
    if not is_employee_doctype_available():
        return {"success": False, "message": _("Employee DocType not available")}

    if not frappe.db.exists("Employee", employee_name):
        return {"success": False, "message": _("Employee not found")}

    emp = frappe.get_doc("Employee", employee_name)

    # Map Employee fields to Orga Resource fields
    return {
        "success": True,
        "data": {
            "resource_name": emp.employee_name,
            "email": emp.company_email or emp.personal_email,
            "user": emp.user_id,
            "department": emp.department,
            "designation": emp.designation,
            "status": _map_employee_status(emp.status),
            # Additional fields that could be useful
            "employee_name": emp.employee_name,
            "employee_id": emp.name,
            "company": emp.company,
            "date_of_joining": emp.date_of_joining,
            "reports_to_employee": emp.reports_to,
            "image": emp.image
        }
    }


def _map_employee_status(erpnext_status):
    """Map ERPNext Employee status to Orga Resource status."""
    status_map = {
        "Active": "Active",
        "Inactive": "Inactive",
        "Left": "Inactive",
        "Suspended": "Inactive"
    }
    return status_map.get(erpnext_status, "Active")


@frappe.whitelist()
def sync_resource_from_employee(resource_name):
    """
    Sync Orga Resource details from linked ERPNext Employee.

    Args:
        resource_name: Orga Resource name

    Returns:
        dict: {success: bool, message: str}
    """
    if not is_employee_doctype_available():
        return {"success": False, "message": _("Employee DocType not available")}

    resource = frappe.get_doc("Orga Resource", resource_name)

    if not resource.employee:
        return {"success": False, "message": _("No employee linked to this resource")}

    if not frappe.db.exists("Employee", resource.employee):
        return {"success": False, "message": _("Linked employee not found")}

    emp = frappe.get_doc("Employee", resource.employee)

    # Update resource fields
    resource.resource_name = emp.employee_name
    resource.email = emp.company_email or emp.personal_email
    resource.user = emp.user_id
    resource.department = emp.department
    resource.designation = emp.designation
    resource.status = _map_employee_status(emp.status)
    resource.last_erpnext_sync = now_datetime()
    resource.erpnext_sync_status = "Synced"

    resource.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("Resource synced from employee {0}").format(emp.employee_name)
    }


@frappe.whitelist()
def sync_all_resources_from_employees():
    """
    Sync all Orga Resources that have linked employees.

    Returns:
        dict: {success: bool, synced: int, failed: int, errors: list}
    """
    if not is_employee_doctype_available():
        return {"success": False, "message": _("Employee DocType not available")}

    resources = frappe.get_all(
        "Orga Resource",
        filters={
            "employee": ["is", "set"],
            "sync_with_erpnext": 1
        },
        fields=["name"]
    )

    synced = 0
    failed = 0
    errors = []

    for res in resources:
        result = sync_resource_from_employee(res.name)
        if result.get("success"):
            synced += 1
        else:
            failed += 1
            errors.append({
                "resource": res.name,
                "error": result.get("message")
            })

    return {
        "success": failed == 0,
        "synced": synced,
        "failed": failed,
        "errors": errors
    }


# =============================================================================
# BRIDGE STATUS (for Dock Integrations dashboard)
# =============================================================================

@frappe.whitelist()
def get_sync_status() -> dict:
    """Bridge status for Dock's Integrations dashboard."""
    if not is_employee_doctype_available():
        return {"active": False, "reason": _("Employee DocType not available")}

    linked_count = frappe.db.count(
        "Orga Resource",
        {"employee": ["is", "set"], "sync_with_erpnext": 1},
    )
    unsynced_count = frappe.db.count(
        "Orga Resource",
        {"employee": ["is", "set"], "sync_with_erpnext": 1, "erpnext_sync_status": ["!=", "Synced"]},
    )

    return {
        "active": True,
        "linked_resources": linked_count,
        "unsynced_count": unsynced_count,
    }


# =============================================================================
# HOOKS FOR REAL-TIME SYNC
# =============================================================================

def on_employee_update(doc, method):
    """
    Hook called when ERPNext Employee is updated.
    Syncs changes to linked Orga Resources.
    """
    # Find linked resources
    resources = frappe.get_all(
        "Orga Resource",
        filters={
            "employee": doc.name,
            "sync_with_erpnext": 1
        },
        fields=["name"]
    )

    for res in resources:
        frappe.enqueue(
            "orga.orga.integrations.erpnext.sync_resource_from_employee",
            resource_name=res.name,
            queue="short"
        )


def on_resource_before_save(doc, method):
    """
    Hook called before Orga Resource is saved.
    Auto-populates from employee if enabled.
    """
    if doc.employee and doc.auto_sync_employee and doc.is_new():
        # Only auto-populate on new documents
        if is_employee_doctype_available() and frappe.db.exists("Employee", doc.employee):
            emp = frappe.get_doc("Employee", doc.employee)
            if not doc.resource_name:
                doc.resource_name = emp.employee_name
            if not doc.email:
                doc.email = emp.company_email or emp.personal_email
            if not doc.user:
                doc.user = emp.user_id
            if not doc.department:
                doc.department = emp.department
            if not doc.designation:
                doc.designation = emp.designation


def on_resource_update(doc, method):
    """
    Hook called when Orga Resource is updated.
    Updates sync status if employee is linked.
    """
    if doc.employee and doc.sync_with_erpnext:
        # Mark as synced if employee link exists
        if not doc.last_erpnext_sync:
            frappe.db.set_value(
                "Orga Resource", doc.name,
                {
                    "last_erpnext_sync": now_datetime(),
                    "erpnext_sync_status": "Synced"
                },
                update_modified=False
            )
