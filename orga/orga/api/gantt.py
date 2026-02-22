# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Gantt chart API endpoints for Orga.

Provides a unified reorder_item endpoint using floating-point
lexicographical ordering (industry standard for Gantt charts).

Only the moved item's sort_order is updated in the DB per drag,
making this O(1) rather than O(n).

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.gantt.reorder_item',
        args: { item_id: 'TASK-00001', item_type: 'task', project: 'ORG-2026-0001',
                prev_item_id: 'MS-00001', next_item_id: 'TASK-00003' }
    })
"""

import frappe
from frappe import _


# Spacing between consecutive sort_order values when initialising
_INITIAL_GAP = 1000.0

# When adjacent items are too close (less than this), renumber all items
_MIN_GAP = 0.001


def _doctype_for(item_type: str) -> str:
    """Map item_type to DocType name."""
    if item_type == "task":
        return "Orga Task"
    elif item_type == "milestone":
        return "Orga Milestone"
    else:
        frappe.throw(_("Invalid item type: {0}").format(item_type))


def _has_sort_order(doctype: str) -> bool:
    """Check if sort_order column exists (pre-migration safe)."""
    try:
        return frappe.db.has_column(doctype, "sort_order")
    except Exception:
        return False


def _get_sort_order(doctype: str, name: str) -> float:
    """Get sort_order for an item, defaulting to 0."""
    try:
        val = frappe.db.get_value(doctype, name, "sort_order")
        return float(val) if val else 0.0
    except Exception:
        return 0.0


def _initialize_sort_orders(project: str) -> None:
    """
    Assign initial sort_order values to all items in a project that have sort_order=0.

    This handles the first-time setup: items created before the float sort_order
    migration get evenly-spaced values based on their current date ordering.
    """
    # Initialise tasks
    if _has_sort_order("Orga Task"):
        tasks = frappe.get_all(
            "Orga Task",
            filters={"project": project},
            fields=["name", "sort_order"],
            order_by="sort_order asc, start_date asc, due_date asc, creation asc"
        )
        _assign_initial_values(tasks, "Orga Task")

    # Initialise milestones
    if _has_sort_order("Orga Milestone"):
        milestones = frappe.get_all(
            "Orga Milestone",
            filters={"project": project},
            fields=["name", "sort_order"],
            order_by="sort_order asc, due_date asc, creation asc"
        )
        _assign_initial_values(milestones, "Orga Milestone")


def _assign_initial_values(items: list, doctype: str) -> None:
    """Assign evenly-spaced sort_order values to items that have sort_order=0."""
    needs_init = all((float(item.sort_order or 0)) == 0 for item in items)
    if not needs_init or not items:
        return

    for idx, item in enumerate(items):
        new_val = (idx + 1) * _INITIAL_GAP
        frappe.db.set_value(
            doctype, item.name, "sort_order", new_val,
            update_modified=False
        )


def _renumber_all(project: str) -> None:
    """
    Renumber all items in a project with evenly-spaced sort_order values.
    Called when floating-point precision gets too tight.
    """
    # Collect all items with their current sort_order
    all_items = []

    if _has_sort_order("Orga Task"):
        tasks = frappe.get_all(
            "Orga Task",
            filters={"project": project},
            fields=["name", "sort_order"],
            order_by="sort_order asc, creation asc"
        )
        for t in tasks:
            all_items.append(("Orga Task", t.name, float(t.sort_order or 0)))

    if _has_sort_order("Orga Milestone"):
        milestones = frappe.get_all(
            "Orga Milestone",
            filters={"project": project},
            fields=["name", "sort_order"],
            order_by="sort_order asc, creation asc"
        )
        for m in milestones:
            all_items.append(("Orga Milestone", m.name, float(m.sort_order or 0)))

    # Sort by current sort_order
    all_items.sort(key=lambda x: x[2])

    # Reassign with even spacing
    for idx, (doctype, name, _old) in enumerate(all_items):
        frappe.db.set_value(
            doctype, name, "sort_order", (idx + 1) * _INITIAL_GAP,
            update_modified=False
        )


@frappe.whitelist()
def reorder_item(item_id: str, item_type: str, project: str,
                 prev_item_id: str = None, next_item_id: str = None,
                 prev_item_type: str = None, next_item_type: str = None):
    """
    Reorder a single Gantt item using floating-point sort_order.

    The new sort_order is calculated as the midpoint between the previous
    and next items' sort_order values. Only 1 DB update per drag.

    Args:
        item_id: ID of the item being moved
        item_type: 'task' or 'milestone'
        project: Project name/ID
        prev_item_id: Item above the drop position (None if dropping at top)
        next_item_id: Item below the drop position (None if dropping at bottom)
        prev_item_type: Type of prev item ('task' or 'milestone')
        next_item_type: Type of next item ('task' or 'milestone')

    Returns:
        dict: {success: True, sort_order: float}
    """
    if not item_id:
        frappe.throw(_("Item ID is required"))
    if not item_type:
        frappe.throw(_("Item type is required"))
    if not project:
        frappe.throw(_("Project is required"))

    doctype = _doctype_for(item_type)

    if not frappe.db.exists("Orga Project", project):
        frappe.throw(_("Project {0} not found").format(project))

    if not frappe.db.exists(doctype, item_id):
        frappe.throw(_("Item {0} not found").format(item_id))

    # Check if sort_order columns exist
    if not _has_sort_order("Orga Task") or not _has_sort_order("Orga Milestone"):
        return {"success": False, "reason": "migration_required"}

    # Ensure all items have initial sort_order values
    _initialize_sort_orders(project)

    # Calculate new sort_order based on neighbours
    prev_sort = None
    next_sort = None

    if prev_item_id and prev_item_type:
        prev_doctype = _doctype_for(prev_item_type)
        if frappe.db.exists(prev_doctype, prev_item_id):
            prev_sort = _get_sort_order(prev_doctype, prev_item_id)

    if next_item_id and next_item_type:
        next_doctype = _doctype_for(next_item_type)
        if frappe.db.exists(next_doctype, next_item_id):
            next_sort = _get_sort_order(next_doctype, next_item_id)

    # Calculate the new sort_order value
    if prev_sort is not None and next_sort is not None:
        # Between two items: average
        new_sort_order = (prev_sort + next_sort) / 2.0
    elif prev_sort is not None:
        # After last item: add gap
        new_sort_order = prev_sort + _INITIAL_GAP
    elif next_sort is not None:
        # Before first item: half of first item's value
        new_sort_order = next_sort / 2.0
    else:
        # Only item (shouldn't happen, but safe fallback)
        new_sort_order = _INITIAL_GAP

    # Check if we're running out of precision
    if prev_sort is not None and next_sort is not None:
        gap = abs(next_sort - prev_sort)
        if gap < _MIN_GAP:
            # Renumber everything, then recalculate
            _renumber_all(project)
            # Re-fetch neighbours after renumbering
            if prev_item_id and prev_item_type:
                prev_sort = _get_sort_order(_doctype_for(prev_item_type), prev_item_id)
            if next_item_id and next_item_type:
                next_sort = _get_sort_order(_doctype_for(next_item_type), next_item_id)

            if prev_sort is not None and next_sort is not None:
                new_sort_order = (prev_sort + next_sort) / 2.0
            elif prev_sort is not None:
                new_sort_order = prev_sort + _INITIAL_GAP
            elif next_sort is not None:
                new_sort_order = next_sort / 2.0
            else:
                new_sort_order = _INITIAL_GAP

    # Single DB update
    frappe.db.set_value(
        doctype, item_id, "sort_order", new_sort_order,
        update_modified=False
    )
    frappe.db.commit()

    return {
        "success": True,
        "sort_order": new_sort_order,
        "item_id": item_id
    }
