# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

app_name = "orga"
app_title = "Orga"
app_publisher = "Orga"
app_description = "Orga - Project Management System"
app_email = "info@orga.localhost"
app_license = "AGPL-3.0-or-later"

# Apps
# ------------------

required_apps = ["frappe", "dock"]

# Website Route Rules (for Vue SPA)
website_route_rules = [
    {"from_route": "/orga/<path:app_path>", "to_route": "orga"},
    # Legacy Client Portal redirects (deprecated - now using Vue at /orga/portal)
    {"from_route": "/orga_portal", "to_route": "orga"},
    {"from_route": "/orga_portal/project/<project>", "to_route": "orga"},
    {"from_route": "/orga_portal/support", "to_route": "orga"},
]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "orga",
        "logo": "/assets/orga/images/orga-logo.svg",
        "title": "Orga",
        "route": "/orga",
    }
]

# Dock ecosystem integration
# Declares Orga to Dock's app switcher — read at boot via frappe.get_hooks("dock_app_registry")
dock_app_registry = {
    "label": "Orga",
    "icon": "/assets/orga/images/orga-icon.svg",
    "color": "#16a34a",
    "route": "/orga",
}

dock_search_sections = [
    {
        "label": "Projects",
        "doctype": "Orga Project",
        "search_fields": ["project_name", "project_code", "description"],
        "display_field": "project_name",
        "description_field": "project_code",
        "status_field": "status",
        "route_template": "/orga/projects/{name}",
    },
    {
        "label": "Tasks",
        "doctype": "Orga Task",
        "search_fields": ["subject", "description"],
        "display_field": "subject",
        "description_field": "project",
        "status_field": "status",
        "meta_field": "priority",
        "category": "task",
        "route_template": "/orga/my-tasks",
    },
    {
        "label": "Team",
        "doctype": "Orga Resource",
        "search_fields": ["resource_name", "department"],
        "display_field": "resource_name",
        "description_field": "department",
        "status_field": "status",
        "route_template": "/orga/people",
    },
    {
        "label": "Milestones",
        "doctype": "Orga Milestone",
        "search_fields": ["milestone_name", "description"],
        "display_field": "milestone_name",
        "description_field": "project",
        "status_field": "status",
        "meta_field": "due_date",
        "route_template": "/orga/projects/{name}",
    },
    {
        "label": "Events",
        "doctype": "Orga Appointment",
        "search_fields": ["subject", "description"],
        "display_field": "subject",
        "description_field": "appointment_type",
        "route_template": "/orga/calendar",
    },
    {
        "label": "Task Templates",
        "doctype": "Orga Task Template",
        "search_fields": ["template_name", "description"],
        "display_field": "template_name",
        "description_field": "category",
        "route_template": "/app/orga-task-template/{name}",
    },
]
dock_settings_sections = [
    {
        "label": "Orga",
        "icon": "/assets/orga/images/orga-icon.svg",
        "icon_url": "/assets/orga/images/orga-icon.svg",
        "route": "orga",
        "component": "OrgaSettings",
        "bundle": "/assets/orga/js/orga-settings.esm.js",
        "sections": [
            {"label": "Defaults", "key": "defaults"},
            {"label": "Features", "key": "features"},
            {"label": "Notifications", "key": "notifications"},
            {"label": "Updates", "key": "updates"},
        ],
    }
]

dock_bridges = [
    {
        "label": "ERPNext Employee Sync",
        "target_app": "erpnext",
        "target_doctype": "Employee",
        "source_doctype": "Orga Resource",
        "direction": "one_way",
        "status_endpoint": "orga.orga.integrations.erpnext.get_sync_status",
        "sync_endpoint": "orga.orga.integrations.erpnext.sync_all_resources_from_employees",
        "settings_route": "/dock/settings/app/orga",
    },
    {
        "label": "Frappe Projects Sync",
        "target_app": "frappe",
        "target_doctype": "Project",
        "source_doctype": "Orga Project",
        "direction": "two_way",
        "status_endpoint": "orga.orga.integrations.frappe_projects.get_sync_status",
        "sync_endpoint": "orga.orga.integrations.frappe_projects.sync_all_projects",
        "settings_route": "/dock/settings/app/orga",
    },
]

