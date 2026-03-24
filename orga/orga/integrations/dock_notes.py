# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import re

import frappe
from frappe import _


@frappe.whitelist()
def convert_to_task(note_name: str) -> dict:
    """
    Convert a Dock Note into a standalone Orga Task.

    - Extracts the first line of text as the task subject
    - Uses the full note content as the task description
    - Soft-deletes the note after successful conversion
    - Returns a route to the new task in My Tasks

    Args:
        note_name: The name (ID) of the Dock Note to convert

    Returns:
        dict with success, message, and route
    """
    if not note_name:
        frappe.throw(_("Note name is required"))

    note = frappe.get_doc("Dock Note", note_name)

    # Only the note owner can convert their own notes
    if note.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("You can only convert your own notes"), frappe.PermissionError)

    # Extract subject from the note content (first line of plain text)
    subject = _extract_subject(note.content)
    if not subject:
        frappe.throw(_("Cannot convert an empty note to a task"))

    # Create the task — standalone (no project), assigned to the note owner
    task = frappe.get_doc({
        "doctype": "Orga Task",
        "subject": subject,
        "description": note.content,
        "assigned_to": frappe.session.user,
        "status": "Open",
        "priority": "Medium",
    })
    task.insert()

    # Soft-delete the note (mark as converted)
    note.deleted_at = frappe.utils.now_datetime()
    note.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Note converted to task: {0}").format(subject),
        "task_name": task.name,
        "route": "/orga/my-tasks",
    }


def _extract_subject(html_content: str) -> str:
    """Extract a short subject line from HTML note content."""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", html_content or "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    # Take the first sentence or first 120 chars, whichever is shorter
    first_line = text.split("\n")[0].strip()
    # Try to cut at a sentence boundary
    for sep in (".", "!", "?"):
        idx = first_line.find(sep)
        if 0 < idx < 120:
            return first_line[: idx + 1]
    # Truncate at 120 chars with ellipsis
    if len(first_line) > 120:
        return first_line[:117] + "..."
    return first_line
