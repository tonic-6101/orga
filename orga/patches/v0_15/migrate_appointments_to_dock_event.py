# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Migrate Orga Appointment context fields to Dock Event custom fields.

Existing Dock Events (created by dock_calendar.py sync) already mirror the
basic calendar data. This patch enriches them with Orga-specific context:
orga_project, orga_task, orga_milestone.

Also populates Dock Event Attendee child table from Orga Appointment Attendee.

Idempotent — safe to run multiple times.
"""

import frappe


def execute():
	if "dock" not in frappe.get_installed_apps():
		return

	if not frappe.db.exists("DocType", "Dock Event"):
		return

	# Ensure custom fields exist before populating
	if not frappe.db.exists("Custom Field", {"dt": "Dock Event", "fieldname": "orga_project"}):
		frappe.log_error("Dock Event custom fields not found — run bench migrate first")
		return

	appointments = frappe.get_all(
		"Orga Appointment",
		fields=["name", "project", "task", "milestone", "created_by", "owner"],
	)

	updated = 0
	for appt in appointments:
		# Find the Dock Event(s) for this appointment — there may be multiple (one per user)
		dock_events = frappe.get_all(
			"Dock Event",
			filters={
				"source_doctype": "Orga Appointment",
				"source_name": appt.name,
			},
			fields=["name"],
		)

		for de in dock_events:
			frappe.db.set_value(
				"Dock Event",
				de.name,
				{
					"orga_project": appt.project or None,
					"orga_task": appt.task or None,
					"orga_milestone": appt.milestone or None,
				},
				update_modified=False,
			)
			updated += 1

		# Populate attendees on the organizer's Dock Event
		organizer = appt.created_by or appt.owner
		organizer_event = frappe.db.get_value(
			"Dock Event",
			{
				"source_doctype": "Orga Appointment",
				"source_name": appt.name,
				"user": organizer,
			},
			"name",
		)
		if organizer_event:
			_sync_attendees(appt.name, organizer_event)

	frappe.db.commit()
	if updated:
		frappe.log_error(
			title="Appointment migration complete",
			message=f"Updated {updated} Dock Event(s) with Orga context fields",
		)


def _sync_attendees(appointment_name: str, dock_event_name: str):
	"""Populate Dock Event Attendee from Orga Appointment Attendee."""
	attendees = frappe.get_all(
		"Orga Appointment Attendee",
		filters={"parent": appointment_name},
		fields=["user", "rsvp_status", "required", "notes", "proposed_start", "proposed_end"],
	)
	if not attendees:
		return

	# Check if attendees already exist on this Dock Event
	existing = frappe.get_all(
		"Dock Event Attendee",
		filters={"parent": dock_event_name},
		pluck="user",
	)
	existing_set = set(existing)

	for att in attendees:
		if not att.user or att.user in existing_set:
			continue
		try:
			frappe.get_doc({
				"doctype": "Dock Event Attendee",
				"parent": dock_event_name,
				"parenttype": "Dock Event",
				"parentfield": "attendees",
				"user": att.user,
				"rsvp_status": att.rsvp_status or "Pending",
				"required": att.required if att.required is not None else 1,
				"notes": att.notes or "",
				"proposed_start": att.proposed_start,
				"proposed_end": att.proposed_end,
			}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Failed to sync attendee {att.user} for {appointment_name}",
			)
