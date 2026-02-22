// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Theme composable for Orga
 *
 * Provides dark/light mode management with:
 * - localStorage persistence
 * - System preference detection (auto mode)
 * - Reactive theme state
 * - SSR-safe initialization
 */

import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'
export type ResolvedTheme = 'light' | 'dark'

export interface UseThemeReturn {
  /** Current theme mode setting (light/dark/auto) */
  mode: Ref<ThemeMode>
  /** Resolved theme after applying auto detection */
  resolvedTheme: ComputedRef<ResolvedTheme>
  /** Whether dark mode is currently active */
  isDark: ComputedRef<boolean>
  /** Toggle between light and dark (skips auto) */
  toggle: () => void
  /** Set specific theme mode */
  setMode: (mode: ThemeMode) => void
}

const STORAGE_KEY = 'orga-theme'
const DARK_CLASS = 'dark'

/**
 * Get system color scheme preference
 */
function getSystemPreference(): ResolvedTheme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * Get stored theme or default to 'auto' (system preference)
 */
function getStoredTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'auto'
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'auto') {
    return stored
  }
  return 'auto'
}

/**
 * Apply theme class to document
 */
function applyTheme(theme: ResolvedTheme): void {
  if (typeof document === 'undefined') return

  const root = document.documentElement
  if (theme === 'dark') {
    root.classList.add(DARK_CLASS)
  } else {
    root.classList.remove(DARK_CLASS)
  }
}

// Shared reactive state (singleton pattern)
const mode = ref<ThemeMode>(getStoredTheme())

// Initialize theme on module load
if (typeof window !== 'undefined') {
  const initialResolved = mode.value === 'auto' ? getSystemPreference() : mode.value
  applyTheme(initialResolved)

  // Listen for system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (mode.value === 'auto') {
      applyTheme(e.matches ? 'dark' : 'light')
    }
  })
}

/**
 * Theme composable
 *
 * @example
 * ```vue
 * <script setup lang="ts">
 * import { useTheme } from '@/composables/useTheme'
 *
 * const { isDark, toggle, setMode } = useTheme()
 * </script>
 *
 * <template>
 *   <button @click="toggle">
 *     <i :class="isDark ? 'fa-sun' : 'fa-moon'" />
 *   </button>
 * </template>
 * ```
 */
export function useTheme(): UseThemeReturn {
  /**
   * Resolved theme considering auto mode
   */
  const resolvedTheme = computed<ResolvedTheme>(() => {
    if (mode.value === 'auto') {
      return getSystemPreference()
    }
    return mode.value
  })

  /**
   * Whether dark mode is currently active
   */
  const isDark = computed(() => resolvedTheme.value === 'dark')

  /**
   * Toggle between light and dark mode
   */
  function toggle(): void {
    // Simple toggle: light <-> dark (auto users get explicit choice)
    const newMode: ThemeMode = resolvedTheme.value === 'dark' ? 'light' : 'dark'
    setMode(newMode)
  }

  /**
   * Set theme mode explicitly
   */
  function setMode(newMode: ThemeMode): void {
    mode.value = newMode
    localStorage.setItem(STORAGE_KEY, newMode)
    applyTheme(newMode === 'auto' ? getSystemPreference() : newMode)
  }

  // Watch for external changes to mode
  watch(mode, (newMode) => {
    applyTheme(newMode === 'auto' ? getSystemPreference() : newMode)
  })

  return {
    mode,
    resolvedTheme,
    isDark,
    toggle,
    setMode
  }
}
