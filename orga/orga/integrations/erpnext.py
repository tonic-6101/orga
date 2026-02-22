# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
ERPNext Integration Module

Provides integration with ERPNext modules:
- Employee linking and sync
- Timesheet export
- Project billing

Usage:
    from orga.orga.integrations.erpnext import (
        get_employees,
        sync_resource_from_employee,
        export_time_log_to_timesheet
    )
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


def is_timesheet_doctype_available():
    """Check if Timesheet DocType exists."""
    return frappe.db.exists("DocType", "Timesheet")


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
# TIMESHEET SYNC (Task 7.2.2)
# =============================================================================

@frappe.whitelist()
def export_time_log_to_timesheet(time_log_name):
    """
    Export an Orga Time Log to ERPNext Timesheet.

    Args:
        time_log_name: Orga Time Log name

    Returns:
        dict: {success: bool, timesheet: str, message: str}
    """
    if not is_timesheet_doctype_available():
        return {"success": False, "message": _("Timesheet DocType not available")}

    if not frappe.db.exists("Orga Time Log", time_log_name):
        return {"success": False, "message": _("Time Log not found")}

    time_log = frappe.get_doc("Orga Time Log", time_log_name)

    # Check if already exported
    if time_log.get("erpnext_timesheet"):
        return {
            "success": False,
            "message": _("Already exported to timesheet {0}").format(time_log.erpnext_timesheet)
        }

    # Get employee from resource
    employee = None
    if time_log.resource:
        employee = frappe.db.get_value("Orga Resource", time_log.resource, "employee")

    if not employee:
        return {"success": False, "message": _("No ERPNext employee linked to resource")}

    # Get ERPNext project if linked
    erpnext_project = None
    if time_log.project:
        erpnext_project = frappe.db.get_value(
            "Orga Project", time_log.project, "frappe_project_link"
        )

    try:
        # Create or find existing timesheet for this employee and date
        existing_timesheet = frappe.db.get_value(
            "Timesheet",
            {
                "employee": employee,
                "start_date": time_log.log_date,
                "docstatus": 0  # Draft only
            },
            "name"
        )

        if existing_timesheet:
            timesheet = frappe.get_doc("Timesheet", existing_timesheet)
        else:
            timesheet = frappe.get_doc({
                "doctype": "Timesheet",
                "employee": employee,
                "start_date": time_log.log_date
            })

        # Add time log entry
        timesheet.append("time_logs", {
            "activity_type": _get_default_activity_type(),
            "from_time": _get_from_time(time_log),
            "to_time": _get_to_time(time_log),
            "hours": time_log.hours,
            "project": erpnext_project,
            "task": time_log.frappe_task_link if hasattr(time_log, 'frappe_task_link') else None,
            "description": time_log.description or f"Work on {time_log.task_subject or 'task'}",
            "is_billable": time_log.billable
        })

        if existing_timesheet:
            timesheet.save(ignore_permissions=True)
        else:
            timesheet.insert(ignore_permissions=True)

        # Update time log with reference
        frappe.db.set_value("Orga Time Log", time_log_name, "erpnext_timesheet", timesheet.name)
        frappe.db.commit()

        return {
            "success": True,
            "timesheet": timesheet.name,
            "message": _("Exported to timesheet {0}").format(timesheet.name)
        }

    except Exception as e:
        frappe.log_error(f"Timesheet export failed: {str(e)}")
        return {"success": False, "message": str(e)}


def _get_default_activity_type():
    """Get default activity type for timesheets."""
    # Try to get a default, or return first available
    activity_types = frappe.get_all("Activity Type", limit=1)
    if activity_types:
        return activity_types[0].name
    return None


def _get_from_time(time_log):
    """Calculate from_time for timesheet entry."""
    from frappe.utils import get_datetime, get_time

    log_date = getdate(time_log.log_date)
    if time_log.from_time:
        return f"{log_date} {time_log.from_time}"
    # Default to 9 AM
    return f"{log_date} 09:00:00"


def _get_to_time(time_log):
    """Calculate to_time for timesheet entry."""
    from frappe.utils import get_datetime, add_to_date

    from_time = _get_from_time(time_log)
    hours = flt(time_log.hours) or 1
    return add_to_date(from_time, hours=hours)


