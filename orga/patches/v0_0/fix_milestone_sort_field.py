# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe


def execute():
	"""Fix malformed sort_field in Orga Milestone DocType.

	The sort_field was set to a comma-separated multi-field value that crashes
	Frappe's db_query.py set_order_by method during migration. This patch runs
	in pre_model_sync to fix the database value before DocType sync loads it.
	"""
	frappe.db.sql(
		"UPDATE `tabDocType` SET `sort_field` = 'due_date' WHERE `name` = 'Orga Milestone'"
	)
