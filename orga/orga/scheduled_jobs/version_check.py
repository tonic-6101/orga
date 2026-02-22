# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Scheduled job: check GitHub for the latest Orga release.

Runs daily. Results are cached in Redis for 24 hours.
"""

import frappe


def check_for_app_updates():
    """Check GitHub for the latest Orga release. Failures are logged silently."""
    from orga.orga.services.version_checker import check_for_updates

    try:
        result = check_for_updates(force=True)
        if result and result.get("update_available"):
            frappe.logger("orga").info(
                f"Orga update available: {result['current_version']} -> {result['latest_version']}"
            )
    except Exception as e:
        frappe.logger("orga").warning(f"Version check failed: {e}")
