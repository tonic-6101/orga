# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
One-time migration: link existing Orga Resources to Frappe Contacts.

For each Orga Resource that has a ``user`` but no ``contact``:
  1. Find an existing Contact whose email matches the user's email.
  2. If no match, create a new Contact with the resource's identity data.
  3. Set ``dock_shared = 1`` so team members are visible in Dock People.
  4. Link the Contact back to the resource.

After this patch, the identity fields (email, phone, etc.) on Orga Resource
are no longer authoritative — the linked Contact is the source of truth.
"""

import frappe


def execute():
    # Only run if Orga Resource has the new `contact` field
    if not frappe.db.has_column("Orga Resource", "contact"):
        return

    resources = frappe.get_all(
        "Orga Resource",
        filters={"contact": ["is", "not set"]},
        fields=["name", "resource_name", "user", "employee",
                "email", "phone", "mobile_no", "designation",
                "company", "address", "image"],
    )

    if not resources:
        return

    has_dock_shared = frappe.db.exists(
        "Custom Field", {"dt": "Contact", "fieldname": "dock_shared"}
    )

    for res in resources:
        contact_name = _find_or_create_contact(res, has_dock_shared)
        if contact_name:
            frappe.db.set_value(
                "Orga Resource", res.name, "contact", contact_name,
                update_modified=False,
            )

    frappe.db.commit()


def _find_or_create_contact(res: dict, has_dock_shared: bool) -> str | None:
    """Find an existing Contact by email, or create a new one."""
    email = res.get("email") or ""
    if not email and res.get("user"):
        email = frappe.db.get_value("User", res["user"], "email") or ""

    # Try to find by email
    if email:
        existing = frappe.db.get_value(
            "Contact Email",
            {"email_id": email, "parenttype": "Contact"},
            "parent",
        )
        if existing:
            if has_dock_shared:
                frappe.db.set_value(
                    "Contact", existing, "dock_shared", 1,
                    update_modified=False,
                )
            return existing

    # No match — create new Contact
    name_parts = (res.get("resource_name") or "").split(None, 1)
    first_name = name_parts[0] if name_parts else "Unknown"
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": first_name,
        "last_name": last_name,
        "designation": res.get("designation") or "",
        "company_name": res.get("company") or "",
        "image": res.get("image") or "",
    })

    if email:
        contact.append("email_ids", {"email_id": email, "is_primary": 1})
    if res.get("phone"):
        contact.append("phone_nos", {"phone": res["phone"], "is_primary_phone": 1})
    if res.get("mobile_no"):
        contact.append("phone_nos", {"phone": res["mobile_no"], "is_primary_mobile_no": 1})

    if has_dock_shared:
        contact.dock_shared = 1

    try:
        contact.insert(ignore_permissions=True)
        return contact.name
    except Exception:
        frappe.log_error(
            f"Failed to create Contact for Orga Resource {res['name']}"
        )
        return None
