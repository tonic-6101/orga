# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

# Copyright (c) 2026, Orga and contributors
# For license information, please see license.txt

"""
Project Health Calculator for Orga.

Calculates project health based on multiple factors:
- Schedule adherence
- Budget utilization
- Task completion rate
- Milestone achievement
"""

import frappe
from frappe.utils import today, date_diff, getdate


class HealthCalculator:
    """Calculate project health based on multiple factors."""

    # Weight factors for health calculation
    WEIGHTS = {
        "schedule": 0.3,      # On-time progress
        "budget": 0.25,       # Budget adherence
        "tasks": 0.25,        # Task completion rate
        "milestones": 0.2     # Milestone achievement
    }

    # Thresholds for health status
    THRESHOLDS = {
        "green": 75,    # Score >= 75 = Green
        "yellow": 50,   # Score >= 50 = Yellow
        "red": 0        # Score < 50 = Red
    }

    def calculate_project_health(self, project_name):
        """
        Calculate health score for a project.

        Args:
            project_name: Name of the project

        Returns:
            dict: Health score, status, factors, and recommendations
        """
        project = frappe.get_doc("Orga Project", project_name)

        scores = {
            "schedule": self._calculate_schedule_score(project),
            "budget": self._calculate_budget_score(project),
            "tasks": self._calculate_task_score(project),
            "milestones": self._calculate_milestone_score(project)
        }

        # Weighted average
        total_score = sum(
            scores[factor] * self.WEIGHTS[factor]
            for factor in scores
        )

        # Determine status
        if total_score >= self.THRESHOLDS["green"]:
            status = "Green"
        elif total_score >= self.THRESHOLDS["yellow"]:
            status = "Yellow"
        else:
            status = "Red"

        return {
            "score": round(total_score, 1),
            "status": status,
            "factors": scores,
            "recommendations": self._get_recommendations(scores)
        }

    def _calculate_schedule_score(self, project):
        """Score based on timeline progress."""
        if not project.start_date or not project.end_date:
            return 100  # No dates = no schedule risk

        today_date = getdate(today())
        start = getdate(project.start_date)
        end = getdate(project.end_date)

        if today_date < start:
            return 100  # Not started yet

        if today_date > end:
            # Project past end date
            if project.progress >= 100:
                return 100  # Completed on time
            return 20  # Past due and not complete

        total_days = date_diff(end, start)
        if total_days <= 0:
            return 100

        elapsed_days = date_diff(today_date, start)
        expected_progress = min(100, (elapsed_days / total_days) * 100)
        actual_progress = project.progress or 0

        # Score based on how well actual matches expected
        variance = actual_progress - expected_progress
        if variance >= 0:
            return 100  # Ahead of schedule
        elif variance >= -10:
            return 80   # Slightly behind
        elif variance >= -25:
            return 60   # Behind schedule
        elif variance >= -50:
            return 40   # Significantly behind
        else:
            return 20   # Critical delay

    def _calculate_budget_score(self, project):
        """Score based on budget utilization."""
        if not project.budget or project.budget <= 0:
            return 100  # No budget = no budget risk

        utilization = (project.spent or 0) / project.budget * 100
        progress = project.progress or 0

        if progress == 0:
            expected_util = 0
        else:
            expected_util = progress  # Expect spending proportional to progress

        variance = utilization - expected_util

        if variance <= 0:
            return 100  # Under budget
        elif variance <= 10:
            return 80   # Slightly over
        elif variance <= 25:
            return 60   # Over budget
        elif variance <= 50:
            return 40   # Significantly over
        else:
            return 20   # Critical overspend

    def _calculate_task_score(self, project):
        """Score based on task completion and overdue tasks."""
        tasks = frappe.get_all(
            "Orga Task",
            filters={"project": project.name},
            fields=["status", "due_date"]
        )

        if not tasks:
            return 100  # No tasks = no task risk

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "Completed")
        overdue = sum(
            1 for t in tasks
            if t.due_date and getdate(t.due_date) < getdate(today())
            and t.status not in ["Completed", "Cancelled"]
        )

        completion_rate = (completed / total) * 100
        overdue_rate = (overdue / total) * 100

        # Penalize for overdue tasks
        score = completion_rate - (overdue_rate * 2)
        return max(0, min(100, score))

    def _calculate_milestone_score(self, project):
        """Score based on milestone achievement."""
        milestones = frappe.get_all(
            "Orga Milestone",
            filters={"project": project.name},
            fields=["status", "due_date"]
        )

        if not milestones:
            return 100  # No milestones = no milestone risk

        total = len(milestones)
        completed = sum(1 for m in milestones if m.status == "Completed")
        missed = sum(1 for m in milestones if m.status == "Missed")

        # Heavy penalty for missed milestones
        score = ((completed / total) * 100) - (missed * 25)
        return max(0, min(100, score))

    def _get_recommendations(self, scores):
        """Generate recommendations based on low scores."""
        recommendations = []

        if scores["schedule"] < 60:
            recommendations.append({
                "area": "Schedule",
                "message": "Project is behind schedule. Consider adding resources or adjusting timeline.",
                "severity": "high" if scores["schedule"] < 40 else "medium"
            })

        if scores["budget"] < 60:
            recommendations.append({
                "area": "Budget",
                "message": "Budget utilization is higher than expected for current progress.",
                "severity": "high" if scores["budget"] < 40 else "medium"
            })

        if scores["tasks"] < 60:
            recommendations.append({
                "area": "Tasks",
                "message": "Task completion rate is low or many tasks are overdue.",
                "severity": "high" if scores["tasks"] < 40 else "medium"
            })

        if scores["milestones"] < 60:
            recommendations.append({
                "area": "Milestones",
                "message": "Milestone achievement is at risk. Review upcoming deadlines.",
                "severity": "high" if scores["milestones"] < 40 else "medium"
            })

        return recommendations


def update_project_health(project_name):
    """
    Update health status for a single project.

    Args:
        project_name: Name of the project

    Returns:
        dict: Health calculation result
    """
    calculator = HealthCalculator()
    result = calculator.calculate_project_health(project_name)

    frappe.db.set_value("Orga Project", project_name, "health_status", result["status"], update_modified=False)
    return result


def update_all_project_health():
    """Scheduled job to update health for all active projects."""
    projects = frappe.get_all(
        "Orga Project",
        filters={"status": ["in", ["Planning", "Active"]]},
        pluck="name"
    )

    updated = 0
    errors = 0

    for project_name in projects:
        try:
            update_project_health(project_name)
            updated += 1
        except Exception as e:
            frappe.log_error(
                message=f"Health calculation failed for {project_name}: {str(e)}",
                title="Health Calculator Error"
            )
            errors += 1

    frappe.db.commit()

    return {"updated": updated, "errors": errors, "total": len(projects)}
