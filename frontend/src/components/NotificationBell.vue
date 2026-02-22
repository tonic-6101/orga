<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * NotificationBell.vue
 *
 * Notification indicator in the header.
 * Shows unread count and opens notification panel on click.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import NotificationPanel from './NotificationPanel.vue'
import { useNotificationApi } from '@/composables/useApi'

const { getUnreadCount } = useNotificationApi()

const unreadCount = ref(0)
const showPanel = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

async function loadCount(): Promise<void> {
  try {
    unreadCount.value = await getUnreadCount()
  } catch (e) {
    console.error('Failed to load notification count:', e)
  }
}

function togglePanel(): void {
  showPanel.value = !showPanel.value
}

function closePanel(): void {
  showPanel.value = false
}

function handleClickOutside(event: MouseEvent): void {
  const target = event.target as HTMLElement
  if (!target.closest('.notification-container')) {
    showPanel.value = false
  }
}

function handleCountUpdated(): void {
  loadCount()
}

onMounted(() => {
  loadCount()
  // Poll every 30 seconds for new notifications
  pollInterval = setInterval(loadCount, 30000)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  document.removeEventListener('click', handleClickOutside)
})

// Expose reload method
defineExpose({ reload: loadCount })
</script>

<template>
  <div class="notification-container relative">
    <button
      class="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
      @click.stop="togglePanel"
      :title="__('Notifications')"
    >
      <i class="fa-solid fa-bell text-gray-600 text-lg"></i>
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Notification Panel -->
    <NotificationPanel
      v-if="showPanel"
      @close="closePanel"
      @count-updated="handleCountUpdated"
    />
  </div>
</template>

<style scoped>
.notification-container {
  z-index: 50;
}
</style>
