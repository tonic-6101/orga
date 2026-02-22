# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Activity API Module

Provides endpoints for managing activity feed entries including:
- Activity details with version history
- Notes/annotations on activities
- Pin/archive functionality
- Admin delete capability

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.activity.get_activity_details',
        args: { doctype: 'Orga Task', docname: 'TASK-0001' }
    })
"""

import frappe
from frappe import _


# ============================================================================
# ACTIVITY DETAILS
# ============================================================================

@frappe.whitelist()
def get_activity_details(doctype: str, docname: str) -> dict:
    """
    Get detailed activity information including field changes.

    Args:
        doctype: Reference document type (e.g., "Orga Task")
        docname: Reference document name

    Returns:
        dict: Activity details with changes, notes, and metadata
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = frappe.get_doc(doctype, docname)

    # Get recent changes from Version doctype
    changes = get_document_changes(doctype, docname)

    # Get notes/comments on this activity
    notes = get_activity_notes(doctype, docname)

    # Get pin/archive status from user preferences
    user_prefs = get_activity_user_prefs(doctype, docname)

    return {
        "doctype": doctype,
        "name": docname,
        "title": get_document_title(doc),
        "modified": doc.modified,
        "modified_by": doc.modified_by,
        "modified_by_name": frappe.db.get_value("User", doc.modified_by, "full_name"),
        "changes": changes,
        "notes": notes,
        "is_pinned": user_prefs.get("is_pinned", False),
        "is_archived": user_prefs.get("is_archived", False),
        "can_delete": frappe.has_permission(doctype, "delete", docname) or "System Manager" in frappe.get_roles()
    }


def get_document_changes(doctype: str, docname: str, limit: int = 10) -> list:
    """
    Get field-level changes from Version doctype.

    Args:
        doctype: Document type
        docname: Document name
        limit: Maximum number of changes to return

    Returns:
        list: Changes with field labels and old/new values
    """
    versions = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": doctype,
            "docname": docname
        },
        fields=["data", "modified", "modified_by"],
        order_by="modified desc",
        limit=limit
    )

    changes = []
    meta = frappe.get_meta(doctype)

    for version in versions:
        try:
            data = frappe.parse_json(version.data)
            if "changed" in data:
                for change in data["changed"]:
                    field_name = change[0]
                    field_meta = meta.get_field(field_name)
                    changes.append({
                        "field": field_name,
                        "field_label": field_meta.label if field_meta else field_name,
                        "old_value": change[1],
                        "new_value": change[2],
                        "modified": str(version.modified) if version.modified else None,
                        "modified_by": version.modified_by,
                        "modified_by_image": frappe.db.get_value("User", version.modified_by, "user_image") if version.modified_by else None
                    })
        except Exception:
            pass

    return changes


def get_document_title(doc) -> str:
    """
    Get appropriate title field for document.

    Args:
        doc: Frappe document

    Returns:
        str: Document title
    """
    title_fields = [
        "title", "subject", "project_name", "milestone_name",
        "resource_name", "client_name", "name"
    ]
    for field in title_fields:
        if hasattr(doc, field) and getattr(doc, field):
            return getattr(doc, field)
    return doc.name


# ============================================================================
# ACTIVITY NOTES
# ============================================================================

@frappe.whitelist()
def add_activity_note(doctype: str, docname: str, content: str) -> dict:
    """
    Add a note to an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name
        content: Note content

    Returns:
        dict: Created note
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not content or not content.strip():
        frappe.throw(_("Note content is required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    comment = frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": doctype,
        "reference_name": docname,
        "content": content.strip(),
        "comment_email": frappe.session.user
    })
    comment.insert(ignore_permissions=True)

    return {
        "name": comment.name,
        "content": comment.content,
        "created_by": frappe.session.user,
        "created_by_name": frappe.db.get_value("User", frappe.session.user, "full_name"),
        "creation": str(comment.creation)
    }


@frappe.whitelist()
def delete_activity_note(note_name: str) -> dict:
    """
    Delete an activity note.

    Args:
        note_name: Comment document name

    Returns:
        dict: Success status
    """
    if not note_name:
        frappe.throw(_("Note name is required"))

    if not frappe.db.exists("Comment", note_name):
        frappe.throw(_("Note not found"), frappe.DoesNotExistError)

    comment = frappe.get_doc("Comment", note_name)

    # Only author or admin can delete
    if comment.comment_email != frappe.session.user:
        if "System Manager" not in frappe.get_roles():
            frappe.throw(_("Not permitted to delete this note"), frappe.PermissionError)

    frappe.delete_doc("Comment", note_name, ignore_permissions=True)

    return {"success": True}


def get_activity_notes(doctype: str, docname: str) -> list:
    """
    Get notes for an activity.

    Args:
        doctype: Document type
        docname: Document name

    Returns:
        list: Notes with author info
    """
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": doctype,
            "reference_name": docname,
            "comment_type": "Info"
        },
        fields=["name", "content", "comment_email", "creation"],
        order_by="creation desc"
    )

    for comment in comments:
        comment["created_by"] = comment.pop("comment_email")
        user_info = frappe.db.get_value(
            "User", comment["created_by"], ["full_name", "user_image"], as_dict=True
        )
        comment["created_by_name"] = (user_info.full_name if user_info else None) or comment["created_by"]
        comment["created_by_image"] = user_info.user_image if user_info else None
        comment["creation"] = str(comment["creation"]) if comment["creation"] else None

    return comments


# ============================================================================
# PIN / ARCHIVE FUNCTIONALITY
# ============================================================================

@frappe.whitelist()
def toggle_activity_pin(doctype: str, docname: str) -> dict:
    """
    Toggle pin status for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: New pin status
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    # Sanitize key - replace spaces with underscores
    safe_doctype = doctype.replace(" ", "_")
    key = f"activity_pinned_{safe_doctype}_{docname}"
    current = frappe.defaults.get_user_default(key)

    if current:
        frappe.defaults.clear_user_default(key)
        is_pinned = False
    else:
        frappe.defaults.set_user_default(key, "1")
        is_pinned = True

    return {"is_pinned": is_pinned}


