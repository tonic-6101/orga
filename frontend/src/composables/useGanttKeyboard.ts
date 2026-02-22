// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * useGanttKeyboard - Keyboard shortcuts composable for Gantt chart operations
 *
 * Provides keyboard-first editing capabilities for power users:
 * - E: Edit selected task inline
 * - D: Add dependency
 * - Tab: Move between fields
 * - Enter: Save changes
 * - Escape: Cancel edit / Close panel
 * - Arrow Up/Down: Navigate dependency chain
 * - Cmd/Ctrl + Z: Undo last change
 */

import { ref, onMounted, onUnmounted, computed, type Ref } from 'vue'

/**
 * Undo history entry
 */
interface UndoEntry {
  id: string
  taskId: string
  field: string
  oldValue: unknown
  newValue: unknown
  timestamp: number
}

/**
 * Keyboard shortcut configuration
 */
interface ShortcutConfig {
  key: string
  modifiers?: {
    meta?: boolean
    ctrl?: boolean
    shift?: boolean
    alt?: boolean
  }
  action: string
  description: string
}

/**
 * Options for useGanttKeyboard composable
 */
interface UseGanttKeyboardOptions {
  /** Callback when E key pressed - start editing */
  onEdit?: () => void
  /** Callback when D key pressed - add dependency */
  onAddDependency?: () => void
  /** Callback when Enter pressed - save changes */
  onSave?: () => void
  /** Callback when Escape pressed - cancel/close */
  onCancel?: () => void
  /** Callback when arrow up pressed - navigate up dependency chain */
  onNavigateUp?: () => void
  /** Callback when arrow down pressed - navigate down dependency chain */
  onNavigateDown?: () => void
  /** Callback when Tab pressed - move to next field */
  onNextField?: () => void
  /** Callback when Shift+Tab pressed - move to previous field */
  onPrevField?: () => void
  /** Callback when Cmd/Ctrl+Z pressed - undo */
  onUndo?: (entry: UndoEntry) => void
  /** Callback when Cmd/Ctrl+Shift+Z pressed - redo */
  onRedo?: (entry: UndoEntry) => void
  /** Function to check if keyboard shortcuts are enabled */
  enabled?: () => boolean
  /** Maximum number of undo entries to keep */
  maxUndoHistory?: number
}

/**
 * Gantt keyboard shortcuts composable
 */
