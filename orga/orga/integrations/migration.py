# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Migration Tools for Frappe Projects to Orga

Provides one-time migration capabilities to import existing Frappe Projects
data into Orga with full dependency preservation and rollback support.

Usage:
    from orga.orga.integrations.migration import migrate_from_frappe_projects

    # Preview migration (dry run)
    preview = preview_migration()

    # Execute migration
    result = migrate_from_frappe_projects()

    # Rollback if needed
    rollback_migration(result["migration_id"])
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, cstr
import json


# =============================================================================
# MIGRATION LOG DOCTYPE
# =============================================================================

def ensure_migration_log_exists():
    """Create Migration Log DocType if it doesn't exist (runtime creation)."""
    # We'll use a simple JSON file for migration logs instead of a DocType
    # to avoid requiring database migrations
    pass


# =============================================================================
# MIGRATION PREVIEW
# =============================================================================

@frappe.whitelist()
def preview_migration(project_filters=None):
    """
    Preview what will be migrated from Frappe Projects.

    Args:
        project_filters: Optional dict of filters for Project selection

    Returns:
        dict: {
            projects: list of projects to migrate,
            tasks: list of tasks to migrate,
            total_projects: int,
            total_tasks: int,
            warnings: list of potential issues
        }
    """
    if not frappe.db.exists("DocType", "Project"):
        return {
            "success": False,
            "message": _("Frappe Projects module not installed")
        }

    filters = project_filters or {}

    # Get all Frappe Projects
    projects = frappe.get_all(
        "Project",
        filters=filters,
        fields=[
            "name", "project_name", "status", "percent_complete",
            "expected_start_date", "expected_end_date",
            "actual_start_date", "actual_end_date",
            "notes", "estimated_costing", "total_costing_amount"
        ]
    )

    # Check which are already migrated
    migrated_projects = frappe.get_all(
        "Orga Project",
        filters={"frappe_project_link": ["is", "set"]},
        fields=["frappe_project_link"]
    )
    migrated_project_names = {p.frappe_project_link for p in migrated_projects}

    # Get all Frappe Tasks
    tasks = []
    task_count = 0
    for project in projects:
        project_tasks = frappe.get_all(
            "Task",
            filters={"project": project.name},
            fields=[
                "name", "subject", "status", "priority",
                "exp_start_date", "exp_end_date", "completed_on",
                "progress", "expected_time", "actual_time",
                "description", "depends_on"
            ]
        )
        task_count += len(project_tasks)
        project["task_count"] = len(project_tasks)
        project["already_migrated"] = project.name in migrated_project_names

    warnings = []

    # Check for potential issues
    if migrated_project_names:
        warnings.append({
            "type": "info",
            "message": _("{0} projects already migrated (will be skipped or updated)").format(
                len(migrated_project_names)
            )
        })

    # Check for tasks without projects
    orphan_tasks = frappe.db.count("Task", {"project": ["is", "not set"]})
    if orphan_tasks > 0:
        warnings.append({
            "type": "warning",
            "message": _("{0} tasks without projects will be skipped").format(orphan_tasks)
        })

    return {
        "success": True,
        "projects": projects,
        "total_projects": len(projects),
        "total_tasks": task_count,
        "already_migrated": len(migrated_project_names),
        "warnings": warnings
    }


# =============================================================================
# MAIN MIGRATION FUNCTION
# =============================================================================