@frappe.whitelist()
def toggle_activity_archive(doctype: str, docname: str) -> dict:
    """
    Toggle archive status for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: New archive status
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    # Sanitize key - replace spaces with underscores
    safe_doctype = doctype.replace(" ", "_")
    key = f"activity_archived_{safe_doctype}_{docname}"
    current = frappe.defaults.get_user_default(key)

    if current:
        frappe.defaults.clear_user_default(key)
        is_archived = False
    else:
        frappe.defaults.set_user_default(key, "1")
        is_archived = True

    return {"is_archived": is_archived}


def get_activity_user_prefs(doctype: str, docname: str) -> dict:
    """
    Get user-specific preferences for an activity.

    Args:
        doctype: Document type
        docname: Document name

    Returns:
        dict: Pin and archive status
    """
    safe_doctype = doctype.replace(" ", "_")
    pin_key = f"activity_pinned_{safe_doctype}_{docname}"
    archive_key = f"activity_archived_{safe_doctype}_{docname}"

    return {
        "is_pinned": bool(frappe.defaults.get_user_default(pin_key)),
        "is_archived": bool(frappe.defaults.get_user_default(archive_key))
    }


@frappe.whitelist()
def get_pinned_activities() -> list:
    """
    Get list of pinned activity keys for current user.

    Returns:
        list: Pinned activity identifiers
    """
    defaults = frappe.defaults.get_defaults_for(frappe.session.user)
    pinned = []

    for key, value in defaults.items():
        if key.startswith("activity_pinned_") and value:
            # Parse the key to extract doctype and name
            # Key format: activity_pinned_Orga_Task_TASK-0001
            remaining = key.replace("activity_pinned_", "")
            # Find the last underscore that separates doctype from name
            # The name could contain underscores, so we need to be careful
            # Assume doctype has a pattern like "Orga_Task" (one underscore)
            parts = remaining.split("_")
            if len(parts) >= 2:
                # Try to reconstruct - typically "Orga_DocType" + "_NAME"
                doctype = parts[0] + " " + parts[1]  # e.g., "Orga Task"
                name = "_".join(parts[2:]) if len(parts) > 2 else ""
                if name:
                    pinned.append({"doctype": doctype, "name": name})

    return pinned


@frappe.whitelist()
def get_archived_activities() -> list:
    """
    Get list of archived activity keys for current user.

    Returns:
        list: Archived activity identifiers
    """
    defaults = frappe.defaults.get_defaults_for(frappe.session.user)
    archived = []

    for key, value in defaults.items():
        if key.startswith("activity_archived_") and value:
            remaining = key.replace("activity_archived_", "")
            parts = remaining.split("_")
            if len(parts) >= 2:
                doctype = parts[0] + " " + parts[1]
                name = "_".join(parts[2:]) if len(parts) > 2 else ""
                if name:
                    archived.append({"doctype": doctype, "name": name})

    return archived


# ============================================================================
# INLINE COMMENTS (Threaded)
# ============================================================================

@frappe.whitelist()
def get_activity_comments(
    doctype: str,
    docname: str,
    limit: int = 10,
    offset: int = 0
) -> dict:
    """
    Get comments for an activity with pagination.

    Args:
        doctype: Reference document type
        docname: Reference document name
        limit: Max comments to return (default 10)
        offset: Pagination offset (default 0)

    Returns:
        dict: {comments: list, has_more: bool, total: int}
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    # Convert to int
    limit = int(limit)
    offset = int(offset)

    # Get top-level comments only (not replies)
    filters = {
        "reference_doctype": doctype,
        "reference_name": docname,
        "parent_comment": ["is", "not set"]
    }

    total = frappe.db.count("Orga Activity Comment", filters)

    # Pinned comments first, then chronological
    pinned = frappe.get_all(
        "Orga Activity Comment",
        filters={**filters, "is_pinned": 1},
        fields=["name", "user", "content", "creation", "is_resolved", "resolved_by", "resolved_at", "is_pinned", "pinned_by", "pinned_at"],
        order_by="pinned_at desc"
    )

    unpinned = frappe.get_all(
        "Orga Activity Comment",
        filters={**filters, "is_pinned": ["!=", 1]},
        fields=["name", "user", "content", "creation", "is_resolved", "resolved_by", "resolved_at", "is_pinned", "pinned_by", "pinned_at"],
        order_by="creation desc",
        limit_page_length=limit,
        limit_start=offset
    )

    comments = pinned + unpinned

    # Add user details and reply counts
    for comment in comments:
        comment["user_fullname"] = frappe.db.get_value("User", comment["user"], "full_name") or comment["user"]
        comment["user_image"] = frappe.db.get_value("User", comment["user"], "user_image")
        comment["reply_count"] = frappe.db.count(
            "Orga Activity Comment",
            {"parent_comment": comment["name"]}
        )
        comment["replies"] = []  # Loaded on demand via get_comment_replies
        comment["creation"] = str(comment["creation"]) if comment["creation"] else None
        comment["can_delete"] = (
            comment["user"] == frappe.session.user or
            "System Manager" in frappe.get_roles()
        )
        # Convert datetimes
        if comment.get("resolved_at"):
            comment["resolved_at"] = str(comment["resolved_at"])
        if comment.get("pinned_at"):
            comment["pinned_at"] = str(comment["pinned_at"])

    return {
        "comments": comments,
        "has_more": offset + len(unpinned) < total,
        "total": total
    }


