// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, readonly, type Ref, type DeepReadonly } from 'vue'

/**
 * Toast notification types
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info'

/**
 * Toast notification interface
 */
export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration: number
  dismissible: boolean
  createdAt: number
}

/**
 * Options for creating a toast
 */
export interface ToastOptions {
  type?: ToastType
  title: string
  message?: string
  duration?: number
  dismissible?: boolean
}

/**
 * Return type for useToast composable
 */
export interface UseToastReturn {
  toasts: DeepReadonly<Ref<Toast[]>>
  show: (options: ToastOptions) => string
  success: (title: string, message?: string) => string
  error: (title: string, message?: string) => string
  warning: (title: string, message?: string) => string
  info: (title: string, message?: string) => string
  dismiss: (id: string) => void
  dismissAll: () => void
}

// Default durations by type (ms)
const DEFAULT_DURATIONS: Record<ToastType, number> = {
  success: 4000,
  error: 6000,
  warning: 5000,
  info: 4000
}

// Maximum number of toasts visible at once
const MAX_TOASTS = 5

// Shared state - declared outside function for persistence across components
const toasts = ref<Toast[]>([])

// Track timeouts for cleanup
const timeouts = new Map<string, ReturnType<typeof setTimeout>>()

/**
 * Generate unique ID for toast
 */
function generateId(): string {
  return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

/**
 * Toast notification composable
 *
 * Provides a simple API for showing toast notifications throughout the app.
 * State is shared across all components using this composable.
 *
 * @example
 * ```ts
 * const { success, error } = useToast()
 *
 * // Show success toast
 * success('Task updated', 'Changes saved successfully')
 *
 * // Show error toast
 * error('Failed to save', 'Please check your connection')
 * ```
 */
export function useToast(): UseToastReturn {
  /**
   * Show a toast notification
   */
  const show = (options: ToastOptions): string => {
    const id = generateId()
    const type = options.type || 'info'
    const duration = options.duration ?? DEFAULT_DURATIONS[type]

    const toast: Toast = {
      id,
      type,
      title: options.title,
      message: options.message,
      duration,
      dismissible: options.dismissible ?? true,
      createdAt: Date.now()
    }

    // Add to list (newest at the end for bottom-up display)
    toasts.value.push(toast)

    // Limit visible toasts
    if (toasts.value.length > MAX_TOASTS) {
      const removed = toasts.value.shift()
      if (removed && timeouts.has(removed.id)) {
        clearTimeout(timeouts.get(removed.id))
        timeouts.delete(removed.id)
      }
    }

    // Auto-dismiss after duration (if duration > 0)
    if (duration > 0) {
      const timeout = setTimeout(() => {
        dismiss(id)
      }, duration)
      timeouts.set(id, timeout)
    }

    return id
  }

  /**
   * Show success toast
   */
  const success = (title: string, message?: string): string => {
    return show({ type: 'success', title, message })
  }

  /**
   * Show error toast
   */
  const error = (title: string, message?: string): string => {
    return show({ type: 'error', title, message })
  }

  /**
   * Show warning toast
   */
  const warning = (title: string, message?: string): string => {
    return show({ type: 'warning', title, message })
  }

  /**
   * Show info toast
   */
  const info = (title: string, message?: string): string => {
    return show({ type: 'info', title, message })
  }

  /**
   * Dismiss a specific toast
   */
  const dismiss = (id: string): void => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }

    // Clear timeout if exists
    if (timeouts.has(id)) {
      clearTimeout(timeouts.get(id))
      timeouts.delete(id)
    }
  }

  /**
   * Dismiss all toasts
   */
  const dismissAll = (): void => {
    toasts.value = []

    // Clear all timeouts
    timeouts.forEach((timeout) => clearTimeout(timeout))
    timeouts.clear()
  }

  return {
    toasts: readonly(toasts),
    show,
    success,
    error,
    warning,
    info,
    dismiss,
    dismissAll
  }
}
