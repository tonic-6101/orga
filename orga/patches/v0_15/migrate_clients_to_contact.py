# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Migrate Orga Client records to Frappe Contact with custom fields.

For each Orga Client:
1. Find or create a Contact by email
2. Map client_name → first_name/last_name, company → company_name
3. Create Address if address fields are populated
4. Set custom fields: is_orga_client, orga_portal_enabled, orga_client_status
5. Update Orga Project.client references

Idempotent — safe to run multiple times.
"""

import frappe
from frappe.utils import cstr


def execute():
	# Ensure custom fields exist
	if not frappe.db.exists("Custom Field", {"dt": "Contact", "fieldname": "is_orga_client"}):
		frappe.log_error("Contact custom fields not found — run bench migrate first")
		return

	if not frappe.db.exists("DocType", "Orga Client"):
		return

	clients = frappe.get_all(
		"Orga Client",
		fields=[
			"name", "client_name", "email", "phone", "company",
			"user", "status", "portal_enabled", "project_count", "notes",
			"address_line1", "address_line2", "city", "state", "country",
		],
	)

	migrated = 0
	mapping = {}  # old Orga Client name → new Contact name

	for client in clients:
		contact_name = _find_or_create_contact(client)
		if not contact_name:
			continue
		mapping[client.name] = contact_name
		migrated += 1

	# Update Orga Project.client references
	if mapping:
		_update_project_references(mapping)

	frappe.db.commit()
	if migrated:
		frappe.log_error(
			title="Client migration complete",
			message=f"Migrated {migrated} Orga Client(s) to Contact. Updated project references.",
		)


def _find_or_create_contact(client: dict) -> str | None:
	"""Find existing Contact by email or create a new one. Returns Contact name."""
	email = cstr(client.email).strip()
	if not email:
		frappe.log_error(f"Orga Client {client.name} has no email — skipped")
		return None

	# Try to find existing Contact by email
	existing = frappe.db.get_value(
		"Contact",
		{"email_id": email},
		"name",
	)

	if existing:
		# Update custom fields on existing Contact
		frappe.db.set_value("Contact", existing, {
			"is_orga_client": 1,
			"orga_portal_enabled": client.portal_enabled or 0,
			"orga_client_status": client.status or "Active",
			"orga_project_count": client.project_count or 0,
		}, update_modified=False)
		return existing

	# Create new Contact
	first_name, last_name = _split_name(client.client_name)

	try:
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": first_name,
			"last_name": last_name,
			"email_id": email,
			"phone": client.phone or "",
			"company_name": client.company or "",
			"user": client.user or None,
			"is_orga_client": 1,
			"orga_portal_enabled": client.portal_enabled or 0,
			"orga_client_status": client.status or "Active",
			"orga_project_count": client.project_count or 0,
		})

		# Add email as Email ID child row (required by Frappe Contact)
		contact.append("email_ids", {
			"email_id": email,
			"is_primary": 1,
		})
		if client.phone:
			contact.append("phone_nos", {
				"phone": client.phone,
				"is_primary_phone": 1,
			})

		contact.insert(ignore_permissions=True, ignore_mandatory=True)

		# Create Address if address fields are populated
		if client.address_line1:
			_create_address(contact.name, client)

		return contact.name

	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Failed to create Contact for Orga Client {client.name}",
		)
		return None


def _split_name(full_name: str) -> tuple[str, str]:
	"""Split a full name into first_name, last_name."""
	parts = cstr(full_name).strip().split(" ", 1)
	first_name = parts[0] or "Client"
	last_name = parts[1] if len(parts) > 1 else ""
	return first_name, last_name


def _create_address(contact_name: str, client: dict):
	"""Create an Address linked to the Contact."""
	try:
		address = frappe.get_doc({
			"doctype": "Address",
			"address_title": client.client_name,
			"address_type": "Billing",
			"address_line1": client.address_line1,
			"address_line2": client.address_line2 or "",
			"city": client.city or "",
			"state": client.state or "",
			"country": client.country or "",
		})
		address.append("links", {
			"link_doctype": "Contact",
			"link_name": contact_name,
		})
		address.insert(ignore_permissions=True, ignore_mandatory=True)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Failed to create Address for Contact {contact_name}",
		)


def _update_project_references(mapping: dict):
	"""Update Orga Project.client from Orga Client name → Contact name."""
	for old_client, new_contact in mapping.items():
		frappe.db.sql(
			"""UPDATE `tabOrga Project`
			   SET client = %s
			   WHERE client = %s""",
			(new_contact, old_client),
		)