@frappe.whitelist()
def export_project_time_logs(project_name, from_date=None, to_date=None):
    """
    Export all time logs for a project to ERPNext timesheets.

    Args:
        project_name: Orga Project name
        from_date: Optional start date filter
        to_date: Optional end date filter

    Returns:
        dict: {success: bool, exported: int, skipped: int, errors: list}
    """
    if not is_timesheet_doctype_available():
        return {"success": False, "message": _("Timesheet DocType not available")}

    filters = {"project": project_name}
    if from_date:
        filters["log_date"] = [">=", from_date]
    if to_date:
        if "log_date" in filters:
            filters["log_date"] = ["between", [from_date, to_date]]
        else:
            filters["log_date"] = ["<=", to_date]

    time_logs = frappe.get_all(
        "Orga Time Log",
        filters=filters,
        fields=["name", "erpnext_timesheet"]
    )

    exported = 0
    skipped = 0
    errors = []

    for tl in time_logs:
        if tl.erpnext_timesheet:
            skipped += 1
            continue

        result = export_time_log_to_timesheet(tl.name)
        if result.get("success"):
            exported += 1
        else:
            errors.append({
                "time_log": tl.name,
                "error": result.get("message")
            })

    return {
        "success": len(errors) == 0,
        "exported": exported,
        "skipped": skipped,
        "errors": errors
    }


# =============================================================================
# PROJECT BILLING (Task 7.2.3)
# =============================================================================

@frappe.whitelist()
def get_project_billing_summary(project_name):
    """
    Get billing summary for an Orga Project.

    Args:
        project_name: Orga Project name

    Returns:
        dict: Billing summary with hours and amounts
    """
    project = frappe.get_doc("Orga Project", project_name)

    # Get all time logs for this project
    time_logs = frappe.get_all(
        "Orga Time Log",
        filters={"project": project_name},
        fields=["hours", "billable", "resource"]
    )

    total_hours = 0
    billable_hours = 0
    non_billable_hours = 0
    estimated_billing = 0

    for tl in time_logs:
        hours = flt(tl.hours)
        total_hours += hours

        if tl.billable:
            billable_hours += hours
            # Get billable rate from resource
            if tl.resource:
                rate = frappe.db.get_value("Orga Resource", tl.resource, "billable_rate") or 0
                estimated_billing += hours * flt(rate)
        else:
            non_billable_hours += hours

    # Get task completion for billing readiness
    total_tasks = frappe.db.count("Orga Task", {"project": project_name})
    completed_tasks = frappe.db.count("Orga Task", {"project": project_name, "status": "Completed"})

    return {
        "success": True,
        "project": project_name,
        "project_name": project.project_name,
        "summary": {
            "total_hours": round(total_hours, 2),
            "billable_hours": round(billable_hours, 2),
            "non_billable_hours": round(non_billable_hours, 2),
            "estimated_billing": round(estimated_billing, 2),
            "budget": project.budget or 0,
            "spent": project.spent or 0,
            "budget_remaining": (project.budget or 0) - (project.spent or 0),
            "progress": project.progress or 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "billing_ready": completed_tasks == total_tasks and total_tasks > 0
        }
    }


@frappe.whitelist()
def get_resource_billing_summary(resource_name, from_date=None, to_date=None):
    """
    Get billing summary for a resource.

    Args:
        resource_name: Orga Resource name
        from_date: Optional start date
        to_date: Optional end date

    Returns:
        dict: Resource billing summary
    """
    resource = frappe.get_doc("Orga Resource", resource_name)

    filters = {"resource": resource_name}
    if from_date:
        filters["log_date"] = [">=", from_date]
    if to_date:
        if "log_date" in filters:
            filters["log_date"] = ["between", [from_date, to_date]]
        else:
            filters["log_date"] = ["<=", to_date]

    time_logs = frappe.get_all(
        "Orga Time Log",
        filters=filters,
        fields=["hours", "billable", "project", "log_date"]
    )

    total_hours = 0
    billable_hours = 0
    by_project = {}

    for tl in time_logs:
        hours = flt(tl.hours)
        total_hours += hours

        if tl.billable:
            billable_hours += hours

        # Group by project
        proj = tl.project or "No Project"
        if proj not in by_project:
            by_project[proj] = {"total": 0, "billable": 0}
        by_project[proj]["total"] += hours
        if tl.billable:
            by_project[proj]["billable"] += hours

    billable_rate = flt(resource.billable_rate) or 0
    hourly_cost = flt(resource.hourly_cost) or 0

    return {
        "success": True,
        "resource": resource_name,
        "resource_name": resource.resource_name,
        "summary": {
            "total_hours": round(total_hours, 2),
            "billable_hours": round(billable_hours, 2),
            "billable_rate": billable_rate,
            "hourly_cost": hourly_cost,
            "estimated_revenue": round(billable_hours * billable_rate, 2),
            "estimated_cost": round(total_hours * hourly_cost, 2),
            "gross_margin": round((billable_hours * billable_rate) - (total_hours * hourly_cost), 2)
        },
        "by_project": by_project
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
