# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Jana Daily Briefing source — Orga project management data."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_briefing(date: str | None = None) -> dict:
	"""Return a briefing summary of the user's project management data.

	Includes overdue tasks, today's appointments, and upcoming milestones.
	"""
	today = getdate(date or nowdate())
	week_end = add_days(today, 7)

	return {
		"overdue_tasks": _get_overdue_tasks(today),
		"today_appointments": _get_today_appointments(today),
		"milestones_this_week": _get_upcoming_milestones(today, week_end),
	}


def _get_overdue_tasks(today) -> list[dict]:
	"""Return tasks that are overdue (past due_date, not completed)."""
	return frappe.get_all(
		"Orga Task",
		filters={
			"assigned_to": frappe.session.user,
			"status": ["not in", ["Completed", "Cancelled"]],
			"due_date": ["<", today],
		},
		fields=["name", "subject", "priority", "due_date", "project", "status"],
		order_by="due_date asc",
		limit_page_length=10,
	)


def _get_today_appointments(today) -> list[dict]:
	"""Return appointments scheduled for today."""
	today_start = f"{today} 00:00:00"
	today_end = f"{today} 23:59:59"

	return frappe.get_all(
		"Orga Appointment",
		filters={
			"created_by": frappe.session.user,
			"start_datetime": ["between", [today_start, today_end]],
			"status": ["not in", ["Cancelled"]],
		},
		fields=["name", "title", "start_datetime", "end_datetime", "status", "location"],
		order_by="start_datetime asc",
		limit_page_length=10,
	)


def _get_upcoming_milestones(today, week_end) -> list[dict]:
	"""Return milestones due within the next 7 days."""
	return frappe.get_all(
		"Orga Milestone",
		filters={
			"status": ["not in", ["Completed", "Cancelled"]],
			"due_date": ["between", [today, week_end]],
		},
		fields=["name", "milestone_name", "due_date", "project", "status"],
		order_by="due_date asc",
		limit_page_length=10,
	)
