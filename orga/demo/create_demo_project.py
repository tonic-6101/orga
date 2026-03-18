"""
Orga Demo Data — "Zenith App Launch" showcase project.

Creates a realistic 4-month project designed for GitHub screenshots/GIFs.
Showcases: Gantt chart, Kanban, Dashboard, Reports.

Usage (inside Frappe Manager container):
    bench --site orga.localhost execute orga.demo.create_demo_project.create_demo_project

To remove demo data:
    bench --site orga.localhost execute orga.demo.create_demo_project.remove_demo_data
"""

import frappe

PROJECT_NAME = "Zenith — Cross-Platform App Launch"
DEMO_TAG = "__orga_demo__"


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def create_demo_project():
    """Create the full demo project. Safe to re-run (skips if already exists)."""
    if frappe.db.exists("Orga Project", {"project_name": PROJECT_NAME}):
        print(f"Demo project already exists. Run remove_demo_data() first to reset.")
        return

    print("Creating demo project: Zenith — Cross-Platform App Launch")

    resources = _create_resources()
    print(f"  ✓ Created {len(resources)} resources")

    project_name = _create_project()
    print(f"  ✓ Created project: {project_name}")

    milestones = _create_milestones(project_name)
    print(f"  ✓ Created {len(milestones)} milestones")

    tasks = _create_tasks(project_name, milestones, resources)
    print(f"  ✓ Created {len(tasks)} tasks")

    _add_dependencies(tasks)
    print("  ✓ Added task dependencies")

    _create_assignments(project_name, tasks, resources)
    print("  ✓ Created resource assignments")

    frappe.db.commit()
    print(f"\nDemo project ready! Open Orga → Projects → '{PROJECT_NAME}'")


def remove_demo_data():
    """Remove all demo data created by this script."""
    print("Removing demo data...")

    # Remove assignments
    for name in frappe.get_all("Orga Assignment", filters={"project": ["like", "Zenith%"]}, pluck="name"):
        frappe.delete_doc("Orga Assignment", name, force=True)

    # Remove tasks (dependencies cascade)
    project = frappe.db.get_value("Orga Project", {"project_name": PROJECT_NAME}, "name")
    if project:
        for name in frappe.get_all("Orga Task", filters={"project": project}, pluck="name"):
            frappe.delete_doc("Orga Task", name, force=True)
        for name in frappe.get_all("Orga Milestone", filters={"project": project}, pluck="name"):
            frappe.delete_doc("Orga Milestone", name, force=True)
        frappe.delete_doc("Orga Project", project, force=True)

    # Remove demo resources (only ones we created)
    for email in [r["email"] for r in RESOURCE_DATA]:
        name = frappe.db.get_value("Orga Resource", {"email": email}, "name")
        if name:
            frappe.delete_doc("Orga Resource", name, force=True)

    frappe.db.commit()
    print("Demo data removed.")


# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

RESOURCE_DATA = [
    {
        "resource_name": "Alex Mercer",
        "email": "alex.mercer@zenith.demo",
        "designation": "Product Manager",
        "weekly_capacity": 40.0,
        "hourly_cost": 95.0,
    },
    {
        "resource_name": "Sofia Reyes",
        "email": "sofia.reyes@zenith.demo",
        "designation": "UX/UI Designer",
        "weekly_capacity": 40.0,
        "hourly_cost": 85.0,
    },
    {
        "resource_name": "Marcus Chen",
        "email": "marcus.chen@zenith.demo",
        "designation": "Backend Engineer",
        "weekly_capacity": 40.0,
        "hourly_cost": 105.0,
    },
    {
        "resource_name": "Priya Patel",
        "email": "priya.patel@zenith.demo",
        "designation": "Frontend Engineer",
        "weekly_capacity": 40.0,
        "hourly_cost": 100.0,
    },
    {
        "resource_name": "Jordan Kim",
        "email": "jordan.kim@zenith.demo",
        "designation": "QA Engineer",
        "weekly_capacity": 40.0,
        "hourly_cost": 80.0,
    },
    {
        "resource_name": "Sam Torres",
        "email": "sam.torres@zenith.demo",
        "designation": "DevOps Engineer",
        "weekly_capacity": 32.0,
        "hourly_cost": 110.0,
    },
]

# Index: 0=Alex(PM), 1=Sofia(UX), 2=Marcus(BE), 3=Priya(FE), 4=Jordan(QA), 5=Sam(DevOps)