dock_notification_types = [
    {"type": "task_assigned", "label": "Task Assigned", "icon": "check-square"},
    {"type": "task_status_change", "label": "Task Status Changed", "icon": "refresh-cw"},
    {"type": "deadline_reminder", "label": "Deadline Reminder", "icon": "clock"},
    {"type": "milestone_due", "label": "Milestone Due", "icon": "flag"},
    {"type": "appointment_reminder", "label": "Appointment Reminder", "icon": "calendar"},
]

dock_guest_views = [
    {
        "view_id": "orga.project_status",
        "label": "Project Status",
        "route": "/orga/guest/project/{name}",
    },
]

watch_timer_contexts = [
    {
        "doctype": "Orga Project",
        "label": "Project",
        "search_fields": ["project_name", "project_code"],
        "display_field": "project_name",
    },
    {
        "doctype": "Orga Task",
        "label": "Task",
        "search_fields": ["subject"],
        "display_field": "subject",
        "parent_field": "project",
        "parent_doctype": "Orga Project",
    },
    {
        "doctype": "Orga Appointment",
        "label": "Event",
        "search_fields": ["subject"],
        "display_field": "subject",
    },
]

# Activity feed — Dock aggregates Version + Comment for these doctypes
dock_activity_sources = [
    {
        "doctype": "Orga Task",
        "label": "Task",
        "icon": "check-square",
        "events": ["after_insert", "on_update", "on_trash"],
        "tracked_fields": ["status", "assigned_to", "priority", "due_date"],
        "summary_template": "{modified_by} {action} task {subject}",
    },
    {
        "doctype": "Orga Milestone",
        "label": "Milestone",
        "icon": "flag",
        "events": ["after_insert", "on_update"],
        "tracked_fields": ["status", "progress"],
        "summary_template": "{modified_by} {action} milestone {milestone_name}",
    },
    {
        "doctype": "Orga Appointment",
        "label": "Appointment",
        "icon": "calendar",
        "events": ["after_insert", "on_update"],
        "tracked_fields": ["status", "appointment_type"],
        "summary_template": "{modified_by} {action} appointment {subject}",
    },
    {
        "doctype": "Orga Project",
        "label": "Project",
        "icon": "folder",
        "events": ["after_insert", "on_update"],
        "tracked_fields": ["status", "progress"],
        "summary_template": "{modified_by} {action} project {project_name}",
    },
]

# Custom activity renderers for richer summaries
dock_activity_renderers = {
    "Orga Task": "orga.orga.integrations.dock_activity.render_task",
    "Orga Appointment": "orga.orga.integrations.dock_activity.render_appointment",
    "Orga Milestone": "orga.orga.integrations.dock_activity.render_milestone",
}

dock_calendar_sources = {
    "event_label": "Orga",
    "event_types": [
        "orga.appointment", "orga.task", "orga.milestone",
    ],
    "create_route_template": "/orga/appointments/new?date={date}",
}

dock_backfill_calendar = "orga.orga.integrations.dock_calendar.backfill_dock_events"

dock_note_actions = [
    {
        "action": "convert_to_task",
        "label": "Convert to Task",
        "icon": "check-square",
        "handler": "orga.orga.integrations.dock_notes.convert_to_task",
    },
]

dock_people_context = "orga.orga.integrations.dock_people.get_people_context"

dock_calendar_context = "orga.orga.integrations.dock_calendar_context.get_calendar_context"

# Include in HTML Head
# --------------------

# app_include_css = ["/assets/orga/css/orga.css"]
# app_include_js = ["/assets/orga/js/orga.bundle.js"]