@frappe.whitelist()
def get_comment_replies(comment_name: str, limit: int = 20) -> list:
    """
    Get replies to a specific comment.

    Args:
        comment_name: Parent comment name
        limit: Max replies to return

    Returns:
        list: Reply comments with user details
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    limit = int(limit)

    replies = frappe.get_all(
        "Orga Activity Comment",
        filters={"parent_comment": comment_name},
        fields=["name", "user", "content", "creation"],
        order_by="creation asc",
        limit_page_length=limit
    )

    for reply in replies:
        reply["user_fullname"] = frappe.db.get_value("User", reply["user"], "full_name") or reply["user"]
        reply["user_image"] = frappe.db.get_value("User", reply["user"], "user_image")
        reply["creation"] = str(reply["creation"]) if reply["creation"] else None
        reply["can_delete"] = (
            reply["user"] == frappe.session.user or
            "System Manager" in frappe.get_roles()
        )

    return replies


@frappe.whitelist()
def add_activity_comment(
    doctype: str,
    docname: str,
    content: str,
    parent_comment: str = None
) -> dict:
    """
    Add a comment to an activity.

    Parses @mentions from content and creates mention records.

    Args:
        doctype: Reference document type
        docname: Reference document name
        content: Comment content (may contain @user references)
        parent_comment: Parent comment name for replies (optional)

    Returns:
        dict: Created comment with user details
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not content or not content.strip():
        frappe.throw(_("Comment content is required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    # Parse @mentions
    mentions = _parse_mentions(content.strip())

    comment = frappe.get_doc({
        "doctype": "Orga Activity Comment",
        "reference_doctype": doctype,
        "reference_name": docname,
        "parent_comment": parent_comment if parent_comment else None,
        "user": frappe.session.user,
        "content": content.strip()
    })

    # Add mention child records
    for mentioned_user in mentions:
        comment.append("mentions", {"user": mentioned_user})

    comment.insert(ignore_permissions=True)

    return {
        "name": comment.name,
        "user": comment.user,
        "user_fullname": frappe.db.get_value("User", comment.user, "full_name") or comment.user,
        "user_image": frappe.db.get_value("User", comment.user, "user_image"),
        "content": comment.content,
        "creation": str(comment.creation),
        "parent_comment": comment.parent_comment,
        "reply_count": 0,
        "replies": [],
        "can_delete": True
    }


@frappe.whitelist()
def delete_activity_comment(comment_name: str) -> dict:
    """
    Delete an activity comment.

    Only the comment author or administrators can delete.
    Deleting a comment also deletes its replies.

    Args:
        comment_name: Comment document name

    Returns:
        dict: Success status
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    comment = frappe.get_doc("Orga Activity Comment", comment_name)

    # Permission check is done in on_trash
    frappe.delete_doc("Orga Activity Comment", comment_name)

    return {"success": True}


@frappe.whitelist()
def resolve_comment(comment_name: str) -> dict:
    """
    Mark a comment thread as resolved.

    Args:
        comment_name: Comment document name

    Returns:
        dict: {success, is_resolved, resolved_by, resolved_at}
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    now = frappe.utils.now()
    frappe.db.set_value("Orga Activity Comment", comment_name, {
        "is_resolved": 1,
        "resolved_by": frappe.session.user,
        "resolved_at": now
    })

    return {
        "success": True,
        "is_resolved": True,
        "resolved_by": frappe.session.user,
        "resolved_at": str(now)
    }


@frappe.whitelist()
def unresolve_comment(comment_name: str) -> dict:
    """
    Reopen a resolved comment thread.

    Args:
        comment_name: Comment document name

    Returns:
        dict: {success, is_resolved}
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    frappe.db.set_value("Orga Activity Comment", comment_name, {
        "is_resolved": 0,
        "resolved_by": None,
        "resolved_at": None
    })

    return {"success": True, "is_resolved": False}


@frappe.whitelist()
def pin_comment(comment_name: str) -> dict:
    """
    Pin a comment to the top of the discussion. Unpins any previously pinned
    comment for the same reference document.

    Args:
        comment_name: Comment document name

    Returns:
        dict: {success, is_pinned, pinned_by, pinned_at}
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    comment = frappe.get_doc("Orga Activity Comment", comment_name)

    # Unpin any existing pinned comment for the same reference
    existing_pinned = frappe.get_all(
        "Orga Activity Comment",
        filters={
            "reference_doctype": comment.reference_doctype,
            "reference_name": comment.reference_name,
            "is_pinned": 1,
            "name": ["!=", comment_name]
        },
        pluck="name"
    )
    for name in existing_pinned:
        frappe.db.set_value("Orga Activity Comment", name, {
            "is_pinned": 0,
            "pinned_by": None,
            "pinned_at": None
        })

    now = frappe.utils.now()
    frappe.db.set_value("Orga Activity Comment", comment_name, {
        "is_pinned": 1,
        "pinned_by": frappe.session.user,
        "pinned_at": now
    })

    return {
        "success": True,
        "is_pinned": True,
        "pinned_by": frappe.session.user,
        "pinned_at": str(now)
    }


@frappe.whitelist()
def unpin_comment(comment_name: str) -> dict:
    """
    Unpin a comment.

    Args:
        comment_name: Comment document name

    Returns:
        dict: {success, is_pinned}
    """
    if not comment_name:
        frappe.throw(_("Comment name is required"))

    if not frappe.db.exists("Orga Activity Comment", comment_name):
        frappe.throw(_("Comment not found"), frappe.DoesNotExistError)

    frappe.db.set_value("Orga Activity Comment", comment_name, {
        "is_pinned": 0,
        "pinned_by": None,
        "pinned_at": None
    })

    return {"success": True, "is_pinned": False}


def _parse_mentions(content: str) -> list:
    """
    Extract @mentioned users from content.

    Supports formats:
    - @username
    - @user@email.com
    - @Full Name (matches against full_name)

    Args:
        content: Comment content

    Returns:
        list: Valid user IDs
    """
    import re

    # Match @word or @word.word@domain.com patterns
    pattern = r'@([\w.]+(?:@[\w.-]+)?)'
    matches = re.findall(pattern, content)

    valid_users = []
    for match in matches:
        # Try direct user ID match
        if frappe.db.exists("User", match):
            valid_users.append(match)
        # Try full name match
        elif frappe.db.exists("User", {"full_name": match}):
            user_id = frappe.db.get_value("User", {"full_name": match}, "name")
            if user_id:
                valid_users.append(user_id)
        # Try partial name match (first word of full name)
        else:
            users = frappe.get_all(
                "User",
                filters=[["full_name", "like", f"{match}%"]],
                pluck="name",
                limit=1
            )
            if users:
                valid_users.append(users[0])

    return list(set(valid_users))


@frappe.whitelist()
def get_users_for_mention(search: str = "", limit: int = 10) -> list:
    """
    Get users for @mention autocomplete.

    Args:
        search: Search string
        limit: Max results

    Returns:
        list: Users with name, full_name, user_image
    """
    limit = int(limit)

    filters = {"enabled": 1, "user_type": "System User"}

    if search:
        filters["full_name"] = ["like", f"%{search}%"]

    users = frappe.get_all(
        "User",
        filters=filters,
        fields=["name", "full_name", "user_image"],
        order_by="full_name",
        limit_page_length=limit
    )

    return users


# ============================================================================
# ADMIN DELETE
# ============================================================================

@frappe.whitelist()
def delete_activity(doctype: str, docname: str) -> dict:
    """
    Delete activity record (admin only).

    Note: This deletes associated comments/notes, not the source document.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: Success status
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only administrators can delete activities"), frappe.PermissionError)

    # Delete associated Info comments (notes)
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": doctype,
            "reference_name": docname,
            "comment_type": "Info"
        },
        pluck="name"
    )

    for comment in comments:
        frappe.delete_doc("Comment", comment, ignore_permissions=True)

    # Clear user preferences for all users
    safe_doctype = doctype.replace(" ", "_")
    try:
        frappe.db.sql("""
            DELETE FROM `tabDefaultValue`
            WHERE defkey LIKE %s
        """, f"activity_%_{safe_doctype}_{docname}")
    except Exception:
        # Ignore errors if table doesn't exist or other issues
        pass

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Activity data deleted successfully"),
        "deleted_notes": len(comments)
    }


# ============================================================================
# REACTIONS
# ============================================================================

VALID_REACTION_TYPES = ["acknowledge", "celebrate", "seen", "flag"]


@frappe.whitelist()
def toggle_reaction(doctype: str, docname: str, reaction_type: str) -> dict:
    """
    Toggle a reaction on an activity.

    If the reaction exists, it will be removed. If not, it will be added.

    Args:
        doctype: Reference document type
        docname: Reference document name
        reaction_type: One of: acknowledge, celebrate, seen, flag

    Returns:
        dict: {reacted: bool, counts: dict, users: dict, user_reactions: list}
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if reaction_type not in VALID_REACTION_TYPES:
        frappe.throw(_("Invalid reaction type. Must be one of: {0}").format(
            ", ".join(VALID_REACTION_TYPES)
        ))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    # Check if reaction exists
    existing = frappe.db.get_value("Orga Activity Reaction", {
        "reference_doctype": doctype,
        "reference_name": docname,
        "user": frappe.session.user,
        "reaction_type": reaction_type
    }, "name")

    if existing:
        # Remove reaction (toggle off)
        frappe.delete_doc("Orga Activity Reaction", existing, ignore_permissions=True)
        reacted = False
    else:
        # Remove any other reaction by this user on the same activity (one reaction per user)
        other_reactions = frappe.get_all("Orga Activity Reaction", filters={
            "reference_doctype": doctype,
            "reference_name": docname,
            "user": frappe.session.user,
            "reaction_type": ["!=", reaction_type]
        }, pluck="name")
        for r in other_reactions:
            frappe.delete_doc("Orga Activity Reaction", r, ignore_permissions=True)

        # Add new reaction
        frappe.get_doc({
            "doctype": "Orga Activity Reaction",
            "reference_doctype": doctype,
            "reference_name": docname,
            "user": frappe.session.user,
            "reaction_type": reaction_type
        }).insert(ignore_permissions=True)
        reacted = True

    # Get updated reaction data
    reaction_data = get_reactions(doctype, docname)

    return {
        "reacted": reacted,
        **reaction_data
    }


@frappe.whitelist()
def get_reactions(doctype: str, docname: str) -> dict:
    """
    Get reaction counts and users for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: {counts: {type: count}, users: {type: [user_info]}, user_reactions: [types]}
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    reactions = frappe.get_all(
        "Orga Activity Reaction",
        filters={
            "reference_doctype": doctype,
            "reference_name": docname
        },
        fields=["reaction_type", "user"]
    )

    counts = {}
    users = {}
    user_reactions = []

    for r in reactions:
        rtype = r["reaction_type"]

        # Count
        counts[rtype] = counts.get(rtype, 0) + 1

        # User info (limit to 5 per type for display)
        if rtype not in users:
            users[rtype] = []
        if len(users[rtype]) < 5:
            users[rtype].append({
                "user": r["user"],
                "user_fullname": frappe.db.get_value("User", r["user"], "full_name") or r["user"]
            })

        # Current user's reactions
        if r["user"] == frappe.session.user:
            user_reactions.append(rtype)

    return {
        "counts": counts,
        "users": users,
        "user_reactions": user_reactions
    }


def get_activity_reaction_summary(doctype: str, docname: str) -> dict:
    """
    Get a summary of reactions for an activity (for embedding in activity list).

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: {counts: {type: count}, user_reactions: [types]}
    """
    try:
        reactions = frappe.get_all(
            "Orga Activity Reaction",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname
            },
            fields=["reaction_type", "user"]
        )

        counts = {}
        user_reactions = []

        for r in reactions:
            rtype = r["reaction_type"]
            counts[rtype] = counts.get(rtype, 0) + 1
            if r["user"] == frappe.session.user:
                user_reactions.append(rtype)

        return {
            "counts": counts,
            "user_reactions": user_reactions
        }
    except Exception:
        # Return empty if table doesn't exist yet
        return {"counts": {}, "user_reactions": []}


# ============================================================================
# DUE DILIGENCE NOTES
# ============================================================================

VALID_NOTE_TYPES = ["General", "Due Diligence", "Offer", "Decision"]
VALID_VISIBILITY_LEVELS = ["Internal", "Team", "Public"]


@frappe.whitelist()
def add_due_diligence_note(
    doctype: str,
    docname: str,
    content: str,
    note_type: str = "Due Diligence",
    visibility: str = "Internal",
    related_company: str = None
) -> dict:
    """
    Add a due diligence or typed note to an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name
        content: Note content
        note_type: One of: General, Due Diligence, Offer, Decision
        visibility: One of: Internal, Team, Public
        related_company: Optional company name for linking

    Returns:
        dict: Created note with user details
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not content or not content.strip():
        frappe.throw(_("Note content is required"))

    if note_type not in VALID_NOTE_TYPES:
        frappe.throw(_("Invalid note type. Must be one of: {0}").format(
            ", ".join(VALID_NOTE_TYPES)
        ))

    if visibility not in VALID_VISIBILITY_LEVELS:
        frappe.throw(_("Invalid visibility. Must be one of: {0}").format(
            ", ".join(VALID_VISIBILITY_LEVELS)
        ))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    # Parse @mentions
    mentions = _parse_mentions(content.strip())

    comment = frappe.get_doc({
        "doctype": "Orga Activity Comment",
        "reference_doctype": doctype,
        "reference_name": docname,
        "user": frappe.session.user,
        "content": content.strip(),
        "note_type": note_type,
        "visibility": visibility,
        "related_company": related_company
    })

    # Add mention child records
    for mentioned_user in mentions:
        comment.append("mentions", {"user": mentioned_user})

    comment.insert(ignore_permissions=True)

    # Notify mentioned users and team for Due Diligence notes
    for mentioned_user in mentions:
        _notify_mention(mentioned_user, comment)

    # Notify document owner for Due Diligence notes
    if note_type == "Due Diligence":
        _notify_due_diligence(doctype, docname, comment)

    return {
        "name": comment.name,
        "user": comment.user,
        "user_fullname": frappe.db.get_value("User", comment.user, "full_name") or comment.user,
        "user_image": frappe.db.get_value("User", comment.user, "user_image"),
        "content": comment.content,
        "creation": str(comment.creation),
        "note_type": comment.note_type,
        "visibility": comment.visibility,
        "related_company": comment.related_company,
        "can_delete": True
    }


@frappe.whitelist()
def get_due_diligence_notes(
    doctype: str,
    docname: str,
    note_type: str = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    Get typed notes for an activity (due diligence, offers, decisions).

    Args:
        doctype: Reference document type
        docname: Reference document name
        note_type: Filter by note type (optional)
        limit: Max notes to return (default 20)
        offset: Pagination offset (default 0)

    Returns:
        dict: {notes: list, has_more: bool, total: int, type_counts: dict}
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    limit = int(limit)
    offset = int(offset)

    # Build filters
    filters = {
        "reference_doctype": doctype,
        "reference_name": docname,
        "parent_comment": ["is", "not set"]  # Only top-level
    }

    # Filter by note type if specified
    if note_type and note_type in VALID_NOTE_TYPES:
        filters["note_type"] = note_type

    # Filter by visibility based on user access
    visibility_filter = _get_visibility_filter()
    if visibility_filter:
        filters["visibility"] = ["in", visibility_filter]

    total = frappe.db.count("Orga Activity Comment", filters)

    notes = frappe.get_all(
        "Orga Activity Comment",
        filters=filters,
        fields=["name", "user", "content", "creation", "note_type", "visibility", "related_company"],
        order_by="creation desc",
        limit_page_length=limit,
        limit_start=offset
    )

    # Add user details
    for note in notes:
        note["user_fullname"] = frappe.db.get_value("User", note["user"], "full_name") or note["user"]
        note["user_image"] = frappe.db.get_value("User", note["user"], "user_image")
        note["creation"] = str(note["creation"]) if note["creation"] else None
        note["can_delete"] = (
            note["user"] == frappe.session.user or
            "System Manager" in frappe.get_roles()
        )

    # Get counts by type
    type_counts = _get_note_type_counts(doctype, docname, visibility_filter)

    return {
        "notes": notes,
        "has_more": offset + len(notes) < total,
        "total": total,
        "type_counts": type_counts
    }


@frappe.whitelist()
def get_compliance_status(doctype: str, docname: str) -> dict:
    """
    Get compliance/due diligence completion status for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        dict: {
            has_due_diligence: bool,
            due_diligence_count: int,
            has_decision: bool,
            is_flagged: bool,
            last_note_date: str,
            checklist_progress: float
        }
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    # Get note type counts
    visibility_filter = _get_visibility_filter()
    type_counts = _get_note_type_counts(doctype, docname, visibility_filter)

    # Check if flagged (has flag reaction)
    is_flagged = frappe.db.exists("Orga Activity Reaction", {
        "reference_doctype": doctype,
        "reference_name": docname,
        "reaction_type": "flag"
    })

    # Get last note date
    last_note = frappe.db.get_value(
        "Orga Activity Comment",
        {
            "reference_doctype": doctype,
            "reference_name": docname,
            "note_type": "Due Diligence"
        },
        "creation",
        order_by="creation desc"
    )

    # Calculate checklist progress (based on standard items)
    # This is a simplified version - could be expanded with actual checklist items
    checklist_items = ["Due Diligence", "Offer", "Decision"]
    completed = sum(1 for item in checklist_items if type_counts.get(item, 0) > 0)
    checklist_progress = (completed / len(checklist_items)) * 100 if checklist_items else 0

    return {
        "has_due_diligence": type_counts.get("Due Diligence", 0) > 0,
        "due_diligence_count": type_counts.get("Due Diligence", 0),
        "has_decision": type_counts.get("Decision", 0) > 0,
        "has_offer": type_counts.get("Offer", 0) > 0,
        "is_flagged": bool(is_flagged),
        "last_note_date": str(last_note) if last_note else None,
        "checklist_progress": checklist_progress,
        "type_counts": type_counts
    }


def _get_visibility_filter() -> list:
    """
    Get visibility levels accessible to current user.

    Returns:
        list: Visibility levels the user can see
    """
    # System Manager can see all
    if "System Manager" in frappe.get_roles():
        return VALID_VISIBILITY_LEVELS

    # Default: Internal and Team visible to all authenticated users
    # Public would be visible to guests (if implemented)
    return ["Internal", "Team", "Public"]


def _get_note_type_counts(doctype: str, docname: str, visibility_filter: list = None) -> dict:
    """
    Get counts of notes by type for an activity.

    Args:
        doctype: Reference document type
        docname: Reference document name
        visibility_filter: Optional visibility filter

    Returns:
        dict: {note_type: count}
    """
    filters = {
        "reference_doctype": doctype,
        "reference_name": docname,
        "parent_comment": ["is", "not set"]
    }

    if visibility_filter:
        filters["visibility"] = ["in", visibility_filter]

    notes = frappe.get_all(
        "Orga Activity Comment",
        filters=filters,
        fields=["note_type"]
    )

    counts = {}
    for note in notes:
        ntype = note.get("note_type") or "General"
        counts[ntype] = counts.get(ntype, 0) + 1

    return counts


def _notify_mention(user: str, comment) -> None:
    """
    Send notification to mentioned user.

    Args:
        user: User to notify
        comment: Comment document
    """
    if user == frappe.session.user:
        return  # Don't notify self

    frappe.publish_realtime(
        "mention_notification",
        {
            "from_user": frappe.session.user,
            "from_user_name": frappe.db.get_value("User", frappe.session.user, "full_name"),
            "reference_doctype": comment.reference_doctype,
            "reference_name": comment.reference_name,
            "comment": comment.name,
            "content_preview": comment.content[:100] if comment.content else ""
        },
        user=user
    )


def _notify_due_diligence(doctype: str, docname: str, comment) -> None:
    """
    Send notification for due diligence notes.

    Args:
        doctype: Reference document type
        docname: Reference document name
        comment: Comment document
    """
    # Get document owner
    owner = frappe.db.get_value(doctype, docname, "owner")

    if owner and owner != frappe.session.user:
        frappe.publish_realtime(
            "due_diligence_note",
            {
                "from_user": frappe.session.user,
                "from_user_name": frappe.db.get_value("User", frappe.session.user, "full_name"),
                "reference_doctype": doctype,
                "reference_name": docname,
                "note_type": comment.note_type,
                "content_preview": comment.content[:100] if comment.content else "",
                "related_company": comment.related_company
            },
            user=owner
        )


# ============================================================================
# READ / UNREAD STATE
# ============================================================================

@frappe.whitelist()
def mark_activity_viewed() -> dict:
    """
    Store current timestamp as the user's last activity view time.

    Called when the user leaves the Activity page to mark everything as read.

    Returns:
        dict: {last_viewed: str}
    """
    from frappe.utils import now_datetime

    ts = str(now_datetime())
    frappe.defaults.set_user_default("activity_last_viewed", ts)
    return {"last_viewed": ts}


@frappe.whitelist()
def get_activity_last_viewed() -> dict:
    """
    Get the user's last activity view timestamp.

    Returns:
        dict: {last_viewed: str | None}
    """
    last_viewed = frappe.defaults.get_user_default("activity_last_viewed")
    return {"last_viewed": last_viewed}


@frappe.whitelist()
def get_unread_activity_count() -> int:
    """
    Count activities newer than the user's last viewed timestamp.

    Checks Orga Task, Orga Milestone, and Orga Appointment modifications.

    Returns:
        int: Number of unread activities (capped at 99)
    """
    last_viewed = frappe.defaults.get_user_default("activity_last_viewed")
    if not last_viewed:
        return 0

    count = 0
    for dt in ("Orga Task", "Orga Milestone", "Orga Appointment"):
        try:
            count += frappe.db.count(dt, {"modified": [">", last_viewed]})
        except Exception:
            pass  # DocType may not exist yet

    return min(count, 99)


# ============================================================================
# RELATED DOCUMENTS
# ============================================================================

@frappe.whitelist()
def get_related_documents(doctype: str, docname: str) -> list:
    """
    Get related/linked documents for an activity.

    Finds documents that are linked to this document through:
    - Link fields on the source document
    - Child tables with references
    - Explicit link doctypes

    Args:
        doctype: Reference document type
        docname: Reference document name

    Returns:
        list: Related documents with doctype, name, title, relationship
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    if not frappe.db.exists(doctype, docname):
        frappe.throw(_("{0} {1} not found").format(doctype, docname), frappe.DoesNotExistError)

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    related = []

    # Get the source document
    doc = frappe.get_doc(doctype, docname)

    # Define Orga doctypes and their title/name fields
    orga_doctypes = {
        "Orga Project": {"title_field": "project_name", "link_field": "project"},
        "Orga Task": {"title_field": "subject", "link_field": "task"},
        "Orga Resource": {"title_field": "resource_name", "link_field": "resource"},
        "Orga Appointment": {"title_field": "subject", "link_field": "appointment"},
        "Orga Milestone": {"title_field": "milestone_name", "link_field": "milestone"}
    }

    # Check link fields on the document
    meta = frappe.get_meta(doctype)
    for df in meta.get_link_fields():
        if df.options in orga_doctypes and hasattr(doc, df.fieldname):
            linked_name = getattr(doc, df.fieldname)
            if linked_name and frappe.db.exists(df.options, linked_name):
                config = orga_doctypes[df.options]
                title = frappe.db.get_value(df.options, linked_name, config["title_field"]) or linked_name
                related.append({
                    "doctype": df.options,
                    "name": linked_name,
                    "title": title,
                    "relationship": "parent"
                })

    # Check for child documents (documents that link to this one)
    for target_doctype, config in orga_doctypes.items():
        if target_doctype == doctype:
            continue  # Skip self

        target_meta = frappe.get_meta(target_doctype)
        for df in target_meta.get_link_fields():
            if df.options == doctype:
                # Find documents that link to this one
                children = frappe.get_all(
                    target_doctype,
                    filters={df.fieldname: docname},
                    fields=["name", config["title_field"]],
                    limit=10
                )
                for child in children:
                    # Avoid duplicates
                    if not any(r["doctype"] == target_doctype and r["name"] == child["name"] for r in related):
                        related.append({
                            "doctype": target_doctype,
                            "name": child["name"],
                            "title": child.get(config["title_field"]) or child["name"],
                            "relationship": "child"
                        })

    # Check for linked tasks (if this is a project)
    if doctype == "Orga Project":
        tasks = frappe.get_all(
            "Orga Task",
            filters={"project": docname},
            fields=["name", "subject", "status"],
            limit=5
        )
        for task in tasks:
            if not any(r["doctype"] == "Orga Task" and r["name"] == task["name"] for r in related):
                related.append({
                    "doctype": "Orga Task",
                    "name": task["name"],
                    "title": task["subject"],
                    "status": task["status"],
                    "relationship": "child"
                })

    # Check for linked appointments (if this is a project or task)
    if doctype in ["Orga Project", "Orga Task"]:
        link_field = "project" if doctype == "Orga Project" else "task"
        appointments = frappe.get_all(
            "Orga Appointment",
            filters={link_field: docname},
            fields=["name", "subject"],
            limit=5
        )
        for appt in appointments:
            if not any(r["doctype"] == "Orga Appointment" and r["name"] == appt["name"] for r in related):
                related.append({
                    "doctype": "Orga Appointment",
                    "name": appt["name"],
                    "title": appt["subject"],
                    "relationship": "linked"
                })

    return related


# ============================================================================
# ACTIVITY SOURCE DOCUMENT DETAILS (for Overview tab)
# ============================================================================

@frappe.whitelist()
def get_source_document_info(doctype: str, docname: str) -> dict:
    """
    Get key fields from the source document for the Activity Overview tab.

    Returns type-specific data depending on the doctype:
    - Orga Task: status, priority, assigned_to, due_date, project, progress, description, checklist stats
    - Orga Milestone: status, due_date, project, description, task completion stats
    - Orga Appointment: event_type, start_datetime, end_datetime, location, description, RSVP info
    - Orga Project: status, progress, start_date, end_date, budget, team count, task stats

    Args:
        doctype: Source document type
        docname: Source document name

    Returns:
        dict: Type-specific document fields
    """
    if not doctype or not docname:
        frappe.throw(_("Both doctype and docname are required"))

    try:
        if not frappe.db.exists(doctype, docname):
            return {"exists": False}
    except Exception:
        frappe.log_error(f"DB error checking existence of {doctype} {docname}")
        return {"exists": False, "error": "Database schema error. Please run bench migrate."}

    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    try:
        doc = frappe.get_doc(doctype, docname)
    except Exception:
        frappe.log_error(f"DB error loading {doctype} {docname}")
        return {"exists": True, "error": "Failed to load document. Please run bench migrate."}

    result: dict = {"exists": True, "doctype": doctype, "name": docname}

    if doctype == "Orga Task":
        result.update(_get_task_info(doc))
    elif doctype == "Orga Milestone":
        result.update(_get_milestone_info(doc))
    elif doctype == "Orga Appointment":
        result.update(_get_appointment_info(doc))
    elif doctype == "Orga Project":
        result.update(_get_project_info(doc))

    return result


def _get_task_info(doc) -> dict:
    """Extract task-specific fields for Overview tab."""
    # Get assigned user info
    assigned_user_name = None
    assigned_user_image = None
    if doc.get("assigned_to"):
        user_info = frappe.db.get_value(
            "User", doc.assigned_to, ["full_name", "user_image"], as_dict=True
        )
        if user_info:
            assigned_user_name = user_info.full_name
            assigned_user_image = user_info.user_image

    # Checklist stats
    checklist_total = 0
    checklist_done = 0
    if frappe.db.exists("DocType", "Orga Task Checklist"):
        checklist_items = frappe.get_all(
            "Orga Task Checklist",
            filters={"parent": doc.name, "parenttype": "Orga Task"},
            fields=["completed"]
        )
        checklist_total = len(checklist_items)
        checklist_done = sum(1 for item in checklist_items if item.get("completed"))

    return {
        "subject": doc.get("subject"),
        "status": doc.get("status"),
        "priority": doc.get("priority"),
        "assigned_to": doc.get("assigned_to"),
        "assigned_user_name": assigned_user_name,
        "assigned_user_image": assigned_user_image,
        "due_date": str(doc.get("due_date")) if doc.get("due_date") else None,
        "project": doc.get("project"),
        "project_name": frappe.db.get_value("Orga Project", doc.get("project"), "project_name") if doc.get("project") else None,
        "progress": doc.get("progress") or 0,
        "description": (doc.get("description") or "")[:300],
        "estimated_hours": doc.get("estimated_hours") or 0,
        "actual_hours": doc.get("actual_hours") or 0,
        "checklist_total": checklist_total,
        "checklist_done": checklist_done,
    }


def _get_milestone_info(doc) -> dict:
    """Extract milestone-specific fields for Overview tab."""
    # Count tasks linked to this milestone's project
    task_total = 0
    task_done = 0
    if doc.get("project"):
        filters = {"project": doc.project}
        if doc.get("name"):
            filters["milestone"] = doc.name
        tasks = frappe.get_all("Orga Task", filters=filters, fields=["status"])
        task_total = len(tasks)
        task_done = sum(1 for t in tasks if t.status == "Completed")

    return {
        "milestone_name": doc.get("milestone_name") or doc.get("title") or doc.get("name"),
        "status": doc.get("status"),
        "due_date": str(doc.get("due_date")) if doc.get("due_date") else None,
        "project": doc.get("project"),
        "project_name": frappe.db.get_value("Orga Project", doc.get("project"), "project_name") if doc.get("project") else None,
        "description": (doc.get("description") or "")[:300],
        "task_total": task_total,
        "task_done": task_done,
    }


def _get_appointment_info(doc) -> dict:
    """Extract appointment-specific fields for Overview tab."""
    # Get attendees
    attendees = []
    attendee_stats = {"total": 0, "accepted": 0, "declined": 0, "tentative": 0, "pending": 0}
    user_rsvp_status = None

    if frappe.db.exists("DocType", "Orga Appointment Attendee"):
        raw_attendees = frappe.get_all(
            "Orga Appointment Attendee",
            filters={"parent": doc.name, "parenttype": "Orga Appointment"},
            fields=["user", "rsvp_status"]
        )
        current_user = frappe.session.user
        for att in raw_attendees:
            user_info = frappe.db.get_value("User", att.user, ["full_name", "user_image"], as_dict=True) or {}
            attendees.append({
                "user": att.user,
                "full_name": user_info.get("full_name", att.user),
                "user_image": user_info.get("user_image"),
                "rsvp_status": att.rsvp_status or "Pending",
            })
            status_key = (att.rsvp_status or "Pending").lower()
            if status_key in attendee_stats:
                attendee_stats[status_key] += 1
            attendee_stats["total"] += 1
            if att.user == current_user:
                user_rsvp_status = att.rsvp_status or "Pending"

    return {
        "subject": doc.get("subject"),
        "event_type": doc.get("event_type"),
        "start_datetime": str(doc.get("start_datetime")) if doc.get("start_datetime") else None,
        "end_datetime": str(doc.get("end_datetime")) if doc.get("end_datetime") else None,
        "location": doc.get("location"),
        "description": (doc.get("description") or "")[:300],
        "project": doc.get("project"),
        "project_name": frappe.db.get_value("Orga Project", doc.get("project"), "project_name") if doc.get("project") else None,
        "attendees": attendees,
        "attendee_stats": attendee_stats,
        "user_rsvp_status": user_rsvp_status,
    }


def _get_project_info(doc) -> dict:
    """Extract project-specific fields for Overview tab."""
    # Task stats
    tasks = frappe.get_all("Orga Task", filters={"project": doc.name}, fields=["status"])
    task_total = len(tasks)
    task_open = sum(1 for t in tasks if t.status in ("Open", "Working"))
    task_done = sum(1 for t in tasks if t.status == "Completed")
    task_overdue = 0

    from frappe.utils import getdate, nowdate
    overdue_tasks = frappe.get_all(
        "Orga Task",
        filters={
            "project": doc.name,
            "status": ["not in", ["Completed", "Cancelled"]],
            "due_date": ["<", nowdate()]
        }
    )
    task_overdue = len(overdue_tasks)

    # Team count (unique assigned users)
    assigned_users = frappe.get_all(
        "Orga Task",
        filters={"project": doc.name, "assigned_to": ["is", "set"]},
        fields=["assigned_to"],
        distinct=True
    )
    team_count = len(assigned_users)

    return {
        "project_name": doc.get("project_name"),
        "status": doc.get("status"),
        "progress": doc.get("progress") or 0,
        "start_date": str(doc.get("start_date")) if doc.get("start_date") else None,
        "end_date": str(doc.get("end_date")) if doc.get("end_date") else None,
        "budget": doc.get("budget") or 0,
        "description": (doc.get("description") or "")[:300],
        "task_total": task_total,
        "task_open": task_open,
        "task_done": task_done,
        "task_overdue": task_overdue,
        "team_count": team_count,
    }
