# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Import/Export API

Endpoints for bulk data import and export in CSV and JSON formats.
"""

import csv
import json
from io import StringIO
import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt


_ALLOWED_ROLES = ("System Manager", "Orga Manager")


def _check_import_permission():
    """Ensure user has permission for import/export operations."""
    roles = frappe.get_roles()
    if not any(role in roles for role in _ALLOWED_ROLES):
        frappe.throw(_("Not permitted to perform import/export operations"), frappe.PermissionError)


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@frappe.whitelist()
def export_projects(format: str = "csv", status: str = None):
    """
    Export projects to CSV or JSON.

    Args:
        format: Output format ('csv' or 'json')
        status: Filter by status (optional)

    Returns:
        dict: {file_url: str} for download
    """
    filters = {}
    if status:
        filters["status"] = status

    projects = frappe.get_all(
        "Orga Project",
        filters=filters,
        fields=[
            "name", "project_name", "project_code", "status", "project_type",
            "start_date", "end_date", "progress", "budget", "spent",
            "project_manager", "description"
        ],
        order_by="project_name asc"
    )

    if not projects:
        return {"file_url": None, "message": _("No projects found")}

    filename = f"orga_projects_export_{now_datetime().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        return _create_json_file({"projects": projects}, filename)
    else:
        return _create_csv_file(projects, filename)


@frappe.whitelist()
def export_tasks(project: str = None, status: str = None, format: str = "csv"):
    """
    Export tasks to CSV or JSON.

    Args:
        project: Filter by project (optional)
        status: Filter by status (optional)
        format: Output format ('csv' or 'json')

    Returns:
        dict: {file_url: str} for download
    """
    filters = {}
    if project:
        filters["project"] = project
    if status:
        filters["status"] = status

    tasks = frappe.get_all(
        "Orga Task",
        filters=filters,
        fields=[
            "name", "subject", "project", "status", "priority",
            "start_date", "due_date", "estimated_hours", "actual_hours",
            "assigned_to", "milestone", "progress", "description"
        ],
        order_by="project asc, subject asc"
    )

    if not tasks:
        return {"file_url": None, "message": _("No tasks found")}

    # Enrich with project names
    for task in tasks:
        if task.get("project"):
            task["project_name"] = frappe.db.get_value(
                "Orga Project", task["project"], "project_name"
            )

    filename = f"orga_tasks_export_{now_datetime().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        return _create_json_file({"tasks": tasks}, filename)
    else:
        return _create_csv_file(tasks, filename)


@frappe.whitelist()
def export_resources(status: str = None, department: str = None, format: str = "csv"):
    """
    Export resources to CSV or JSON.

    Args:
        status: Filter by status (optional)
        department: Filter by department (optional)
        format: Output format ('csv' or 'json')

    Returns:
        dict: {file_url: str} for download
    """
    filters = {}
    if status:
        filters["status"] = status
    if department:
        filters["department"] = department

    resources = frappe.get_all(
        "Orga Resource",
        filters=filters,
        fields=[
            "name", "resource_name", "email", "user", "resource_type",
            "status", "department", "designation", "weekly_capacity",
            "hourly_cost", "billable_rate"
        ],
        order_by="resource_name asc"
    )

    if not resources:
        return {"file_url": None, "message": _("No resources found")}

    filename = f"orga_resources_export_{now_datetime().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        return _create_json_file({"resources": resources}, filename)
    else:
        return _create_csv_file(resources, filename)


@frappe.whitelist()
def export_time_logs(project: str = None, resource: str = None,
                     from_date: str = None, to_date: str = None, format: str = "csv"):
    """
    Export time logs to CSV or JSON.

    Args:
        project: Filter by project (optional)
        resource: Filter by resource (optional)
        from_date: Filter by start date (optional)
        to_date: Filter by end date (optional)
        format: Output format ('csv' or 'json')

    Returns:
        dict: {file_url: str} for download
    """
    filters = {}
    if project:
        filters["project"] = project
    if resource:
        filters["resource"] = resource

    if from_date and to_date:
        filters["log_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["log_date"] = [">=", from_date]
    elif to_date:
        filters["log_date"] = ["<=", to_date]

    time_logs = frappe.get_all(
        "Orga Time Log",
        filters=filters,
        fields=[
            "name", "task", "project", "user", "resource",
            "log_date", "from_time", "to_time", "hours",
            "billable", "description"
        ],
        order_by="log_date desc"
    )

    if not time_logs:
        return {"file_url": None, "message": _("No time logs found")}

    # Enrich with names
    for log in time_logs:
        if log.get("task"):
            log["task_subject"] = frappe.db.get_value("Orga Task", log["task"], "subject")
        if log.get("project"):
            log["project_name"] = frappe.db.get_value("Orga Project", log["project"], "project_name")
        if log.get("resource"):
            log["resource_name"] = frappe.db.get_value("Orga Resource", log["resource"], "resource_name")

    filename = f"orga_time_logs_export_{now_datetime().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        return _create_json_file({"time_logs": time_logs}, filename)
    else:
        return _create_csv_file(time_logs, filename)


@frappe.whitelist()
def export_timesheet_report(project: str = None, from_date: str = None,
                            to_date: str = None, format: str = "csv"):
    """
    Export aggregated timesheet report.

    Args:
        project: Filter by project (optional)
        from_date: Report start date
        to_date: Report end date
        format: Output format ('csv' or 'json')

    Returns:
        dict: {file_url: str} for download
    """
    filters = {}
    if project:
        filters["project"] = project

    if from_date and to_date:
        filters["log_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["log_date"] = [">=", from_date]
    elif to_date:
        filters["log_date"] = ["<=", to_date]

    # Get aggregated data by resource and date
    time_logs = frappe.get_all(
        "Orga Time Log",
        filters=filters,
        fields=["resource", "log_date", "hours", "billable", "project"]
    )

    # Aggregate by resource and date
    aggregated = {}
    for log in time_logs:
        key = (log.get("resource") or "Unassigned", str(log.get("log_date")))
        if key not in aggregated:
            aggregated[key] = {
                "resource": log.get("resource") or "Unassigned",
                "date": str(log.get("log_date")),
                "total_hours": 0,
                "billable_hours": 0,
                "non_billable_hours": 0
            }

        hours = flt(log.get("hours"))
        aggregated[key]["total_hours"] += hours
        if log.get("billable"):
            aggregated[key]["billable_hours"] += hours
        else:
            aggregated[key]["non_billable_hours"] += hours

    # Convert to list and enrich with resource names
    report = list(aggregated.values())
    for row in report:
        if row["resource"] != "Unassigned":
            row["resource_name"] = frappe.db.get_value(
                "Orga Resource", row["resource"], "resource_name"
            )
        else:
            row["resource_name"] = "Unassigned"

        # Round hours
        row["total_hours"] = round(row["total_hours"], 2)
        row["billable_hours"] = round(row["billable_hours"], 2)
        row["non_billable_hours"] = round(row["non_billable_hours"], 2)

    if not report:
        return {"file_url": None, "message": _("No time data found")}

    filename = f"orga_timesheet_report_{now_datetime().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        return _create_json_file({"report": report}, filename)
    else:
        return _create_csv_file(report, filename)


# =============================================================================
# IMPORT ENDPOINTS
# =============================================================================

@frappe.whitelist()
def import_tasks(file_url: str, project: str, update_existing: bool = False):
    """
    Import tasks from CSV file.

    Args:
        file_url: URL of uploaded CSV file
        project: Target project for imported tasks
        update_existing: Whether to update existing tasks by name

    Returns:
        dict: Import summary
    """
    _check_import_permission()

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project not found"))

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    content = file_doc.get_content()

    if isinstance(content, bytes):
        content = content.decode("utf-8")

    reader = csv.DictReader(content.splitlines())

    imported = 0
    updated = 0
    errors = []
    row_num = 1

    for row in reader:
        row_num += 1
        try:
            # Validate required fields
            if not row.get("subject"):
                errors.append({
                    "row": row_num,
                    "error": "Subject is required"
                })
                continue

            # Check if task exists
            existing = None
            if row.get("name"):
                existing = frappe.db.exists("Orga Task", row["name"])

            if existing and update_existing:
                task = frappe.get_doc("Orga Task", existing)
                _update_task_from_row(task, row)
                task.save()
                updated += 1
            elif not existing:
                task = frappe.get_doc({
                    "doctype": "Orga Task",
                    "project": project
                })
                _update_task_from_row(task, row)
                task.insert()
                imported += 1
            else:
                # Task exists but update_existing is False
                errors.append({
                    "row": row_num,
                    "error": f"Task {row['name']} already exists"
                })

        except Exception as e:
            errors.append({
                "row": row_num,
                "error": str(e)
            })

    frappe.db.commit()

    return {
        "success": len(errors) == 0,
        "imported": imported,
        "updated": updated,
        "total_rows": row_num - 1,
        "errors": errors[:10],  # Return first 10 errors
        "error_count": len(errors)
    }


def _update_task_from_row(task, row):
    """Update task fields from CSV row."""
    field_map = {
        "subject": "subject",
        "description": "description",
        "status": "status",
        "priority": "priority",
        "start_date": "start_date",
        "due_date": "due_date",
        "estimated_hours": "estimated_hours",
        "assigned_to": "assigned_to",
        "milestone": "milestone"
    }

    for csv_field, doc_field in field_map.items():
        if row.get(csv_field):
            value = row[csv_field]

            # Handle numeric fields
            if doc_field == "estimated_hours":
                value = flt(value)

            # Handle date fields
            if doc_field in ["start_date", "due_date"] and value:
                try:
                    value = getdate(value)
                except Exception:
                    pass

            setattr(task, doc_field, value)


@frappe.whitelist()
def import_resources(file_url: str, update_existing: bool = False):
    """
    Import resources from CSV file.

    Args:
        file_url: URL of uploaded CSV file
        update_existing: Whether to update existing resources

    Returns:
        dict: Import summary
    """
    _check_import_permission()

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    content = file_doc.get_content()

    if isinstance(content, bytes):
        content = content.decode("utf-8")

    reader = csv.DictReader(content.splitlines())

    imported = 0
    updated = 0
    errors = []
    row_num = 1

    for row in reader:
        row_num += 1
        try:
            # Validate required fields
            if not row.get("resource_name"):
                errors.append({
                    "row": row_num,
                    "error": "Resource name is required"
                })
                continue

            # Check if resource exists by name or email
            existing = None
            if row.get("name"):
                existing = frappe.db.exists("Orga Resource", row["name"])
            elif row.get("email"):
                existing = frappe.db.exists("Orga Resource", {"email": row["email"]})

            if existing and update_existing:
                resource = frappe.get_doc("Orga Resource", existing)
                _update_resource_from_row(resource, row)
                resource.save()
                updated += 1
            elif not existing:
                resource = frappe.get_doc({
                    "doctype": "Orga Resource"
                })
                _update_resource_from_row(resource, row)
                resource.insert()
                imported += 1
            else:
                errors.append({
                    "row": row_num,
                    "error": f"Resource already exists"
                })

        except Exception as e:
            errors.append({
                "row": row_num,
                "error": str(e)
            })

    frappe.db.commit()

    return {
        "success": len(errors) == 0,
        "imported": imported,
        "updated": updated,
        "total_rows": row_num - 1,
        "errors": errors[:10],
        "error_count": len(errors)
    }


def _update_resource_from_row(resource, row):
    """Update resource fields from CSV row."""
    field_map = {
        "resource_name": "resource_name",
        "email": "email",
        "resource_type": "resource_type",
        "status": "status",
        "department": "department",
        "designation": "designation",
        "weekly_capacity": "weekly_capacity",
        "hourly_cost": "hourly_cost",
        "billable_rate": "billable_rate"
    }

    for csv_field, doc_field in field_map.items():
        if row.get(csv_field):
            value = row[csv_field]

            # Handle numeric fields
            if doc_field in ["weekly_capacity", "hourly_cost", "billable_rate"]:
                value = flt(value)

            setattr(resource, doc_field, value)


@frappe.whitelist()
def validate_import_file(file_url: str, doctype: str):
    """
    Validate an import file before processing.

    Args:
        file_url: URL of uploaded CSV file
        doctype: Target DocType ('Orga Task' or 'Orga Resource')

    Returns:
        dict: Validation results
    """
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    content = file_doc.get_content()

    if isinstance(content, bytes):
        content = content.decode("utf-8")

    try:
        reader = csv.DictReader(content.splitlines())
        headers = reader.fieldnames

        if not headers:
            return {
                "valid": False,
                "error": "No headers found in CSV file"
            }

        # Required fields by doctype
        required_fields = {
            "Orga Task": ["subject"],
            "Orga Resource": ["resource_name"]
        }

        required = required_fields.get(doctype, [])
        missing = [f for f in required if f not in headers]

        if missing:
            return {
                "valid": False,
                "error": f"Missing required columns: {', '.join(missing)}",
                "headers": headers
            }

        # Count rows
        rows = list(reader)

        return {
            "valid": True,
            "headers": headers,
            "row_count": len(rows),
            "required_fields": required,
            "sample_row": rows[0] if rows else None
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_import_template(doctype: str):
    """
    Get a CSV template for importing data.

    Args:
        doctype: DocType to get template for

    Returns:
        dict: {file_url: str} for download
    """
    templates = {
        "Orga Task": [
            "subject", "description", "status", "priority",
            "start_date", "due_date", "estimated_hours", "assigned_to"
        ],
        "Orga Resource": [
            "resource_name", "email", "resource_type", "status",
            "department", "designation", "weekly_capacity",
            "hourly_cost", "billable_rate"
        ],
        "Orga Time Log": [
            "task", "log_date", "hours", "billable", "description"
        ]
    }

    if doctype not in templates:
        frappe.throw(_("Invalid DocType for import"))

    headers = templates[doctype]

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    # Add example row
    if doctype == "Orga Task":
        writer.writerow([
            "Example Task", "Task description", "Open", "Medium",
            "2026-02-01", "2026-02-15", "8", "user@example.com"
        ])
    elif doctype == "Orga Resource":
        writer.writerow([
            "John Doe", "john@example.com", "Employee", "Active",
            "Engineering", "Software Engineer", "40", "50", "100"
        ])
    elif doctype == "Orga Time Log":
        writer.writerow([
            "TASK-00001", "2026-02-01", "8", "1", "Worked on feature"
        ])

    filename = f"orga_{doctype.lower().replace(' ', '_')}_template"
    return _create_csv_file_from_string(output.getvalue(), filename)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _create_csv_file(data: list, filename: str) -> dict:
    """Create a CSV file from list of dicts."""
    if not data:
        return {"file_url": None, "message": _("No data to export")}

    output = StringIO()
    fieldnames = list(data[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    return _create_csv_file_from_string(output.getvalue(), filename)


def _create_csv_file_from_string(content: str, filename: str) -> dict:
    """Create a CSV file from string content."""
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{filename}.csv",
        "content": content,
        "is_private": 1
    })
    file_doc.insert()
    frappe.db.commit()

    return {"file_url": file_doc.file_url, "filename": file_doc.file_name}


def _create_json_file(data: dict, filename: str) -> dict:
    """Create a JSON file from data."""
    content = json.dumps(data, default=str, indent=2)

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{filename}.json",
        "content": content,
        "is_private": 1
    })
    file_doc.insert()
    frappe.db.commit()

    return {"file_url": file_doc.file_url, "filename": file_doc.file_name}
