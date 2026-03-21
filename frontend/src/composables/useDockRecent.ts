// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Dock recent items integration.
 *
 * Tracks visited Orga records in Dock's recent items list so they
 * appear in the top bar's "Recent" dropdown across all apps.
 *
 * Usage:
 *   const { trackRecent } = useDockRecent()
 *   onMounted(() => trackRecent('Orga Project', project.name, project.project_name))
 */

import { frappeRequest } from 'frappe-ui'

// Icon mapping for Orga doctypes shown in Dock's recent list
const DOCTYPE_ICONS: Record<string, string> = {
  'Orga Project': 'folder',
  'Orga Task': 'check-square',
  'Orga Appointment': 'calendar',
  'Orga Milestone': 'flag',
  'Orga Resource': 'users',
}

export function useDockRecent() {
  /**
   * Track a visited Orga record in Dock's recent items.
   * Silently no-ops if Dock is not installed or recent items are disabled.
   */
  async function trackRecent(doctype: string, docname: string, label: string): Promise<void> {
    try {
      await frappeRequest({
        url: '/api/method/dock.api.recent.track',
        params: {
          app: 'orga',
          doctype,
          docname,
          label,
          icon: DOCTYPE_ICONS[doctype] || '',
        },
      })
    } catch {
      // Dock not installed or recent items disabled — silent no-op
    }
  }

  return { trackRecent }
}
