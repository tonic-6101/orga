# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Orga Webhooks Module

Provides webhook delivery system for external integrations.

Usage:
    from orga.orga.webhooks import dispatch_event

    # Dispatch a webhook event
    dispatch_event("task.created", task_doc)
"""

from orga.orga.webhooks.dispatcher import dispatch_event, get_webhook_events

__all__ = ["dispatch_event", "get_webhook_events"]
