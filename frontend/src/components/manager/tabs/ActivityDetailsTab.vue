<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityDetailsTab.vue - Details tab content for Activity Manager
-->
<template>
  <div class="space-y-4">
    <!-- Activity Type Badge -->
    <div class="flex items-center gap-2">
      <span :class="['px-2 py-1 text-xs rounded-full', getTypeBadgeClass(activity.type)]">
        <i :class="['mr-1', getTypeIcon(activity.type)]"></i>
        {{ activity.type || __('Activity') }}
      </span>
      <span v-if="state.is_pinned" class="text-amber-500" :title="__('Pinned')">
        <i class="fa-solid fa-thumbtack text-xs"></i>
      </span>
      <span v-if="state.is_archived" class="text-gray-400 dark:text-gray-500" :title="__('Archived')">
        <i class="fa-solid fa-archive text-xs"></i>
      </span>
    </div>

    <!-- Title -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Title') }}</label>
      <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ activity.title || activity.subject || activity.name }}</p>
    </div>

    <!-- Action & Timestamp -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Action') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1 capitalize">{{ activity.action }}</p>
      </div>
      <div>
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('When') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ formatRelativeTime(activity.timestamp) }}</p>
      </div>
    </div>

    <!-- User -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('By') }}</label>
      <div class="flex items-center gap-2 mt-1">
        <UserAvatar
          :name="activity.user_name || activity.user_fullname || activity.user"
          :image="activity.user_image"
          size="xs"
          color="orga"
        />
        <span class="text-sm text-gray-800 dark:text-gray-200">{{ activity.user_name || activity.user_fullname || activity.user }}</span>
      </div>
    </div>

    <!-- Project Reference -->
    <div v-if="activity.project">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Project') }}</label>
      <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ activity.project_name || activity.project }}</p>
    </div>

    <!-- Document Reference -->
    <div v-if="activity.reference_doctype">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Reference') }}</label>
      <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
        {{ activity.reference_doctype }}: {{ activity.reference_name }}
      </p>
    </div>

    <!-- Status -->
    <div v-if="activity.status">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Status') }}</label>
      <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ activity.status }}</p>
    </div>

    <!-- Divider -->
    <div class="border-t border-gray-100 dark:border-gray-800 pt-4 mt-4">
      <!-- Related Documents -->
      <RelatedDocumentsSection
        v-if="activity.reference_doctype && activity.reference_name"
        :doctype="activity.reference_doctype"
        :docname="activity.reference_name"
        :activity="activity"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from '@/composables/useTranslate'
import type { ActivityItem } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'
import RelatedDocumentsSection from '@/components/manager/RelatedDocumentsSection.vue'

interface Props {
  activity: ActivityItem
  state: {
    is_pinned: boolean
    is_archived: boolean
    can_delete: boolean
  }
}

defineProps<Props>()

/**
 * Get badge class for activity type
 */
function getTypeBadgeClass(type?: string): string {
  const classes: Record<string, string> = {
    task: 'bg-blue-100 text-blue-700',
    project: 'bg-purple-100 text-purple-700',
    milestone: 'bg-amber-100 text-amber-700',
    resource: 'bg-green-100 text-green-700',
    event: 'bg-pink-100 text-pink-700'
  }
  return classes[type?.toLowerCase() || ''] || 'bg-gray-100 text-gray-700'
}

/**
 * Get icon for activity type
 */
function getTypeIcon(type?: string): string {
  const icons: Record<string, string> = {
    task: 'fa-solid fa-check-square',
    project: 'fa-solid fa-folder',
    milestone: 'fa-solid fa-flag',
    resource: 'fa-solid fa-user',
    event: 'fa-solid fa-calendar'
  }
  return icons[type?.toLowerCase() || ''] || 'fa-solid fa-circle'
}

/**
 * Format timestamp as relative time
 */
function formatRelativeTime(timestamp?: string): string {
  if (!timestamp) return __('Unknown')

  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0} min ago', [diffMins])
  if (diffHours < 24) return diffHours > 1 ? __('{0} hours ago', [diffHours]) : __('1 hour ago')
  if (diffDays < 7) return diffDays > 1 ? __('{0} days ago', [diffDays]) : __('1 day ago')

  return date.toLocaleDateString()
}
</script>
