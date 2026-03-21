# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Dock Notification integration — publishes Orga events to Dock's bell icon.

Uses dock.api.notifications.publish() which validates notification_type
against dock_notification_types declared in orga/hooks.py, creates a
Dock Notification record, and pushes a realtime event to the recipient.
"""

import frappe

# Route templates for deep-linking from Dock bell → Orga SPA
_ROUTE_MAP = {
	"Orga Task": "/orga/tasks/{name}",
	"Orga Project": "/orga/projects/{name}",
	"Orga Appointment": "/orga/appointments/{name}",
	"Orga Milestone": "/orga/projects/{project}#milestones",
}


def _dock_installed() -> bool:
	return "dock" in frappe.get_installed_apps()


def _build_action_url(reference_doctype: str, reference_name: str) -> str:
	"""Build a deep-link URL for the Dock notification."""
	template = _ROUTE_MAP.get(reference_doctype)
	if not template or not reference_name:
		return ""
	try:
		doc = frappe.db.get_value(
			reference_doctype,
			reference_name,
			["name", "project"],
			as_dict=True,
		)
		if not doc:
			return ""
		return template.format(name=doc.name, project=doc.get("project") or "")
	except Exception:
		return ""


def publish(
	notification_type: str,
	title: str,
	for_user: str,
	message: str = None,
	reference_doctype: str = None,
	reference_name: str = None,
):
	"""
	Publish a notification to Dock's bell icon.

	Safe to call when Dock is not installed — silently returns.
	Failures are logged but never break the calling code.
	"""
	if not _dock_installed():
		return

	action_url = _build_action_url(reference_doctype, reference_name)

	try:
		from dock.api.notifications import publish as dock_publish
		dock_publish(
			for_user=for_user,
			from_app="orga",
			notification_type=notification_type,
			title=title,
			message=message,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			action_url=action_url,
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Orga: failed to publish Dock notification",
		)


# ------------------------------------------------------------------
# Doc event handlers — wire these in hooks.py doc_events
# ------------------------------------------------------------------

def on_task_update(doc, method=None):
	"""Publish Dock notification when a task is assigned or its status changes."""
	if not _dock_installed():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	# Assignment change
	new_assignee = doc.get("assigned_to")
	old_assignee = old_doc.get("assigned_to")
	if new_assignee and new_assignee != old_assignee and new_assignee != frappe.session.user:
		publish(
			notification_type="task_assigned",
			title=frappe._("You have been assigned to: {0}").format(doc.subject),
			for_user=new_assignee,
			message=frappe._("Task '{0}' in project '{1}' was assigned to you.").format(
				doc.subject, doc.get("project") or ""
			),
			reference_doctype="Orga Task",
			reference_name=doc.name,
		)

	# Status change — notify owner
	new_status = doc.get("status")
	old_status = old_doc.get("status")
	if new_status and new_status != old_status and doc.owner != frappe.session.user:
		publish(
			notification_type="task_status_change",
			title=frappe._("Task status changed to {0}: {1}").format(new_status, doc.subject),
			for_user=doc.owner,
			message=frappe._("'{0}' was changed from {1} to {2}.").format(
				doc.subject, old_status, new_status
			),
			reference_doctype="Orga Task",
			reference_name=doc.name,
		)


def on_milestone_update(doc, method=None):
	"""Publish Dock notification when a milestone's status changes to approaching due date."""
	if not _dock_installed():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	# Status change — notify project owner
	new_status = doc.get("status")
	old_status = old_doc.get("status")
	if new_status and new_status != old_status:
		project_owner = frappe.db.get_value("Orga Project", doc.project, "owner") if doc.project else None
		if project_owner and project_owner != frappe.session.user:
			publish(
				notification_type="milestone_due",
				title=frappe._("Milestone {0}: {1}").format(new_status, doc.milestone_name),
				for_user=project_owner,
				message=frappe._("Milestone '{0}' status changed to {1}.").format(
					doc.milestone_name, new_status
				),
				reference_doctype="Orga Milestone",
				reference_name=doc.name,
			)