export function useGanttKeyboard(options: UseGanttKeyboardOptions = {}) {
  const {
    onEdit,
    onAddDependency,
    onSave,
    onCancel,
    onNavigateUp,
    onNavigateDown,
    onNextField,
    onPrevField,
    onUndo,
    onRedo,
    enabled = () => true,
    maxUndoHistory = 50
  } = options

  // Internal state
  const isEditing = ref(false)
  const lastShortcut = ref<string | null>(null)
  const undoStack = ref<UndoEntry[]>([])
  const redoStack = ref<UndoEntry[]>([])

  // Computed values
  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  // Shortcut definitions for display
  const shortcuts: ShortcutConfig[] = [
    { key: 'e', action: 'edit', description: 'Edit selected task' },
    { key: 'd', action: 'addDependency', description: 'Add dependency' },
    { key: 'Tab', action: 'nextField', description: 'Next field' },
    { key: 'Tab', modifiers: { shift: true }, action: 'prevField', description: 'Previous field' },
    { key: 'Enter', action: 'save', description: 'Save changes' },
    { key: 'Escape', action: 'cancel', description: 'Cancel / Close' },
    { key: 'ArrowUp', action: 'navigateUp', description: 'Navigate up dependency chain' },
    { key: 'ArrowDown', action: 'navigateDown', description: 'Navigate down dependency chain' },
    { key: 'z', modifiers: { meta: true }, action: 'undo', description: 'Undo (Mac)' },
    { key: 'z', modifiers: { ctrl: true }, action: 'undo', description: 'Undo (Windows/Linux)' },
    { key: 'z', modifiers: { meta: true, shift: true }, action: 'redo', description: 'Redo (Mac)' },
    { key: 'z', modifiers: { ctrl: true, shift: true }, action: 'redo', description: 'Redo (Windows/Linux)' }
  ]

  /**
   * Check if the current focus is on an input element
   */
  function isInputFocused(): boolean {
    const activeElement = document.activeElement
    if (!activeElement) return false
    return (
      activeElement instanceof HTMLInputElement ||
      activeElement instanceof HTMLTextAreaElement ||
      activeElement instanceof HTMLSelectElement ||
      activeElement.getAttribute('contenteditable') === 'true'
    )
  }

  /**
   * Check if modifiers match
   */
  function matchModifiers(
    event: KeyboardEvent,
    modifiers?: ShortcutConfig['modifiers']
  ): boolean {
    if (!modifiers) {
      return !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey
    }
    return (
      (modifiers.meta === undefined || event.metaKey === modifiers.meta) &&
      (modifiers.ctrl === undefined || event.ctrlKey === modifiers.ctrl) &&
      (modifiers.shift === undefined || event.shiftKey === modifiers.shift) &&
      (modifiers.alt === undefined || event.altKey === modifiers.alt)
    )
  }

  /**
   * Flash feedback for shortcut activation
   */
  function flashShortcutFeedback(shortcut: string): void {
    lastShortcut.value = shortcut
    setTimeout(() => {
      lastShortcut.value = null
    }, 300)
  }

  /**
   * Main keyboard event handler
   */
  function handleKeydown(event: KeyboardEvent): void {
    if (!enabled()) return

    const inputFocused = isInputFocused()

    // Handle input-specific shortcuts
    if (inputFocused) {
      if (event.key === 'Escape') {
        onCancel?.()
        flashShortcutFeedback('cancel')
        event.preventDefault()
        return
      }

      if (event.key === 'Enter' && !event.shiftKey) {
        onSave?.()
        flashShortcutFeedback('save')
        event.preventDefault()
        return
      }

      // Allow Tab in inputs for field navigation
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          onPrevField?.()
          flashShortcutFeedback('prevField')
        } else {
          onNextField?.()
          flashShortcutFeedback('nextField')
        }
        event.preventDefault()
        return
      }

      // Allow undo/redo in inputs
      if (event.key === 'z' && (event.metaKey || event.ctrlKey)) {
        if (event.shiftKey) {
          handleRedo()
          flashShortcutFeedback('redo')
        } else {
          handleUndo()
          flashShortcutFeedback('undo')
        }
        event.preventDefault()
        return
      }

      // Don't capture other keys when in input
      return
    }

    // Non-input shortcuts
    switch (event.key.toLowerCase()) {
      case 'e':
        if (!event.metaKey && !event.ctrlKey && !event.altKey) {
          onEdit?.()
          isEditing.value = true
          flashShortcutFeedback('edit')
          event.preventDefault()
        }
        break

      case 'd':
        if (!event.metaKey && !event.ctrlKey && !event.altKey) {
          onAddDependency?.()
          flashShortcutFeedback('addDependency')
          event.preventDefault()
        }
        break

      case 'escape':
        onCancel?.()
        isEditing.value = false
        flashShortcutFeedback('cancel')
        event.preventDefault()
        break

      case 'arrowup':
        onNavigateUp?.()
        flashShortcutFeedback('navigateUp')
        event.preventDefault()
        break

      case 'arrowdown':
        onNavigateDown?.()
        flashShortcutFeedback('navigateDown')
        event.preventDefault()
        break

      case 'z':
        if (event.metaKey || event.ctrlKey) {
          if (event.shiftKey) {
            handleRedo()
            flashShortcutFeedback('redo')
          } else {
            handleUndo()
            flashShortcutFeedback('undo')
          }
          event.preventDefault()
        }
        break
    }
  }

  /**
   * Push a change to the undo stack
   */
  function pushUndoEntry(taskId: string, field: string, oldValue: unknown, newValue: unknown): void {
    const entry: UndoEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      taskId,
      field,
      oldValue,
      newValue,
      timestamp: Date.now()
    }

    undoStack.value.push(entry)

    // Limit stack size
    if (undoStack.value.length > maxUndoHistory) {
      undoStack.value.shift()
    }

    // Clear redo stack on new change
    redoStack.value = []
  }

  /**
   * Handle undo action
   */
  function handleUndo(): void {
    if (undoStack.value.length === 0) return

    const entry = undoStack.value.pop()!
    redoStack.value.push(entry)
    onUndo?.(entry)
  }

  /**
   * Handle redo action
   */
  function handleRedo(): void {
    if (redoStack.value.length === 0) return

    const entry = redoStack.value.pop()!
    undoStack.value.push(entry)
    onRedo?.(entry)
  }

  /**
   * Clear undo/redo history
   */
  function clearHistory(): void {
    undoStack.value = []
    redoStack.value = []
  }

  /**
   * Set editing state
   */
  function setEditing(value: boolean): void {
    isEditing.value = value
  }

  /**
   * Get shortcut hint text for a key
   */
  function getShortcutHint(action: string): string {
    const shortcut = shortcuts.find(s => s.action === action)
    if (!shortcut) return ''

    let hint = ''
    if (shortcut.modifiers?.meta) hint += '⌘'
    if (shortcut.modifiers?.ctrl) hint += 'Ctrl+'
    if (shortcut.modifiers?.shift) hint += '⇧'
    if (shortcut.modifiers?.alt) hint += '⌥'

    const keyDisplay = shortcut.key === 'ArrowUp' ? '↑'
      : shortcut.key === 'ArrowDown' ? '↓'
      : shortcut.key === 'Tab' ? '⇥'
      : shortcut.key === 'Enter' ? '↵'
      : shortcut.key === 'Escape' ? 'Esc'
      : shortcut.key.toUpperCase()

    return hint + keyDisplay
  }

  /**
   * Format shortcut for display (cross-platform)
   */
  function formatShortcut(action: string): string {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0

    switch (action) {
      case 'undo':
        return isMac ? '⌘Z' : 'Ctrl+Z'
      case 'redo':
        return isMac ? '⌘⇧Z' : 'Ctrl+Shift+Z'
      case 'save':
        return '↵ Enter'
      case 'cancel':
        return 'Esc'
      case 'edit':
        return 'E'
      case 'addDependency':
        return 'D'
      case 'navigateUp':
        return '↑'
      case 'navigateDown':
        return '↓'
      case 'nextField':
        return '⇥ Tab'
      case 'prevField':
        return '⇧⇥'
      default:
        return getShortcutHint(action)
    }
  }

  // Setup and cleanup
  onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })

  return {
    // State
    isEditing,
    lastShortcut,
    canUndo,
    canRedo,

    // Methods
    pushUndoEntry,
    handleUndo,
    handleRedo,
    clearHistory,
    setEditing,
    getShortcutHint,
    formatShortcut,

    // Config
    shortcuts
  }
}

/**
 * Shortcut reference for displaying in UI
 */
export const GANTT_SHORTCUTS = [
  { key: 'E', description: 'Edit selected task inline' },
  { key: 'D', description: 'Add dependency' },
  { key: 'Tab', description: 'Move between fields' },
  { key: 'Enter', description: 'Save changes' },
  { key: 'Escape', description: 'Cancel edit / Close panel' },
  { key: '↑ / ↓', description: 'Navigate dependency chain' },
  { key: 'Cmd/Ctrl + Z', description: 'Undo last change' },
  { key: 'Cmd/Ctrl + Shift + Z', description: 'Redo' }
] as const
