# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Client API Module

Provides API endpoints for managing Orga Clients and portal access.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_clients(
    status: str = None,
    company: str = None,
    portal_enabled: int = None,
    limit: int = 100,
    offset: int = 0
) -> dict:
    """
    Get list of clients with optional filtering.

    Args:
        status: Filter by status (Active, Inactive, Pending)
        company: Filter by company name
        portal_enabled: Filter by portal access (0 or 1)
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        dict: {clients: list, total: int}
    """
    filters = {}
    if status:
        filters["status"] = status
    if company:
        filters["company"] = ["like", f"%{company}%"]
    if portal_enabled is not None:
        filters["portal_enabled"] = portal_enabled

    total = frappe.db.count("Orga Client", filters=filters)

    clients = frappe.get_all(
        "Orga Client",
        filters=filters,
        fields=[
            "name", "client_name", "company", "email", "phone",
            "status", "portal_enabled", "user", "project_count",
            "last_login", "creation"
        ],
        order_by="client_name asc",
        start=offset,
        limit_page_length=limit
    )

    return {
        "clients": clients,
        "total": total
    }


@frappe.whitelist()
def get_client(client_id: str) -> dict:
    """
    Get single client details.

    Args:
        client_id: Client document name (e.g., CLT-00001)

    Returns:
        dict: Client document with additional computed fields
    """
    if not frappe.has_permission("Orga Client", "read", client_id):
        frappe.throw(_("Not permitted to view this client"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)

    result = client.as_dict()
    result["projects"] = client.get_linked_projects()
    result["milestones"] = client.get_linked_milestones()

    return result


@frappe.whitelist()
def create_client(
    client_name: str,
    email: str,
    company: str = None,
    phone: str = None,
    status: str = "Pending",
    portal_enabled: int = 0,
    address_line1: str = None,
    address_line2: str = None,
    city: str = None,
    state: str = None,
    country: str = None,
    notes: str = None
) -> dict:
    """
    Create a new client.

    Args:
        client_name: Client's full name
        email: Client's email address (must be unique)
        company: Company name (optional)
        phone: Phone number (optional)
        status: Initial status (default: Pending)
        portal_enabled: Enable portal access (default: 0)
        address_line1: Address line 1 (optional)
        address_line2: Address line 2 (optional)
        city: City (optional)
        state: State/Province (optional)
        country: Country (optional)
        notes: Additional notes (optional)

    Returns:
        dict: Created client document
    """
    if not frappe.has_permission("Orga Client", "create"):
        frappe.throw(_("Not permitted to create clients"), frappe.PermissionError)

    client = frappe.get_doc({
        "doctype": "Orga Client",
        "client_name": client_name,
        "email": email,
        "company": company,
        "phone": phone,
        "status": status,
        "portal_enabled": portal_enabled,
        "address_line1": address_line1,
        "address_line2": address_line2,
        "city": city,
        "state": state,
        "country": country,
        "notes": notes
    })
    client.insert()

    return client.as_dict()


@frappe.whitelist()
def update_client(client_id: str, **kwargs) -> dict:
    """
    Update an existing client.

    Args:
        client_id: Client document name
        **kwargs: Fields to update

    Returns:
        dict: Updated client document
    """
    if not frappe.has_permission("Orga Client", "write", client_id):
        frappe.throw(_("Not permitted to update this client"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)

    allowed_fields = [
        "client_name", "company", "email", "phone", "status",
        "portal_enabled", "address_line1", "address_line2",
        "city", "state", "country", "notes"
    ]

    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(client, field, value)

    client.save()

    return client.as_dict()


@frappe.whitelist()
def delete_client(client_id: str) -> dict:
    """
    Delete a client.

    Args:
        client_id: Client document name

    Returns:
        dict: {success: True, message: str}
    """
    if not frappe.has_permission("Orga Client", "delete", client_id):
        frappe.throw(_("Not permitted to delete this client"), frappe.PermissionError)

    # Check for linked projects
    linked_projects = frappe.db.count("Orga Project", {"client": client_id})
    if linked_projects:
        frappe.throw(
            _("Cannot delete client with {0} linked projects. Unlink projects first.").format(linked_projects)
        )

    frappe.delete_doc("Orga Client", client_id)

    return {
        "success": True,
        "message": _("Client {0} deleted successfully").format(client_id)
    }


@frappe.whitelist()
def get_client_projects(client_id: str) -> list:
    """
    Get all projects linked to a client.

    Args:
        client_id: Client document name

    Returns:
        list: List of project documents
    """
    if not frappe.has_permission("Orga Client", "read", client_id):
        frappe.throw(_("Not permitted to view this client"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)
    return client.get_linked_projects()


@frappe.whitelist()
def invite_client(client_id: str, send_email: int = 1) -> dict:
    """
    Invite a client to the portal by creating their user account.

    Args:
        client_id: Client document name
        send_email: Whether to send welcome email (default: 1)

    Returns:
        dict: {success: True, user: str, message: str}
    """
    if not frappe.has_permission("Orga Client", "write", client_id):
        frappe.throw(_("Not permitted to invite clients"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)

    if client.user:
        return {
            "success": True,
            "user": client.user,
            "message": _("Client already has portal access")
        }

    user_name = client.create_portal_user(send_welcome_email=bool(send_email))

    return {
        "success": True,
        "user": user_name,
        "message": _("Portal user created successfully. Welcome email {0}").format(
            _("sent") if send_email else _("not sent")
        )
    }


@frappe.whitelist()
def revoke_portal_access(client_id: str) -> dict:
    """
    Revoke a client's portal access by disabling their user account.

    Args:
        client_id: Client document name

    Returns:
        dict: {success: True, message: str}
    """
    if not frappe.has_permission("Orga Client", "write", client_id):
        frappe.throw(_("Not permitted to modify client access"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)

    if not client.user:
        return {
            "success": True,
            "message": _("Client has no portal user to revoke")
        }

    # Disable portal access flag
    client.portal_enabled = 0
    client.save()

    # Optionally disable the user account
    user = frappe.get_doc("User", client.user)
    user.enabled = 0
    user.save(ignore_permissions=True)

    return {
        "success": True,
        "message": _("Portal access revoked for {0}").format(client.client_name)
    }


@frappe.whitelist()
def get_client_milestones(client_id: str, project: str = None) -> list:
    """
    Get milestones for a client's projects.

    Args:
        client_id: Client document name
        project: Optional project filter

    Returns:
        list: List of milestone documents
    """
    if not frappe.has_permission("Orga Client", "read", client_id):
        frappe.throw(_("Not permitted to view this client"), frappe.PermissionError)

    client = frappe.get_doc("Orga Client", client_id)
    return client.get_linked_milestones(project=project)


@frappe.whitelist()
def link_project_to_client(project_id: str, client_id: str) -> dict:
    """
    Link an existing project to a client.

    Args:
        project_id: Project document name
        client_id: Client document name

    Returns:
        dict: {success: True, message: str}
    """
    if not frappe.has_permission("Orga Project", "write", project_id):
        frappe.throw(_("Not permitted to modify this project"), frappe.PermissionError)

    project = frappe.get_doc("Orga Project", project_id)
    project.client = client_id
    project.save()

    # Update client's project count
    client = frappe.get_doc("Orga Client", client_id)
    client.update_project_count()
    client.save()

    return {
        "success": True,
        "message": _("Project {0} linked to client {1}").format(project_id, client_id)
    }


@frappe.whitelist()
def unlink_project_from_client(project_id: str) -> dict:
    """
    Remove client link from a project.

    Args:
        project_id: Project document name

    Returns:
        dict: {success: True, message: str}
    """
    if not frappe.has_permission("Orga Project", "write", project_id):
        frappe.throw(_("Not permitted to modify this project"), frappe.PermissionError)

    project = frappe.get_doc("Orga Project", project_id)
    old_client = project.client

    if not old_client:
        return {
            "success": True,
            "message": _("Project has no linked client")
        }

    project.client = None
    project.save()

    # Update old client's project count
    if old_client:
        client = frappe.get_doc("Orga Client", old_client)
        client.update_project_count()
        client.save()

    return {
        "success": True,
        "message": _("Client link removed from project {0}").format(project_id)
    }
