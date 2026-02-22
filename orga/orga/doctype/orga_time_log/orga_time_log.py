# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours, now_datetime, time_diff_in_seconds


class OrgaTimeLog(Document):
    def before_validate(self):
        self._clear_auto_defaulted_times()

    def _clear_auto_defaulted_times(self):
        """Clear from_time/to_time if they were auto-filled by Frappe's defaults.

        Frappe's set_dynamic_default_values sets ALL Time fields to nowtime()
        during _set_defaults(). For manual time entries (where user provides
        hours directly), this produces from_time == to_time which would
        zero out hours in calculate_hours(). Clear them so only user-provided
        time values persist.
        """
        if self.is_new() and self.from_time and self.to_time:
            if self.from_time == self.to_time and not self.flags.get("explicit_times"):
                self.from_time = None
                self.to_time = None

    def validate(self):
        self.validate_tracking_context()
        self.set_project_from_context()
        self.calculate_hours()
        self.validate_times()

    def before_save(self):
        self.enforce_one_active_timer()

    def validate_tracking_context(self):
        """Ensure correct FK is set per tracking context."""
        ctx = self.tracking_context or "task"

        if ctx == "task" and not self.task:
            frappe.throw(_("Task is required when tracking context is 'task'"))
        if ctx == "event" and not self.event:
            frappe.throw(_("Event is required when tracking context is 'event'"))
        if ctx == "project" and not self.project:
            frappe.throw(_("Project is required when tracking context is 'project'"))

    def set_project_from_context(self):
        """Auto-populate project from task or event when not explicitly set."""
        if self.project:
            return

        if self.task:
            project = frappe.db.get_value("Orga Task", self.task, "project")
            if project:
                self.project = project
        elif self.event:
            project = frappe.db.get_value("Orga Appointment", self.event, "project")
            if project:
                self.project = project

    def enforce_one_active_timer(self):
        """Stop other running timers for the same user when this one starts."""
        if not self.is_running:
            return

        running = frappe.get_all(
            "Orga Time Log",
            filters={
                "user": self.user,
                "is_running": 1,
                "name": ["!=", self.name or ""]
            },
            fields=["name", "timer_started_at"]
        )

        for timer in running:
            self._stop_running_timer(timer.name, timer.timer_started_at)

    def _stop_running_timer(self, name, timer_started_at):
        """Stop a running timer by calculating its hours."""
        now = now_datetime()
        hours = 0
        if timer_started_at:
            seconds = time_diff_in_seconds(now, timer_started_at)
            hours = max(round(seconds / 3600, 4), 0)
        if hours == 0 and timer_started_at:
            hours = 0.01

        frappe.db.set_value("Orga Time Log", name, {
            "is_running": 0,
            "hours": hours
        }, update_modified=True)

    def calculate_hours(self):
        """Calculate hours from from_time and to_time if both provided.

        Frappe auto-fills all Time fields with nowtime() during _set_defaults,
        which sets from_time == to_time for manual entries. This would zero out
        hours if we blindly recalculated. We only recalculate when from_time
        and to_time are meaningfully different (user explicitly set them).
        """
        if self.timer_started_at and not self.is_running:
            # Hours already calculated by stop_timer — don't override
            return
        if self.from_time and self.to_time:
            calculated = time_diff_in_hours(self.to_time, self.from_time)
            if calculated > 0:
                self.hours = calculated
            # If calculated is 0 (from_time == to_time from auto-default),
            # keep the existing hours value set by the user/API

    def validate_times(self):
        """Ensure to_time is after from_time."""
        if self.to_time and self.from_time:
            if self.to_time < self.from_time:
                frappe.throw(_("To Time cannot be before From Time"))

    def on_update(self):
        self.update_task_actual_hours()

    def on_trash(self):
        self.update_task_actual_hours()

    def update_task_actual_hours(self):
        """Update task's actual_hours field (only when task is set)."""
        if not self.task:
            return

        total = frappe.db.sql("""
            SELECT COALESCE(SUM(hours), 0) as total
            FROM `tabOrga Time Log`
            WHERE task = %s AND name != %s AND is_running = 0
        """, (self.task, self.name))[0][0]

        # Add current hours if not being deleted and not running
        if not self.flags.in_delete and not self.is_running:
            total += self.hours or 0

        frappe.db.set_value("Orga Task", self.task, "actual_hours", total)
