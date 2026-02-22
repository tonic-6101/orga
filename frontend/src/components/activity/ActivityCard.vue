<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityCard.vue - Individual activity card for the activity feed
-->
<script setup lang="ts">
import UserAvatar from '@/components/common/UserAvatar.vue'
import ActivityCardComments from '@/components/activity/ActivityCardComments.vue'
import ActivityCardReactions from '@/components/activity/ActivityCardReactions.vue'
import EventActivityContent from '@/components/activity/EventActivityContent.vue'
import ExternalActivityContent from '@/components/activity/ExternalActivityContent.vue'
import type { ActivityItem } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

interface Props {
  activity: ActivityItem
  isSelected?: boolean
  isPinned?: boolean
  isArchived?: boolean
  isUnread?: boolean
}

withDefaults(defineProps<Props>(), {
  isSelected: false,
  isPinned: false,
  isArchived: false,
  isUnread: false
})

const emit = defineEmits<{
  select: [activity: ActivityItem]
  update: []
}>()

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

function isExternalActivity(activity: ActivityItem): boolean {
  const extendedActivity = activity as ActivityItem & { company_name?: string }
  return activity.type === 'external' || Boolean(extendedActivity.company_name)
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
      'py-5 px-4 border-b border-gray-200 dark:border-gray-700 last:border-0 cursor-pointer transition-colors relative',
      isSelected ? 'bg-orga-50 dark:bg-orga-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800',
      isUnread ? 'border-l-4 border-l-orga-500 bg-orga-50/50 dark:bg-orga-900/10' : ''
    ]"
    @click="emit('select', activity)"
  >
    <!-- Unread Indicator -->
    <div v-if="isUnread" class="absolute top-5 left-0.5 w-2.5 h-2.5 rounded-full bg-orga-500 ring-2 ring-white dark:ring-gray-900" :title="__('New activity')"></div>

    <!-- Pin Indicator -->
    <div v-if="isPinned" class="absolute top-2 right-2" :title="__('Pinned')">
      <i class="fa-solid fa-thumbtack text-amber-500 text-xs"></i>
    </div>

    <!-- Archive Indicator -->
    <div v-if="isArchived" class="absolute top-2 right-6" :title="__('Archived')">
      <i class="fa-solid fa-archive text-gray-400 text-xs"></i>
    </div>

    <div class="flex gap-3">
      <!-- Avatar -->
      <UserAvatar
        :name="activity.user_name || activity.user_fullname || activity.user"
        :image="activity.user_image"
        size="xl"
        color="teal"
      />

      <!-- Content -->
      <div class="flex-1">
        <div class="font-semibold text-orga-500 text-sm mb-1">
          {{ activity.user_name || activity.user_fullname || activity.user }}
        </div>

        <!-- Activity Card -->
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mt-2">
          <!-- Type Badge -->
          <span :class="[
            'inline-block px-2.5 py-1 rounded-xl text-xs font-medium mb-2 border',
            activity.action === 'deleted'
              ? 'bg-red-500/20 text-red-600 border-red-500'
              : getTypeBadgeClass(activity.type || '')
          ]">
            <i :class="['fa-solid mr-1', activity.action === 'deleted' ? 'fa-trash' : getTypeIcon(activity.type || '')]"></i>
            {{ activity.action === 'deleted' ? __('Deleted') : (activity.type || 'Activity').charAt(0).toUpperCase() + (activity.type || 'Activity').slice(1) }}
          </span>

          <!-- Event-specific Content -->
          <template v-if="activity.type === 'event'">
            <div class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
              {{ activity.title }}
            </div>
            <EventActivityContent
              :activity="activity"
              @rsvp-updated="emit('update')"
            />
          </template>

          <!-- External Company Content -->
          <template v-else-if="isExternalActivity(activity)">
            <ExternalActivityContent
              :activity="activity"
              @note-added="emit('update')"
              @flagged="emit('update')"
            />
          </template>

          <!-- Deletion Event -->
          <template v-else-if="activity.action === 'deleted'">
            <div class="text-sm text-gray-800 dark:text-gray-200">
              <span class="font-medium text-red-600 dark:text-red-400">{{ activity.title }}</span>
            </div>
          </template>

          <!-- Standard Activity Description -->
          <template v-else>
            <div class="text-sm text-gray-800 dark:text-gray-200">
              {{ __('Updated') }}
              <router-link
                v-if="activity.project"
                :to="{ path: `/orga/projects/${activity.project}`, query: activity.type === 'milestone' ? { milestone: activity.reference_name || activity.name } : { task: activity.reference_name || activity.name } }"
                class="text-orga-500 no-underline hover:underline"
                @click.stop
              >
                {{ activity.title }}
              </router-link>
              <span v-else class="font-medium">{{ activity.title }}</span>
              <template v-if="activity.status">
                {{ __('to') }} <span class="font-medium">{{ activity.status }}</span>
              </template>
            </div>
            <div v-if="activity.project_name || activity.project" class="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {{ __('Project:') }} {{ activity.project_name || activity.project }}
            </div>
          </template>

          <!-- Reactions -->
          <div class="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
            <ActivityCardReactions
              :doctype="activity.reference_doctype || activity.doctype || 'Activity Log'"
              :docname="activity.reference_name || activity.name"
              :initial-counts="activity.reaction_counts || {}"
              :initial-user-reactions="activity.user_reactions || []"
              @reaction-changed="emit('update')"
            />
          </div>

          <!-- Inline Comments -->
          <ActivityCardComments
            :doctype="activity.reference_doctype || activity.doctype || 'Activity Log'"
            :docname="activity.reference_name || activity.name"
            :initial-count="activity.comment_count || 0"
            @comment-added="emit('update')"
            @comment-deleted="emit('update')"
          />
        </div>
      </div>

      <!-- Timestamp -->
      <span class="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
        <i class="fa-regular fa-clock mr-1"></i>{{ formatRelativeTime(activity.timestamp) }}
      </span>
    </div>
  </div>
</template>