@frappe.whitelist()
def migrate_from_frappe_projects(
    project_filters=None,
    skip_existing=True,
    dry_run=False,
    batch_size=50
):
    """
    Migrate all projects and tasks from Frappe Projects to Orga.

    Args:
        project_filters: Optional dict of filters for Project selection
        skip_existing: If True, skip projects already migrated
        dry_run: If True, don't actually create records
        batch_size: Number of records to process before committing

    Returns:
        dict: {
            success: bool,
            migration_id: str,
            projects_created: int,
            projects_updated: int,
            projects_skipped: int,
            tasks_created: int,
            tasks_updated: int,
            errors: list
        }
    """
    if not frappe.db.exists("DocType", "Project"):
        return {
            "success": False,
            "message": _("Frappe Projects module not installed")
        }

    # Generate migration ID for tracking
    migration_id = f"MIG-{now_datetime().strftime('%Y%m%d-%H%M%S')}"

    filters = project_filters or {}

    # Get all Frappe Projects
    frappe_projects = frappe.get_all(
        "Project",
        filters=filters,
        fields=["name"]
    )

    # Track results
    results = {
        "success": True,
        "migration_id": migration_id,
        "dry_run": dry_run,
        "projects_created": 0,
        "projects_updated": 0,
        "projects_skipped": 0,
        "tasks_created": 0,
        "tasks_updated": 0,
        "errors": [],
        "migrated_projects": [],
        "migrated_tasks": []
    }

    # Get settings
    prefix = frappe.db.get_single_value("Orga Settings", "project_code_prefix") or "ORG"
    year = frappe.utils.nowdate()[:4]

    # Process each project
    for idx, fp in enumerate(frappe_projects):
        try:
            project_result = _migrate_single_project(
                fp.name, prefix, year, skip_existing, dry_run, migration_id
            )

            if project_result["action"] == "created":
                results["projects_created"] += 1
                results["migrated_projects"].append({
                    "frappe_project": fp.name,
                    "orga_project": project_result["orga_project"],
                    "action": "created"
                })
            elif project_result["action"] == "updated":
                results["projects_updated"] += 1
                results["migrated_projects"].append({
                    "frappe_project": fp.name,
                    "orga_project": project_result["orga_project"],
                    "action": "updated"
                })
            elif project_result["action"] == "skipped":
                results["projects_skipped"] += 1

            # Migrate tasks for this project
            if project_result["orga_project"]:
                task_results = _migrate_project_tasks(
                    fp.name,
                    project_result["orga_project"],
                    skip_existing,
                    dry_run,
                    migration_id
                )
                results["tasks_created"] += task_results["created"]
                results["tasks_updated"] += task_results["updated"]
                results["migrated_tasks"].extend(task_results["tasks"])
                results["errors"].extend(task_results["errors"])

            # Commit in batches
            if not dry_run and (idx + 1) % batch_size == 0:
                frappe.db.commit()

        except Exception as e:
            results["errors"].append({
                "type": "project",
                "name": fp.name,
                "error": str(e)
            })
            frappe.log_error(f"Migration error for project {fp.name}: {str(e)}")

    # Final commit
    if not dry_run:
        frappe.db.commit()

        # Save migration log
        _save_migration_log(migration_id, results)

    results["success"] = len(results["errors"]) == 0

    return results


def _migrate_single_project(frappe_project_name, prefix, year, skip_existing, dry_run, migration_id):
    """Migrate a single Frappe Project to Orga."""
    frappe_project = frappe.get_doc("Project", frappe_project_name)

    # Check if already migrated
    existing = frappe.db.get_value(
        "Orga Project",
        {"frappe_project_link": frappe_project_name},
        "name"
    )

    if existing:
        if skip_existing:
            return {"action": "skipped", "orga_project": existing}
        else:
            # Update existing
            if not dry_run:
                orga_project = frappe.get_doc("Orga Project", existing)
                _update_orga_project_fields(orga_project, frappe_project)
                orga_project.save(ignore_permissions=True)
            return {"action": "updated", "orga_project": existing}

    # Create new project
    if dry_run:
        return {"action": "created", "orga_project": f"[DRY-RUN]-{frappe_project_name}"}

    # Generate unique project code
    count = frappe.db.count("Orga Project") + 1
    project_code = f"{prefix}-{year}-{count:04d}"

    # Ensure unique
    while frappe.db.exists("Orga Project", project_code):
        count += 1
        project_code = f"{prefix}-{year}-{count:04d}"

    orga_project = frappe.get_doc({
        "doctype": "Orga Project",
        "project_code": project_code,
        "sync_with_frappe_projects": 1,
        "frappe_project_link": frappe_project_name,
        "project_manager": frappe.session.user
    })

    _update_orga_project_fields(orga_project, frappe_project)
    orga_project.insert(ignore_permissions=True)

    return {"action": "created", "orga_project": orga_project.name}


def _update_orga_project_fields(orga_project, frappe_project):
    """Update Orga Project fields from Frappe Project."""
    from .frappe_projects import PROJECT_STATUS_FROM_FRAPPE

    orga_project.project_name = frappe_project.project_name
    orga_project.status = PROJECT_STATUS_FROM_FRAPPE.get(frappe_project.status, "Active")
    orga_project.description = frappe_project.notes or ""
    orga_project.start_date = frappe_project.expected_start_date or frappe.utils.nowdate()
    orga_project.end_date = frappe_project.expected_end_date
    orga_project.actual_start = frappe_project.actual_start_date
    orga_project.actual_end = frappe_project.actual_end_date
    orga_project.progress = frappe_project.percent_complete or 0

    if hasattr(frappe_project, "estimated_costing"):
        orga_project.budget = frappe_project.estimated_costing or 0
    if hasattr(frappe_project, "total_costing_amount"):
        orga_project.spent = frappe_project.total_costing_amount or 0

    orga_project.last_frappe_sync = now_datetime()
    orga_project.frappe_sync_status = "Synced"


