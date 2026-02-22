// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, onUnmounted } from 'vue'
import { useActivityApi } from '@/composables/useApi'

const unreadCount = ref(0)
let pollInterval: ReturnType<typeof setInterval> | null = null
let subscriberCount = 0

const POLL_INTERVAL_MS = 60_000 // 60 seconds

/**
 * Shared composable for activity unread count.
 *
 * Polls getUnreadActivityCount every 60 seconds when at least one
 * component is subscribed. Multiple consumers (Sidebar, Activity page)
 * share the same singleton state and polling timer.
 */
export function useActivityUnread() {
  const { getUnreadActivityCount, markActivityViewed } = useActivityApi()

  async function fetchCount() {
    try {
      unreadCount.value = await getUnreadActivityCount()
    } catch {
      // Silently ignore — endpoint may not be deployed yet
    }
  }

  function startPolling() {
    if (pollInterval) return
    fetchCount()
    pollInterval = setInterval(() => {
      // Only poll when the tab is visible
      if (document.visibilityState === 'visible') {
        fetchCount()
      }
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  // Subscribe: start polling when first consumer mounts
  subscriberCount++
  if (subscriberCount === 1) {
    startPolling()
  }

  // Unsubscribe: stop polling when last consumer unmounts
  onUnmounted(() => {
    subscriberCount--
    if (subscriberCount <= 0) {
      subscriberCount = 0
      stopPolling()
    }
  })

  /**
   * Mark all activity as read and reset the counter.
   * Call when the user leaves the Activity page.
   */
  async function resetCount() {
    try {
      await markActivityViewed()
      unreadCount.value = 0
    } catch {
      // Silently ignore
    }
  }

  return {
    unreadCount,
    resetCount,
    refreshCount: fetchCount
  }
}
