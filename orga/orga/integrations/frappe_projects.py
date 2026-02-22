# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Frappe Projects Integration Module

Provides two-way synchronization between Orga and Frappe Projects module.

Usage:
    from orga.orga.integrations.frappe_projects import sync_project, sync_all_projects

    # Sync a single project
    sync_project("ORG-2026-0001")

    # Sync all enabled projects
    sync_all_projects()
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cstr


# =============================================================================
# STATUS MAPPINGS
# =============================================================================

# Orga Project Status -> Frappe Project Status
PROJECT_STATUS_TO_FRAPPE = {
    "Planning": "Open",
    "Active": "Open",
    "On Hold": "Open",
    "Completed": "Completed",
    "Cancelled": "Cancelled"
}

# Frappe Project Status -> Orga Project Status
PROJECT_STATUS_FROM_FRAPPE = {
    "Open": "Active",
    "Completed": "Completed",
    "Cancelled": "Cancelled"
}

# Orga Task Status -> Frappe Task Status
TASK_STATUS_TO_FRAPPE = {
    "Open": "Open",
    "In Progress": "Working",
    "Review": "Pending Review",
    "Completed": "Completed",
    "Cancelled": "Cancelled"
}

# Frappe Task Status -> Orga Task Status
TASK_STATUS_FROM_FRAPPE = {
    "Open": "Open",
    "Working": "In Progress",
    "Pending Review": "Review",
    "Completed": "Completed",
    "Cancelled": "Cancelled",
    "Overdue": "Open"  # Map overdue to Open
}


# =============================================================================
# SETTINGS HELPERS
# =============================================================================

def get_sync_settings():
    """Get Frappe Projects sync settings from Orga Settings."""
    settings = frappe.get_single("Orga Settings")
    return {
        "enabled": settings.enable_frappe_projects_sync,
        "direction": settings.frappe_projects_sync_direction or "Two Way",
        "auto_sync": settings.auto_sync_frappe_projects,
        "interval_minutes": settings.frappe_sync_interval_minutes or 60
    }


def is_sync_enabled():
    """Check if Frappe Projects sync is globally enabled."""
    return frappe.db.get_single_value("Orga Settings", "enable_frappe_projects_sync")


def get_sync_direction():
    """Get the configured sync direction."""
    return frappe.db.get_single_value("Orga Settings", "frappe_projects_sync_direction") or "Two Way"


# =============================================================================
# PROJECT SYNC: ORGA -> FRAPPE
# =============================================================================

