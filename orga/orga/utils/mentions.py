# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Utility for parsing @mentions in comments.

Supports multiple mention formats:
- @[Full Name](user@email.com) - Rich format from editors
- @user@email.com - Email format
- @username - Username format
"""

import re
import frappe
from frappe import _


# Pattern for rich mentions: @[Name](email)
RICH_MENTION_PATTERN = re.compile(r'@\[([^\]]+)\]\(([^)]+)\)')

# Pattern for simple mentions: @email or @username
SIMPLE_MENTION_PATTERN = re.compile(r'@([\w.-]+@[\w.-]+\.\w+|\w+)')


def parse_mentions(text: str) -> list:
    """
    Parse @mentions from text.

    Supports formats:
    - @[Full Name](user@email.com)
    - @user@email.com
    - @username

    Args:
        text: Text to parse for mentions

    Returns:
        list: List of unique user emails/IDs mentioned
    """
    if not text:
        return []

    mentions = []

    # Rich mentions: @[Name](email)
    for match in RICH_MENTION_PATTERN.finditer(text):
        email = match.group(2)
        if frappe.db.exists("User", email):
            mentions.append(email)

    # Simple mentions: @email or @username
    for match in SIMPLE_MENTION_PATTERN.finditer(text):
        identifier = match.group(1)

        # Check if it looks like an email
        if '@' in identifier and '.' in identifier.split('@')[-1]:
            if frappe.db.exists("User", identifier):
                mentions.append(identifier)
        else:
            # Try to find user by username or match email
            user = frappe.db.get_value(
                "User",
                {"username": identifier, "enabled": 1},
                "name"
            )
            if user:
                mentions.append(user)
            else:
                # Try partial email match
                user = frappe.db.get_value(
                    "User",
                    {"name": ["like", f"{identifier}@%"], "enabled": 1},
                    "name"
                )
                if user:
                    mentions.append(user)

    # Return unique mentions
    return list(set(mentions))


def process_comment_mentions(doc, comment_text: str):
    """
    Process mentions in a comment and send notifications.

    Args:
        doc: Parent document (Task, Project, etc.)
        comment_text: Comment text to parse
    """
    from orga.orga.doctype.orga_notification.orga_notification import notify_mention

    mentions = parse_mentions(comment_text)

    for user in mentions:
        # Don't notify self
        if user != frappe.session.user:
            notify_mention(doc, user, comment_text)


def get_user_mentions_autocomplete(search: str, limit: int = 10) -> list:
    """
    Get users for mention autocomplete.

    Args:
        search: Search term
        limit: Maximum results

    Returns:
        list: Users matching search [{name, full_name, email}]
    """
    filters = {"enabled": 1}

    if search:
        filters["full_name"] = ["like", f"%{search}%"]

    users = frappe.get_all(
        "User",
        filters=filters,
        fields=["name", "full_name", "user_image"],
        order_by="full_name",
        limit_page_length=limit
    )

    # Format for autocomplete
    return [
        {
            "id": u.name,
            "name": u.full_name,
            "email": u.name,
            "image": u.user_image
        }
        for u in users
        if u.name not in ("Administrator", "Guest")
    ]
