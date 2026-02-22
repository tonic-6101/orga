# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Scheduled job to send appointment reminders.

Runs every 15 minutes via scheduler_events in hooks.py.
Finds appointments where:
- send_reminder = 1
- reminder_sent = 0
- start_datetime - reminder_minutes <= now
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date, get_datetime


def send_appointment_reminders():
    """
    Main scheduled job function.
    Finds due reminders and sends notifications.
    """
    try:
        appointments = get_appointments_needing_reminder()

        for appointment in appointments:
            try:
                send_reminder_for_appointment(appointment)
                mark_reminder_sent(appointment.name)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(
                    message=f"Failed to send reminder for {appointment.name}: {str(e)}",
                    title="Orga Appointment Reminder Error"
                )
                frappe.db.rollback()

    except Exception as e:
        frappe.log_error(
            message=f"Appointment reminder job failed: {str(e)}",
            title="Orga Appointment Reminder Job Error"
        )


def get_appointments_needing_reminder():
    """
    Find appointments that need reminders sent now.

    Criteria:
    - send_reminder = 1
    - reminder_sent = 0
    - status = 'Scheduled' (not completed/cancelled)
    - reminder time has passed (start_datetime - reminder_minutes <= now)
    """
    current_time = now_datetime()

    # Get all appointments with reminders enabled but not yet sent
    appointments = frappe.get_all(
        "Orga Appointment",
        filters={
            "send_reminder": 1,
            "reminder_sent": 0,
            "status": "Scheduled"
        },
        fields=[
            "name", "title", "event_type", "start_datetime",
            "end_datetime", "location", "meeting_url", "reminder_minutes",
            "project", "description"
        ]
    )

    # Filter to those where reminder time has passed
    due_appointments = []
    for apt in appointments:
        reminder_minutes = apt.reminder_minutes or 60  # Default 60 minutes
        reminder_time = add_to_date(
            get_datetime(apt.start_datetime),
            minutes=-reminder_minutes
        )

        if get_datetime(reminder_time) <= current_time:
            due_appointments.append(apt)

    return due_appointments


def send_reminder_for_appointment(appointment):
    """
    Send reminder email to all attendees of an appointment.

    Args:
        appointment: dict with appointment data
    """
    # Get attendees with their email addresses
    attendees = get_appointment_attendees(appointment.name)

    if not attendees:
        frappe.log_error(
            message=f"No attendees found for appointment {appointment.name}",
            title="Orga Appointment Reminder Warning"
        )
        return

    # Get project name if applicable
    project_name = None
    if appointment.project:
        project_name = frappe.db.get_value(
            "Orga Project", appointment.project, "project_name"
        )

    # Format the appointment time
    start_dt = get_datetime(appointment.start_datetime)
    formatted_date = start_dt.strftime("%A, %B %d, %Y")
    formatted_time = start_dt.strftime("%I:%M %p")

    # Send email to each attendee
    for attendee in attendees:
        if not attendee.email:
            continue

        try:
            send_reminder_email(
                recipient=attendee.email,
                recipient_name=attendee.resource_name,
                appointment=appointment,
                project_name=project_name,
                formatted_date=formatted_date,
                formatted_time=formatted_time
            )
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send reminder to {attendee.email}: {str(e)}",
                title="Orga Appointment Reminder Email Error"
            )


def get_appointment_attendees(appointment_name):
    """
    Get attendees for an appointment with their resource details.

    Args:
        appointment_name: Name of the appointment

    Returns:
        list of dicts with resource details
    """
    attendees = frappe.get_all(
        "Orga Appointment Attendee",
        filters={"parent": appointment_name},
        fields=["resource", "rsvp_status", "required"]
    )

    result = []
    for attendee in attendees:
        # Only send to attendees who haven't declined
        if attendee.rsvp_status == "Declined":
            continue

        resource = frappe.db.get_value(
            "Orga Resource",
            attendee.resource,
            ["resource_name", "email", "user"],
            as_dict=True
        )

        if resource:
            result.append({
                "resource": attendee.resource,
                "resource_name": resource.resource_name,
                "email": resource.email,
                "user": resource.user,
                "rsvp_status": attendee.rsvp_status,
                "required": attendee.required
            })

    return result


def send_reminder_email(recipient, recipient_name, appointment, project_name,
                        formatted_date, formatted_time):
    """
    Send a reminder email to a single recipient.

    Args:
        recipient: Email address
        recipient_name: Name of recipient
        appointment: Appointment dict
        project_name: Project name if applicable
        formatted_date: Human-readable date string
        formatted_time: Human-readable time string
    """
    subject = _("Reminder: {0} - {1} at {2}").format(appointment.title, formatted_date, formatted_time)

    # Build location string
    location_info = ""
    if appointment.location:
        location_info = f"<p><strong>{_('Location')}:</strong> {appointment.location}</p>"
    if appointment.meeting_url:
        location_info += f'<p><strong>{_("Meeting Link")}:</strong> <a href="{appointment.meeting_url}">{appointment.meeting_url}</a></p>'

    # Build project string
    project_info = ""
    if project_name:
        project_info = f"<p><strong>{_('Project')}:</strong> {project_name}</p>"

    # Build description
    description_info = ""
    if appointment.description:
        description_info = f"<p><strong>{_('Details')}:</strong></p><div>{appointment.description}</div>"

    message = f"""
    <p>{_("Hello {0}").format(recipient_name)},</p>

    <p>{_("This is a reminder for your upcoming appointment")}:</p>

    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin: 16px 0;">
        <h3 style="margin: 0 0 12px 0; color: #333;">{appointment.title}</h3>
        <p style="margin: 4px 0;"><strong>{_("Type")}:</strong> {appointment.event_type}</p>
        <p style="margin: 4px 0;"><strong>{_("Date")}:</strong> {formatted_date}</p>
        <p style="margin: 4px 0;"><strong>{_("Time")}:</strong> {formatted_time}</p>
        {location_info}
        {project_info}
    </div>

    {description_info}

    <p>{_("Best regards")},<br>Orga</p>
    """

    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        now=True  # Send immediately
    )


def mark_reminder_sent(appointment_name):
    """
    Mark an appointment's reminder as sent.

    Args:
        appointment_name: Name of the appointment
    """
    frappe.db.set_value(
        "Orga Appointment",
        appointment_name,
        "reminder_sent",
        1
    )


# API endpoint to manually trigger reminders (for testing)
@frappe.whitelist()
def trigger_reminders():
    """
    Manually trigger the reminder job.
    Useful for testing.

    Returns:
        dict with status and count of reminders sent
    """
    if not frappe.has_permission("Orga Appointment", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    appointments = get_appointments_needing_reminder()
    sent_count = 0

    for appointment in appointments:
        try:
            send_reminder_for_appointment(appointment)
            mark_reminder_sent(appointment.name)
            frappe.db.commit()
            sent_count += 1
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send reminder for {appointment.name}: {str(e)}",
                title="Orga Appointment Reminder Error"
            )

    return {
        "success": True,
        "found": len(appointments),
        "sent": sent_count
    }
