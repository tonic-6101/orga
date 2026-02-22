# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class OrgaDefect(Document):
    def validate(self):
        self.validate_dates()
        self.validate_cost()

    def validate_dates(self):
        """Ensure resolved date is not before reported date."""
        if self.resolved_date and self.reported_date:
            if getdate(self.resolved_date) < getdate(self.reported_date):
                frappe.throw(_("Resolved date cannot be before reported date"))

    def validate_cost(self):
        """Ensure costs are not negative."""
        if self.actual_cost and self.actual_cost < 0:
            frappe.throw(_("Actual cost cannot be negative"))
        if self.cost_estimate and self.cost_estimate < 0:
            frappe.throw(_("Cost estimate cannot be negative"))

    def on_update(self):
        """Auto-set resolved_date when status changes to Resolved or Closed."""
        if self.status in ("Resolved", "Closed") and not self.resolved_date:
            self.db_set("resolved_date", frappe.utils.today(), update_modified=False)
