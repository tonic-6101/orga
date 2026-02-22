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

# required_apps = []

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
    {"dt": "Role", "filters": [["role_name", "in", ["Orga Manager", "Orga User", "Orga Client"]]]}
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
			"orga.orga.webhooks.dispatcher.trigger_on_insert"
		],
		"on_update": [
			"orga.orga.automation.engine.run_automation",
			"orga.orga.integrations.frappe_projects.on_orga_task_update",
			"orga.orga.webhooks.dispatcher.trigger_on_update"
		],
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
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
		"on_update": "orga.orga.webhooks.dispatcher.trigger_on_update",
		"on_trash": "orga.orga.webhooks.dispatcher.trigger_on_trash"
	},
	"Orga Milestone": {
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert",
		"on_update": "orga.orga.webhooks.dispatcher.trigger_on_update"
	},
	"Orga Time Log": {
		"after_insert": "orga.orga.webhooks.dispatcher.trigger_on_insert"
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
	"weekly": [
		# Clean up old read notifications
		"orga.orga.scheduled_jobs.deadline_reminders.cleanup_old_notifications"
	],
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

ignore_links_on_delete = ["Orga Notification"]

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
