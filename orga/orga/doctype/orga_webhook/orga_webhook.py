# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaWebhook(Document):
    def validate(self):
        self.validate_url()
        self.validate_events()
        self.validate_timeout()
        self.validate_retry_count()

    def validate_url(self):
        """Validate that URL is properly formatted."""
        if not self.url:
            return

        if not self.url.startswith(('http://', 'https://')):
            frappe.throw(_("Webhook URL must start with http:// or https://"))

        # Warn about non-HTTPS URLs
        if self.url.startswith('http://') and not self.url.startswith('http://localhost'):
            frappe.msgprint(
                _("Warning: Using HTTP instead of HTTPS. Webhook payloads may not be secure."),
                indicator="orange"
            )

    def validate_events(self):
        """Validate that at least one event is selected."""
        if not self.events:
            frappe.throw(_("At least one event must be selected"))

        # Check for duplicate events
        event_names = [e.event_name for e in self.events]
        if len(event_names) != len(set(event_names)):
            frappe.throw(_("Duplicate events are not allowed"))

    def validate_timeout(self):
        """Validate request timeout is within allowed range."""
        if self.request_timeout:
            if self.request_timeout < 1:
                self.request_timeout = 1
            elif self.request_timeout > 60:
                self.request_timeout = 60

    def validate_retry_count(self):
        """Validate retry count is within allowed range."""
        if self.retry_count:
            if self.retry_count < 0:
                self.retry_count = 0
            elif self.retry_count > 5:
                self.retry_count = 5

    def is_subscribed_to(self, event_name: str) -> bool:
        """Check if this webhook is subscribed to a specific event."""
        if not self.is_active:
            return False

        for event in self.events:
            if event.event_name == event_name or event.event_name == "*":
                return True
        return False

    def increment_success(self):
        """Increment success counter and update last delivery info."""
        frappe.db.set_value(
            "Orga Webhook", self.name,
            {
                "success_count": (self.success_count or 0) + 1,
                "last_delivery": frappe.utils.now_datetime(),
                "last_status": "Success"
            },
            update_modified=False
        )

    def increment_failure(self):
        """Increment failure counter and update last delivery info."""
        frappe.db.set_value(
            "Orga Webhook", self.name,
            {
                "failure_count": (self.failure_count or 0) + 1,
                "last_delivery": frappe.utils.now_datetime(),
                "last_status": "Failed"
            },
            update_modified=False
        )
