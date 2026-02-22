# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Unified search API for Orga.

Searches across multiple Orga doctypes and returns grouped results.
"""

import frappe
from frappe import _


# Doctype search configurations: (doctype, search_fields, return_fields, category, label_field, description_field, extra_field)
SEARCH_CONFIG = [
    {
        "doctype": "Orga Project",
        "category": "project",
        "search_fields": ["project_name", "project_code", "description"],
        "return_fields": ["name", "project_name", "project_code", "status", "progress"],
        "label_field": "project_name",
        "description_field": "project_code",
        "extra_field": None,
    },
    {
        "doctype": "Orga Task",
        "category": "task",
        "search_fields": ["subject", "description"],
        "return_fields": ["name", "subject", "project", "status", "priority"],
        "label_field": "subject",
        "description_field": "project",
        "extra_field": "priority",
    },
    {
        "doctype": "Orga Resource",
        "category": "resource",
        "search_fields": ["resource_name", "email", "department"],
        "return_fields": ["name", "resource_name", "email", "department", "status"],
        "label_field": "resource_name",
        "description_field": "department",
        "extra_field": "email",
    },
    {
        "doctype": "Orga Milestone",
        "category": "milestone",
        "search_fields": ["milestone_name", "description"],
        "return_fields": ["name", "milestone_name", "project", "status", "due_date"],
        "label_field": "milestone_name",
        "description_field": "project",
        "extra_field": "due_date",
    },
    {
        "doctype": "Orga Appointment",
        "category": "event",
        "search_fields": ["subject", "description"],
        "return_fields": ["name", "subject", "appointment_type", "start_datetime"],
        "label_field": "subject",
        "description_field": "appointment_type",
        "extra_field": "start_datetime",
    },
]


@frappe.whitelist()
def unified_search(query: str, category: str = "", limit: int = 5) -> dict:
    """
    Search across Orga doctypes and return grouped results.

    Args:
        query: Search string (min 2 characters)
        category: Optional filter to search only one category
        limit: Max results per category (default 5, max 20)

    Returns:
        dict with 'results' (grouped by category) and 'total' count
    """
    min_length = 1 if category else 2
    if not query or len(query.strip()) < min_length:
        return {"results": _empty_results(), "total": 0}

    query = query.strip()
    limit = min(int(limit), 20)

    results = {
        "projects": [],
        "tasks": [],
        "contacts": [],
        "milestones": [],
        "events": [],
    }

    total = 0
    search_term = f"%{query}%"

    for config in SEARCH_CONFIG:
        # Skip if category filter is set and doesn't match
        if category and config["category"] != category:
            continue

        or_filters = []
        for field in config["search_fields"]:
            or_filters.append([field, "like", search_term])

        try:
            rows = frappe.get_all(
                config["doctype"],
                or_filters=or_filters,
                fields=config["return_fields"],
                limit_page_length=limit,
                order_by="modified desc",
            )
        except Exception:
            # Skip doctypes that don't exist or user has no access to
            continue

        category_key = _category_to_key(config["category"])
        for row in rows:
            item = {
                "name": row.name,
                "label": row.get(config["label_field"], row.name),
                "status": row.get("status", ""),
                "category": config["category"],
            }

            desc_field = config["description_field"]
            if desc_field and row.get(desc_field):
                item["description"] = str(row.get(desc_field))

            extra_field = config["extra_field"]
            if extra_field and row.get(extra_field):
                item["extra"] = str(row.get(extra_field))

            results[category_key].append(item)

        total += len(rows)

    return {"results": results, "total": total}


_CATEGORY_KEY_MAP = {
    "project": "projects",
    "task": "tasks",
    "resource": "contacts",
    "milestone": "milestones",
    "event": "events",
}


def _category_to_key(category: str) -> str:
    return _CATEGORY_KEY_MAP.get(category, category + "s")


def _empty_results() -> dict:
    return {
        "projects": [],
        "tasks": [],
        "contacts": [],
        "milestones": [],
        "events": [],
    }
