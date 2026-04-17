# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Assignment API endpoints for Orga.
"""

import json
import frappe
from frappe import _


@frappe.whitelist()
def get_assignments(task=None, resource=None, project=None, status=None, limit=100, offset=0):
    """
    Get assignments with optional filters.

    Args:
        task: Filter by task
        resource: Filter by resource
        project: Filter by project
        status: Filter by status
        limit: Max results
        offset: Pagination offset

    Returns:
        dict: {assignments: [...], total: int}
    """
    filters = {}
    if task:
        filters["task"] = task
    if resource:
        filters["resource"] = resource
    if project:
        filters["project"] = project
    if status:
        filters["status"] = status

    assignments = frappe.get_all(
        "Orga Assignment",
        filters=filters,
        fields=[
            "name", "task", "resource", "project", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="start_date desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Assignment", filters)

    # Enrich with names
    for assignment in assignments:
        assignment["task_subject"] = frappe.db.get_value(
            "Orga Task", assignment["task"], "subject"
        )
        assignment["resource_name"] = frappe.db.get_value(
            "Orga Resource", assignment["resource"], "resource_name"
        )
        if assignment["project"]:
            assignment["project_name"] = frappe.db.get_value(
                "Orga Project", assignment["project"], "project_name"
            )

    return {
        "assignments": assignments,
        "total": total
    }


@frappe.whitelist()
def get_assignment(name):
    """
    Get single assignment details.

    Args:
        name: Assignment name/ID

    Returns:
        dict: Assignment data
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Assignment", name)
    assignment = doc.as_dict()

    # Enrich
    assignment["task_subject"] = frappe.db.get_value(
        "Orga Task", assignment["task"], "subject"
    )
    assignment["resource_name"] = frappe.db.get_value(
        "Orga Resource", assignment["resource"], "resource_name"
    )
    if assignment["project"]:
        assignment["project_name"] = frappe.db.get_value(
            "Orga Project", assignment["project"], "project_name"
        )

    return assignment


