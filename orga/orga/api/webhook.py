# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Webhook API

Endpoints for managing webhooks and testing webhook delivery.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import frappe
from frappe import _


# =============================================================================
# SECURITY UTILITIES
# =============================================================================

_ALLOWED_ROLES = ("System Manager", "Orga Manager")


def _check_webhook_permission():
    """Ensure user has permission to manage webhooks."""
    roles = frappe.get_roles()
    if not any(role in roles for role in _ALLOWED_ROLES):
        frappe.throw(_("Not permitted to manage webhooks"), frappe.PermissionError)


def validate_webhook_url(url: str) -> None:
    """
    Validate a webhook URL to prevent SSRF attacks.

    Blocks:
    - Private/internal IP ranges (RFC 1918)
    - Loopback addresses (127.0.0.0/8, ::1)
    - Link-local addresses (169.254.0.0/16, fe80::/10)
    - Cloud metadata endpoints (169.254.169.254)
    - Non-HTTP(S) schemes
    """
    if not url:
        frappe.throw(_("Webhook URL is required"))

    parsed = urlparse(url)

    # Only allow http and https
    if parsed.scheme not in ("http", "https"):
        frappe.throw(_("Only HTTP and HTTPS webhook URLs are allowed"))

    hostname = parsed.hostname
    if not hostname:
        frappe.throw(_("Invalid webhook URL: no hostname"))

    # Block common internal hostnames
    blocked_hostnames = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
    if hostname.lower() in blocked_hostnames:
        frappe.throw(_("Webhook URL must not point to localhost or internal addresses"))

    # Resolve hostname and check IP
    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        frappe.throw(_("Cannot resolve webhook URL hostname: {0}").format(hostname))

    for family, _type, _proto, _canonname, sockaddr in resolved_ips:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            frappe.throw(
                _("Webhook URL must not resolve to a private or internal IP address")
            )

        # Specifically block cloud metadata endpoint
        if ip_str == "169.254.169.254":
            frappe.throw(
                _("Webhook URL must not point to cloud metadata endpoints")
            )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@frappe.whitelist()
def get_webhooks(limit: int = 50, offset: int = 0):
    """
    Get list of configured webhooks.

    Args:
        limit: Maximum results (default: 50)
        offset: Pagination offset

    Returns:
        dict: {webhooks: list, total: int}
    """
    _check_webhook_permission()

    webhooks = frappe.get_all(
        "Orga Webhook",
        fields=[
            "name", "webhook_name", "url", "is_active",
            "last_delivery", "last_status", "success_count", "failure_count"
        ],
        limit_page_length=int(limit),
        limit_start=int(offset),
        order_by="webhook_name asc"
    )

    # Get event counts for each webhook
    for webhook in webhooks:
        webhook["event_count"] = frappe.db.count(
            "Orga Webhook Event",
            {"parent": webhook.name}
        )

    total = frappe.db.count("Orga Webhook")

    return {"webhooks": webhooks, "total": total}


@frappe.whitelist()
def get_webhook(name: str):
    """
    Get detailed webhook information.

    Args:
        name: Webhook name

    Returns:
        dict: Full webhook data with events
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    webhook = frappe.get_doc("Orga Webhook", name)

    return {
        "name": webhook.name,
        "webhook_name": webhook.webhook_name,
        "url": webhook.url,
        "is_active": webhook.is_active,
        "request_timeout": webhook.request_timeout,
        "retry_count": webhook.retry_count,
        "include_doc_data": webhook.include_doc_data,
        "last_delivery": webhook.last_delivery,
        "last_status": webhook.last_status,
        "success_count": webhook.success_count,
        "failure_count": webhook.failure_count,
        "notes": webhook.notes,
        "events": [
            {"event_name": e.event_name, "description": e.description}
            for e in webhook.events
        ]
    }


@frappe.whitelist()
def create_webhook(data: dict):
    """
    Create a new webhook.

    Args:
        data: Webhook configuration including:
            - webhook_name (required)
            - url (required)
            - events (required): list of event names
            - secret (optional)
            - is_active (optional, default: 1)
            - request_timeout (optional, default: 30)
            - retry_count (optional, default: 3)

    Returns:
        dict: Created webhook info
    """
    _check_webhook_permission()

    if isinstance(data, str):
        import json
        data = json.loads(data)

    if not data.get("webhook_name"):
        frappe.throw(_("Webhook name is required"))

    if not data.get("url"):
        frappe.throw(_("Webhook URL is required"))

    # Validate URL against SSRF
    validate_webhook_url(data["url"])

    if not data.get("events"):
        frappe.throw(_("At least one event is required"))

    webhook = frappe.get_doc({
        "doctype": "Orga Webhook",
        "webhook_name": data.get("webhook_name"),
        "url": data.get("url"),
        "secret": data.get("secret"),
        "is_active": data.get("is_active", 1),
        "request_timeout": data.get("request_timeout", 30),
        "retry_count": data.get("retry_count", 3),
        "include_doc_data": data.get("include_doc_data", 1),
        "notes": data.get("notes")
    })

    # Add events
    events = data.get("events", [])
    if isinstance(events, str):
        events = [events]

    for event_name in events:
        webhook.append("events", {"event_name": event_name})

    webhook.insert()
    frappe.db.commit()

    return {
        "name": webhook.name,
        "webhook_name": webhook.webhook_name,
        "url": webhook.url,
        "is_active": webhook.is_active
    }


@frappe.whitelist()
def update_webhook(name: str, data: dict):
    """
    Update an existing webhook.

    Args:
        name: Webhook name
        data: Fields to update

    Returns:
        dict: Updated webhook info
    """
    _check_webhook_permission()

    if isinstance(data, str):
        import json
        data = json.loads(data)

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    # Validate URL against SSRF if being changed
    if "url" in data:
        validate_webhook_url(data["url"])

    webhook = frappe.get_doc("Orga Webhook", name)

    # Update allowed fields
    allowed_fields = [
        "url", "secret", "is_active", "request_timeout",
        "retry_count", "include_doc_data", "notes"
    ]

    for field in allowed_fields:
        if field in data:
            setattr(webhook, field, data[field])

    # Update events if provided
    if "events" in data:
        webhook.events = []
        events = data["events"]
        if isinstance(events, str):
            events = [events]

        for event_name in events:
            webhook.append("events", {"event_name": event_name})

    webhook.save()
    frappe.db.commit()

    return {
        "name": webhook.name,
        "webhook_name": webhook.webhook_name,
        "url": webhook.url,
        "is_active": webhook.is_active
    }


@frappe.whitelist()
def delete_webhook(name: str):
    """
    Delete a webhook.

    Args:
        name: Webhook name

    Returns:
        dict: Success status
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    frappe.delete_doc("Orga Webhook", name)
    frappe.db.commit()

    return {"success": True, "message": _("Webhook deleted")}