@frappe.whitelist()
def sync_project_to_frappe(orga_project_name):
    """
    Sync an Orga Project to Frappe Projects module.

    Args:
        orga_project_name: Name of the Orga Project to sync

    Returns:
        dict: {success: bool, frappe_project: str, message: str}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    direction = get_sync_direction()
    if direction == "Frappe to Orga":
        return {"success": False, "message": _("Sync direction is set to Frappe to Orga only")}

    try:
        orga_project = frappe.get_doc("Orga Project", orga_project_name)

        if not orga_project.sync_with_frappe_projects:
            return {"success": False, "message": _("Sync not enabled for this project")}

        # Check if Frappe Projects module exists
        if not frappe.db.exists("DocType", "Project"):
            return {"success": False, "message": _("Frappe Projects module not installed")}

        frappe_project_name = orga_project.frappe_project_link

        if frappe_project_name and frappe.db.exists("Project", frappe_project_name):
            # Update existing project
            frappe_project = frappe.get_doc("Project", frappe_project_name)
            _update_frappe_project_from_orga(frappe_project, orga_project)
            frappe_project.save(ignore_permissions=True)
            action = "updated"
        else:
            # Create new project
            frappe_project = frappe.get_doc({
                "doctype": "Project",
                "project_name": orga_project.project_name,
            })
            _update_frappe_project_from_orga(frappe_project, orga_project)
            frappe_project.insert(ignore_permissions=True)

            # Update Orga Project with link
            orga_project.frappe_project_link = frappe_project.name
            action = "created"

        # Update sync timestamp
        orga_project.last_frappe_sync = now_datetime()
        orga_project.frappe_sync_status = "Synced"
        orga_project.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "frappe_project": frappe_project.name,
            "message": _("Project {0} to Frappe Projects").format(action)
        }

    except Exception as e:
        frappe.log_error(f"Sync to Frappe failed for {orga_project_name}: {str(e)}")
        # Update sync status to error
        frappe.db.set_value("Orga Project", orga_project_name, "frappe_sync_status", "Error", update_modified=False)
        return {"success": False, "message": str(e)}


def _update_frappe_project_from_orga(frappe_project, orga_project):
    """Update Frappe Project fields from Orga Project."""
    frappe_project.project_name = orga_project.project_name
    frappe_project.status = PROJECT_STATUS_TO_FRAPPE.get(orga_project.status, "Open")
    frappe_project.notes = orga_project.description or ""
    frappe_project.expected_start_date = orga_project.start_date
    frappe_project.expected_end_date = orga_project.end_date
    frappe_project.actual_start_date = orga_project.actual_start
    frappe_project.actual_end_date = orga_project.actual_end
    frappe_project.percent_complete = orga_project.progress or 0

    # Budget fields (if they exist in Frappe Project)
    if hasattr(frappe_project, "estimated_costing"):
        frappe_project.estimated_costing = orga_project.budget or 0
    if hasattr(frappe_project, "total_costing_amount"):
        frappe_project.total_costing_amount = orga_project.spent or 0


# =============================================================================
# PROJECT SYNC: FRAPPE -> ORGA
# =============================================================================

@frappe.whitelist()
def sync_project_from_frappe(frappe_project_name, orga_project_name=None):
    """
    Sync a Frappe Project to Orga.

    Args:
        frappe_project_name: Name of the Frappe Project to sync from
        orga_project_name: Optional - existing Orga Project to update

    Returns:
        dict: {success: bool, orga_project: str, message: str}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    direction = get_sync_direction()
    if direction == "Orga to Frappe":
        return {"success": False, "message": _("Sync direction is set to Orga to Frappe only")}

    try:
        if not frappe.db.exists("Project", frappe_project_name):
            return {"success": False, "message": _("Frappe Project {0} not found").format(frappe_project_name)}

        frappe_project = frappe.get_doc("Project", frappe_project_name)

        if orga_project_name and frappe.db.exists("Orga Project", orga_project_name):
            # Update existing Orga Project
            orga_project = frappe.get_doc("Orga Project", orga_project_name)
            _update_orga_project_from_frappe(orga_project, frappe_project)
            orga_project.save(ignore_permissions=True)
            action = "updated"
        else:
            # Find by link or create new
            existing = frappe.db.get_value(
                "Orga Project",
                {"frappe_project_link": frappe_project_name},
                "name"
            )

            if existing:
                orga_project = frappe.get_doc("Orga Project", existing)
                _update_orga_project_from_frappe(orga_project, frappe_project)
                orga_project.save(ignore_permissions=True)
                action = "updated"
            else:
                # Create new Orga Project
                # Generate project code
                prefix = frappe.db.get_single_value("Orga Settings", "project_code_prefix") or "ORG"
                year = frappe.utils.nowdate()[:4]
                count = frappe.db.count("Orga Project") + 1
                project_code = f"{prefix}-{year}-{count:04d}"

                orga_project = frappe.get_doc({
                    "doctype": "Orga Project",
                    "project_code": project_code,
                    "sync_with_frappe_projects": 1,
                    "frappe_project_link": frappe_project_name
                })
                _update_orga_project_from_frappe(orga_project, frappe_project)

                # Set required fields with defaults
                if not orga_project.project_manager:
                    orga_project.project_manager = frappe.session.user

                orga_project.insert(ignore_permissions=True)
                action = "created"

        # Update sync timestamp
        orga_project.last_frappe_sync = now_datetime()
        orga_project.frappe_sync_status = "Synced"
        orga_project.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "orga_project": orga_project.name,
            "message": _("Orga Project {0} from Frappe Projects").format(action)
        }

    except Exception as e:
        frappe.log_error(f"Sync from Frappe failed for {frappe_project_name}: {str(e)}")
        return {"success": False, "message": str(e)}


