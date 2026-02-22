<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * NotificationPanel.vue
 *
 * Dropdown panel showing recent notifications.
 * Supports marking as read, bulk operations, and navigation to referenced documents.
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from 'frappe-ui'
import NotificationItem from './NotificationItem.vue'
import { useNotificationApi } from '@/composables/useApi'
import type { OrgaNotification } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'count-updated'): void
}>()

const router = useRouter()
const { getMyNotifications, markAllAsRead, deleteAllRead, loading } = useNotificationApi()

const notifications = ref<OrgaNotification[]>([])
const total = ref(0)
const unreadCount = ref(0)
const showUnreadOnly = ref(false)
const isMarkingAll = ref(false)

const hasUnread = computed(() => unreadCount.value > 0)

async function loadNotifications(): Promise<void> {
  try {
    const result = await getMyNotifications({
      limit: 20,
      offset: 0,
      unread_only: showUnreadOnly.value
    })
    notifications.value = result.notifications
    total.value = result.total
    unreadCount.value = result.unread_count
    emit('count-updated')
  } catch (e) {
    console.error('Failed to load notifications:', e)
  }
}

async function handleMarkAllAsRead(): Promise<void> {
  isMarkingAll.value = true
  try {
    await markAllAsRead()
    await loadNotifications()
  } catch (e) {
    console.error('Failed to mark all as read:', e)
  } finally {
    isMarkingAll.value = false
  }
}

async function handleClearAll(): Promise<void> {
  if (!confirm(__('Delete all read notifications?'))) return

  try {
    await deleteAllRead()
    await loadNotifications()
  } catch (e) {
    console.error('Failed to clear notifications:', e)
  }
}

async function handleNotificationClick(notification: OrgaNotification): Promise<void> {
  if (!notification.reference_doctype || !notification.reference_name) return

  const ref = notification.reference_name

  switch (notification.reference_doctype) {
    case 'Orga Project':
      router.push(`/orga/projects/${ref}`)
      break
    case 'Orga Task':
      // Look up the task's project to navigate to the right project detail page
      try {
        const task = await fetch(`/api/resource/Orga Task/${ref}`, {
          headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token }
        }).then(r => r.json())
        if (task.data?.project) {
          router.push(`/orga/projects/${task.data.project}`)
        } else {
          router.push('/orga/projects')
        }
      } catch {
        router.push('/orga/projects')
      }
      break
    case 'Orga Appointment':
      router.push('/orga/schedule')
      break
    case 'Orga Resource':
      router.push('/orga/contacts')
      break
    case 'Orga Milestone':
      // Milestones belong to a project — look up the project
      try {
        const milestone = await fetch(`/api/resource/Orga Milestone/${ref}`, {
          headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token }
        }).then(r => r.json())
        if (milestone.data?.project) {
          router.push(`/orga/projects/${milestone.data.project}`)
        } else {
          router.push('/orga/projects')
        }
      } catch {
        router.push('/orga/projects')
      }
      break
    default:
      router.push('/orga/activity')
      break
  }

  emit('close')
}

function handleNotificationUpdate(): void {
  loadNotifications()
}

function toggleFilter(): void {
  showUnreadOnly.value = !showUnreadOnly.value
  loadNotifications()
}

onMounted(loadNotifications)
</script>

<template>
  <div class="notification-panel absolute right-0 top-full mt-2 w-96 max-h-[70vh] bg-white dark:bg-gray-800 rounded-lg shadow-xl dark:shadow-black/30 border border-gray-200 dark:border-gray-700 overflow-hidden z-50">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <div class="flex items-center justify-between">
        <h3 class="font-semibold text-gray-800 dark:text-gray-100 text-sm">
          {{ __('Notifications') }}
          <span v-if="unreadCount > 0" class="text-gray-400 font-normal">
            ({{ __("{0} unread", [unreadCount]) }})
          </span>
        </h3>
        <button @click="emit('close')" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 mt-2">
        <button
          @click="toggleFilter"
          :class="[
            'text-xs px-2 py-1 rounded transition-colors',
            showUnreadOnly ? 'bg-orga-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
          ]"
        >
          {{ __('Unread only') }}
        </button>
        <button
          v-if="hasUnread"
          @click="handleMarkAllAsRead"
          :disabled="isMarkingAll"
          class="text-xs text-orga-500 hover:text-orga-600 disabled:opacity-50"
        >
          {{ isMarkingAll ? __('Marking...') : __('Mark all read') }}
        </button>
        <button
          v-if="total > 0"
          @click="handleClearAll"
          class="text-xs text-gray-400 hover:text-red-500 ml-auto"
        >
          {{ __('Clear all read') }}
        </button>
      </div>
    </div>

    <!-- Notification List -->
    <div class="overflow-y-auto max-h-[50vh]">
      <!-- Loading -->
      <div v-if="loading" class="p-8 text-center text-gray-500">
        <i class="fa-solid fa-spinner fa-spin mr-2"></i>
        {{ __('Loading...') }}
      </div>

      <!-- Empty State -->
      <div v-else-if="notifications.length === 0" class="p-8 text-center">
        <i class="fa-regular fa-bell-slash text-3xl text-gray-300 mb-3"></i>
        <p class="text-gray-500 text-sm">
          {{ showUnreadOnly ? __('No unread notifications') : __('No notifications') }}
        </p>
      </div>

      <!-- Notification Items -->
      <div v-else>
        <NotificationItem
          v-for="notification in notifications"
          :key="notification.name"
          :notification="notification"
          @click="handleNotificationClick(notification)"
          @update="handleNotificationUpdate"
        />
      </div>
    </div>

    <!-- Footer -->
    <div v-if="total > notifications.length" class="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-center">
      <button class="text-xs text-orga-500 hover:text-orga-600">
        {{ __('View all {0} notifications', [total]) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.notification-panel {
  box-shadow: 0 10px 40px -5px rgba(0, 0, 0, 0.15);
}
</style>