@frappe.whitelist()
def activate_webhook(name: str):
    """
    Activate a webhook.

    Args:
        name: Webhook name

    Returns:
        dict: Updated status
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    frappe.db.set_value("Orga Webhook", name, "is_active", 1)
    frappe.db.commit()

    return {"name": name, "is_active": 1}


@frappe.whitelist()
def deactivate_webhook(name: str):
    """
    Deactivate a webhook.

    Args:
        name: Webhook name

    Returns:
        dict: Updated status
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    frappe.db.set_value("Orga Webhook", name, "is_active", 0)
    frappe.db.commit()

    return {"name": name, "is_active": 0}


@frappe.whitelist()
def test_webhook(name: str, event: str = "test.ping"):
    """
    Send a test webhook to verify configuration.

    Args:
        name: Webhook name
        event: Event name to simulate (default: test.ping)

    Returns:
        dict: Test result with success/failure status
    """
    import requests
    import hashlib
    import hmac
    import json

    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    webhook = frappe.get_doc("Orga Webhook", name)

    # Validate URL against SSRF before sending test request
    validate_webhook_url(webhook.url)

    # Build test payload
    payload = {
        "event": event,
        "timestamp": frappe.utils.now_datetime().isoformat(),
        "site": frappe.local.site,
        "test": True,
        "data": {
            "message": "This is a test webhook from Orga"
        }
    }

    body = json.dumps(payload, default=str)

    headers = {
        "Content-Type": "application/json",
        "X-Orga-Event": event,
        "X-Orga-Delivery": frappe.generate_hash(length=32),
        "X-Orga-Test": "true",
        "User-Agent": "Orga-Webhook/1.0"
    }

    # Sign if secret provided
    if webhook.secret:
        signature = hmac.new(
            webhook.get_password("secret").encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        headers["X-Orga-Signature"] = f"sha256={signature}"

    try:
        response = requests.post(
            webhook.url,
            data=body,
            headers=headers,
            timeout=webhook.request_timeout or 30
        )

        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out",
            "status_code": 0
        }

    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)[:200]}",
            "status_code": 0
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 0
        }


@frappe.whitelist()
def get_available_events():
    """
    Get list of available webhook events.

    Returns:
        list: Available events with descriptions
    """
    _check_webhook_permission()

    from orga.orga.webhooks.dispatcher import get_webhook_events

    events = get_webhook_events()
    return [
        {"event_name": name, "description": desc}
        for name, desc in events.items()
    ]


@frappe.whitelist()
def get_webhook_stats(name: str):
    """
    Get delivery statistics for a webhook.

    Args:
        name: Webhook name

    Returns:
        dict: Delivery statistics
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    webhook = frappe.get_doc("Orga Webhook", name)

    total_deliveries = (webhook.success_count or 0) + (webhook.failure_count or 0)
    success_rate = 0
    if total_deliveries > 0:
        success_rate = round((webhook.success_count or 0) / total_deliveries * 100, 1)

    return {
        "name": webhook.name,
        "total_deliveries": total_deliveries,
        "success_count": webhook.success_count or 0,
        "failure_count": webhook.failure_count or 0,
        "success_rate": success_rate,
        "last_delivery": webhook.last_delivery,
        "last_status": webhook.last_status
    }


@frappe.whitelist()
def reset_webhook_stats(name: str):
    """
    Reset delivery statistics for a webhook.

    Args:
        name: Webhook name

    Returns:
        dict: Success status
    """
    _check_webhook_permission()

    if not frappe.db.exists("Orga Webhook", name):
        frappe.throw(_("Webhook not found"), frappe.DoesNotExistError)

    frappe.db.set_value("Orga Webhook", name, {
        "success_count": 0,
        "failure_count": 0,
        "last_delivery": None,
        "last_status": None
    })
    frappe.db.commit()

    return {"success": True, "message": _("Statistics reset")}
