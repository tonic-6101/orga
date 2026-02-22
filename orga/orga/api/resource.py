# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Resource API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.resource.get_resources',
        args: { status: 'Active' }
    })
"""

import json
import frappe
from frappe import _
from frappe.utils import today, add_days


@frappe.whitelist()
def get_resources(status=None, department=None, resource_type=None, skill=None, limit=100, offset=0):
    """
    Get list of resources with optional filters.

    Args:
        status: Filter by status (Active, Inactive, On Leave)
        department: Filter by department
        resource_type: Filter by type (Employee, Contractor, External)
        skill: Filter by skill name
        limit: Max results (default 100)
        offset: Pagination offset

    Returns:
        dict: {resources: [...], total: int}
    """
    filters = {}
    if status:
        filters["status"] = status
    if department:
        filters["department"] = department
    if resource_type:
        filters["resource_type"] = resource_type

    # Base query
    resources = frappe.get_all(
        "Orga Resource",
        filters=filters,
        fields=[
            "name", "resource_name", "user", "email", "phone", "mobile_no",
            "resource_type", "status", "department", "designation", "company",
            "availability_hours", "weekly_capacity"
        ],
        order_by="resource_name asc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Resource", filters)

    # Enrich with skills and workload
    for resource in resources:
        # Get skills
        resource["skills"] = frappe.get_all(
            "Orga Resource Skill",
            filters={"parent": resource["name"]},
            fields=["skill_name", "proficiency", "years_experience"]
        )

        # Get current assignment count and workload
        assignments = frappe.get_all(
            "Orga Assignment",
            filters={"resource": resource["name"], "status": ["in", ["Assigned", "In Progress"]]},
            fields=["allocated_hours"]
        )
        resource["active_assignments"] = len(assignments)

        # Calculate workload/utilization
        allocated_hours = sum(a.get("allocated_hours") or 0 for a in assignments)
        weekly_capacity = resource.get("weekly_capacity") or 40
        utilization = (allocated_hours / weekly_capacity * 100) if weekly_capacity else 0

        resource["allocated_hours"] = round(allocated_hours, 1)
        resource["utilization_percent"] = round(utilization, 1)
        resource["workload_status"] = (
            "overallocated" if utilization > 100
            else "busy" if utilization > 80
            else "moderate" if utilization > 50
            else "available"
        )

        # Get initials for avatar
        name_parts = resource["resource_name"].split()
        if len(name_parts) >= 2:
            resource["initials"] = (name_parts[0][0] + name_parts[-1][0]).upper()
        else:
            resource["initials"] = resource["resource_name"][:2].upper()

    # Filter by skill if specified (post-filter since it's in child table)
    if skill:
        resources = [r for r in resources if any(
            s["skill_name"].lower() == skill.lower() for s in r.get("skills", [])
        )]

    return {
        "resources": resources,
        "total": total
    }


@frappe.whitelist()
def get_resource(name):
    """
    Get single resource with full details.

    Args:
        name: Resource name/ID

    Returns:
        dict: Resource data with skills and assignments
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if not frappe.db.exists("Orga Resource", name):
        frappe.throw(_("Resource {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Resource", name)
    resource = doc.as_dict()

    # Get skills
    resource["skills"] = [s.as_dict() for s in doc.skills] if doc.skills else []

    # Get active assignments with task details
    assignments = frappe.get_all(
        "Orga Assignment",
        filters={
            "resource": name,
            "status": ["in", ["Assigned", "In Progress"]]
        },
        fields=[
            "name", "task", "project", "status", "role",
            "start_date", "end_date", "allocated_hours"
        ],
        order_by="start_date asc"
    )

    for assignment in assignments:
        assignment["task_subject"] = frappe.db.get_value(
            "Orga Task", assignment["task"], "subject"
        )
        assignment["project_name"] = frappe.db.get_value(
            "Orga Project", assignment["project"], "project_name"
        ) if assignment["project"] else None

    resource["assignments"] = assignments

    # Resolve reports_to name
    if resource.get("reports_to"):
        resource["reports_to_name"] = frappe.db.get_value(
            "Orga Resource", resource["reports_to"], "resource_name"
        )

    # Calculate workload
    resource["workload"] = doc.get_current_workload()

    # Get initials
    name_parts = resource["resource_name"].split()
    if len(name_parts) >= 2:
        resource["initials"] = (name_parts[0][0] + name_parts[-1][0]).upper()
    else:
        resource["initials"] = resource["resource_name"][:2].upper()

    return resource


@frappe.whitelist()
def create_resource(data):
    """
    Create a new resource.

    Args:
        data: dict or JSON string with resource fields

    Returns:
        dict: Created resource data
    """
    if isinstance(data, str):
        data = json.loads(data)

    required_fields = ["resource_name"]
    for field in required_fields:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    allowed_fields = [
        "resource_name", "user", "employee", "email", "phone", "mobile_no",
        "resource_type", "status", "department", "designation", "company",
        "reports_to", "date_of_joining", "address",
        "availability_hours", "weekly_capacity", "hourly_cost",
        "billable_rate", "notes"
    ]

    doc_data = {"doctype": "Orga Resource"}
    for field in allowed_fields:
        if field in data:
            doc_data[field] = data[field]

    doc = frappe.get_doc(doc_data)
    doc.insert()
    frappe.db.commit()

    return get_resource(doc.name)


@frappe.whitelist()
def update_resource(name, data):
    """
    Update a resource.

    Args:
        name: Resource name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated resource data
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Resource", name):
        frappe.throw(_("Resource {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Resource", name)

    allowed_fields = [
        "resource_name", "user", "employee", "email", "phone", "mobile_no",
        "resource_type", "status", "department", "designation", "company",
        "reports_to", "date_of_joining", "address",
        "availability_hours", "weekly_capacity", "hourly_cost",
        "billable_rate", "notes"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return get_resource(doc.name)


@frappe.whitelist()
def delete_resource(name):
    """
    Delete a resource.

    Args:
        name: Resource name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if not frappe.db.exists("Orga Resource", name):
        frappe.throw(_("Resource {0} not found").format(name), frappe.DoesNotExistError)

    # Check for active assignments
    active_assignments = frappe.db.count(
        "Orga Assignment",
        {"resource": name, "status": ["in", ["Assigned", "In Progress"]]}
    )
    if active_assignments > 0:
        frappe.throw(
            _("Cannot delete resource with {0} active assignments. Complete or cancel them first.").format(
                active_assignments
            )
        )

    frappe.delete_doc("Orga Resource", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_resource_workload(name, start_date=None, end_date=None):
    """
    Get resource workload and utilization.

    Args:
        name: Resource name/ID
        start_date: Period start (default: today)
        end_date: Period end (default: 7 days from start)

    Returns:
        dict: Workload details
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if not start_date:
        start_date = today()
    if not end_date:
        end_date = add_days(start_date, 7)

    resource = frappe.get_doc("Orga Resource", name)

    # Get assignments in date range
    assignments = frappe.get_all(
        "Orga Assignment",
        filters={
            "resource": name,
            "status": ["in", ["Assigned", "In Progress"]],
            "start_date": ["<=", end_date],
            "end_date": [">=", start_date]
        },
        fields=[
            "name", "task", "project", "allocated_hours",
            "start_date", "end_date", "status"
        ]
    )

    for assignment in assignments:
        assignment["task_subject"] = frappe.db.get_value(
            "Orga Task", assignment["task"], "subject"
        )

    total_allocated = sum(a.get("allocated_hours") or 0 for a in assignments)
    utilization = (total_allocated / resource.weekly_capacity * 100) if resource.weekly_capacity else 0

    return {
        "resource": name,
        "resource_name": resource.resource_name,
        "period": {"start": start_date, "end": end_date},
        "weekly_capacity": resource.weekly_capacity,
        "allocated_hours": total_allocated,
        "utilization_percent": round(utilization, 1),
        "status": "overallocated" if utilization > 100 else ("busy" if utilization > 80 else "available"),
        "assignments": assignments
    }


@frappe.whitelist()
def search_resources_by_skill(skill, min_proficiency=None, status="Active"):
    """
    Find resources with a specific skill.

    Args:
        skill: Skill name to search
        min_proficiency: Minimum proficiency level
        status: Resource status filter

    Returns:
        list: Matching resources with skill details
    """
    if not skill:
        frappe.throw(_("Skill is required"))

    proficiency_order = ["Beginner", "Intermediate", "Advanced", "Expert"]

    # Find resources with this skill
    skill_entries = frappe.get_all(
        "Orga Resource Skill",
        filters={"skill_name": ["like", f"%{skill}%"]},
        fields=["parent", "skill_name", "proficiency", "years_experience"]
    )

    # Filter by proficiency if specified
    if min_proficiency and min_proficiency in proficiency_order:
        min_idx = proficiency_order.index(min_proficiency)
        skill_entries = [
            s for s in skill_entries
            if proficiency_order.index(s.get("proficiency", "Beginner")) >= min_idx
        ]

    # Get unique resource IDs
    resource_ids = list(set(s["parent"] for s in skill_entries))

    if not resource_ids:
        return []

    # Get resource details
    filters = {"name": ["in", resource_ids]}
    if status:
        filters["status"] = status

    resources = frappe.get_all(
        "Orga Resource",
        filters=filters,
        fields=[
            "name", "resource_name", "email", "status",
            "department", "designation", "weekly_capacity"
        ]
    )

    # Attach matching skill info
    skill_map = {s["parent"]: s for s in skill_entries}
    for resource in resources:
        resource["matched_skill"] = skill_map.get(resource["name"])

    return resources


@frappe.whitelist()
def add_resource_skill(resource_name, skill_name, proficiency="Intermediate", years_experience=0):
    """
    Add a skill to a resource.

    Args:
        resource_name: Resource name/ID
        skill_name: Skill name
        proficiency: Proficiency level
        years_experience: Years of experience

    Returns:
        dict: Updated resource skills
    """
    if not resource_name or not skill_name:
        frappe.throw(_("Resource and skill name are required"))

    resource = frappe.get_doc("Orga Resource", resource_name)

    # Check if skill already exists
    for skill in resource.skills:
        if skill.skill_name.lower() == skill_name.lower():
            frappe.throw(_("Skill {0} already exists for this resource").format(skill_name))

    resource.append("skills", {
        "skill_name": skill_name,
        "proficiency": proficiency,
        "years_experience": float(years_experience) if years_experience else 0
    })

    resource.save()
    frappe.db.commit()

    return [s.as_dict() for s in resource.skills]


@frappe.whitelist()
def remove_resource_skill(resource_name, skill_name):
    """
    Remove a skill from a resource.

    Args:
        resource_name: Resource name/ID
        skill_name: Skill name to remove

    Returns:
        dict: {success: True}
    """
    if not resource_name or not skill_name:
        frappe.throw(_("Resource and skill name are required"))

    resource = frappe.get_doc("Orga Resource", resource_name)

    resource.skills = [s for s in resource.skills if s.skill_name.lower() != skill_name.lower()]

    resource.save()
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_contact_stats(name):
    """
    Get comprehensive statistics for a contact.

    Args:
        name: Resource name/ID

    Returns:
        dict: Aggregated stats across assignments, time logs, defects, projects, financial
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if not frappe.db.exists("Orga Resource", name):
        frappe.throw(_("Resource {0} not found").format(name), frappe.DoesNotExistError)

    resource = frappe.get_doc("Orga Resource", name)

    # Assignment stats
    assignment_total = frappe.db.count("Orga Assignment", {"resource": name})
    assignment_active = frappe.db.count(
        "Orga Assignment", {"resource": name, "status": ["in", ["Assigned", "In Progress"]]}
    )
    assignment_completed = frappe.db.count(
        "Orga Assignment", {"resource": name, "status": "Completed"}
    )
    assignment_cancelled = frappe.db.count(
        "Orga Assignment", {"resource": name, "status": "Cancelled"}
    )

    # Time log stats - query by user (primary link)
    user_email = resource.user or resource.email
    time_stats = {"total_hours": 0, "billable_hours": 0, "log_count": 0}
    if user_email:
        time_result = frappe.db.sql("""
            SELECT
                COALESCE(SUM(hours), 0) as total_hours,
                COALESCE(SUM(CASE WHEN billable = 1 THEN hours ELSE 0 END), 0) as billable_hours,
                COUNT(*) as log_count
            FROM `tabOrga Time Log`
            WHERE user = %s
        """, (user_email,), as_dict=True)
        time_stats = time_result[0] if time_result else time_stats

    # Defect stats
    defect_stats = {"total": 0, "open": 0, "resolved": 0, "total_cost": 0, "total_estimate": 0}
    try:
        if frappe.db.exists("DocType", "Orga Defect") and frappe.db.table_exists("Orga Defect"):
            defect_result = frappe.db.sql("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('Open', 'In Progress') THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved,
                    COALESCE(SUM(actual_cost), 0) as total_cost,
                    COALESCE(SUM(cost_estimate), 0) as total_estimate
                FROM `tabOrga Defect`
                WHERE contact = %s
            """, (name,), as_dict=True)
            if defect_result:
                d = defect_result[0]
                defect_stats = {
                    "total": d.total or 0,
                    "open": d.open_count or 0,
                    "resolved": d.resolved or 0,
                    "total_cost": float(d.total_cost or 0),
                    "total_estimate": float(d.total_estimate or 0)
                }
    except Exception:
        pass  # Defect table not yet created

    # Project stats - distinct projects from assignments
    project_rows = frappe.db.sql("""
        SELECT DISTINCT a.project, p.project_name, p.status
        FROM `tabOrga Assignment` a
        JOIN `tabOrga Project` p ON a.project = p.name
        WHERE a.resource = %s AND a.project IS NOT NULL AND a.project != ''
    """, (name,), as_dict=True)
    active_projects = [p for p in project_rows if p.status in ("Planning", "Active")]

    # Financial calculations
    total_billed_hours = float(time_stats.get("billable_hours") or 0)
    hourly_cost = float(resource.hourly_cost or 0)
    billable_rate = float(resource.billable_rate or 0)

    return {
        "assignments": {
            "total": assignment_total,
            "active": assignment_active,
            "completed": assignment_completed,
            "cancelled": assignment_cancelled
        },
        "time_logs": {
            "total_hours": float(time_stats.get("total_hours") or 0),
            "billable_hours": total_billed_hours,
            "log_count": time_stats.get("log_count") or 0
        },
        "defects": defect_stats,
        "projects": {
            "total": len(project_rows),
            "active_count": len(active_projects),
            "project_list": [
                {"name": p.project, "project_name": p.project_name, "status": p.status}
                for p in project_rows
            ]
        },
        "financial": {
            "hourly_cost": hourly_cost,
            "billable_rate": billable_rate,
            "total_billed_hours": total_billed_hours,
            "total_cost_to_org": round(float(time_stats.get("total_hours") or 0) * hourly_cost, 2),
            "defect_cost": float(defect_stats.get("total_cost") or 0)
        }
    }


@frappe.whitelist()
def get_contact_timeline(name, limit=20, offset=0):
    """
    Get assignment history over time for a contact.

    Args:
        name: Resource name/ID
        limit: Max results (default 20)
        offset: Pagination offset

    Returns:
        dict: {timeline: [...], total: int}
    """
    if not name:
        frappe.throw(_("Resource name is required"))

    if not frappe.db.exists("Orga Resource", name):
        frappe.throw(_("Resource {0} not found").format(name), frappe.DoesNotExistError)

    total = frappe.db.count("Orga Assignment", {"resource": name})

    timeline = frappe.db.sql("""
        SELECT
            a.name, a.task, a.project, a.status,
            a.start_date, a.end_date, a.allocated_hours, a.actual_hours,
            t.subject as task_subject,
            p.project_name
        FROM `tabOrga Assignment` a
        LEFT JOIN `tabOrga Task` t ON a.task = t.name
        LEFT JOIN `tabOrga Project` p ON a.project = p.name
        WHERE a.resource = %s
        ORDER BY a.start_date DESC
        LIMIT %s OFFSET %s
    """, (name, int(limit), int(offset)), as_dict=True)

    return {"timeline": timeline, "total": total}
