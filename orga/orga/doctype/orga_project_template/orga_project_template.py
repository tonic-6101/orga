# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import json
import frappe
from frappe.model.document import Document


class OrgaProjectTemplate(Document):
    def validate(self):
        self.compute_counts()

    def compute_counts(self):
        """Parse template_data JSON and count tasks, milestones, dependencies."""
        if not self.template_data:
            self.task_count = 0
            self.milestone_count = 0
            self.dependency_count = 0
            return

        try:
            data = json.loads(self.template_data) if isinstance(self.template_data, str) else self.template_data
        except (json.JSONDecodeError, TypeError):
            self.task_count = 0
            self.milestone_count = 0
            self.dependency_count = 0
            return

        tasks = data.get("tasks", [])
        milestones = data.get("milestones", [])

        dep_count = 0
        for task in tasks:
            dep_count += len(task.get("dependencies", []))

        self.task_count = len(tasks)
        self.milestone_count = len(milestones)
        self.dependency_count = dep_count