@frappe.whitelist()
def create_assignment(task, resource, allocated_hours=None, start_date=None, end_date=None, role=None):
    """
    Create a task assignment.

    Args:
        task: Task name/ID
        resource: Resource name/ID
        allocated_hours: Hours to allocate
        start_date: Assignment start
        end_date: Assignment end
        role: Role on this task

    Returns:
        dict: Created assignment
    """
    if not task or not resource:
        frappe.throw(_("Task and resource are required"))

    if not frappe.db.exists("Orga Task", task):
        frappe.throw(_("Task {0} not found").format(task), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Resource", resource):
        frappe.throw(_("Resource {0} not found").format(resource), frappe.DoesNotExistError)

    doc = frappe.get_doc({
        "doctype": "Orga Assignment",
        "task": task,
        "resource": resource,
        "allocated_hours": float(allocated_hours) if allocated_hours else None,
        "start_date": start_date,
        "end_date": end_date,
        "role": role,
        "status": "Assigned"
    })
    doc.insert()
    frappe.db.commit()

    return get_assignment(doc.name)


@frappe.whitelist()
def update_assignment(name, data):
    """
    Update an assignment.

    Args:
        name: Assignment name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated assignment
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Assignment", name)

    allowed_fields = [
        "status", "role", "start_date", "end_date",
        "allocated_hours", "notes"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return get_assignment(doc.name)


@frappe.whitelist()
def delete_assignment(name):
    """
    Delete an assignment.

    Args:
        name: Assignment name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Assignment name is required"))

    if not frappe.db.exists("Orga Assignment", name):
        frappe.throw(_("Assignment {0} not found").format(name), frappe.DoesNotExistError)

    frappe.delete_doc("Orga Assignment", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_task_assignments(task_name):
    """
    Get all assignments for a task.

    Args:
        task_name: Task name/ID

    Returns:
        list: Assignments with resource details
    """
    if not task_name:
        frappe.throw(_("Task name is required"))

    assignments = frappe.get_all(
        "Orga Assignment",
        filters={"task": task_name},
        fields=[
            "name", "resource", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="creation asc"
    )

    for assignment in assignments:
        if not assignment.get("resource"):
            assignment["resource_name"] = None
            assignment["resource_email"] = None
            assignment["resource_status"] = None
            assignment["initials"] = ""
            continue
        resource = frappe.get_doc("Orga Resource", assignment["resource"])
        assignment["resource_name"] = resource.resource_name
        assignment["resource_email"] = resource.email
        assignment["resource_status"] = resource.status

        name_parts = resource.resource_name.split()
        if len(name_parts) >= 2:
            assignment["initials"] = (name_parts[0][0] + name_parts[-1][0]).upper()
        else:
            assignment["initials"] = resource.resource_name[:2].upper()

    return assignments


@frappe.whitelist()
def get_resource_assignments(resource_name, status=None, include_completed=False):
    """
    Get all assignments for a resource.

    Args:
        resource_name: Resource name/ID
        status: Filter by status
        include_completed: Include completed assignments

    Returns:
        list: Assignments with task details
    """
    if not resource_name:
        frappe.throw(_("Resource name is required"))

    filters = {"resource": resource_name}

    if status:
        filters["status"] = status
    elif not include_completed:
        filters["status"] = ["in", ["Assigned", "In Progress"]]

    assignments = frappe.get_all(
        "Orga Assignment",
        filters=filters,
        fields=[
            "name", "task", "project", "status", "role",
            "start_date", "end_date", "allocated_hours", "actual_hours"
        ],
        order_by="start_date asc"
    )

    for assignment in assignments:
        task = frappe.db.get_value(
            "Orga Task",
            assignment["task"],
            ["subject", "status", "priority", "due_date"],
            as_dict=True
        )
        assignment["task_subject"] = task.subject if task else None
        assignment["task_status"] = task.status if task else None
        assignment["task_priority"] = task.priority if task else None
        assignment["task_due_date"] = task.due_date if task else None

        if assignment["project"]:
            assignment["project_name"] = frappe.db.get_value(
                "Orga Project", assignment["project"], "project_name"
            )

    return assignments


# ---------------------------------------------------------------------------
# Picker API — flat Assignees model (Model 1a)
# Spec: ecosystem.localhost/spec/apps/orga/features/community/task-assignment.md
#
# Task has a flat list of assignees (internal or external, all equal). No
# per-task Owner concept — the PM owns the project. Identity is Contact.
# Orga Task.assigned_to is a derived convenience pointer to the first
# internal assignee's user (for My Tasks / notifications), set by this API.
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_task_assignees(task: str) -> dict:
    """Return current assignees for the task — picker initial state."""
    task_doc = frappe.get_doc("Orga Task", task)
    task_doc.check_permission("read")

    rows = frappe.get_all(
        "Orga Assignment",
        filters={"task": task},
        fields=["contact"],
        order_by="creation asc",
    )
    contact_names = [r["contact"] for r in rows if r.get("contact")]
    assignees = []
    if contact_names:
        contacts = frappe.get_all(
            "Contact",
            filters={"name": ("in", contact_names)},
            fields=["name", "full_name", "image", "user", "email_id"],
        )
        by_name = {c["name"]: c for c in contacts}
        for cname in contact_names:
            c = by_name.get(cname)
            if not c:
                continue
            assignees.append({
                "contact": c["name"],
                "name": c.get("full_name") or c["name"],
                "avatar": c.get("image"),
                "email": c.get("email_id"),
                "is_internal": bool(c.get("user")),
            })

    return {"task": task, "assignees": assignees}


@frappe.whitelist()
def search_assignable(query: str = "", project: str | None = None, limit: int = 20):
    """Return ranked assignable rows sourced from Dock People, enriched with Orga Resource.

    Row shape:
      {contact, name, avatar, email, is_internal, role_label, resource, last_assigned}
    """
    from dock.api.people import get_list as dock_people_get_list

    limit = max(1, min(int(limit), 50))
    query = (query or "").strip()

    people = dock_people_get_list(limit=max(limit * 2, 50), query=query or None)
    items = people.get("items", []) if isinstance(people, dict) else []
    if not items:
        return []

    contact_names = [i["name"] for i in items]
    resource_map = _resource_map_for_contacts(contact_names)
    last_assigned_map = _last_assigned_map(contact_names, project=project)

    rows = []
    for item in items:
        cname = item["name"]
        res = resource_map.get(cname)
        role_label = (
            (res.get("department") or res.get("resource_type") or "")
            if res
            else (frappe.db.get_value("Contact", cname, "designation") or "")
        )
        rows.append({
            "contact": cname,
            "name": item.get("full_name") or cname,
            "avatar": item.get("image"),
            "email": item.get("email_id"),
            "is_internal": bool(item.get("user")),
            "role_label": role_label,
            "resource": res["name"] if res else None,
            "last_assigned": last_assigned_map.get(cname),
        })

    _rank_rows(rows, query=query, project=project)
    return rows[:limit]


def _resource_map_for_contacts(contact_names: list[str]) -> dict[str, dict]:
    if not contact_names:
        return {}
    rows = frappe.get_all(
        "Orga Resource",
        filters={"contact": ("in", contact_names), "status": "Active"},
        fields=["name", "contact", "department", "resource_type"],
    )
    return {r["contact"]: r for r in rows if r.get("contact")}


def _last_assigned_map(contact_names: list[str], project: str | None) -> dict[str, str]:
    """Most-recent Orga Assignment.modified per contact (optionally scoped to a project)."""
    if not contact_names:
        return {}
    filters = {"contact": ("in", contact_names)}
    if project:
        filters["project"] = project
    rows = frappe.get_all(
        "Orga Assignment",
        filters=filters,
        fields=["contact", "modified"],
        order_by="modified desc",
    )
    out: dict[str, str] = {}
    for r in rows:
        out.setdefault(r["contact"], r["modified"])
    return out


def _rank_rows(rows: list[dict], query: str, project: str | None) -> None:
    q = (query or "").lower()

    def score(row):
        name = (row.get("name") or "").lower()
        prefix = 0 if q and name.startswith(q) else 1
        substr = 0 if q and q in name else 1
        recency = 0 if row.get("last_assigned") else 1
        return (prefix, substr, recency, name)

    rows.sort(key=score)


@frappe.whitelist()
def set_assignees(task: str, contacts=None):
    """Idempotently set the flat assignee list for a task.

    - contacts: list of Contact names. Internal or external, order preserved.

    Task.assigned_to is derived as the first internal assignee's user (or None)
    so My Tasks / notifications still work. Resource is populated on Assignment
    rows only when an Orga Resource exists for that contact; never auto-created.
    """
    if isinstance(contacts, str):
        contacts = json.loads(contacts)
    contacts = list(dict.fromkeys(contacts or []))  # dedup, keep order

    task_doc = frappe.get_doc("Orga Task", task)
    task_doc.check_permission("write")

    # Validate and classify
    contact_rows = []
    if contacts:
        rows = frappe.get_all(
            "Contact",
            filters={"name": ("in", contacts)},
            fields=["name", "user", "email_id", "full_name"],
        )
        by_name = {r["name"]: r for r in rows}
        missing = [c for c in contacts if c not in by_name]
        if missing:
            frappe.throw(_("Contact {0} not found").format(missing[0]))
        contact_rows = [by_name[c] for c in contacts]

    # Derive assigned_to from first internal contact (or None)
    derived_user = next((r["user"] for r in contact_rows if r.get("user")), None)
    user_changed = task_doc.assigned_to != derived_user
    task_doc.assigned_to = derived_user

    # Upsert Assignment rows keyed by contact
    project = task_doc.project
    existing = frappe.get_all(
        "Orga Assignment",
        filters={"task": task},
        fields=["name", "contact"],
    )
    existing_by_contact: dict[str, str] = {
        r["contact"]: r["name"] for r in existing if r.get("contact")
    }

    target = set(contacts)
    current = set(existing_by_contact)

    for contact in current - target:
        frappe.delete_doc("Orga Assignment", existing_by_contact[contact], ignore_permissions=False)

    for contact in target - current:
        resource = frappe.db.get_value(
            "Orga Resource", {"contact": contact, "status": "Active"}, "name"
        )
        frappe.get_doc({
            "doctype": "Orga Assignment",
            "task": task,
            "contact": contact,
            "resource": resource,
            "project": project,
            "status": "Assigned",
        }).insert()

    if user_changed or (target != current):
        task_doc.save()

    frappe.db.commit()

    # Notify newly added assignees (after commit so the data is consistent).
    # Skip the derived assigned_to user — on_task_update hook already notifies them
    # when task_doc.save() fires above, so we only notify the rest here.
    newly_added = target - current
    if newly_added:
        _notify_new_assignees(
            task_doc, newly_added,
            {r["name"]: r for r in contact_rows},
            skip_user=derived_user if user_changed else None,
        )

    return {
        "task": task_doc.name,
        "assigned_user": derived_user,
        "contacts": list(contacts),
    }


def _notify_new_assignees(
    task_doc,
    contact_names: set[str],
    contact_map: dict[str, dict],
    skip_user: str | None = None,
) -> None:
    """Notify newly assigned contacts — Dock bell for internal, email for external.

    skip_user: if set, skip this Frappe User (already notified by on_task_update hook
    when assigned_to changed on the task doc).
    """
    for cname in contact_names:
        crow = contact_map.get(cname)
        if not crow:
            continue

        user = crow.get("user")
        if user and user == skip_user:
            continue
        if user and user != frappe.session.user:
            # Internal: Dock bell notification
            try:
                from orga.orga.integrations.dock_notification import publish
                publish(
                    notification_type="task_assigned",
                    title=_("You have been assigned to: {0}").format(task_doc.subject),
                    for_user=user,
                    message=_("Task '{0}' in project '{1}' was assigned to you.").format(
                        task_doc.subject, task_doc.project or ""
                    ),
                    reference_doctype="Orga Task",
                    reference_name=task_doc.name,
                )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    _("Failed to send Dock notification for {0}").format(cname),
                )
        elif not user:
            # External: email notification
            _email_external_assignee(task_doc, cname)


def _email_external_assignee(task_doc, contact_name: str) -> None:
    """Send assignment email to an external contact. Honors dock_do_not_contact."""
    contact = frappe.db.get_value(
        "Contact",
        contact_name,
        ["email_id", "full_name", "dock_do_not_contact"],
        as_dict=True,
    )
    if not contact or not contact.get("email_id"):
        return
    if contact.get("dock_do_not_contact"):
        return

    project_name = ""
    if task_doc.project:
        project_name = frappe.db.get_value(
            "Orga Project", task_doc.project, "project_name"
        ) or task_doc.project

    subject = _("You've been assigned to: {0}").format(task_doc.subject)
    message = frappe.render_template(
        """<p>{{ _("Hello") }} {{ contact_name }},</p>
<p>{{ _("You have been assigned to the task") }} <b>{{ task_subject }}</b>
{% if project_name %} {{ _("in project") }} <b>{{ project_name }}</b>{% endif %}.</p>
{% if due_date %}<p>{{ _("Due date") }}: {{ due_date }}</p>{% endif %}
<p>{{ _("Assigned by") }}: {{ assigned_by }}</p>""",
        {
            "contact_name": contact.get("full_name") or contact_name,
            "task_subject": task_doc.subject,
            "project_name": project_name,
            "due_date": task_doc.due_date or "",
            "assigned_by": frappe.utils.get_fullname(frappe.session.user),
        },
    )

    try:
        frappe.sendmail(
            recipients=[contact.get("email_id")],
            subject=subject,
            message=message,
            reference_doctype="Orga Task",
            reference_name=task_doc.name,
            now=False,  # queue it
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            _("Failed to email assignment to {0}").format(contact_name),
        )