TASK_DATA = [
    # ── Discovery ───────────────────────────────────────────────────────────
    {
        "key": "t01",
        "subject": "Project Kickoff & Scope Definition",
        "task_group": "Discovery",
        "start_date": "2026-02-10",
        "due_date": "2026-02-12",
        "status": "Completed",
        "priority": "High",
        "task_type": "Meeting",
        "estimated_hours": 16.0,
        "actual_hours": 18.0,
        "progress": 100,
        "completed_date": "2026-02-12",
        "resource_idx": 0,
        "milestone_key": "m1",
    },
    {
        "key": "t02",
        "subject": "Stakeholder Interviews",
        "task_group": "Discovery",
        "start_date": "2026-02-11",
        "due_date": "2026-02-18",
        "status": "Completed",
        "priority": "Medium",
        "task_type": "Research",
        "estimated_hours": 24.0,
        "actual_hours": 22.0,
        "progress": 100,
        "completed_date": "2026-02-17",
        "resource_idx": 0,
        "milestone_key": "m1",
    },
    {
        "key": "t03",
        "subject": "Competitor & Market Analysis",
        "task_group": "Discovery",
        "start_date": "2026-02-13",
        "due_date": "2026-02-20",
        "status": "Completed",
        "priority": "Medium",
        "task_type": "Research",
        "estimated_hours": 20.0,
        "actual_hours": 20.0,
        "progress": 100,
        "completed_date": "2026-02-20",
        "resource_idx": 1,
        "milestone_key": "m1",
    },
    {
        "key": "t04",
        "subject": "User Persona Research",
        "task_group": "Discovery",
        "start_date": "2026-02-17",
        "due_date": "2026-02-25",
        "status": "Completed",
        "priority": "High",
        "task_type": "Research",
        "estimated_hours": 32.0,
        "actual_hours": 35.0,
        "progress": 100,
        "completed_date": "2026-02-25",
        "resource_idx": 1,
        "milestone_key": "m1",
    },
    {
        "key": "t05",
        "subject": "Technical Architecture Document",
        "task_group": "Discovery",
        "start_date": "2026-02-20",
        "due_date": "2026-03-01",
        "status": "Completed",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 40.0,
        "actual_hours": 44.0,
        "progress": 100,
        "completed_date": "2026-03-01",
        "resource_idx": 2,
        "milestone_key": "m1",
        "depends_on": ["t01"],
    },
    # ── Design ───────────────────────────────────────────────────────────────
    {
        "key": "t06",
        "subject": "Information Architecture",
        "task_group": "Design",
        "start_date": "2026-03-01",
        "due_date": "2026-03-05",
        "status": "Completed",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 20.0,
        "actual_hours": 18.0,
        "progress": 100,
        "completed_date": "2026-03-05",
        "resource_idx": 1,
        "milestone_key": "m2",
        "depends_on": ["t04", "t05"],
    },
    {
        "key": "t07",
        "subject": "Wireframes — All Screens",
        "task_group": "Design",
        "start_date": "2026-03-03",
        "due_date": "2026-03-09",
        "status": "Completed",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 40.0,
        "actual_hours": 38.0,
        "progress": 100,
        "completed_date": "2026-03-09",
        "resource_idx": 1,
        "milestone_key": "m2",
        "depends_on": ["t06"],
    },
    {
        "key": "t08",
        "subject": "Design System & Component Library",
        "task_group": "Design",
        "start_date": "2026-03-06",
        "due_date": "2026-03-18",
        "status": "In Progress",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 60.0,
        "actual_hours": 28.0,
        "progress": 45,
        "resource_idx": 1,
        "milestone_key": "m2",
        "depends_on": ["t07"],
    },
    {
        "key": "t09",
        "subject": "High-Fidelity UI Mockups",
        "task_group": "Design",
        "start_date": "2026-03-10",
        "due_date": "2026-03-22",
        "status": "In Progress",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 80.0,
        "actual_hours": 16.0,
        "progress": 20,
        "resource_idx": 1,
        "milestone_key": "m2",
        "depends_on": ["t08"],
    },
    {
        "key": "t10",
        "subject": "Interactive Prototype & User Testing",
        "task_group": "Design",
        "start_date": "2026-03-18",
        "due_date": "2026-03-25",
        "status": "Open",
        "priority": "Medium",
        "task_type": "Research",
        "estimated_hours": 32.0,
        "resource_idx": 1,
        "milestone_key": "m2",
        "depends_on": ["t09"],
    },
    # ── Backend ──────────────────────────────────────────────────────────────
    {
        "key": "t11",
        "subject": "Database Schema & Migrations",
        "task_group": "Backend",
        "start_date": "2026-03-05",
        "due_date": "2026-03-10",
        "status": "Completed",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 24.0,
        "actual_hours": 26.0,
        "progress": 100,
        "completed_date": "2026-03-10",
        "resource_idx": 2,
        "milestone_key": "m3",
        "depends_on": ["t05"],
    },
    {
        "key": "t12",
        "subject": "Authentication & User Management",
        "task_group": "Backend",
        "start_date": "2026-03-10",
        "due_date": "2026-03-22",
        "status": "In Progress",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 48.0,
        "actual_hours": 8.0,
        "progress": 15,
        "resource_idx": 2,
        "milestone_key": "m3",
        "depends_on": ["t11"],
    },
    {
        "key": "t13",
        "subject": "Core REST API Endpoints",
        "task_group": "Backend",
        "start_date": "2026-03-18",
        "due_date": "2026-04-04",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 80.0,
        "resource_idx": 2,
        "milestone_key": "m3",
        "depends_on": ["t12"],
    },
    {
        "key": "t14",
        "subject": "Real-Time Sync Engine",
        "task_group": "Backend",
        "start_date": "2026-04-04",
        "due_date": "2026-04-20",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 60.0,
        "resource_idx": 2,
        "milestone_key": "m3",
        "depends_on": ["t13"],
    },
    {
        "key": "t15",
        "subject": "Push Notification Service",
        "task_group": "Backend",
        "start_date": "2026-04-08",
        "due_date": "2026-04-22",
        "status": "Open",
        "priority": "Medium",
        "task_type": "Feature",
        "estimated_hours": 40.0,
        "resource_idx": 5,
        "milestone_key": "m3",
        "depends_on": ["t13"],
    },
    {
        "key": "t16",
        "subject": "Analytics & Event Tracking",
        "task_group": "Backend",
        "start_date": "2026-04-16",
        "due_date": "2026-04-30",
        "status": "Open",
        "priority": "Low",
        "task_type": "Feature",
        "estimated_hours": 32.0,
        "resource_idx": 5,
        "milestone_key": "m3",
        "depends_on": ["t13"],
    },
    # ── Frontend ─────────────────────────────────────────────────────────────
    {
        "key": "t17",
        "subject": "App Scaffolding & Navigation",
        "task_group": "Frontend",
        "start_date": "2026-03-18",
        "due_date": "2026-03-22",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 16.0,
        "resource_idx": 3,
        "milestone_key": "m3",
        "depends_on": ["t08"],
    },
    {
        "key": "t18",
        "subject": "Onboarding & Auth Flow",
        "task_group": "Frontend",
        "start_date": "2026-03-22",
        "due_date": "2026-04-06",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 56.0,
        "resource_idx": 3,
        "milestone_key": "m3",
        "depends_on": ["t17", "t10"],
    },
    {
        "key": "t19",
        "subject": "Home Dashboard & Core Screens",
        "task_group": "Frontend",
        "start_date": "2026-04-06",
        "due_date": "2026-04-20",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 64.0,
        "resource_idx": 3,
        "milestone_key": "m3",
        "depends_on": ["t18", "t12"],
    },
    {
        "key": "t20",
        "subject": "Settings, Profile & Account Screens",
        "task_group": "Frontend",
        "start_date": "2026-04-16",
        "due_date": "2026-04-28",
        "status": "Open",
        "priority": "Medium",
        "task_type": "Feature",
        "estimated_hours": 40.0,
        "resource_idx": 3,
        "milestone_key": "m3",
        "depends_on": ["t19"],
    },
    {
        "key": "t21",
        "subject": "Offline Mode & Background Sync",
        "task_group": "Frontend",
        "start_date": "2026-04-24",
        "due_date": "2026-05-08",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 56.0,
        "resource_idx": 3,
        "milestone_key": "m3",
        "depends_on": ["t14", "t20"],
    },
    # ── QA & Testing ─────────────────────────────────────────────────────────
    {
        "key": "t22",
        "subject": "Unit & Integration Test Suite",
        "task_group": "QA & Testing",
        "start_date": "2026-04-28",
        "due_date": "2026-05-10",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 48.0,
        "resource_idx": 4,
        "milestone_key": "m3",
        "depends_on": ["t21"],
    },
    {
        "key": "t23",
        "subject": "Beta Testing Program",
        "task_group": "QA & Testing",
        "start_date": "2026-05-07",
        "due_date": "2026-05-18",
        "status": "Open",
        "priority": "High",
        "task_type": "Feature",
        "estimated_hours": 40.0,
        "resource_idx": 4,
        "milestone_key": "m4",
        "depends_on": ["t22"],
    },
    {
        "key": "t24",
        "subject": "Performance Optimization",
        "task_group": "QA & Testing",
        "start_date": "2026-05-12",
        "due_date": "2026-05-22",
        "status": "Open",
        "priority": "High",
        "task_type": "Bug",
        "estimated_hours": 32.0,
        "resource_idx": 3,
        "milestone_key": "m4",
        "depends_on": ["t23"],
    },
    {
        "key": "t25",
        "subject": "Security Audit & Penetration Testing",
        "task_group": "QA & Testing",
        "start_date": "2026-05-14",
        "due_date": "2026-05-24",
        "status": "Open",
        "priority": "Urgent",
        "task_type": "Feature",
        "estimated_hours": 32.0,
        "resource_idx": 5,
        "milestone_key": "m4",
        "depends_on": ["t22"],
    },
    # ── Launch Preparation ───────────────────────────────────────────────────
    {
        "key": "t26",
        "subject": "App Store Assets & Screenshots",
        "task_group": "Launch",
        "start_date": "2026-05-10",
        "due_date": "2026-05-20",
        "status": "Open",
        "priority": "Medium",
        "task_type": "Feature",
        "estimated_hours": 24.0,
        "resource_idx": 1,
        "milestone_key": "m4",
        "depends_on": ["t10"],
    },
    {
        "key": "t27",
        "subject": "Marketing Materials & Press Kit",
        "task_group": "Launch",
        "start_date": "2026-05-08",
        "due_date": "2026-05-22",
        "status": "Open",
        "priority": "Medium",
        "task_type": "Feature",
        "estimated_hours": 32.0,
        "resource_idx": 0,
        "milestone_key": "m4",
        "depends_on": ["t10"],
    },
    {
        "key": "t28",
        "subject": "App Store Submission & Review",
        "task_group": "Launch",
        "start_date": "2026-05-22",
        "due_date": "2026-05-28",
        "status": "Open",
        "priority": "Urgent",
        "task_type": "Feature",
        "estimated_hours": 16.0,
        "resource_idx": 0,
        "milestone_key": "m4",
        "depends_on": ["t24", "t25", "t26"],
    },
    {
        "key": "t29",
        "subject": "Launch Day Execution",
        "task_group": "Launch",
        "start_date": "2026-05-31",
        "due_date": "2026-05-31",
        "status": "Open",
        "priority": "Urgent",
        "task_type": "Meeting",
        "estimated_hours": 8.0,
        "resource_idx": 0,
        "milestone_key": "m4",
        "depends_on": ["t28"],
    },
]

