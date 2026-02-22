# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe

def execute():
    """Set Orga workspace icon to 'project'"""
    if frappe.db.exists("Workspace", "Orga"):
        frappe.db.set_value("Workspace", "Orga", "icon", "project")
