<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  AggregatedActivityCard.vue - Collapsed card for multiple consecutive activities by the same user
-->
<script setup lang="ts">
import { ref } from 'vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import ActivityCard from '@/components/activity/ActivityCard.vue'
import type { ActivityItem } from '@/types/orga'
import type { AggregatedActivity } from '@/composables/useActivityGrouping'
import { __ } from '@/composables/useTranslate'

interface Props {
  activity: AggregatedActivity
  isUnread?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isUnread: false
})

const emit = defineEmits<{
  select: [activity: ActivityItem]
  update: []
  read: []
}>()

const expanded = ref(false)

function toggle() {
  expanded.value = !expanded.value
  if (props.isUnread) {
    emit('read')
  }
}

function getTypeBadgeClass(type: string): string {
  const classes: Record<string, string> = {
    'task': 'bg-teal-500/20 text-teal-600 border-teal-500',
    'milestone': 'bg-amber-500/20 text-amber-600 border-amber-500',
    'project': 'bg-blue-500/20 text-blue-600 border-blue-500',
    'event': 'bg-purple-500/20 text-purple-600 border-purple-500',
    'external': 'bg-indigo-500/20 text-indigo-600 border-indigo-500'
  }
  return classes[type] || 'bg-gray-100 text-gray-600 border-gray-300'
}

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    'task': 'fa-list-check',
    'milestone': 'fa-flag',
    'project': 'fa-folder',
    'event': 'fa-calendar-check',
    'external': 'fa-building'
  }
  return icons[type] || 'fa-circle'
}

function getActionLabel(action: string): string {
  const labels: Record<string, string> = {
    'updated': 'updated',
    'created': 'created',
    'completed': 'completed',
    'deleted': 'deleted',
    'assigned': 'assigned'
  }
  return labels[action] || action
}

function formatRelativeTime(timestamp: string | null | undefined): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __("{0} min ago", [diffMins])
  if (diffHours < 24) return __("{0} hours ago", [diffHours])
  if (diffDays === 1) return __('Yesterday')
  if (diffDays < 7) return __("{0} days ago", [diffDays])
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div
    :class="[
      'py-4 px-4 border-b border-gray-200 dark:border-gray-700 last:border-0 relative',
      isUnread ? 'border-l-4 border-l-orga-500 bg-orga-50/50 dark:bg-orga-900/10' : ''
    ]"
  >
    <!-- Unread Indicator -->
    <div v-if="isUnread" class="absolute top-5 left-0.5 w-2.5 h-2.5 rounded-full bg-orga-500 ring-2 ring-white dark:ring-gray-900" :title="__('New activity')"></div>

    <!-- Collapsed summary -->
    <div
      class="flex gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg p-2 -m-2 transition-colors"
      @click="toggle"
    >
      <!-- Avatar -->
      <UserAvatar
        :name="activity.user_name"
        :image="activity.user_image"
        size="xl"
        color="teal"
      />

      <!-- Summary content -->
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-orga-500 text-sm mb-1">
          {{ activity.user_name }}
        </div>

        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <!-- Type Badge -->
          <span :class="[
            'inline-block px-2.5 py-1 rounded-xl text-xs font-medium mb-2 border',
            getTypeBadgeClass(activity.type)
          ]">
            <i :class="['fa-solid mr-1', getTypeIcon(activity.type)]"></i>
            {{ activity.type.charAt(0).toUpperCase() + activity.type.slice(1) }}
          </span>

          <!-- Summary text -->
          <div class="text-sm text-gray-800 dark:text-gray-200">
            {{ getActionLabel(activity.action) }}
            <span class="font-semibold">{{ activity.count }}</span>
            {{ activity.type }}{{ activity.count !== 1 ? 's' : '' }}
            <template v-if="activity.projects.length === 1">
              {{ __('in') }} <span class="font-medium text-orga-500">{{ activity.projects[0] }}</span>
            </template>
            <template v-else-if="activity.projects.length > 1">
              {{ __('across') }} <span class="font-medium">{{ __("{0} projects", [activity.projects.length]) }}</span>
            </template>
          </div>

          <!-- Expand/Collapse toggle -->
          <button
            class="mt-2 text-xs text-orga-500 hover:text-orga-600 dark:text-orga-400 dark:hover:text-orga-300 transition-colors"
            @click.stop="toggle"
          >
            <i :class="['fa-solid mr-1', expanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
            {{ expanded ? __('Hide') : __('Show') }} {{ __("{0} items", [activity.count]) }}
          </button>
        </div>
      </div>

      <!-- Timestamp -->
      <span class="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
        <i class="fa-regular fa-clock mr-1"></i>{{ formatRelativeTime(activity.timestamp) }}
      </span>
    </div>

    <!-- Expanded individual items -->
    <Transition name="expand">
      <div v-if="expanded" class="ml-14 mt-2 space-y-1 border-l-2 border-gray-100 dark:border-gray-700 pl-3">
        <ActivityCard
          v-for="item in activity.items"
          :key="item.name + item.timestamp"
          :activity="item"
          @select="emit('select', $event)"
          @update="emit('update')"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 2000px;
}
</style>
