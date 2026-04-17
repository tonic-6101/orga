# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Backfill Orga Assignment.contact from assignment.resource.contact.

Feature: task-assignment (Owner + Collaborators).

Before this patch, Orga Assignment was keyed solely by Orga Resource. With the
move to Contact-as-identity, every row needs a `contact` pointer. We copy it
from the resource's linked Contact where possible. Rows whose Resource has no
Contact are logged and left with contact = NULL for manual resolution — the
caller of set_assignees enforces required-ness going forward.
"""

import frappe


def execute():
    if not frappe.db.has_column("Orga Assignment", "contact"):
        return

    rows = frappe.db.sql(
        """
        SELECT a.name AS assignment, a.resource, r.contact
        FROM `tabOrga Assignment` a
        LEFT JOIN `tabOrga Resource` r ON r.name = a.resource
        WHERE (a.contact IS NULL OR a.contact = '')
          AND a.resource IS NOT NULL
        """,
        as_dict=True,
    )

    filled, orphaned = 0, []
    for row in rows:
        if row.contact:
            frappe.db.set_value(
                "Orga Assignment", row.assignment, "contact", row.contact,
                update_modified=False,
            )
            filled += 1
        else:
            orphaned.append(row.assignment)

    if orphaned:
        frappe.log_error(
            title="backfill_assignment_contact: orphaned rows",
            message=(
                "Orga Assignment rows whose Resource has no linked Contact "
                "(contact left NULL, resolve manually):\n"
                + "\n".join(orphaned)
            ),
        )

    frappe.db.commit()
    print(f"[orga] backfill_assignment_contact: filled={filled} orphaned={len(orphaned)}")
