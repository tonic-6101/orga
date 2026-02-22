# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe


def setup_roles():
    """Create Orga roles if they don't exist"""
    roles = [
        {
            "role_name": "Orga Manager",
            "desk_access": 1,
            "is_custom": 1
        },
        {
            "role_name": "Orga User",
            "desk_access": 1,
            "is_custom": 1
        },
        {
            "role_name": "Orga Client",
            "desk_access": 0,  # Clients access portal, not Desk
            "is_custom": 1
        }
    ]

    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.get_doc({
                "doctype": "Role",
                **role_data
            })
            role.insert(ignore_permissions=True)
            print(f"Created Role: {role_data['role_name']}")
        else:
            print(f"Role {role_data['role_name']} already exists")

    frappe.db.commit()


def setup_orga():
    """Setup Orga module, pages, and workspace"""

    # Create Module Def if not exists
    if not frappe.db.exists("Module Def", "Orga"):
        module_def = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Orga",
            "app_name": "orga"
        })
        module_def.insert(ignore_permissions=True)
        print("Created Module Def: Orga")
    else:
        print("Module Def Orga already exists")

    # Create Page if not exists
    if not frappe.db.exists("Page", "orga"):
        page = frappe.get_doc({
            "doctype": "Page",
            "name": "orga",
            "page_name": "orga",
            "title": "Orga",
            "module": "Orga",
            "standard": "Yes",
            "roles": [{"role": "System Manager"}]
        })
        page.insert(ignore_permissions=True)
        print("Created Page: orga")
    else:
        print("Page orga already exists")

    # Create or update Workspace
    # Note: DocType links will be added after DocTypes are created in Phase 1
    if not frappe.db.exists("Workspace", "Orga"):
        workspace = frappe.get_doc({
            "doctype": "Workspace",
            "name": "Orga",
            "label": "Orga",
            "title": "Orga",
            "module": "Orga",
            "icon": "project",
            "public": 1,
            "sequence_id": 1,
            "links": [
                {
                    "label": "Dashboard",
                    "link_to": "orga",
                    "link_type": "Page",
                    "onboard": 1,
                    "type": "Link"
                }
            ],
            "shortcuts": [
                {
                    "color": "Grey",
                    "label": "Dashboard",
                    "link_to": "orga",
                    "type": "Page"
                }
            ]
        })
        workspace.insert(ignore_permissions=True)
        print("Created Workspace: Orga")
    else:
        # Update existing workspace to ensure icon is set
        workspace = frappe.get_doc("Workspace", "Orga")
        if workspace.icon != "project":
            workspace.icon = "project"
            workspace.save(ignore_permissions=True)
            print("Updated Workspace icon: project")
        else:
            print("Workspace Orga already exists with correct icon")

    frappe.db.commit()
    print("Setup complete!")


def add_doctype_links():
    """
    Call this after creating DocTypes in Phase 1 to add them to the workspace.
    Run: bench --site [site] execute orga.install.add_doctype_links
    """
    ws = frappe.get_doc("Workspace", "Orga")

    doctype_links = [
        {"label": "Projects", "link_to": "Orga Project", "link_type": "DocType", "onboard": 1},
        {"label": "Tasks", "link_to": "Orga Task", "link_type": "DocType", "onboard": 1},
        {"label": "Milestones", "link_to": "Orga Milestone", "link_type": "DocType"},
        {"label": "Resources", "link_to": "Orga Resource", "link_type": "DocType"},
        {"label": "Assignments", "link_to": "Orga Assignment", "link_type": "DocType"},
        {"label": "Appointments", "link_to": "Orga Appointment", "link_type": "DocType"},

        {"label": "Clients", "link_to": "Orga Client", "link_type": "DocType"},
        {"label": "Settings", "link_to": "Orga Settings", "link_type": "DocType"},
    ]

    for link in doctype_links:
        # Only add if DocType exists
        if frappe.db.exists("DocType", link["link_to"]):
            ws.append("links", {
                "label": link["label"],
                "link_to": link["link_to"],
                "link_type": link["link_type"],
                "onboard": link.get("onboard", 0),
                "type": "Link"
            })
            print(f"Added link: {link['label']}")
        else:
            print(f"Skipped (DocType not found): {link['label']}")

    ws.save()
    frappe.db.commit()
    print("Workspace links updated!")


def update_workspace_icon():
    """
    Update Orga workspace icon to 'project'.
    Run: bench --site [site] execute orga.install.update_workspace_icon
    """
    if frappe.db.exists("Workspace", "Orga"):
        frappe.db.set_value("Workspace", "Orga", "icon", "project")
        frappe.db.commit()
        print("Updated Workspace icon to: project")
    else:
        print("Workspace Orga not found")


def after_install():
    """Called after app installation"""
    setup_roles()
    setup_orga()