# Fixtures
# --------
fixtures = [
    {"dt": "Module Def", "filters": [["module_name", "=", "Orga"]]},
    {"dt": "Page", "filters": [["module", "=", "Orga"]]},
    {"dt": "Workspace", "filters": [["module", "=", "Orga"]]},
    {"dt": "Role", "filters": [["role_name", "in", ["Orga Manager", "Orga User", "Orga Client"]]]},
    {"dt": "Custom Field", "filters": [["dt", "=", "Dock Event"], ["fieldname", "like", "orga_%"]]},
    {"dt": "Custom Field", "filters": [["dt", "=", "Contact"], ["fieldname", "like", "orga_client%"]]},
    {"dt": "Custom Field", "filters": [["dt", "=", "Contact"], ["fieldname", "=", "is_orga_client"]]},
]

# Include CSS in web pages
# ------------------------

# web_include_css = "/assets/orga/css/orga-portal.css"
# web_include_js = "/assets/orga/js/orga.js"

# Include CSS/JS for specific doctypes
# ------------------------------------

# doctype_css = {"DocType": "public/css/doctype.css"}
# doctype_js = {"DocType": "public/js/doctype.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
role_home_page = {
	"Orga Client": "orga/portal"
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "orga.install.before_install"
after_install = "orga.install.after_install"
after_migrate = "orga.install.setup_watch_custom_fields"

# Uninstallation
# ------------

# before_uninstall = "orga.uninstall.before_uninstall"
# after_uninstall = "orga.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "orga.utils.before_app_install"
# after_app_install = "orga.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "orga.utils.before_app_uninstall"
# after_app_uninstall = "orga.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "orga.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Orga Task": {
		"after_insert": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.webhooks.dispatcher.trigger_on_insert",
		],
		"on_update": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.integrations.frappe_projects.on_orga_task_update",
			"orga.orga.webhooks.dispatcher.trigger_on_update",
			"orga.orga.integrations.dock_calendar.sync_task",
			"orga.orga.integrations.dock_notification.on_task_update",
		],
		"on_trash": [
			"orga.orga.webhooks.dispatcher.trigger_on_trash",
			"orga.orga.integrations.dock_calendar.remove_event",
		],
	},
	"Orga Project": {
		"after_insert": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.webhooks.dispatcher.trigger_on_insert"
		],
		"on_update": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.integrations.frappe_projects.on_orga_project_update",
			"orga.orga.webhooks.dispatcher.trigger_on_update"
		],
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
	},
	"Orga Assignment": {
		"after_insert": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.webhooks.dispatcher.trigger_on_insert"
		],
		"on_update": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.webhooks.dispatcher.trigger_on_update"
		],
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
	},
	"Orga Resource": {
		"before_save": "orga.orga.integrations.erpnext.on_resource_before_save",
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert",
		"on_update": [
			"orga.orga.integrations.erpnext.on_resource_update",
			"orga.orga.webhooks.dispatcher.trigger_on_update"
		],
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
	},
	"Orga Appointment": {
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert",
		"on_update": [
			"orga.orga.webhooks.dispatcher.trigger_on_update",
			"orga.orga.integrations.dock_calendar.sync_appointment",
		],
		"on_trash": [
			"orga.orga.webhooks.dispatcher.trigger_on_trash",
			"orga.orga.integrations.dock_calendar.remove_event",
		]
	},
	"Orga Milestone": {
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert",
		"on_update": [
			"orga.orga.webhooks.dispatcher.trigger_on_update",
			"orga.orga.integrations.dock_calendar.sync_milestone",
			"orga.orga.integrations.dock_notification.on_milestone_update",
		],
		"on_trash": "orga.orga.integrations.dock_calendar.remove_event",
	},
	"Watch Entry": {
		"on_update": "orga.orga.integrations.watch.on_watch_entry_update",
		"on_trash": "orga.orga.integrations.watch.on_watch_entry_delete",
	},
	"Orga Client": {
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert",
		"on_update": "orga.orga.webhooks.dispatcher.trigger_on_update",
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
	},
	"Employee": {
		"on_update": "orga.orga.integrations.erpnext.on_employee_update"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		# Send deadline reminder notifications each morning
		"orga.orga.scheduled_jobs.deadline_reminders.send_deadline_reminders",
		# Trail start dates for Open tasks with auto_trail_start enabled
		"orga.orga.scheduled_jobs.trailing_dates.update_trailing_start_dates",
		# Check GitHub for app updates
		"orga.orga.scheduled_jobs.version_check.check_for_app_updates"
	],
	"weekly": [],
	"hourly": [
		# Frappe Projects sync (runs hourly, checks settings internally)
		"orga.orga.integrations.frappe_projects.scheduled_sync"
	],
	"cron": {
		# Run appointment reminders every 15 minutes
		"*/15 * * * *": [
			"orga.orga.scheduled_jobs.send_reminders.send_appointment_reminders"
		],
		# Run project health calculator every 4 hours
		"0 */4 * * *": [
			"orga.orga.services.health_calculator.update_all_project_health"
		]
	}
}