MILESTONE_DATA = [
    {
        "key": "m1",
        "milestone_name": "Discovery Complete",
        "due_date": "2026-03-01",
        "status": "Completed",
        "completed_date": "2026-03-01",
        "description": "All research, interviews, and architecture documents finalized. Team aligned on scope and technical approach.",
    },
    {
        "key": "m2",
        "milestone_name": "Design Approved",
        "due_date": "2026-03-25",
        "status": "In Progress",
        "description": "UI/UX design system complete, all screens signed off, interactive prototype validated with users.",
    },
    {
        "key": "m3",
        "milestone_name": "Feature Complete",
        "due_date": "2026-05-08",
        "status": "Upcoming",
        "description": "All backend and frontend features implemented. App functional end-to-end and ready for QA sign-off.",
    },
    {
        "key": "m4",
        "milestone_name": "App Store Launch",
        "due_date": "2026-05-31",
        "status": "Upcoming",
        "description": "App approved in both App Store and Google Play. Marketing live. Launch day execution complete.",
    },
]


# ---------------------------------------------------------------------------
# Creation helpers
# ---------------------------------------------------------------------------

def _create_resources():
    resources = {}
    for r in RESOURCE_DATA:
        if frappe.db.exists("Orga Resource", {"email": r["email"]}):
            name = frappe.db.get_value("Orga Resource", {"email": r["email"]}, "name")
            resources[r["email"]] = name
            continue
        doc = frappe.get_doc({
            "doctype": "Orga Resource",
            "resource_name": r["resource_name"],
            "email": r["email"],
            "designation": r["designation"],
            "weekly_capacity": r["weekly_capacity"],
            "hourly_cost": r["hourly_cost"],
            "status": "Active",
            "resource_type": "Employee",
        })
        doc.insert(ignore_permissions=True)
        resources[r["email"]] = doc.name
    return resources


