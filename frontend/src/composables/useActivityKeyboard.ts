// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Keyboard shortcuts composable for the Activity feed.
 *
 * Provides Linear-style J/K navigation, Enter to open panel,
 * Escape to close, P to pin, A to archive, R to reply, ? for help.
 *
 * Automatically ignores shortcuts when user is typing in form fields.
 */

import { onMounted, onUnmounted } from 'vue'

export interface ActivityKeyboardShortcut {
  key: string
  label: string
  description: string
}

export const ACTIVITY_SHORTCUTS: ActivityKeyboardShortcut[] = [
  { key: 'J', label: 'J', description: 'Select next activity' },
  { key: 'K', label: 'K', description: 'Select previous activity' },
  { key: 'Enter', label: 'Enter', description: 'Open Manager panel for selected' },
  { key: 'Escape', label: 'Esc', description: 'Close panel / deselect' },
  { key: 'P', label: 'P', description: 'Toggle pin on selected' },
  { key: 'A', label: 'A', description: 'Toggle archive on selected' },
  { key: 'R', label: 'R', description: 'Focus comment input for selected' },
  { key: 'M', label: 'M', description: 'Mark all as read' },
  { key: '?', label: '?', description: 'Show keyboard shortcuts' },
]

interface ActivityKeyboardOptions {
  onNext: () => void
  onPrevious: () => void
  onOpen: () => void
  onClose: () => void
  onTogglePin: () => void
  onToggleArchive: () => void
  onReply: () => void
  onMarkRead: () => void
  onShowHelp: () => void
}

function isInputFocused(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement ||
    target.isContentEditable ||
    target.closest('.ProseMirror') !== null
  )
}

export function useActivityKeyboard(options: ActivityKeyboardOptions) {
  function handleKeydown(e: KeyboardEvent) {
    // Ignore when typing in inputs
    if (isInputFocused(e.target)) return

    // Ignore with modifier keys (except shift for ?)
    if (e.ctrlKey || e.metaKey || e.altKey) return

    switch (e.key) {
      case 'j':
      case 'J':
        e.preventDefault()
        options.onNext()
        break

      case 'k':
      case 'K':
        e.preventDefault()
        options.onPrevious()
        break

      case 'Enter':
        e.preventDefault()
        options.onOpen()
        break

      case 'Escape':
        e.preventDefault()
        options.onClose()
        break

      case 'p':
      case 'P':
        e.preventDefault()
        options.onTogglePin()
        break

      case 'a':
      case 'A':
        e.preventDefault()
        options.onToggleArchive()
        break

      case 'r':
      case 'R':
        e.preventDefault()
        options.onReply()
        break

      case 'm':
      case 'M':
        e.preventDefault()
        options.onMarkRead()
        break

      case '?':
        e.preventDefault()
        options.onShowHelp()
        break
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
