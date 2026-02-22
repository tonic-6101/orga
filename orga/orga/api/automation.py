# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Automation API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.automation.get_rules'
    })
"""

import json
import frappe
from frappe import _


_ALLOWED_ROLES = ("System Manager", "Orga Manager")


def _check_automation_permission():
    """Ensure user has permission to manage automation rules."""
    roles = frappe.get_roles()
    if not any(role in roles for role in _ALLOWED_ROLES):
        frappe.throw(_("Not permitted to manage automation rules"), frappe.PermissionError)


@frappe.whitelist()
def get_rules(applies_to=None, is_active=None, limit=50, offset=0):
    """
    Get all automation rules with optional filters.

    Args:
        applies_to: Filter by DocType
        is_active: Filter by active status
        limit: Maximum results
        offset: Pagination offset

    Returns:
        dict: {rules: [...], total: int}
    """
    filters = {}
    if applies_to:
        filters["applies_to"] = applies_to
    if is_active is not None:
        filters["is_active"] = int(is_active)

    rules = frappe.get_all(
        "Orga Automation Rule",
        filters=filters,
        fields=[
            "name", "rule_name", "description", "applies_to",
            "trigger_event", "is_active", "last_run", "run_count", "modified"
        ],
        order_by="modified desc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    # Add condition and action counts
    for rule in rules:
        rule["condition_count"] = frappe.db.count(
            "Orga Rule Condition",
            {"parent": rule.name}
        )
        rule["action_count"] = frappe.db.count(
            "Orga Rule Action",
            {"parent": rule.name}
        )

    total = frappe.db.count("Orga Automation Rule", filters)

    return {
        "rules": rules,
        "total": total
    }


@frappe.whitelist()
def get_rule(name):
    """
    Get a single automation rule with all details.

    Args:
        name: Rule name

    Returns:
        dict: Full rule document
    """
    if not frappe.db.exists("Orga Automation Rule", name):
        frappe.throw(_("Automation rule {0} not found").format(name))

    rule = frappe.get_doc("Orga Automation Rule", name)
    return rule.as_dict()


@frappe.whitelist()
def create_rule(rule_name, applies_to, trigger_event, actions, conditions=None, description=None):
    """
    Create a new automation rule.

    Args:
        rule_name: Unique rule name
        applies_to: DocType to apply rule to
        trigger_event: When to trigger (On Create, On Update, etc.)
        actions: List of action dicts
        conditions: Optional list of condition dicts
        description: Optional description

    Returns:
        dict: {name: rule_name}
    """
    _check_automation_permission()

    if isinstance(actions, str):
        actions = json.loads(actions)
    if isinstance(conditions, str):
        conditions = json.loads(conditions) if conditions else []

    rule = frappe.get_doc({
        "doctype": "Orga Automation Rule",
        "rule_name": rule_name,
        "applies_to": applies_to,
        "trigger_event": trigger_event,
        "description": description,
        "conditions": conditions or [],
        "actions": actions
    })
    rule.insert()

    return {"name": rule.name}


@frappe.whitelist()
def update_rule(name, data):
    """
    Update an existing automation rule.

    Args:
        name: Rule name
        data: Fields to update

    Returns:
        dict: {name, modified}
    """
    _check_automation_permission()

    if not frappe.db.exists("Orga Automation Rule", name):
        frappe.throw(_("Automation rule {0} not found").format(name))

    if isinstance(data, str):
        data = json.loads(data)

    rule = frappe.get_doc("Orga Automation Rule", name)

    # Update simple fields
    for field in ["rule_name", "description", "applies_to", "trigger_event", "is_active", "schedule_type"]:
        if field in data:
            rule.set(field, data[field])

    # Update child tables if provided
    if "conditions" in data:
        rule.conditions = []
        for cond in data["conditions"]:
            rule.append("conditions", cond)

    if "actions" in data:
        rule.actions = []
        for action in data["actions"]:
            rule.append("actions", action)

    rule.save()

    return {"name": rule.name, "modified": str(rule.modified)}


@frappe.whitelist()
def delete_rule(name):
    """
    Delete an automation rule.

    Args:
        name: Rule name

    Returns:
        dict: {success: True}
    """
    _check_automation_permission()

    if not frappe.db.exists("Orga Automation Rule", name):
        frappe.throw(_("Automation rule {0} not found").format(name))

    frappe.delete_doc("Orga Automation Rule", name)

    return {"success": True}


@frappe.whitelist()
def activate_rule(name):
    """
    Activate an automation rule.

    Args:
        name: Rule name

    Returns:
        dict: Updated rule
    """
    _check_automation_permission()

    if not frappe.db.exists("Orga Automation Rule", name):
        frappe.throw(_("Automation rule {0} not found").format(name))

    rule = frappe.get_doc("Orga Automation Rule", name)
    rule.is_active = 1
    rule.save()

    return rule.as_dict()


@frappe.whitelist()
def deactivate_rule(name):
    """
    Deactivate an automation rule.

    Args:
        name: Rule name

    Returns:
        dict: Updated rule
    """
    _check_automation_permission()

    if not frappe.db.exists("Orga Automation Rule", name):
        frappe.throw(_("Automation rule {0} not found").format(name))

    rule = frappe.get_doc("Orga Automation Rule", name)
    rule.is_active = 0
    rule.save()

    return rule.as_dict()


@frappe.whitelist()
def test_rule(name, doc_name=None):
    """
    Test an automation rule without executing actions.

    Args:
        name: Rule name
        doc_name: Optional specific document to test

    Returns:
        dict: Test results
    """
    from orga.orga.automation.engine import test_rule as _test_rule

    return _test_rule(name, doc_name)


@frappe.whitelist()
def get_field_options(doctype):
    """
    Get available fields for a DocType (for condition/action configuration).

    Args:
        doctype: DocType name

    Returns:
        list: Field options with name and label
    """
    if doctype not in ("Orga Task", "Orga Project", "Orga Assignment"):
        frappe.throw(_("Invalid DocType"))

    meta = frappe.get_meta(doctype)

    fields = []
    for field in meta.fields:
        if field.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML"):
            fields.append({
                "fieldname": field.fieldname,
                "label": field.label,
                "fieldtype": field.fieldtype,
                "options": field.options
            })

    return fields
