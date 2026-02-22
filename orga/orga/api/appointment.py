# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Appointment API endpoints for Orga.

Usage from frontend:
    frappe.call({
        method: 'orga.orga.api.appointment.get_appointments',
        args: { project: 'ORG-2026-0001' }
    })
"""

import json
import frappe
from frappe import _
from frappe.utils import today, add_days, get_datetime, getdate


@frappe.whitelist()
def get_appointments(
    project=None,
    event_type=None,
    status=None,
    start_date=None,
    end_date=None,
    resource=None,
    limit=100,
    offset=0
):
    """
    Get list of appointments with optional filters.

    Args:
        project: Filter by project
        event_type: Filter by type (Meeting, Deadline, etc.)
        status: Filter by status (Scheduled, Completed, Cancelled)
        start_date: Filter events on or after this date
        end_date: Filter events on or before this date
        resource: Filter by attendee resource
        limit: Max results (default 100)
        offset: Pagination offset

    Returns:
        dict: {appointments: [...], total: int}
    """
    filters = {}
    if project:
        filters["project"] = project
    if event_type:
        filters["event_type"] = event_type
    if status:
        filters["status"] = status
    if start_date:
        filters["start_datetime"] = [">=", start_date]
    if end_date:
        if "start_datetime" in filters:
            filters["start_datetime"] = ["between", [start_date, end_date + " 23:59:59"]]
        else:
            filters["start_datetime"] = ["<=", end_date + " 23:59:59"]

    appointments = frappe.get_all(
        "Orga Appointment",
        filters=filters,
        fields=[
            "name", "title", "event_type", "status", "all_day",
            "start_datetime", "end_datetime", "duration_minutes",
            "project", "task", "location", "meeting_url", "color"
        ],
        order_by="start_datetime asc",
        limit_page_length=int(limit),
        limit_start=int(offset)
    )

    total = frappe.db.count("Orga Appointment", filters)

    # Enrich with project name and attendee count
    for apt in appointments:
        if apt.get("project"):
            apt["project_name"] = frappe.db.get_value(
                "Orga Project", apt["project"], "project_name"
            )

        # Get attendee count
        apt["attendee_count"] = frappe.db.count(
            "Orga Appointment Attendee",
            {"parent": apt["name"]}
        )

    # Post-filter by resource if specified
    if resource:
        resource_appointments = frappe.get_all(
            "Orga Appointment Attendee",
            filters={"resource": resource},
            fields=["parent"],
            pluck="parent"
        )
        appointments = [a for a in appointments if a["name"] in resource_appointments]

    return {
        "appointments": appointments,
        "total": total
    }


@frappe.whitelist()
def get_appointment(name):
    """
    Get single appointment with full details.

    Args:
        name: Appointment name/ID

    Returns:
        dict: Appointment data with attendees
    """
    if not name:
        frappe.throw(_("Appointment name is required"))

    if not frappe.db.exists("Orga Appointment", name):
        frappe.throw(_("Appointment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Appointment", name)
    appointment = doc.as_dict()

    # Get attendees with resource details
    attendees = []
    for attendee in doc.attendees:
        resource = frappe.get_doc("Orga Resource", attendee.resource)
        attendees.append({
            "name": attendee.name,
            "resource": attendee.resource,
            "resource_name": resource.resource_name,
            "email": resource.email,
            "rsvp_status": attendee.rsvp_status,
            "required": attendee.required,
            "notes": attendee.notes,
            "initials": get_initials(resource.resource_name)
        })

    appointment["attendees"] = attendees

    # Get project/task names
    if appointment.get("project"):
        appointment["project_name"] = frappe.db.get_value(
            "Orga Project", appointment["project"], "project_name"
        )
    if appointment.get("task"):
        appointment["task_subject"] = frappe.db.get_value(
            "Orga Task", appointment["task"], "subject"
        )

    return appointment


@frappe.whitelist()
def create_appointment(data):
    """
    Create a new appointment.

    Args:
        data: dict or JSON string with appointment fields

    Returns:
        dict: Created appointment data
    """
    if isinstance(data, str):
        data = json.loads(data)

    required_fields = ["title", "start_datetime"]
    for field in required_fields:
        if not data.get(field):
            frappe.throw(_("{0} is required").format(field))

    # Handle attendees
    attendees = data.pop("attendees", [])

    allowed_fields = [
        "title", "event_type", "status", "all_day",
        "start_datetime", "end_datetime", "location", "meeting_url",
        "project", "task", "milestone", "description", "color",
        "send_reminder", "reminder_minutes"
    ]

    doc_data = {"doctype": "Orga Appointment"}
    for field in allowed_fields:
        if field in data:
            doc_data[field] = data[field]

    doc = frappe.get_doc(doc_data)

    # Add attendees
    for attendee in attendees:
        doc.append("attendees", {
            "resource": attendee.get("resource"),
            "rsvp_status": attendee.get("rsvp_status", "Pending"),
            "required": attendee.get("required", 1)
        })

    doc.insert()
    frappe.db.commit()

    return get_appointment(doc.name)


@frappe.whitelist()
def update_appointment(name, data):
    """
    Update an appointment.

    Args:
        name: Appointment name/ID
        data: dict or JSON string with fields to update

    Returns:
        dict: Updated appointment data
    """
    if not name:
        frappe.throw(_("Appointment name is required"))

    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.db.exists("Orga Appointment", name):
        frappe.throw(_("Appointment {0} not found").format(name), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Appointment", name)

    allowed_fields = [
        "title", "event_type", "status", "all_day",
        "start_datetime", "end_datetime", "location", "meeting_url",
        "project", "task", "milestone", "description", "color",
        "send_reminder", "reminder_minutes"
    ]

    for field, value in data.items():
        if field in allowed_fields:
            setattr(doc, field, value)

    doc.save()
    frappe.db.commit()

    return get_appointment(doc.name)


@frappe.whitelist()
def delete_appointment(name):
    """
    Delete an appointment.

    Args:
        name: Appointment name/ID

    Returns:
        dict: {success: True}
    """
    if not name:
        frappe.throw(_("Appointment name is required"))

    if not frappe.db.exists("Orga Appointment", name):
        frappe.throw(_("Appointment {0} not found").format(name), frappe.DoesNotExistError)

    frappe.delete_doc("Orga Appointment", name)
    frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def get_calendar_events(start_date, end_date, project=None, resource=None, event_type=None):
    """
    Get events formatted for calendar display.

    Args:
        start_date: Period start (YYYY-MM-DD)
        end_date: Period end (YYYY-MM-DD)
        project: Optional project filter
        resource: Optional resource/attendee filter
        event_type: Optional event type filter

    Returns:
        list: Calendar-formatted events
    """
    filters = {
        "status": ["!=", "Cancelled"],
        "start_datetime": ["between", [start_date, end_date + " 23:59:59"]]
    }

    if project:
        filters["project"] = project
    if event_type:
        filters["event_type"] = event_type

    appointments = frappe.get_all(
        "Orga Appointment",
        filters=filters,
        fields=["name"]
    )

    events = []
    for apt in appointments:
        doc = frappe.get_doc("Orga Appointment", apt.name)

        # Filter by resource if specified
        if resource:
            attendee_resources = [a.resource for a in doc.attendees]
            if resource not in attendee_resources:
                continue

        events.append(doc.get_calendar_event_data())

    return events


@frappe.whitelist()
def get_my_appointments(status=None, upcoming_only=True, limit=20):
    """
    Get appointments for the current user.

    Args:
        status: Filter by status
        upcoming_only: Only show future appointments (default: True)
        limit: Max results

    Returns:
        list: User's appointments
    """
    # Get current user's resource
    user_resource = frappe.db.get_value(
        "Orga Resource",
        {"user": frappe.session.user},
        "name"
    )

    if not user_resource:
        return []

    # Find appointments where user is an attendee
    attendee_entries = frappe.get_all(
        "Orga Appointment Attendee",
        filters={"resource": user_resource},
        fields=["parent"],
        pluck="parent"
    )

    if not attendee_entries:
        return []

    filters = {"name": ["in", attendee_entries]}

    if status:
        filters["status"] = status

    if upcoming_only:
        filters["start_datetime"] = [">=", today()]

    appointments = frappe.get_all(
        "Orga Appointment",
        filters=filters,
        fields=[
            "name", "title", "event_type", "status",
            "start_datetime", "end_datetime", "location",
            "project", "color"
        ],
        order_by="start_datetime asc",
        limit_page_length=int(limit)
    )

    # Enrich with RSVP status
    for apt in appointments:
        rsvp = frappe.db.get_value(
            "Orga Appointment Attendee",
            {"parent": apt["name"], "resource": user_resource},
            "rsvp_status"
        )
        apt["my_rsvp"] = rsvp

        if apt.get("project"):
            apt["project_name"] = frappe.db.get_value(
                "Orga Project", apt["project"], "project_name"
            )

    return appointments


@frappe.whitelist()
def update_rsvp(appointment_name, rsvp_status):
    """
    Update RSVP status for current user.

    Args:
        appointment_name: Appointment name/ID
        rsvp_status: New status (Accepted, Declined, Tentative)

    Returns:
        dict: {success: True, rsvp_status: ...}
    """
    if not appointment_name:
        frappe.throw(_("Appointment name is required"))

    if rsvp_status not in ["Pending", "Accepted", "Declined", "Tentative"]:
        frappe.throw(_("Invalid RSVP status"))

    # Get current user's resource
    user_resource = frappe.db.get_value(
        "Orga Resource",
        {"user": frappe.session.user},
        "name"
    )

    if not user_resource:
        frappe.throw(_("You are not linked to any resource"))

    # Find attendee entry
    attendee = frappe.db.get_value(
        "Orga Appointment Attendee",
        {"parent": appointment_name, "resource": user_resource},
        "name"
    )

    if not attendee:
        frappe.throw(_("You are not an attendee of this appointment"))

    # Update RSVP
    frappe.db.set_value(
        "Orga Appointment Attendee",
        attendee,
        "rsvp_status",
        rsvp_status
    )
    frappe.db.commit()

    return {"success": True, "rsvp_status": rsvp_status}


@frappe.whitelist()
def add_attendee(appointment_name, resource, required=1):
    """
    Add an attendee to an appointment.

    Args:
        appointment_name: Appointment name/ID
        resource: Resource name/ID
        required: Is attendance required (default: 1)

    Returns:
        dict: Attendee data
    """
    if not appointment_name or not resource:
        frappe.throw(_("Appointment and resource are required"))

    if not frappe.db.exists("Orga Appointment", appointment_name):
        frappe.throw(_("Appointment not found"), frappe.DoesNotExistError)

    if not frappe.db.exists("Orga Resource", resource):
        frappe.throw(_("Resource not found"), frappe.DoesNotExistError)

    # Check if already an attendee
    existing = frappe.db.exists(
        "Orga Appointment Attendee",
        {"parent": appointment_name, "resource": resource}
    )
    if existing:
        frappe.throw(_("Resource is already an attendee"))

    doc = frappe.get_doc("Orga Appointment", appointment_name)
    doc.append("attendees", {
        "resource": resource,
        "rsvp_status": "Pending",
        "required": required
    })
    doc.save()
    frappe.db.commit()

    return get_appointment(appointment_name)


@frappe.whitelist()
def remove_attendee(appointment_name, resource):
    """
    Remove an attendee from an appointment.

    Args:
        appointment_name: Appointment name/ID
        resource: Resource name/ID

    Returns:
        dict: {success: True}
    """
    if not appointment_name or not resource:
        frappe.throw(_("Appointment and resource are required"))

    doc = frappe.get_doc("Orga Appointment", appointment_name)
    doc.attendees = [a for a in doc.attendees if a.resource != resource]
    doc.save()
    frappe.db.commit()

    return {"success": True}


def get_initials(name):
    """Helper to get initials from a name"""
    if not name:
        return "?"
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


@frappe.whitelist()
def send_invitations(appointment_name):
    """
    Send email invitations to all attendees of an appointment.

    Args:
        appointment_name: Appointment name/ID

    Returns:
        dict: {success: True, sent_count: int, failed: []}
    """
    if not appointment_name:
        frappe.throw(_("Appointment name is required"))

    if not frappe.db.exists("Orga Appointment", appointment_name):
        frappe.throw(_("Appointment not found"), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Appointment", appointment_name)

    if not doc.attendees:
        return {"success": True, "sent_count": 0, "failed": []}

    # Get organizer info
    organizer_name = "Orga"
    if doc.created_by:
        organizer_name = frappe.db.get_value("User", doc.created_by, "full_name") or doc.created_by

    # Format appointment details
    start_dt = get_datetime(doc.start_datetime)
    formatted_date = start_dt.strftime("%A, %B %d, %Y")
    formatted_time = start_dt.strftime("%I:%M %p")

    # Get project name
    project_name = None
    if doc.project:
        project_name = frappe.db.get_value("Orga Project", doc.project, "project_name")

    sent_count = 0
    failed = []

    for attendee in doc.attendees:
        resource = frappe.db.get_value(
            "Orga Resource",
            attendee.resource,
            ["resource_name", "email"],
            as_dict=True
        )

        if not resource or not resource.email:
            failed.append({
                "resource": attendee.resource,
                "reason": "No email address"
            })
            continue

        try:
            send_invitation_email(
                recipient=resource.email,
                recipient_name=resource.resource_name,
                appointment=doc,
                organizer_name=organizer_name,
                project_name=project_name,
                formatted_date=formatted_date,
                formatted_time=formatted_time,
                is_required=attendee.required
            )
            sent_count += 1
        except Exception as e:
            failed.append({
                "resource": attendee.resource,
                "reason": str(e)
            })
            frappe.log_error(
                message=f"Failed to send invitation to {resource.email}: {str(e)}",
                title="Orga Appointment Invitation Error"
            )

    return {
        "success": True,
        "sent_count": sent_count,
        "failed": failed
    }


def send_invitation_email(recipient, recipient_name, appointment, organizer_name,
                          project_name, formatted_date, formatted_time, is_required):
    """
    Send an invitation email to a single attendee.

    Args:
        recipient: Email address
        recipient_name: Name of recipient
        appointment: Appointment document
        organizer_name: Name of the meeting organizer
        project_name: Project name if applicable
        formatted_date: Human-readable date string
        formatted_time: Human-readable time string
        is_required: Whether attendance is required
    """
    subject = _("Invitation: {0} - {1} at {2}").format(appointment.title, formatted_date, formatted_time)

    # Build attendance requirement string
    attendance_type = _("Required") if is_required else _("Optional")

    # Build location info
    location_info = ""
    if appointment.location:
        location_info = f"<p><strong>{_('Location')}:</strong> {appointment.location}</p>"
    if appointment.meeting_url:
        location_info += f'<p><strong>{_("Meeting Link")}:</strong> <a href="{appointment.meeting_url}">{appointment.meeting_url}</a></p>'

    # Build project info
    project_info = ""
    if project_name:
        project_info = f"<p><strong>{_('Project')}:</strong> {project_name}</p>"

    # Build description
    description_info = ""
    if appointment.description:
        description_info = f"<hr><p><strong>{_('Details')}:</strong></p><div>{appointment.description}</div>"

    # Calculate end time
    end_time_info = ""
    if appointment.end_datetime:
        end_dt = get_datetime(appointment.end_datetime)
        end_time_str = end_dt.strftime("%I:%M %p")
        end_time_info = f" - {end_time_str}"

    message = f"""
    <p>{_("Hello {0}").format(recipient_name)},</p>

    <p>{_("You have been invited to the following appointment")}:</p>

    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #8B5CF6;">
        <h3 style="margin: 0 0 12px 0; color: #333;">{appointment.title}</h3>
        <p style="margin: 4px 0;"><strong>{_("Type")}:</strong> {appointment.event_type}</p>
        <p style="margin: 4px 0;"><strong>{_("Date")}:</strong> {formatted_date}</p>
        <p style="margin: 4px 0;"><strong>{_("Time")}:</strong> {formatted_time}{end_time_info}</p>
        <p style="margin: 4px 0;"><strong>{_("Organizer")}:</strong> {organizer_name}</p>
        <p style="margin: 4px 0;"><strong>{_("Your attendance")}:</strong> <span style="color: {'#dc2626' if is_required else '#6b7280'};">{attendance_type}</span></p>
        {location_info}
        {project_info}
    </div>

    {description_info}

    <p style="margin-top: 20px;">{_("Please respond to this invitation in Orga")}.</p>

    <p>{_("Best regards")},<br>Orga</p>
    """

    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        now=True
    )


@frappe.whitelist()
def create_appointment_with_invitations(data, send_invites=True):
    """
    Create a new appointment and optionally send invitations to attendees.

    Args:
        data: dict or JSON string with appointment fields
        send_invites: Whether to send email invitations (default: True)

    Returns:
        dict: Created appointment data with invitation status
    """
    if isinstance(data, str):
        data = json.loads(data)

    if isinstance(send_invites, str):
        send_invites = send_invites.lower() in ['true', '1', 'yes']

    # Create the appointment
    appointment = create_appointment(json.dumps(data))

    # Send invitations if requested and there are attendees
    invitation_result = None
    if send_invites and appointment.get("attendees"):
        try:
            invitation_result = send_invitations(appointment["name"])
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send invitations for {appointment['name']}: {str(e)}",
                title="Orga Appointment Invitation Error"
            )
            invitation_result = {
                "success": False,
                "error": str(e)
            }

    appointment["invitation_result"] = invitation_result
    return appointment


# ============================================================================
# ENHANCED RSVP API (for Activity Feed integration)
# ============================================================================

@frappe.whitelist()
def update_rsvp_enhanced(appointment: str, status: str, note: str = None) -> dict:
    """
    Update RSVP status for current user with enhanced response.

    Supports both resource-based and user-based attendee lookup.

    Args:
        appointment: Orga Appointment name
        status: One of: Accepted, Declined, Tentative, Pending
        note: Optional response note

    Returns:
        dict: {status, attendee_stats, attendees}
    """
    if not appointment:
        frappe.throw(_("Appointment name is required"))

    valid_statuses = ["Pending", "Accepted", "Declined", "Tentative"]
    if status not in valid_statuses:
        frappe.throw(_("Invalid status. Must be one of: {0}").format(", ".join(valid_statuses)))

    if not frappe.db.exists("Orga Appointment", appointment):
        frappe.throw(_("Appointment {0} not found").format(appointment), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Appointment", appointment)

    # Find current user in attendees (by user field or resource.user)
    attendee = None
    attendee_idx = None

    for idx, att in enumerate(doc.attendees):
        # Check direct user link
        if att.user == frappe.session.user:
            attendee = att
            attendee_idx = idx
            break
        # Check via resource
        if att.resource:
            resource_user = frappe.db.get_value("Orga Resource", att.resource, "user")
            if resource_user == frappe.session.user:
                attendee = att
                attendee_idx = idx
                break

    if not attendee:
        frappe.throw(_("You are not an attendee of this appointment"))

    # Update status
    old_status = attendee.rsvp_status
    attendee.rsvp_status = status
    if note:
        attendee.notes = note

    # Clear proposed times if accepting
    if status == "Accepted":
        attendee.proposed_start = None
        attendee.proposed_end = None

    doc.save(ignore_permissions=True)

    # Notify organizer of change
    if old_status != status:
        _notify_rsvp_change(doc, frappe.session.user, old_status, status)

    # Get updated attendee info
    attendees = _get_attendee_list(doc)
    stats = _get_attendee_stats(doc)

    return {
        "status": status,
        "attendee_stats": stats,
        "attendees": attendees
    }


@frappe.whitelist()
def propose_new_time(
    appointment: str,
    proposed_start: str,
    proposed_end: str,
    note: str = None
) -> dict:
    """
    Propose an alternative time for an appointment.

    Args:
        appointment: Orga Appointment name
        proposed_start: Proposed start datetime (ISO format)
        proposed_end: Proposed end datetime (ISO format)
        note: Optional note explaining the proposal

    Returns:
        dict: {status, proposed_start, proposed_end, attendee_stats}
    """
    if not appointment:
        frappe.throw(_("Appointment name is required"))

    if not proposed_start or not proposed_end:
        frappe.throw(_("Both proposed start and end times are required"))

    if not frappe.db.exists("Orga Appointment", appointment):
        frappe.throw(_("Appointment {0} not found").format(appointment), frappe.DoesNotExistError)

    doc = frappe.get_doc("Orga Appointment", appointment)

    # Find current user in attendees
    attendee = None
    for att in doc.attendees:
        if att.user == frappe.session.user:
            attendee = att
            break
        if att.resource:
            resource_user = frappe.db.get_value("Orga Resource", att.resource, "user")
            if resource_user == frappe.session.user:
                attendee = att
                break

    if not attendee:
        frappe.throw(_("You are not an attendee of this appointment"))

    # Update attendee with proposal
    attendee.rsvp_status = "Tentative"
    attendee.proposed_start = proposed_start
    attendee.proposed_end = proposed_end
    if note:
        attendee.notes = note

    doc.save(ignore_permissions=True)

    # Notify organizer
    _notify_time_proposal(doc, frappe.session.user, proposed_start, proposed_end)

    return {
        "status": "Tentative",
        "proposed_start": proposed_start,
        "proposed_end": proposed_end,
        "attendee_stats": _get_attendee_stats(doc)
    }


@frappe.whitelist()
def get_appointment_rsvp_info(appointment: str) -> dict:
    """
    Get RSVP information for an appointment (for activity cards).

    Args:
        appointment: Orga Appointment name

    Returns:
        dict: {
            is_attendee: bool,
            user_rsvp_status: str,
            attendee_stats: dict,
            attendees: list
        }
    """
    if not appointment:
        frappe.throw(_("Appointment name is required"))

    if not frappe.db.exists("Orga Appointment", appointment):
        return {
            "is_attendee": False,
            "user_rsvp_status": None,
            "attendee_stats": {"total": 0, "accepted": 0, "declined": 0, "tentative": 0, "pending": 0},
            "attendees": []
        }

    doc = frappe.get_doc("Orga Appointment", appointment)

    # Find current user's status
    is_attendee = False
    user_rsvp_status = None

    for att in doc.attendees:
        if att.user == frappe.session.user:
            is_attendee = True
            user_rsvp_status = att.rsvp_status
            break
        if att.resource:
            resource_user = frappe.db.get_value("Orga Resource", att.resource, "user")
            if resource_user == frappe.session.user:
                is_attendee = True
                user_rsvp_status = att.rsvp_status
                break

    return {
        "is_attendee": is_attendee,
        "user_rsvp_status": user_rsvp_status,
        "attendee_stats": _get_attendee_stats(doc),
        "attendees": _get_attendee_list(doc)
    }


def _get_attendee_stats(doc) -> dict:
    """Get RSVP statistics for appointment."""
    stats = {
        "total": len(doc.attendees),
        "accepted": 0,
        "declined": 0,
        "tentative": 0,
        "pending": 0
    }

    for att in doc.attendees:
        status_key = (att.rsvp_status or "Pending").lower()
        if status_key in stats:
            stats[status_key] += 1

    return stats


def _get_attendee_list(doc) -> list:
    """Get list of attendees with their info."""
    attendees = []
    for att in doc.attendees:
        # Get name from resource or user
        name = att.resource_name
        user_image = None

        if att.user:
            user_info = frappe.db.get_value(
                "User", att.user, ["full_name", "user_image"], as_dict=True
            )
            if user_info:
                name = user_info.get("full_name") or name
                user_image = user_info.get("user_image")
        elif att.resource:
            resource_info = frappe.db.get_value(
                "Orga Resource", att.resource, ["resource_name", "user"], as_dict=True
            )
            if resource_info:
                name = resource_info.get("resource_name") or name
                if resource_info.get("user"):
                    user_image = frappe.db.get_value("User", resource_info["user"], "user_image")

        attendees.append({
            "resource": att.resource,
            "user": att.user,
            "name": name,
            "user_image": user_image,
            "rsvp_status": att.rsvp_status or "Pending",
            "required": att.required,
            "proposed_start": str(att.proposed_start) if att.proposed_start else None,
            "proposed_end": str(att.proposed_end) if att.proposed_end else None
        })

    return attendees


def _notify_rsvp_change(doc, user: str, old_status: str, new_status: str) -> None:
    """Send notification when RSVP status changes."""
    try:
        user_fullname = frappe.db.get_value("User", user, "full_name") or user

        # Notify the appointment owner
        if doc.owner and doc.owner != user:
            frappe.publish_realtime(
                "orga_rsvp_updated",
                {
                    "appointment": doc.name,
                    "appointment_title": doc.title,
                    "from_user": user,
                    "from_user_fullname": user_fullname,
                    "old_status": old_status,
                    "new_status": new_status
                },
                user=doc.owner
            )
    except Exception as e:
        frappe.log_error(f"Appointment notification failed: {e}", "Orga Appointment")


def _notify_time_proposal(doc, user: str, proposed_start: str, proposed_end: str) -> None:
    """Send notification when user proposes alternative time."""
    try:
        user_fullname = frappe.db.get_value("User", user, "full_name") or user

        # Notify the appointment owner
        if doc.owner and doc.owner != user:
            frappe.publish_realtime(
                "orga_time_proposed",
                {
                    "appointment": doc.name,
                    "appointment_title": doc.title,
                    "from_user": user,
                    "from_user_fullname": user_fullname,
                    "proposed_start": proposed_start,
                    "proposed_end": proposed_end
                },
                user=doc.owner
            )
    except Exception as e:
        frappe.log_error(f"Time proposal notification failed: {e}", "Orga Appointment")
