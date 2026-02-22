# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
User API Module

Provides meta-driven endpoints for querying users based on DocType field definitions.
Used for Link fields that point to User (e.g., Orga Task.assigned_to).
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_assignable_users(
    doctype: str = "Orga Task",
    fieldname: str = "assigned_to",
    search: str = "",
    limit: int = 50,
) -> list:
    """
    Get users for a Link field, driven by the field's metadata.

    Reads the field definition from the DocType to determine the target DocType,
    then queries it with appropriate filters.

    Args:
        doctype: The source DocType containing the Link field
        fieldname: The fieldname of the Link field
        search: Optional search string (searches name and full_name)
        limit: Max results (default 50)

    Returns:
        list: Users with name, full_name, user_image
    """
    limit = min(int(limit), 200)

    # Meta-driven: read field definition to get target DocType
    meta = frappe.get_meta(doctype)
    field = meta.get_field(fieldname)

    if not field:
        frappe.throw(_("Field {0} not found in {1}").format(fieldname, doctype))

    if field.fieldtype != "Link":
        frappe.throw(_("Field {0} is not a Link field").format(fieldname))

    target_doctype = field.options

    if target_doctype != "User":
        return frappe.get_all(
            target_doctype,
            fields=["name"],
            limit_page_length=limit,
            order_by="name",
        )

    # User-specific query: enabled users, excluding Guest
    # Include both System Users and Website Users linked to Orga Resources
    filters = {"enabled": 1, "name": ["not in", ["Guest"]]}
    or_filters = None

    if search:
        or_filters = [
            ["full_name", "like", f"%{search}%"],
            ["name", "like", f"%{search}%"],
        ]

    users = frappe.get_all(
        "User",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "full_name", "user_image"],
        order_by="full_name",
        limit_page_length=limit,
    )

    # Also include Orga Resources that have no linked User account
    # These are team members managed only as resources
    resource_filters = {"user": ["is", "not set"], "status": "Active"}
    if search:
        resource_filters["resource_name"] = ["like", f"%{search}%"]

    unlinked_resources = frappe.get_all(
        "Orga Resource",
        filters=resource_filters,
        fields=["name", "resource_name", "email"],
        order_by="resource_name",
        limit_page_length=limit,
    )

    # Map unlinked resources to the same shape: use email as name (for assigned_to Link field)
    for res in unlinked_resources:
        if res.email:
            users.append({
                "name": res.email,
                "full_name": res.resource_name,
                "user_image": None,
            })

    return users
