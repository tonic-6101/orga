<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * NotificationItem.vue
 *
 * Single notification item in the notification panel.
 */
import { computed } from 'vue'
import { useNotificationApi } from '@/composables/useApi'
import type { OrgaNotification, NotificationType } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

interface Props {
  notification: OrgaNotification
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'update'): void
}>()

const { markAsRead, markAsUnread, deleteNotification } = useNotificationApi()

// Icon and color mapping for notification types
const typeConfig: Record<NotificationType, { icon: string; color: string }> = {
  'Assignment': { icon: 'fa-user-plus', color: 'text-blue-500' },
  'Status Change': { icon: 'fa-arrow-right-arrow-left', color: 'text-yellow-500' },
  'Comment': { icon: 'fa-comment', color: 'text-green-500' },
  'Mention': { icon: 'fa-at', color: 'text-purple-500' },
  'Deadline': { icon: 'fa-clock', color: 'text-red-500' },
  'System': { icon: 'fa-gear', color: 'text-gray-500' }
}

const config = computed(() => typeConfig[props.notification.notification_type] || typeConfig['System'])

const timeAgo = computed(() => {
  if (!props.notification.creation) return ''

  const now = new Date()
  const date = new Date(props.notification.creation)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __("{0}m ago", [diffMins])
  if (diffHours < 24) return __("{0}h ago", [diffHours])
  if (diffDays === 1) return __('Yesterday')
  if (diffDays < 7) return __("{0}d ago", [diffDays])

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
})

async function handleToggleRead(event: Event): Promise<void> {
  event.stopPropagation()

  try {
    if (props.notification.is_read) {
      await markAsUnread(props.notification.name)
    } else {
      await markAsRead(props.notification.name)
    }
    emit('update')
  } catch (e) {
    console.error('Failed to toggle read status:', e)
  }
}

async function handleDelete(event: Event): Promise<void> {
  event.stopPropagation()

  try {
    await deleteNotification(props.notification.name)
    emit('update')
  } catch (e) {
    console.error('Failed to delete notification:', e)
  }
}

function handleClick(): void {
  // Mark as read when clicked
  if (!props.notification.is_read) {
    markAsRead(props.notification.name).catch(console.error)
  }
  emit('click')
}
</script>

<template>
  <div
    :class="[
      'notification-item px-4 py-3 border-b border-gray-100 dark:border-gray-700 cursor-pointer transition-colors group',
      notification.is_read ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700' : 'bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50'
    ]"
    @click="handleClick"
  >
    <div class="flex items-start gap-3">
      <!-- Type Icon -->
      <div :class="['w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0', notification.is_read ? 'bg-gray-100 dark:bg-gray-700' : 'bg-white dark:bg-gray-800']">
        <i :class="['fa-solid', config.icon, config.color, 'text-sm']"></i>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-2">
          <p :class="['text-sm m-0 leading-tight', notification.is_read ? 'text-gray-700 dark:text-gray-300' : 'text-gray-900 dark:text-gray-100 font-medium']">
            {{ notification.subject }}
          </p>
          <span class="text-[10px] text-gray-400 flex-shrink-0 whitespace-nowrap">
            {{ timeAgo }}
          </span>
        </div>

        <!-- Message Preview -->
        <p v-if="notification.message" class="text-xs text-gray-500 m-0 mt-1 line-clamp-2">
          {{ notification.message }}
        </p>

        <!-- From User -->
        <p v-if="notification.from_user_name" class="text-[10px] text-gray-400 m-0 mt-1">
          {{ notification.from_user_name }}
        </p>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          @click="handleToggleRead"
          class="p-1 text-gray-400 dark:text-gray-500 hover:text-orga-500 dark:hover:text-orga-400 rounded"
          :title="notification.is_read ? __('Mark as unread') : __('Mark as read')"
        >
          <i :class="['fa-solid text-xs', notification.is_read ? 'fa-envelope' : 'fa-envelope-open']"></i>
        </button>
        <button
          @click="handleDelete"
          class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 rounded"
          :title="__('Delete')"
        >
          <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
      </div>
    </div>

    <!-- Unread Indicator -->
    <div
      v-if="!notification.is_read"
      class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-1/2 bg-orga-500 rounded-r"
    ></div>
  </div>
</template>

<style scoped>
.notification-item {
  position: relative;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