def _update_orga_project_from_frappe(orga_project, frappe_project):
    """Update Orga Project fields from Frappe Project."""
    orga_project.project_name = frappe_project.project_name
    orga_project.status = PROJECT_STATUS_FROM_FRAPPE.get(frappe_project.status, "Active")
    orga_project.description = frappe_project.notes or ""
    orga_project.start_date = frappe_project.expected_start_date
    orga_project.end_date = frappe_project.expected_end_date
    orga_project.actual_start = frappe_project.actual_start_date
    orga_project.actual_end = frappe_project.actual_end_date
    orga_project.progress = frappe_project.percent_complete or 0

    # Budget fields
    if hasattr(frappe_project, "estimated_costing"):
        orga_project.budget = frappe_project.estimated_costing or 0
    if hasattr(frappe_project, "total_costing_amount"):
        orga_project.spent = frappe_project.total_costing_amount or 0


# =============================================================================
# TASK SYNC: ORGA -> FRAPPE
# =============================================================================

@frappe.whitelist()
def sync_task_to_frappe(orga_task_name):
    """
    Sync an Orga Task to Frappe Task.

    Args:
        orga_task_name: Name of the Orga Task to sync

    Returns:
        dict: {success: bool, frappe_task: str, message: str}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    direction = get_sync_direction()
    if direction == "Frappe to Orga":
        return {"success": False, "message": _("Sync direction is set to Frappe to Orga only")}

    try:
        orga_task = frappe.get_doc("Orga Task", orga_task_name)

        # Check if parent project is synced
        orga_project = frappe.get_doc("Orga Project", orga_task.project)
        if not orga_project.sync_with_frappe_projects:
            return {"success": False, "message": _("Parent project sync not enabled")}

        if not orga_project.frappe_project_link:
            return {"success": False, "message": _("Parent project not synced to Frappe yet")}

        # Check if Frappe Task exists
        if not frappe.db.exists("DocType", "Task"):
            return {"success": False, "message": _("Frappe Task DocType not found")}

        frappe_task_name = orga_task.frappe_task_link

        if frappe_task_name and frappe.db.exists("Task", frappe_task_name):
            # Update existing task
            frappe_task = frappe.get_doc("Task", frappe_task_name)
            _update_frappe_task_from_orga(frappe_task, orga_task, orga_project.frappe_project_link)
            frappe_task.save(ignore_permissions=True)
            action = "updated"
        else:
            # Create new task
            frappe_task = frappe.get_doc({
                "doctype": "Task",
                "subject": orga_task.subject,
                "project": orga_project.frappe_project_link
            })
            _update_frappe_task_from_orga(frappe_task, orga_task, orga_project.frappe_project_link)
            frappe_task.insert(ignore_permissions=True)

            # Update Orga Task with link
            orga_task.frappe_task_link = frappe_task.name
            action = "created"

        # Update sync timestamp
        orga_task.last_frappe_sync = now_datetime()
        orga_task.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "frappe_task": frappe_task.name,
            "message": _("Task {0} to Frappe").format(action)
        }

    except Exception as e:
        frappe.log_error(f"Task sync to Frappe failed for {orga_task_name}: {str(e)}")
        return {"success": False, "message": str(e)}


def _update_frappe_task_from_orga(frappe_task, orga_task, frappe_project_name):
    """Update Frappe Task fields from Orga Task."""
    frappe_task.subject = orga_task.subject
    frappe_task.project = frappe_project_name
    frappe_task.status = TASK_STATUS_TO_FRAPPE.get(orga_task.status, "Open")
    frappe_task.priority = orga_task.priority
    frappe_task.description = orga_task.description or ""
    frappe_task.exp_start_date = orga_task.start_date
    frappe_task.exp_end_date = orga_task.due_date
    frappe_task.completed_on = orga_task.completed_date
    frappe_task.progress = orga_task.progress or 0
    frappe_task.expected_time = orga_task.estimated_hours or 0
    frappe_task.actual_time = orga_task.actual_hours or 0


# =============================================================================
# TASK SYNC: FRAPPE -> ORGA
# =============================================================================

@frappe.whitelist()
def sync_task_from_frappe(frappe_task_name, orga_task_name=None):
    """
    Sync a Frappe Task to Orga Task.

    Args:
        frappe_task_name: Name of the Frappe Task to sync from
        orga_task_name: Optional - existing Orga Task to update

    Returns:
        dict: {success: bool, orga_task: str, message: str}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    direction = get_sync_direction()
    if direction == "Orga to Frappe":
        return {"success": False, "message": _("Sync direction is set to Orga to Frappe only")}

    try:
        if not frappe.db.exists("Task", frappe_task_name):
            return {"success": False, "message": _("Frappe Task {0} not found").format(frappe_task_name)}

        frappe_task = frappe.get_doc("Task", frappe_task_name)

        # Find corresponding Orga Project
        if not frappe_task.project:
            return {"success": False, "message": _("Frappe Task has no project")}

        orga_project_name = frappe.db.get_value(
            "Orga Project",
            {"frappe_project_link": frappe_task.project},
            "name"
        )

        if not orga_project_name:
            return {"success": False, "message": _("No Orga Project linked to Frappe Project {0}").format(frappe_task.project)}

        if orga_task_name and frappe.db.exists("Orga Task", orga_task_name):
            # Update existing Orga Task
            orga_task = frappe.get_doc("Orga Task", orga_task_name)
            _update_orga_task_from_frappe(orga_task, frappe_task, orga_project_name)
            orga_task.save(ignore_permissions=True)
            action = "updated"
        else:
            # Find by link or create new
            existing = frappe.db.get_value(
                "Orga Task",
                {"frappe_task_link": frappe_task_name},
                "name"
            )

            if existing:
                orga_task = frappe.get_doc("Orga Task", existing)
                _update_orga_task_from_frappe(orga_task, frappe_task, orga_project_name)
                orga_task.save(ignore_permissions=True)
                action = "updated"
            else:
                # Create new Orga Task
                orga_task = frappe.get_doc({
                    "doctype": "Orga Task",
                    "frappe_task_link": frappe_task_name,
                    "project": orga_project_name
                })
                _update_orga_task_from_frappe(orga_task, frappe_task, orga_project_name)
                orga_task.insert(ignore_permissions=True)
                action = "created"

        # Update sync timestamp
        orga_task.last_frappe_sync = now_datetime()
        orga_task.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "orga_task": orga_task.name,
            "message": _("Orga Task {0} from Frappe").format(action)
        }

    except Exception as e:
        frappe.log_error(f"Task sync from Frappe failed for {frappe_task_name}: {str(e)}")
        return {"success": False, "message": str(e)}