# Jana integration (AI assistant permissions)
# ---------------

jana_briefing_source = "orga.orga.api.jana_briefing.get_briefing"

jana_permissions = {
	"doctypes": {
		"read": [
			"Orga Project", "Orga Task", "Orga Milestone",
			"Orga Appointment", "Orga Resource",
		],
		"create": [],
		"update": [],
		"never": [],
	},
	"endpoints": [
		{
			"label": "Orga — Dashboard",
			"description": "Project stats, task summaries, health indicators",
			"methods": [
				"orga.orga.api.dashboard.get_stats",
				"orga.orga.api.dashboard.get_project_summary",
				"orga.orga.api.dashboard.get_task_summary",
				"orga.orga.api.dashboard.get_milestone_summary",
				"orga.orga.api.dashboard.get_health_check",
			],
			"scoping": "user",
		},
		{
			"label": "Orga — Calendar",
			"description": "Appointments and calendar events",
			"methods": [
				"orga.orga.api.appointment.get_appointments",
				"orga.orga.api.appointment.get_my_appointments",
			],
			"scoping": "user",
		},
		{
			"label": "Orga — Reports",
			"description": "Milestone and task completion reports",
			"methods": [
				"orga.orga.api.report.get_milestone_report",
				"orga.orga.api.report.get_task_completion_report",
			],
			"scoping": "user",
		},
		{
			"label": "Orga — Daily Briefing",
			"description": "Aggregated briefing data for Jana Daily Briefing agent",
			"methods": [
				"orga.orga.api.jana_briefing.get_briefing",
			],
			"scoping": "user",
		},
	],
}

# Testing
# -------

# before_tests = "orga.install.before_tests"

# Overriding Methods
# ------------------------------

# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "orga.event.get_events"
# }

# Each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "orga.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = []

# Request Events
# ----------------
# before_request = ["orga.utils.before_request"]
# after_request = ["orga.utils.after_request"]

# Job Events
# ----------
# before_job = ["orga.utils.before_job"]
# after_job = ["orga.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"orga.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation / i18n
# ------------------
# Frappe's build-message-files scans .py, .js, .vue, .html but NOT .ts files.
# This hook tells Frappe to also extract translatable strings from TypeScript files.

def get_messages():
    """Extract translatable strings from TypeScript files in the Vue frontend."""
    import os
    import re

    messages = []
    ts_pattern = re.compile(r"""__\(\s*(['"])(.*?)\1""")
    frontend_dir = os.path.join(os.path.dirname(__file__), "public", "frontend")
    src_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")

    for search_dir in [frontend_dir, src_dir]:
        if not os.path.isdir(search_dir):
            continue
        for root, _dirs, files in os.walk(search_dir):
            for fname in files:
                if not fname.endswith(".ts"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line_no, line in enumerate(f, 1):
                            for match in ts_pattern.finditer(line):
                                messages.append((fpath + ":" + str(line_no), match.group(2)))
                except Exception:
                    pass

    return messages