def _migrate_project_tasks(frappe_project_name, orga_project_name, skip_existing, dry_run, migration_id):
    """Migrate all tasks for a project."""
    from .frappe_projects import TASK_STATUS_FROM_FRAPPE

    results = {
        "created": 0,
        "updated": 0,
        "tasks": [],
        "errors": []
    }

    # Get all tasks for this project
    frappe_tasks = frappe.get_all(
        "Task",
        filters={"project": frappe_project_name},
        fields=["name"]
    )

    # First pass: create/update tasks
    task_mapping = {}  # frappe_task_name -> orga_task_name

    for ft in frappe_tasks:
        try:
            frappe_task = frappe.get_doc("Task", ft.name)

            # Check if already migrated
            existing = frappe.db.get_value(
                "Orga Task",
                {"frappe_task_link": ft.name},
                "name"
            )

            if existing:
                task_mapping[ft.name] = existing
                if skip_existing:
                    continue
                else:
                    # Update existing
                    if not dry_run:
                        orga_task = frappe.get_doc("Orga Task", existing)
                        _update_orga_task_fields(orga_task, frappe_task, orga_project_name)
                        orga_task.save(ignore_permissions=True)
                    results["updated"] += 1
                    results["tasks"].append({
                        "frappe_task": ft.name,
                        "orga_task": existing,
                        "action": "updated"
                    })
                    continue

            # Create new task
            if dry_run:
                task_mapping[ft.name] = f"[DRY-RUN]-{ft.name}"
                results["created"] += 1
                results["tasks"].append({
                    "frappe_task": ft.name,
                    "orga_task": f"[DRY-RUN]-{ft.name}",
                    "action": "created"
                })
                continue

            orga_task = frappe.get_doc({
                "doctype": "Orga Task",
                "project": orga_project_name,
                "frappe_task_link": ft.name
            })

            _update_orga_task_fields(orga_task, frappe_task, orga_project_name)
            orga_task.insert(ignore_permissions=True)

            task_mapping[ft.name] = orga_task.name
            results["created"] += 1
            results["tasks"].append({
                "frappe_task": ft.name,
                "orga_task": orga_task.name,
                "action": "created"
            })

        except Exception as e:
            results["errors"].append({
                "type": "task",
                "name": ft.name,
                "error": str(e)
            })

    # Second pass: set up dependencies
    if not dry_run:
        _migrate_task_dependencies(frappe_project_name, task_mapping)

    return results


def _update_orga_task_fields(orga_task, frappe_task, orga_project_name):
    """Update Orga Task fields from Frappe Task."""
    from .frappe_projects import TASK_STATUS_FROM_FRAPPE

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
    orga_task.last_frappe_sync = now_datetime()


def _migrate_task_dependencies(frappe_project_name, task_mapping):
    """Migrate task dependencies after all tasks are created."""
    # Get tasks with dependencies
    frappe_tasks = frappe.get_all(
        "Task",
        filters={
            "project": frappe_project_name,
            "depends_on": ["is", "set"]
        },
        fields=["name", "depends_on"]
    )

    for ft in frappe_tasks:
        if ft.name not in task_mapping:
            continue

        orga_task_name = task_mapping[ft.name]

        # Parse depends_on (it's a comma-separated list in Frappe Task)
        depends_on_names = [d.strip() for d in (ft.depends_on or "").split(",") if d.strip()]

        for dep_name in depends_on_names:
            if dep_name not in task_mapping:
                continue

            orga_dep_name = task_mapping[dep_name]

            # Check if dependency already exists
            existing_dep = frappe.db.exists(
                "Orga Task Dependency",
                {"parent": orga_task_name, "depends_on": orga_dep_name}
            )

            if not existing_dep:
                try:
                    orga_task = frappe.get_doc("Orga Task", orga_task_name)
                    orga_task.append("depends_on", {
                        "depends_on": orga_dep_name,
                        "dependency_type": "Finish to Start",
                        "lag_days": 0
                    })
                    orga_task.save(ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Failed to create dependency {orga_dep_name} -> {orga_task_name}: {str(e)}")


# =============================================================================
# MIGRATION LOG
# =============================================================================

def _get_migration_log_path():
    """Get the path for migration logs."""
    import os
    site_path = frappe.get_site_path()
    log_dir = os.path.join(site_path, "private", "orga_migrations")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir


def _save_migration_log(migration_id, results):
    """Save migration results to a JSON file for rollback capability."""
    import os

    log_path = os.path.join(_get_migration_log_path(), f"{migration_id}.json")

    log_data = {
        "migration_id": migration_id,
        "timestamp": str(now_datetime()),
        "user": frappe.session.user,
        "results": {
            "projects_created": results["projects_created"],
            "projects_updated": results["projects_updated"],
            "tasks_created": results["tasks_created"],
            "tasks_updated": results["tasks_updated"],
        },
        "migrated_projects": results["migrated_projects"],
        "migrated_tasks": results["migrated_tasks"],
        "errors": results["errors"]
    }

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2, default=str)

    return log_path