def _update_orga_task_from_frappe(orga_task, frappe_task, orga_project_name):
    """Update Orga Task fields from Frappe Task."""
    orga_task.subject = frappe_task.subject
    orga_task.project = orga_project_name
    orga_task.status = TASK_STATUS_FROM_FRAPPE.get(frappe_task.status, "Open")
    orga_task.priority = frappe_task.priority or "Medium"
    orga_task.description = frappe_task.description or ""
    orga_task.start_date = frappe_task.exp_start_date
    orga_task.due_date = frappe_task.exp_end_date
    orga_task.completed_date = frappe_task.completed_on
    orga_task.progress = frappe_task.progress or 0
    orga_task.estimated_hours = frappe_task.expected_time or 0
    orga_task.actual_hours = frappe_task.actual_time or 0


# =============================================================================
# BULK SYNC OPERATIONS
# =============================================================================

@frappe.whitelist()
def sync_project(project_name):
    """
    Sync a single project based on configured direction.

    Args:
        project_name: Orga Project name

    Returns:
        dict: Sync result
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    direction = get_sync_direction()

    if direction == "Orga to Frappe":
        return sync_project_to_frappe(project_name)
    elif direction == "Frappe to Orga":
        orga_project = frappe.get_doc("Orga Project", project_name)
        if orga_project.frappe_project_link:
            return sync_project_from_frappe(orga_project.frappe_project_link, project_name)
        return {"success": False, "message": _("No Frappe Project linked")}
    else:
        # Two-way: sync to Frappe (Orga is source of truth for existing projects)
        return sync_project_to_frappe(project_name)


@frappe.whitelist()
def sync_all_projects():
    """
    Sync all projects that have sync enabled.

    Returns:
        dict: {success: bool, synced: int, failed: int, errors: list}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    # Get all projects with sync enabled
    projects = frappe.get_all(
        "Orga Project",
        filters={"sync_with_frappe_projects": 1},
        fields=["name"]
    )

    synced = 0
    failed = 0
    errors = []

    for project in projects:
        result = sync_project(project.name)
        if result.get("success"):
            synced += 1
        else:
            failed += 1
            errors.append({
                "project": project.name,
                "error": result.get("message")
            })

    return {
        "success": failed == 0,
        "synced": synced,
        "failed": failed,
        "errors": errors
    }


