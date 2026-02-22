// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, computed, onUnmounted } from 'vue'
import { useApi } from '@/composables/useApi'
import type { UpdateInfo } from '@/types/orga'

// ============================================
// Singleton state (shared across all consumers)
// ============================================

const updateInfo = ref<UpdateInfo | null>(null)
const isChecking = ref(false)
const checkError = ref<string | null>(null)

const DISMISS_KEY = 'orga_update_dismissed_version'

function getDismissedVersion(): string | null {
  try {
    return localStorage.getItem(DISMISS_KEY)
  } catch {
    return null
  }
}

const updateAvailable = computed(() => {
  if (!updateInfo.value?.update_available) return false
  const dismissed = getDismissedVersion()
  if (dismissed && dismissed === updateInfo.value.latest_version) return false
  return true
})

let subscriberCount = 0
let hasFetched = false

// ============================================
// Composable
// ============================================

/**
 * Shared composable for app update checking.
 *
 * Fetches cached update info once on first mount (no polling).
 * Multiple consumers (Sidebar, Settings) share the same singleton state.
 */
export function useUpdateChecker() {
  const { call } = useApi()

  async function fetchUpdateInfo(): Promise<void> {
    if (isChecking.value) return
    isChecking.value = true
    checkError.value = null

    try {
      const result = await call<UpdateInfo>(
        'orga.orga.api.settings.get_update_info'
      )
      if (result && result.current_version) {
        updateInfo.value = result
      }
    } catch {
      // Silently ignore — update check is non-critical
    } finally {
      isChecking.value = false
    }
  }

  async function forceCheck(): Promise<void> {
    isChecking.value = true
    checkError.value = null

    try {
      const result = await call<UpdateInfo>(
        'orga.orga.api.settings.check_updates_now'
      )
      if (result && result.current_version) {
        updateInfo.value = result
      }
    } catch (e) {
      checkError.value = (e as Error).message || 'Check failed'
    } finally {
      isChecking.value = false
    }
  }

  function dismissUpdate(): void {
    if (updateInfo.value?.latest_version) {
      localStorage.setItem(DISMISS_KEY, updateInfo.value.latest_version)
      // Force reactivity update
      updateInfo.value = { ...updateInfo.value }
    }
  }

  function undismissUpdate(): void {
    localStorage.removeItem(DISMISS_KEY)
    if (updateInfo.value) {
      updateInfo.value = { ...updateInfo.value }
    }
  }

  // Fetch once on first subscriber mount
  subscriberCount++
  if (!hasFetched) {
    hasFetched = true
    fetchUpdateInfo()
  }

  onUnmounted(() => {
    subscriberCount--
    if (subscriberCount <= 0) {
      subscriberCount = 0
    }
  })

  return {
    updateInfo,
    updateAvailable,
    isChecking,
    checkError,
    fetchUpdateInfo,
    forceCheck,
    dismissUpdate,
    undismissUpdate,
  }
}
