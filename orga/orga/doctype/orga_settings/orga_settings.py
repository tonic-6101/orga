# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OrgaSettings(Document):
    pass


def get_settings():
    """
    Get Orga Settings as a dict.
    Creates default settings if they don't exist.
    """
    if not frappe.db.exists("Orga Settings", "Orga Settings"):
        # Create default settings
        doc = frappe.new_doc("Orga Settings")
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

    return frappe.get_single("Orga Settings").as_dict()


def get_setting(field, default=None):
    """
    Get a single setting value.

    Args:
        field: The setting field name
        default: Default value if field not found

    Returns:
        The setting value or default
    """
    settings = get_settings()
    return settings.get(field, default)
