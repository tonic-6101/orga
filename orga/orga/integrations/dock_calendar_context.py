# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Dock Calendar context provider for Orga.

Called by Dock when rendering an event detail view via the
``dock_calendar_context`` hook. Returns context panels showing
project, task, and time tracking data for Orga-sourced events.
"""

import frappe
from frappe import _


def get_calendar_context(event_name: str) -> dict | None:
	"""Return Orga context panels for a Dock Event.

	Only returns data for events where source_app == 'orga'.
	"""
	event = frappe.db.get_value(
		"Dock Event",
		event_name,
		["source_app", "source_doctype", "source_name"],
		as_dict=True,
	)
	if not event or event.source_app != "orga":
		return None

	panels = []

	if event.source_doctype == "Orga Appointment":
		_add_appointment_panels(event.source_name, panels)
	elif event.source_doctype == "Orga Task":
		_add_task_panels(event.source_name, panels)
	elif event.source_doctype == "Orga Milestone":
		_add_milestone_panels(event.source_name, panels)

	if not panels:
		return None

	return {"panels": panels}


def _add_appointment_panels(name: str, panels: list):
	"""Add project + task context for an Orga Appointment."""
	appt = frappe.db.get_value(
		"Orga Appointment",
		name,
		["project", "task", "title", "appointment_type"],
		as_dict=True,
	)
	if not appt:
		return

	if appt.project:
		project = frappe.db.get_value(
			"Orga Project", appt.project, ["project_name", "status", "progress"], as_dict=True
		)
		if project:
			fields = [
				{"label": _("Project"), "value": project.project_name},
				{"label": _("Status"), "value": project.status or ""},
				{"label": _("Progress"), "value": f"{project.progress or 0}%"},
			]
			if appt.task:
				task_subject = frappe.db.get_value("Orga Task", appt.task, "subject")
				if task_subject:
					fields.append({"label": _("Task"), "value": task_subject})

			panels.append({
				"label": _("Project"),
				"icon": "folder",
				"fields": fields,
				"link": f"/orga/projects/{appt.project}",
			})

	_add_time_tracking_panel(appt.get("task"), panels)


def _add_task_panels(name: str, panels: list):
	"""Add project + assignment context for an Orga Task."""
	task = frappe.db.get_value(
		"Orga Task",
		name,
		["subject", "project", "status", "priority", "assigned_to", "due_date", "actual_hours"],
		as_dict=True,
	)
	if not task:
		return

	fields = [
		{"label": _("Task"), "value": task.subject},
		{"label": _("Status"), "value": task.status or ""},
		{"label": _("Priority"), "value": task.priority or "—"},
	]
	if task.assigned_to:
		assignee_name = frappe.db.get_value("User", task.assigned_to, "full_name")
		fields.append({"label": _("Assigned to"), "value": assignee_name or task.assigned_to})

	link = f"/orga/tasks/{name}"
	if task.project:
		project_name = frappe.db.get_value("Orga Project", task.project, "project_name")
		if project_name:
			fields.insert(0, {"label": _("Project"), "value": project_name})
		link = f"/orga/projects/{task.project}"

	panels.append({
		"label": _("Task"),
		"icon": "check-square",
		"fields": fields,
		"link": link,
	})

	_add_time_tracking_panel(name, panels)


def _add_milestone_panels(name: str, panels: list):
	"""Add project context for an Orga Milestone."""
	ms = frappe.db.get_value(
		"Orga Milestone",
		name,
		["milestone_name", "project", "status", "due_date", "completion_date"],
		as_dict=True,
	)
	if not ms:
		return

	fields = [
		{"label": _("Milestone"), "value": ms.milestone_name},
		{"label": _("Status"), "value": ms.status or ""},
	]
	if ms.completion_date:
		fields.append({"label": _("Completed"), "value": str(ms.completion_date)})

	if ms.project:
		project_name = frappe.db.get_value("Orga Project", ms.project, "project_name")
		if project_name:
			fields.insert(0, {"label": _("Project"), "value": project_name})

	panels.append({
		"label": _("Milestone"),
		"icon": "flag",
		"fields": fields,
		"link": f"/orga/projects/{ms.project}" if ms.project else "/orga",
	})


def _add_time_tracking_panel(task_name: str | None, panels: list):
	"""Add time tracking summary if Watch is installed and task has tracked time."""
	if not task_name:
		return
	if "watch" not in frappe.get_installed_apps():
		return

	try:
		total = frappe.db.sql(
			"""SELECT COALESCE(SUM(duration_hours), 0)
			   FROM `tabWatch Entry`
			   WHERE orga_task = %s AND is_running = 0""",
			task_name,
		)[0][0]
	except Exception:
		return

	if not total:
		return

	panels.append({
		"label": _("Time Tracking"),
		"icon": "clock",
		"fields": [
			{"label": _("Tracked"), "value": f"{round(total, 1)}h"},
		],
		"link": f"/watch?task={task_name}",
		"link_label": _("View in Watch"),
	})