def _load_migration_log(migration_id):
    """Load migration log from JSON file."""
    import os

    log_path = os.path.join(_get_migration_log_path(), f"{migration_id}.json")

    if not os.path.exists(log_path):
        return None

    with open(log_path, "r") as f:
        return json.load(f)


# =============================================================================
# ROLLBACK
# =============================================================================

@frappe.whitelist()
def rollback_migration(migration_id):
    """
    Rollback a migration by deleting created records.

    Args:
        migration_id: The migration ID to rollback

    Returns:
        dict: {success: bool, deleted_projects: int, deleted_tasks: int}
    """
    log = _load_migration_log(migration_id)

    if not log:
        return {
            "success": False,
            "message": _("Migration log not found: {0}").format(migration_id)
        }

    deleted_tasks = 0
    deleted_projects = 0
    errors = []

    # Delete tasks first (to avoid foreign key issues)
    for task in log.get("migrated_tasks", []):
        if task.get("action") == "created":
            try:
                if frappe.db.exists("Orga Task", task["orga_task"]):
                    frappe.delete_doc("Orga Task", task["orga_task"], ignore_permissions=True)
                    deleted_tasks += 1
            except Exception as e:
                errors.append({
                    "type": "task",
                    "name": task["orga_task"],
                    "error": str(e)
                })

    # Delete projects
    for project in log.get("migrated_projects", []):
        if project.get("action") == "created":
            try:
                if frappe.db.exists("Orga Project", project["orga_project"]):
                    # First delete any remaining tasks
                    remaining_tasks = frappe.get_all(
                        "Orga Task",
                        filters={"project": project["orga_project"]},
                        fields=["name"]
                    )
                    for rt in remaining_tasks:
                        frappe.delete_doc("Orga Task", rt.name, ignore_permissions=True)
                        deleted_tasks += 1

                    frappe.delete_doc("Orga Project", project["orga_project"], ignore_permissions=True)
                    deleted_projects += 1
            except Exception as e:
                errors.append({
                    "type": "project",
                    "name": project["orga_project"],
                    "error": str(e)
                })

    frappe.db.commit()

    # Mark migration as rolled back
    import os
    log_path = os.path.join(_get_migration_log_path(), f"{migration_id}.json")
    log["rolled_back"] = True
    log["rollback_timestamp"] = str(now_datetime())
    log["rollback_results"] = {
        "deleted_projects": deleted_projects,
        "deleted_tasks": deleted_tasks,
        "errors": errors
    }

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2, default=str)

    return {
        "success": len(errors) == 0,
        "deleted_projects": deleted_projects,
        "deleted_tasks": deleted_tasks,
        "errors": errors
    }


# =============================================================================
# MIGRATION STATUS & HISTORY
# =============================================================================

@frappe.whitelist()
def get_migration_history():
    """
    Get list of all migrations performed.

    Returns:
        list: Migration logs sorted by date
    """
    import os

    log_dir = _get_migration_log_path()
    migrations = []

    if not os.path.exists(log_dir):
        return migrations

    for filename in os.listdir(log_dir):
        if filename.endswith(".json"):
            log_path = os.path.join(log_dir, filename)
            try:
                with open(log_path, "r") as f:
                    log = json.load(f)
                    migrations.append({
                        "migration_id": log.get("migration_id"),
                        "timestamp": log.get("timestamp"),
                        "user": log.get("user"),
                        "projects_created": log.get("results", {}).get("projects_created", 0),
                        "tasks_created": log.get("results", {}).get("tasks_created", 0),
                        "rolled_back": log.get("rolled_back", False)
                    })
            except Exception:
                pass

    # Sort by timestamp descending
    migrations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return migrations


@frappe.whitelist()
def get_migration_details(migration_id):
    """
    Get detailed information about a specific migration.

    Args:
        migration_id: The migration ID

    Returns:
        dict: Full migration log
    """
    log = _load_migration_log(migration_id)

    if not log:
        return {
            "success": False,
            "message": _("Migration log not found: {0}").format(migration_id)
        }

    return {
        "success": True,
        "migration": log
    }
