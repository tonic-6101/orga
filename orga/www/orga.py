# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.translate import get_messages_for_boot

no_cache = 1


def get_context():
    # Guest portal routes (/orga/guest/*) are public — loaded inside Dock guest portal iframe.
    # All other /orga/* routes require a logged-in user.
    path = frappe.request.path if frappe.request else ""
    is_guest_route = frappe.session.user == "Guest" and "/guest/" in path

    if frappe.session.user == "Guest" and not is_guest_route:
        frappe.throw(_("Please login to access Orga"), frappe.PermissionError)

    context = frappe._dict()
    context.site_name = frappe.local.site
    context.title = "Orga"
    context.description = "Project Management System"

    if is_guest_route:
        # Minimal boot — no user data, no CSRF needed (guest API uses allow_guest=True)
        context.boot = frappe._dict({
            "is_guest": True,
            "site_name": frappe.local.site,
        })
        context.csrf_token = ""
    else:
        csrf_token = frappe.sessions.get_csrf_token()
        frappe.db.commit()
        context.boot = get_boot()
        context.boot.csrf_token = csrf_token
        context.csrf_token = csrf_token

    return context


@frappe.whitelist(methods=["POST"])
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw(_("This method is only meant for developer mode"))
    return get_boot()


def _get_dock_boot():
    """Return dock boot info if dock is installed, else None."""
    if "dock" not in frappe.get_installed_apps():
        return None
    try:
        from dock.boot import get_boot as dock_get_boot
        return dock_get_boot()
    except Exception:
        return {"installed": True}


def get_boot():
    """Build boot data for Vue SPA including user session info."""
    user = frappe.session.user
    user_info = frappe.get_doc("User", user)

    return frappe._dict(
        {
            "frappe": {
                "boot": {
                    "user": {
                        "name": user,
                        "email": user_info.email or "",
                        "full_name": user_info.full_name or user,
                        "user_image": user_info.user_image or "",
                    },
                    "user_roles": frappe.get_roles(user),
                    "dock": _get_dock_boot(),
                },
                "csrf_token": frappe.sessions.get_csrf_token(),
            },
            "frappe_version": frappe.__version__,
            "default_route": "/orga",
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "lang": frappe.local.lang,
            "__messages": get_messages_for_boot(),
        }
    )
