# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Orga Automation Rule DocType controller.

Manages automation rules that trigger on document events.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class OrgaAutomationRule(Document):
    def validate(self):
        self.validate_actions()
        self.validate_schedule()

    def validate_actions(self):
        """Ensure at least one action is defined."""
        if not self.actions:
            frappe.throw(_("At least one action is required"))

        for action in self.actions:
            if action.action_type == "Set Field Value" and not action.field_name:
                frappe.throw(_("Field name is required for 'Set Field Value' action"))

            if action.action_type == "Set Field Value" and action.field_name in self._BLOCKED_FIELDS:
                frappe.throw(
                    _("Cannot set system field '{0}' via automation rule").format(action.field_name)
                )

            if action.action_type in ("Assign To", "Send Notification") and not action.target_user:
                frappe.throw(_("Target user is required for '{0}' action").format(action.action_type))

            if action.action_type in ("Send Notification", "Add Comment") and not action.message:
                frappe.throw(_("Message is required for '{0}' action").format(action.action_type))

    def validate_schedule(self):
        """Validate schedule settings."""
        if self.trigger_event == "Scheduled" and not self.schedule_type:
            frappe.throw(_("Schedule type is required for scheduled triggers"))

    def execute(self, doc):
        """
        Execute this rule for a document.

        Args:
            doc: Document to execute rule on

        Returns:
            bool: True if rule was executed, False if conditions not met
        """
        if not self.is_active:
            return False

        # Check all conditions
        if not self._check_conditions(doc):
            return False

        # Execute all actions
        self._execute_actions(doc)

        # Update run tracking
        self.last_run = now_datetime()
        self.run_count = (self.run_count or 0) + 1
        self.db_update()

        return True

    def _check_conditions(self, doc):
        """Check if all conditions are met."""
        for condition in self.conditions or []:
            if not self._evaluate_condition(doc, condition):
                return False
        return True

    def _evaluate_condition(self, doc, condition):
        """Evaluate a single condition."""
        field_value = doc.get(condition.field_name)
        target_value = condition.value
        operator = condition.operator

        if operator == "equals":
            return str(field_value or "") == str(target_value or "")
        elif operator == "not equals":
            return str(field_value or "") != str(target_value or "")
        elif operator == "greater than":
            try:
                return float(field_value or 0) > float(target_value or 0)
            except (ValueError, TypeError):
                return False
        elif operator == "less than":
            try:
                return float(field_value or 0) < float(target_value or 0)
            except (ValueError, TypeError):
                return False
        elif operator == "contains":
            return str(target_value or "") in str(field_value or "")
        elif operator == "not contains":
            return str(target_value or "") not in str(field_value or "")
        elif operator == "is set":
            return bool(field_value)
        elif operator == "is not set":
            return not bool(field_value)

        return False

    def _execute_actions(self, doc):
        """Execute all actions for this rule."""
        for action in self.actions:
            self._execute_action(doc, action)

    # Fields that automation rules are NOT allowed to modify
    _BLOCKED_FIELDS = frozenset({
        "owner", "creation", "modified", "modified_by",
        "docstatus", "doctype", "name", "idx", "parent",
        "parenttype", "parentfield", "_user_tags", "_comments",
        "_assign", "_liked_by"
    })

    def _execute_action(self, doc, action):
        """Execute a single action."""
        if action.action_type == "Set Field Value":
            field_name = action.field_name
            # Block modification of system/internal fields
            if field_name in self._BLOCKED_FIELDS:
                frappe.log_error(
                    title=f"Automation Rule Blocked: {self.name}",
                    message=f"Cannot set blocked field '{field_name}' on {doc.doctype} {doc.name}"
                )
                return
            # Verify field exists on the DocType
            if not doc.meta.has_field(field_name):
                frappe.log_error(
                    title=f"Automation Rule Error: {self.name}",
                    message=f"Field '{field_name}' does not exist on {doc.doctype}"
                )
                return
            doc.set(field_name, action.value)

        elif action.action_type == "Assign To":
            if action.target_user and hasattr(doc, "assigned_to"):
                doc.assigned_to = action.target_user

        elif action.action_type == "Send Notification":
            from orga.orga.doctype.orga_notification.orga_notification import create_notification

            recipient = action.target_user or doc.owner
            create_notification(
                notification_type="System",
                subject=_("Automation: {0}").format(self.rule_name),
                recipient=recipient,
                message=action.message,
                reference_doctype=doc.doctype,
                reference_name=doc.name,
                from_user=None  # System notification
            )

        elif action.action_type == "Add Comment":
            doc.add_comment("Comment", action.message)

        elif action.action_type == "Update Status":
            if action.value and hasattr(doc, "status"):
                doc.status = action.value


def get_applicable_rules(doctype, event):
    """
    Get active rules for a DocType and event.

    Args:
        doctype: Document type
        event: Trigger event name

    Returns:
        list: Matching rule names
    """
    event_map = {
        "before_insert": "On Create",
        "after_insert": "On Create",
        "on_update": "On Update",
        "on_change": "On Status Change"
    }

    trigger = event_map.get(event)
    if not trigger:
        return []

    return frappe.get_all(
        "Orga Automation Rule",
        filters={
            "applies_to": doctype,
            "trigger_event": trigger,
            "is_active": 1
        },
        pluck="name"
    )