@frappe.whitelist()
def sync_project_tasks(project_name):
    """
    Sync all tasks for a project.

    Args:
        project_name: Orga Project name

    Returns:
        dict: {success: bool, synced: int, failed: int, errors: list}
    """
    if not is_sync_enabled():
        return {"success": False, "message": _("Frappe Projects sync is not enabled")}

    orga_project = frappe.get_doc("Orga Project", project_name)
    if not orga_project.sync_with_frappe_projects:
        return {"success": False, "message": _("Sync not enabled for this project")}

    # Get all tasks for this project
    tasks = frappe.get_all(
        "Orga Task",
        filters={"project": project_name},
        fields=["name"]
    )

    synced = 0
    failed = 0
    errors = []

    for task in tasks:
        result = sync_task_to_frappe(task.name)
        if result.get("success"):
            synced += 1
        else:
            failed += 1
            errors.append({
                "task": task.name,
                "error": result.get("message")
            })

    return {
        "success": failed == 0,
        "synced": synced,
        "failed": failed,
        "errors": errors
    }


# =============================================================================
# SCHEDULED SYNC
# =============================================================================

def scheduled_sync():
    """
    Scheduled job to sync all enabled projects.
    Called by Frappe scheduler based on Orga Settings interval.
    """
    settings = get_sync_settings()

    if not settings["enabled"] or not settings["auto_sync"]:
        return

    frappe.logger().info("Starting scheduled Frappe Projects sync")

    try:
        result = sync_all_projects()
        frappe.logger().info(
            f"Scheduled sync completed: {result.get('synced')} synced, {result.get('failed')} failed"
        )
    except Exception as e:
        frappe.log_error(f"Scheduled Frappe Projects sync failed: {str(e)}")


# =============================================================================
# HOOKS FOR REAL-TIME SYNC
# =============================================================================

def on_orga_project_update(doc, method):
    """
    Hook called when Orga Project is saved.
    Triggers sync if enabled.
    """
    if not is_sync_enabled():
        return

    if not doc.sync_with_frappe_projects:
        return

    direction = get_sync_direction()
    if direction in ["Orga to Frappe", "Two Way"]:
        # Queue the sync to avoid blocking
        frappe.enqueue(
            "orga.orga.integrations.frappe_projects.sync_project_to_frappe",
            orga_project_name=doc.name,
            queue="short"
        )


def on_orga_task_update(doc, method):
    """
    Hook called when Orga Task is saved.
    Triggers sync if parent project is synced.
    """
    if not is_sync_enabled():
        return

    # Check if parent project is synced
    project_synced = frappe.db.get_value(
        "Orga Project",
        doc.project,
        "sync_with_frappe_projects"
    )

    if not project_synced:
        return

    direction = get_sync_direction()
    if direction in ["Orga to Frappe", "Two Way"]:
        frappe.enqueue(
            "orga.orga.integrations.frappe_projects.sync_task_to_frappe",
            orga_task_name=doc.name,
            queue="short"
        )
