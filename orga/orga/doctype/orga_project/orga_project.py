# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class OrgaProject(Document):
    def before_insert(self):
        self.generate_project_code()

    def validate(self):
        self.validate_dates()

    def validate_dates(self):
        """Ensure end date is not before start date"""
        if self.end_date and self.start_date:
            if getdate(self.start_date) > getdate(self.end_date):
                frappe.throw(_("End date cannot be before start date"))

        if self.actual_end and self.actual_start:
            if getdate(self.actual_start) > getdate(self.actual_end):
                frappe.throw(_("Actual end date cannot be before actual start date"))

    def generate_project_code(self):
        """Auto-generate project code if not provided"""
        if not self.project_code:
            year = getdate(nowdate()).year
            prefix = f"ORG-{year}-"
            # Use MAX on the numeric suffix to avoid collisions from deleted projects
            result = frappe.db.sql("""
                SELECT MAX(CAST(SUBSTRING(project_code, %s) AS UNSIGNED)) as max_num
                FROM `tabOrga Project`
                WHERE project_code LIKE %s
            """, (len(prefix) + 1, f"{prefix}%"))
            next_num = (result[0][0] or 0) + 1
            self.project_code = f"{prefix}{next_num:04d}"

    def on_update(self):
        self.update_progress()
        self.update_estimated_cost()
        self.update_spent()

    def update_estimated_cost(self):
        """Calculate estimated_cost as sum of estimated_cost from all project tasks"""
        if not frappe.db.exists("DocType", "Orga Task"):
            return

        result = frappe.db.sql("""
            SELECT COALESCE(SUM(estimated_cost), 0) as total
            FROM `tabOrga Task`
            WHERE project = %s
        """, self.name, as_dict=True)

        estimated_cost = result[0].total if result else 0

        if self.estimated_cost != estimated_cost:
            self.db_set("estimated_cost", estimated_cost, update_modified=False)

    def update_spent(self):
        """Calculate spent as sum of actual_cost from all project tasks"""
        if not frappe.db.exists("DocType", "Orga Task"):
            return

        result = frappe.db.sql("""
            SELECT COALESCE(SUM(actual_cost), 0) as total
            FROM `tabOrga Task`
            WHERE project = %s
        """, self.name, as_dict=True)

        spent = result[0].total if result else 0

        if self.spent != spent:
            self.db_set("spent", spent, update_modified=False)

    def update_progress(self):
        """Calculate progress as average of all task progress values"""
        if not frappe.db.exists("DocType", "Orga Task"):
            return

        tasks = frappe.get_all(
            "Orga Task",
            filters={"project": self.name},
            fields=["progress"]
        )

        if not tasks:
            if self.progress != 0:
                self.db_set("progress", 0, update_modified=False)
            return

        total_progress = sum(t.progress or 0 for t in tasks)
        progress = round(total_progress / len(tasks), 2)

        if self.progress != progress:
            self.db_set("progress", progress, update_modified=False)

    def on_trash(self):
        """Prevent deletion if project has tasks"""
        if frappe.db.exists("DocType", "Orga Task"):
            task_count = frappe.db.count("Orga Task", filters={"project": self.name})
            if task_count > 0:
                frappe.throw(
                    _("Cannot delete project with {0} linked tasks. Delete tasks first.").format(task_count)
                )
