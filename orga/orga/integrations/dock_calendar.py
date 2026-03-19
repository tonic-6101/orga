# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.utils import get_datetime, add_to_date

_ORGA_COLOR = "#16a34a"


def _dock_installed():
	return "dock" in frappe.get_installed_apps()


def _orga_color():
	"""Return Orga's brand color. Read from boot registry when available, fallback to hardcoded."""
	try:
		registered = frappe.get_hooks("dock_app_registry", app_name="orga")
		if registered:
			return registered[0].get("color") or _ORGA_COLOR
	except Exception:
		pass
	return _ORGA_COLOR


def _upsert(source_doc, payload: dict):
	"""Create or update the Dock Event for a source document + user pair."""
	user = payload.get("user")
	existing = frappe.db.get_value(
		"Dock Event",
		{
			"source_doctype": source_doc.doctype,
			"source_name": source_doc.name,
			"user": user,
		},
		"name",
	)
	if existing:
		frappe.db.set_value("Dock Event", existing, payload, update_modified=False)
	else:
		frappe.get_doc({
			"doctype": "Dock Event",
			**payload,
			"source_doctype": source_doc.doctype,
			"source_name": source_doc.name,
			"source_app": "orga",
		}).insert(ignore_permissions=True)


def _remove_stale_user_events(source_doc, current_users: set):
	"""Delete Dock Event rows for users no longer associated with a source doc."""
	existing_users = frappe.db.get_all(
		"Dock Event",
		filters={"source_doctype": source_doc.doctype, "source_name": source_doc.name},
		pluck="user",
	)
	for user in existing_users:
		if user not in current_users:
			frappe.db.delete("Dock Event", {
				"source_doctype": source_doc.doctype,
				"source_name": source_doc.name,
				"user": user,
			})


def sync_appointment(doc, method=None):
	if not _dock_installed():
		return
	if not doc.start_datetime:
		remove_event(doc)
		return

	color = _orga_color()
	payload = {
		"title":          doc.title or doc.name,
		"start_datetime": doc.start_datetime,
		"end_datetime":   doc.end_datetime or None,
		"all_day":        int(doc.all_day or 0),
		"event_type":     "orga.appointment",
		"color":          color,
		"url":            f"/orga/appointments/{doc.name}",
		"description":    None,
	}

	# Write for the creator (and attendees if needed — one record per calendar owner)
	owner = doc.created_by or doc.owner
	users = {owner}
	for row in (doc.attendees or []):
		if row.get("user"):
			users.add(row.user)

	for user in users:
		_upsert(doc, {**payload, "user": user})

	_remove_stale_user_events(doc, users)


def sync_task(doc, method=None):
	if not _dock_installed():
		return
	if not doc.due_date:
		remove_event(doc)
		return

	color = _orga_color()
	start_dt = get_datetime(f"{doc.start_date} 00:00:00") if doc.start_date else get_datetime(f"{doc.due_date} 00:00:00")
	end_dt = get_datetime(f"{doc.due_date} 00:00:00")

	payload = {
		"title":          doc.subject,
		"start_datetime": start_dt,
		"end_datetime":   end_dt,
		"all_day":        1,
		"event_type":     "orga.task",
		"color":          color,
		"url":            f"/orga/tasks/{doc.name}",
		"description":    None,
	}

	users = set()
	if doc.assigned_to:
		users.add(doc.assigned_to)
	if doc.owner and doc.owner != doc.assigned_to:
		users.add(doc.owner)
	if not users:
		users.add(doc.owner)

	for user in users:
		_upsert(doc, {**payload, "user": user})

	_remove_stale_user_events(doc, users)


def sync_milestone(doc, method=None):
	if not _dock_installed():
		return
	if not doc.due_date:
		remove_event(doc)
		return

	color = _orga_color()
	due_dt = get_datetime(f"{doc.due_date} 00:00:00")

	_upsert(doc, {
		"title":          doc.milestone_name,
		"start_datetime": due_dt,
		"end_datetime":   None,
		"all_day":        1,
		"event_type":     "orga.milestone",
		"color":          color,
		"url":            f"/orga/projects/{doc.project}" if doc.project else f"/orga",
		"description":    None,
		"user":           doc.owner,
	})

	_remove_stale_user_events(doc, {doc.owner})


def remove_event(doc, method=None):
	if not _dock_installed():
		return
	frappe.db.delete("Dock Event", {
		"source_doctype": doc.doctype,
		"source_name":    doc.name,
	})


def backfill_dock_events():
	"""
	Create Dock Events for all existing Orga records.
	Safe to run multiple times — uses upsert pattern.
	Called by Dock's after_install via the dock_backfill_calendar hook.
	"""
	for appt in frappe.get_all("Orga Appointment", fields=["name"]):
		try:
			sync_appointment(frappe.get_doc("Orga Appointment", appt.name))
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"dock_calendar backfill: Orga Appointment {appt.name}")

	for task in frappe.get_all("Orga Task", filters={"due_date": ["is", "set"]}, fields=["name"]):
		try:
			sync_task(frappe.get_doc("Orga Task", task.name))
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"dock_calendar backfill: Orga Task {task.name}")

	for ms in frappe.get_all("Orga Milestone", filters={"due_date": ["is", "set"]}, fields=["name"]):
		try:
			sync_milestone(frappe.get_doc("Orga Milestone", ms.name))
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"dock_calendar backfill: Orga Milestone {ms.name}")
