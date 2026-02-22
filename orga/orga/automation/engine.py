# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Automation rule execution engine.

This module handles executing automation rules when documents are created,
updated, or when specific events occur.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


class AutomationEngine:
    """Execute automation rules for documents."""

    def __init__(self, doc, event):
        """
        Initialize the automation engine.

        Args:
            doc: Frappe document that triggered the event
            event: Event type (e.g., 'after_insert', 'on_update')
        """
        self.doc = doc
        self.event = event
        self.doctype = doc.doctype

    def execute(self):
        """Find and execute all matching rules."""
        rules = self._get_applicable_rules()

        executed_count = 0
        for rule_name in rules:
            try:
                rule = frappe.get_doc("Orga Automation Rule", rule_name)
                if rule.execute(self.doc):
                    executed_count += 1
            except Exception as e:
                frappe.log_error(
                    title=f"Automation Rule Error: {rule_name}",
                    message=f"Error executing rule on {self.doctype} {self.doc.name}: {str(e)}"
                )

        return executed_count

    def _get_applicable_rules(self):
        """Get active rules that match this document and event."""
        event_map = {
            "before_insert": "On Create",
            "after_insert": "On Create",
            "on_update": "On Update",
            "validate": "On Update"
        }

        trigger = event_map.get(self.event)
        if not trigger:
            return []

        return frappe.get_all(
            "Orga Automation Rule",
            filters={
                "applies_to": self.doctype,
                "trigger_event": trigger,
                "is_active": 1
            },
            pluck="name"
        )


def run_automation(doc, event):
    """
    Entry point for document hooks.

    This function is called from hooks.py for document events.

    Args:
        doc: Frappe document
        event: Event type
    """
    # Only run for supported doctypes
    supported_doctypes = ["Orga Task", "Orga Project", "Orga Assignment"]
    if doc.doctype not in supported_doctypes:
        return

    try:
        engine = AutomationEngine(doc, event)
        engine.execute()
    except Exception as e:
        # Log error but don't break document save
        frappe.log_error(
            title=f"Automation Engine Error",
            message=f"Error running automation on {doc.doctype} {doc.name}: {str(e)}"
        )


def run_scheduled_automations():
    """
    Execute scheduled automation rules.

    Called by the scheduler for rules with trigger_event='Scheduled'.
    """
    from frappe.utils import add_days, today, getdate

    # Get all active scheduled rules
    rules = frappe.get_all(
        "Orga Automation Rule",
        filters={
            "is_active": 1,
            "trigger_event": "Scheduled"
        },
        fields=["name", "applies_to", "schedule_type", "last_run"]
    )

    for rule_data in rules:
        # Check if rule should run based on schedule
        if not _should_run_scheduled(rule_data):
            continue

        # Get documents of the applicable type (bounded to prevent runaway queries)
        try:
            rule = frappe.get_doc("Orga Automation Rule", rule_data.name)

            # Only allow automation on supported Orga doctypes
            allowed_doctypes = ["Orga Task", "Orga Project", "Orga Assignment"]
            if rule.applies_to not in allowed_doctypes:
                frappe.log_error(
                    title=f"Scheduled Automation Skipped: {rule_data.name}",
                    message=f"DocType '{rule.applies_to}' is not allowed for scheduled automation"
                )
                continue

            docs = frappe.get_all(rule.applies_to, pluck="name", limit=1000)

            for doc_name in docs:
                doc = frappe.get_doc(rule.applies_to, doc_name)
                rule.execute(doc)
                doc.save()

        except Exception as e:
            frappe.log_error(
                title=f"Scheduled Automation Error: {rule_data.name}",
                message=str(e)
            )

    frappe.db.commit()


def _should_run_scheduled(rule_data):
    """Check if a scheduled rule should run based on its schedule type."""
    from frappe.utils import now_datetime, get_datetime

    if not rule_data.last_run:
        return True

    last_run = get_datetime(rule_data.last_run)
    now = now_datetime()

    if rule_data.schedule_type == "Daily":
        return (now - last_run).days >= 1

    elif rule_data.schedule_type == "Weekly":
        return (now - last_run).days >= 7

    elif rule_data.schedule_type == "Monthly":
        return (now - last_run).days >= 30

    return False


def test_rule(rule_name, doc_name=None):
    """
    Test an automation rule without saving changes.

    Args:
        rule_name: Name of the rule to test
        doc_name: Optional specific document to test on

    Returns:
        dict: Test results
    """
    rule = frappe.get_doc("Orga Automation Rule", rule_name)

    if doc_name:
        docs = [frappe.get_doc(rule.applies_to, doc_name)]
    else:
        # Test on first 5 documents
        doc_names = frappe.get_all(rule.applies_to, limit=5, pluck="name")
        docs = [frappe.get_doc(rule.applies_to, name) for name in doc_names]

    results = []
    for doc in docs:
        # Check conditions without executing
        conditions_met = rule._check_conditions(doc)
        results.append({
            "document": doc.name,
            "conditions_met": conditions_met,
            "would_execute": conditions_met and rule.is_active
        })

    return {
        "rule_name": rule_name,
        "is_active": rule.is_active,
        "applies_to": rule.applies_to,
        "trigger_event": rule.trigger_event,
        "conditions": len(rule.conditions or []),
        "actions": len(rule.actions),
        "test_results": results
    }
