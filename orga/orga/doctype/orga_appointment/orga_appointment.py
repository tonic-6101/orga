# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, time_diff_in_seconds, add_to_date


class OrgaAppointment(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_duration()
        self.set_created_by()
        self.auto_fill_project_from_task()

    def validate_dates(self):
        """Ensure end_datetime >= start_datetime, auto-correct if needed"""
        if self.end_datetime and self.start_datetime:
            start = get_datetime(self.start_datetime)
            end = get_datetime(self.end_datetime)
            if end < start:
                # Auto-correct: set end to start + 1 hour
                self.end_datetime = add_to_date(self.start_datetime, hours=1)
                frappe.msgprint(
                    _("End time was before start time. Adjusted to 1 hour after start."),
                    indicator="orange",
                    alert=True
                )

    def calculate_duration(self):
        """Auto-calculate duration in minutes"""
        if self.start_datetime and self.end_datetime:
            diff = time_diff_in_seconds(self.end_datetime, self.start_datetime)
            self.duration_minutes = int(diff / 60)
        elif self.all_day:
            self.duration_minutes = 1440  # 24 hours

    def set_created_by(self):
        """Set created_by on first save"""
        if not self.created_by:
            self.created_by = frappe.session.user

    def auto_fill_project_from_task(self):
        """Auto-fill project if task is set"""
        if self.task and not self.project:
            self.project = frappe.db.get_value("Orga Task", self.task, "project")

    def get_attendee_count(self):
        """Get count of attendees"""
        return len(self.attendees) if self.attendees else 0

    def get_accepted_count(self):
        """Get count of accepted attendees"""
        if not self.attendees:
            return 0
        return sum(1 for a in self.attendees if a.rsvp_status == "Accepted")

    def get_calendar_event_data(self):
        """Return data formatted for calendar display"""
        return {
            "id": self.name,
            "title": self.title,
            "start": str(self.start_datetime),
            "end": str(self.end_datetime) if self.end_datetime else None,
            "allDay": bool(self.all_day),
            "color": self.color or self.get_default_color(),
            "extendedProps": {
                "event_type": self.event_type,
                "status": self.status,
                "project": self.project,
                "project_name": frappe.db.get_value("Orga Project", self.project, "project_name") if self.project else None,
                "location": self.location,
                "meeting_url": self.meeting_url,
                "attendee_count": self.get_attendee_count(),
                "accepted_count": self.get_accepted_count()
            }
        }

    def get_default_color(self):
        """Return default color based on event type"""
        colors = {
            "Meeting": "#8B5CF6",    # Purple
            "Deadline": "#EF4444",   # Red
            "Review": "#3B82F6",     # Blue
            "Milestone": "#F59E0B",  # Amber
            "Other": "#6B7280"       # Gray
        }
        return colors.get(self.event_type, "#6B7280")

    def after_insert(self):
        """Log activity on creation"""
        self.log_activity("created", f"Created {self.event_type.lower()}: {self.title}")

    def on_update(self):
        """Log activity on update"""
        if self.has_value_changed("start_datetime") or self.has_value_changed("end_datetime"):
            self.log_activity("rescheduled", f"Rescheduled {self.event_type.lower()}: {self.title}")
        elif self.has_value_changed("status"):
            self.log_activity("status_changed", f"{self.event_type} '{self.title}' status changed to {self.status}")
        else:
            self.log_activity("updated", f"Updated {self.event_type.lower()}: {self.title}")

    def log_activity(self, action: str, content: str):
        """Create activity log entry for this appointment"""
        try:
            frappe.get_doc({
                "doctype": "Activity Log",
                "subject": content,
                "content": content,
                "reference_doctype": "Orga Appointment",
                "reference_name": self.name,
                "user": frappe.session.user,
                "full_name": frappe.db.get_value("User", frappe.session.user, "full_name")
            }).insert(ignore_permissions=True)
        except Exception as e:
            # Don't fail the main operation if logging fails
            frappe.log_error(f"Failed to log appointment activity: {e}")
