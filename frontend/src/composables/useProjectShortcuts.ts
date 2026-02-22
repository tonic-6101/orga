// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Keyboard shortcuts composable for project views.
 *
 * Provides Shift+T for Add Task and Shift+M for Add Milestone shortcuts.
 * Automatically ignores shortcuts when user is typing in form fields.
 */

import { onMounted, onUnmounted } from 'vue'

interface ProjectShortcutsOptions {
  onAddTask: () => void
  onAddMilestone: () => void
}

/**
 * Register keyboard shortcuts for project views.
 *
 * @param options - Callbacks for shortcut actions
 * @param options.onAddTask - Called when Shift+T is pressed
 * @param options.onAddMilestone - Called when Shift+M is pressed
 *
 * @example
 * ```ts
 * useProjectShortcuts({
 *   onAddTask: () => { isTaskModalOpen.value = true },
 *   onAddMilestone: () => { isMilestoneModalOpen.value = true }
 * })
 * ```
 */
export function useProjectShortcuts(options: ProjectShortcutsOptions) {
  function handleKeydown(e: KeyboardEvent) {
    // Ignore if user is typing in an input
    if (
      e.target instanceof HTMLInputElement ||
      e.target instanceof HTMLTextAreaElement ||
      e.target instanceof HTMLSelectElement ||
      (e.target as HTMLElement).isContentEditable
    ) {
      return
    }

    // Shift + T → Add Task
    if (e.shiftKey && e.key === 'T') {
      e.preventDefault()
      options.onAddTask()
    }

    // Shift + M → Add Milestone
    if (e.shiftKey && e.key === 'M') {
      e.preventDefault()
      options.onAddMilestone()
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })
}
