# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Webhook Dispatcher

Handles delivery of webhook events to subscribed endpoints.
"""

import hashlib
import hmac
import json
import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime_str


# Available webhook events with descriptions
WEBHOOK_EVENTS = {
    "*": "All events",
    "project.created": "When a new project is created",
    "project.updated": "When a project is modified",
    "project.completed": "When a project status changes to Completed",
    "project.deleted": "When a project is deleted",
    "task.created": "When a new task is created",
    "task.updated": "When a task is modified",
    "task.completed": "When a task status changes to Completed",
    "task.assigned": "When a task is assigned to a resource",
    "task.deleted": "When a task is deleted",
    "resource.created": "When a new resource is created",
    "resource.updated": "When a resource is modified",
    "resource.deleted": "When a resource is deleted",
    "assignment.created": "When a new assignment is created",
    "assignment.updated": "When an assignment is modified",
    "assignment.deleted": "When an assignment is deleted",
    "event.created": "When a new event is created",
    "event.updated": "When an event is modified",
    "event.deleted": "When an event is deleted",
    "event.rsvp": "When an attendee responds to an invitation",
    "milestone.created": "When a new milestone is created",
    "milestone.completed": "When a milestone is marked complete",
    "time_log.created": "When a new time log is created"
}


def get_webhook_events() -> dict:
    """Get list of available webhook events with descriptions."""
    return WEBHOOK_EVENTS


def dispatch_event(event_name: str, doc=None, data: dict = None, changes: dict = None):
    """
    Dispatch a webhook event to all subscribed webhooks.

    Args:
        event_name: The event name (e.g., "task.created")
        doc: The Frappe document that triggered the event (optional)
        data: Custom data to include in payload (optional)
        changes: Dict of field changes for update events (optional)
    """
    if event_name not in WEBHOOK_EVENTS and event_name != "*":
        frappe.log_error(f"Unknown webhook event: {event_name}", "Webhook Dispatcher")
        return

    # Get all active webhooks
    webhooks = frappe.get_all(
        "Orga Webhook",
        filters={"is_active": 1},
        fields=["name", "url", "request_timeout", "retry_count", "include_doc_data"]
    )

    if not webhooks:
        return

    # Build payload
    payload = build_payload(event_name, doc, data, changes)

    for webhook in webhooks:
        # Check if webhook is subscribed to this event
        if not is_subscribed(webhook.name, event_name):
            continue

        # Optionally strip doc data
        webhook_payload = payload.copy()
        if not webhook.include_doc_data and "data" in webhook_payload:
            # Keep only essential fields
            if "doc" in webhook_payload["data"]:
                webhook_payload["data"]["doc"] = {
                    "doctype": webhook_payload["data"]["doc"].get("doctype"),
                    "name": webhook_payload["data"]["doc"].get("name")
                }

        # Queue delivery (secret is retrieved inside worker via get_password)
        frappe.enqueue(
            "orga.orga.webhooks.dispatcher.deliver_webhook",
            webhook_name=webhook.name,
            url=webhook.url,
            timeout=webhook.request_timeout or 30,
            retry_count=webhook.retry_count or 3,
            event=event_name,
            payload=webhook_payload,
            queue="short",
            retry=webhook.retry_count or 3
        )


def build_payload(event_name: str, doc=None, data: dict = None, changes: dict = None) -> dict:
    """Build the webhook payload."""
    payload = {
        "event": event_name,
        "timestamp": get_datetime_str(now_datetime()),
        "site": frappe.local.site
    }

    if doc:
        doc_data = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)
        # Remove internal fields
        for key in ["_comments", "_assign", "_liked_by", "_user_tags", "docstatus"]:
            doc_data.pop(key, None)

        payload["data"] = {
            "doctype": doc.doctype if hasattr(doc, "doctype") else doc.get("doctype"),
            "name": doc.name if hasattr(doc, "name") else doc.get("name"),
            "doc": doc_data
        }

    if data:
        if "data" in payload:
            payload["data"].update(data)
        else:
            payload["data"] = data

    if changes:
        if "data" not in payload:
            payload["data"] = {}
        payload["data"]["changes"] = changes

    return payload


def is_subscribed(webhook_name: str, event_name: str) -> bool:
    """Check if a webhook is subscribed to a specific event."""
    events = frappe.get_all(
        "Orga Webhook Event",
        filters={"parent": webhook_name},
        pluck="event_name"
    )
    return event_name in events or "*" in events


def deliver_webhook(webhook_name: str, url: str, timeout: int,
                    retry_count: int, event: str, payload: dict,
                    secret: str = None):
    """
    Deliver a webhook payload to the target URL.

    Args:
        webhook_name: Name of the webhook config
        url: Target URL
        timeout: Request timeout in seconds
        retry_count: Number of retries remaining
        event: Event name
        payload: Payload data
        secret: Deprecated, ignored. Secret is retrieved via get_password.
    """
    import requests

    # Validate URL against SSRF before delivery
    from orga.orga.api.webhook import validate_webhook_url
    try:
        validate_webhook_url(url)
    except Exception as e:
        log_delivery_failure(webhook_name, event, url, 0, f"URL validation failed: {str(e)}")
        return

    body = json.dumps(payload, default=str, indent=None, separators=(',', ':'))

    headers = {
        "Content-Type": "application/json",
        "X-Orga-Event": event,
        "X-Orga-Delivery": frappe.generate_hash(length=32),
        "User-Agent": "Orga-Webhook/1.0"
    }

    # Retrieve secret securely via get_password (never passed as parameter)
    try:
        webhook_doc = frappe.get_doc("Orga Webhook", webhook_name)
        secret_value = webhook_doc.get_password("secret") if webhook_doc.secret else None
    except Exception:
        secret_value = None

    if secret_value:
        signature = hmac.new(
            secret_value.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers["X-Orga-Signature"] = f"sha256={signature}"

    try:
        response = requests.post(
            url,
            data=body,
            headers=headers,
            timeout=timeout
        )

        success = response.status_code < 400

        if success:
            # Update success stats
            frappe.db.set_value(
                "Orga Webhook", webhook_name,
                {
                    "success_count": frappe.db.get_value("Orga Webhook", webhook_name, "success_count") + 1,
                    "last_delivery": now_datetime(),
                    "last_status": "Success"
                },
                update_modified=False
            )
            frappe.db.commit()
        else:
            log_delivery_failure(
                webhook_name, event, url,
                response.status_code, response.text[:500]
            )

    except requests.exceptions.Timeout:
        log_delivery_failure(webhook_name, event, url, 0, "Request timed out")

    except requests.exceptions.ConnectionError as e:
        log_delivery_failure(webhook_name, event, url, 0, f"Connection error: {str(e)[:200]}")

    except Exception as e:
        log_delivery_failure(webhook_name, event, url, 0, str(e)[:500])


def log_delivery_failure(webhook_name: str, event: str, url: str,
                         status_code: int, error: str):
    """Log a failed webhook delivery."""
    # Update failure stats
    frappe.db.set_value(
        "Orga Webhook", webhook_name,
        {
            "failure_count": frappe.db.get_value("Orga Webhook", webhook_name, "failure_count") + 1,
            "last_delivery": now_datetime(),
            "last_status": "Failed"
        },
        update_modified=False
    )
    frappe.db.commit()

    # Log error for debugging
    frappe.log_error(
        message=f"URL: {url}\nStatus: {status_code}\nError: {error}",
        title=f"Webhook Delivery Failed: {webhook_name} - {event}"
    )


# =============================================================================
# HELPER FUNCTIONS FOR TRIGGERING EVENTS FROM DOC EVENTS
# =============================================================================

def trigger_on_insert(doc, method):
    """Trigger webhook on document insert."""
    doctype_event_map = {
        "Orga Project": "project.created",
        "Orga Task": "task.created",
        "Orga Resource": "resource.created",
        "Orga Assignment": "assignment.created",
        "Orga Appointment": "event.created",
        "Orga Milestone": "milestone.created",
        "Orga Time Log": "time_log.created"
    }

    event = doctype_event_map.get(doc.doctype)
    if event:
        dispatch_event(event, doc)


def trigger_on_update(doc, method):
    """Trigger webhook on document update."""
    doctype_event_map = {
        "Orga Project": "project.updated",
        "Orga Task": "task.updated",
        "Orga Resource": "resource.updated",
        "Orga Assignment": "assignment.updated",
        "Orga Appointment": "event.updated"
    }

    event = doctype_event_map.get(doc.doctype)
    if event:
        # Get changes
        changes = {}
        if hasattr(doc, "_doc_before_save") and doc._doc_before_save:
            for field in doc.meta.get_valid_columns():
                old_value = doc._doc_before_save.get(field)
                new_value = doc.get(field)
                if old_value != new_value:
                    changes[field] = {"from": old_value, "to": new_value}

        dispatch_event(event, doc, changes=changes if changes else None)

        # Check for status changes
        if "status" in changes:
            new_status = changes["status"]["to"]

            if doc.doctype == "Orga Project" and new_status == "Completed":
                dispatch_event("project.completed", doc)
            elif doc.doctype == "Orga Task" and new_status == "Completed":
                dispatch_event("task.completed", doc)
            elif doc.doctype == "Orga Milestone" and new_status == "Completed":
                dispatch_event("milestone.completed", doc)


def trigger_on_trash(doc, method):
    """Trigger webhook on document delete."""
    doctype_event_map = {
        "Orga Project": "project.deleted",
        "Orga Task": "task.deleted",
        "Orga Resource": "resource.deleted",
        "Orga Assignment": "assignment.deleted",
        "Orga Appointment": "event.deleted"
    }

    event = doctype_event_map.get(doc.doctype)
    if event:
        dispatch_event(event, doc)