def _create_project():
    admin_user = frappe.db.get_value("User", {"name": "Administrator"}, "name") or "Administrator"
    doc = frappe.get_doc({
        "doctype": "Orga Project",
        "project_name": PROJECT_NAME,
        "project_code": "ZENITH-001",
        "status": "Active",
        "project_type": "Client",
        "start_date": "2026-02-10",
        "end_date": "2026-05-31",
        "budget": 250000.0,
        "estimated_cost": 230000.0,
        "spent": 68000.0,
        "description": (
            "Full-cycle launch of the Zenith cross-platform mobile application. "
            "Covers discovery, design, backend/frontend development, QA, and go-to-market execution."
        ),
        "health_status": "Yellow",
        "progress": 28,
        "project_manager": admin_user,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _create_milestones(project_name):
    milestones = {}
    for i, m in enumerate(MILESTONE_DATA):
        data = {
            "doctype": "Orga Milestone",
            "milestone_name": m["milestone_name"],
            "project": project_name,
            "due_date": m["due_date"],
            "status": m["status"],
            "description": m.get("description", ""),
            "sort_order": float(i + 1),
        }
        if "completed_date" in m:
            data["completed_date"] = m["completed_date"]
        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True)
        milestones[m["key"]] = doc.name
    return milestones


def _create_tasks(project_name, milestones, resources):
    """Create all tasks (without dependencies — added in a second pass)."""
    resource_names = [r["email"] for r in RESOURCE_DATA]  # index → email

    tasks = {}
    for i, t in enumerate(TASK_DATA):
        resource_email = resource_names[t["resource_idx"]]
        resource_doc_name = resources.get(resource_email)

        data = {
            "doctype": "Orga Task",
            "subject": t["subject"],
            "project": project_name,
            "status": t["status"],
            "priority": t["priority"],
            "task_type": t.get("task_type", "Task"),
            "task_group": t["task_group"],
            "start_date": t["start_date"],
            "due_date": t["due_date"],
            "estimated_hours": t.get("estimated_hours", 0),
            "actual_hours": t.get("actual_hours", 0),
            "progress": t.get("progress", 0),
            "sort_order": float(i + 1),
        }

        if "milestone_key" in t and t["milestone_key"] in milestones:
            data["milestone"] = milestones[t["milestone_key"]]
        if "completed_date" in t:
            data["completed_date"] = t["completed_date"]

        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True)
        tasks[t["key"]] = {"name": doc.name, "resource": resource_doc_name}

    return tasks


