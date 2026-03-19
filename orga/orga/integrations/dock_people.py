# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Dock People context provider for Orga.

Called by Dock when rendering a contact detail view via the
``dock_people_context`` hook.  Returns a context panel showing
the Orga Resource enrichment data (workload, skills, capacity)
for the given Frappe Contact.
"""

import frappe
from frappe import _


def get_people_context(contact_name: str) -> dict | None:
    """Return an Orga context panel for a Frappe Contact.

    Looks up the ``Orga Resource`` linked to *contact_name* via the
    ``contact`` field.  Returns ``None`` if no resource is linked.
    """
    resource = frappe.db.get_value(
        "Orga Resource",
        {"contact": contact_name},
        [
            "name",
            "resource_name",
            "resource_type",
            "status",
            "department",
            "weekly_capacity",
        ],
        as_dict=True,
    )
    if not resource:
        return None

    # Workload summary
    workload_label = _("Available")
    try:
        doc = frappe.get_doc("Orga Resource", resource.name)
        wl = doc.get_current_workload()
        utilization = wl.get("utilization_percent", 0)
        active = wl.get("assignment_count", 0)
        if utilization > 100:
            workload_label = _("{0}% — Overallocated").format(utilization)
        elif utilization > 80:
            workload_label = _("{0}% — Busy").format(utilization)
        elif utilization > 0:
            workload_label = _("{0}%").format(utilization)
    except Exception:
        active = 0

    # Skills summary
    skills = frappe.get_all(
        "Orga Resource Skill",
        filters={"parent": resource.name},
        fields=["skill_name", "proficiency"],
        order_by="proficiency desc",
        limit_page_length=5,
    )
    skills_str = ", ".join(
        f"{s.skill_name} ({s.proficiency})" for s in skills
    ) if skills else _("None")

    fields = [
        {"label": _("Type"), "value": resource.resource_type or ""},
        {"label": _("Status"), "value": resource.status or ""},
        {"label": _("Department"), "value": resource.department or "—"},
        {"label": _("Utilization"), "value": workload_label},
        {"label": _("Active Tasks"), "value": str(active)},
        {"label": _("Capacity"), "value": _("{0} h/week").format(resource.weekly_capacity or 40)},
        {"label": _("Skills"), "value": skills_str},
    ]

    return {
        "label": _("Team Member"),
        "icon": "users",
        "link": f"/orga/people/{contact_name}",
        "fields": fields,
    }
