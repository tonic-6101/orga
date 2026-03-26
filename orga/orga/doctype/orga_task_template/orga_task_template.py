# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OrgaTaskTemplate(Document):
    def before_save(self):
        self._protect_system_template()

    def before_delete(self):
        self._protect_system_template()

    def _protect_system_template(self):
        """Prevent modification or deletion of system templates."""
        if self.is_system_template and not frappe.flags.in_install:
            frappe.throw(_("System templates cannot be modified or deleted"))