def _add_dependencies(tasks):
    """Second pass: add Finish-to-Start dependencies between tasks."""
    for t in TASK_DATA:
        if not t.get("depends_on"):
            continue
        task_name = tasks[t["key"]]["name"]
        doc = frappe.get_doc("Orga Task", task_name)
        for dep_key in t["depends_on"]:
            if dep_key in tasks:
                doc.append("depends_on", {
                    "depends_on": tasks[dep_key]["name"],
                    "dependency_type": "Finish to Start",
                    "lag_days": 0,
                })
        doc.save(ignore_permissions=True)


def _create_assignments(project_name, tasks, resources):
    """Create Orga Assignment records linking resources to tasks."""
    resource_names = [r["email"] for r in RESOURCE_DATA]

    for t in TASK_DATA:
        task_info = tasks[t["key"]]
        resource_email = resource_names[t["resource_idx"]]
        resource_name = resources.get(resource_email)
        if not resource_name:
            continue

        status_map = {
            "Completed": "Completed",
            "In Progress": "In Progress",
            "Open": "Assigned",
        }

        doc = frappe.get_doc({
            "doctype": "Orga Assignment",
            "task": task_info["name"],
            "resource": resource_name,
            "project": project_name,
            "status": status_map.get(t["status"], "Planned"),
            "start_date": t["start_date"],
            "end_date": t["due_date"],
            "allocated_hours": t.get("estimated_hours", 0),
            "actual_hours": t.get("actual_hours", 0),
        })
        doc.insert(ignore_permissions=True)
