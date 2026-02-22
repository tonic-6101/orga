// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Translation utility using Frappe's native i18n system.
 *
 * Reads translated strings from window.__messages (populated by boot data).
 * Falls back to the original English string when no translation exists.
 */

declare global {
  interface Window {
    __messages: Record<string, string>
    lang: string
    __: (text: string, replace?: unknown[] | Record<string, unknown>) => string
  }
}

/**
 * Translate a string, with optional positional or named substitution.
 *
 * Usage:
 *   __('Dashboard')                          → translated string
 *   __('{0} tasks remaining', [count])       → positional substitution
 *   __('{name} updated', { name: 'Alice' })  → named substitution
 */
export function __(text: string, replace?: unknown[] | Record<string, unknown>): string {
  const messages: Record<string, string> = window.__messages || {}
  let translated = messages[text] || text

  if (replace) {
    if (Array.isArray(replace)) {
      for (let i = 0; i < replace.length; i++) {
        translated = translated.replace(new RegExp(`\\{${i}\\}`, 'g'), String(replace[i]))
      }
    } else {
      for (const [key, value] of Object.entries(replace)) {
        translated = translated.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value))
      }
    }
  }

  return translated
}

/** Return the current user language (e.g. "de", "en"). */
export function getLang(): string {
  return window.lang || 'en'
}
