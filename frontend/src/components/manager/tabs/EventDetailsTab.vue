<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventDetailsTab.vue - Details tab content for Event Manager
  Shows subject, status/type badges, date/time, location, project/task links, description
-->
<template>
  <div class="space-y-4">
    <!-- Status & Type Badges -->
    <div class="flex flex-wrap items-center gap-2">
      <span :class="['text-xs px-2 py-1 rounded-full', statusColors[event.status] || statusColors['Scheduled']]">
        {{ __(event.status) }}
      </span>
      <span :class="['text-xs px-2 py-1 rounded-full flex items-center gap-1', eventTypeColors[event.event_type] || eventTypeColors['Other']]">
        <i :class="['fa-solid', eventTypeIcons[event.event_type] || eventTypeIcons['Other']]"></i>
        {{ __(event.event_type) }}
      </span>
    </div>

    <!-- Title -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Subject') }}</label>
      <p class="text-sm text-gray-800 dark:text-gray-200 mt-1 font-medium">{{ event.title || event.subject }}</p>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ event.name }}</p>
    </div>

    <!-- Date & Time -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-clock text-orga-500"></i>
        {{ __('When') }}
      </h5>
      <div class="space-y-2">
        <div class="flex items-center gap-2 text-gray-700 dark:text-gray-300">
          <i class="fa-regular fa-calendar w-4 text-gray-400 dark:text-gray-500"></i>
          <span class="text-sm">{{ formattedDate }}</span>
        </div>
        <div class="flex items-center gap-2 text-gray-700 dark:text-gray-300">
          <i class="fa-regular fa-clock w-4 text-gray-400 dark:text-gray-500"></i>
          <span class="text-sm">{{ formattedTime }}</span>
          <span v-if="formattedDuration" class="text-xs text-gray-400 dark:text-gray-500">({{ formattedDuration }})</span>
        </div>
      </div>
    </div>

    <!-- Location -->
    <div v-if="event.location || event.meeting_url">
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-location-dot text-orga-500"></i>
        {{ __('Where') }}
      </h5>
      <div class="space-y-2">
        <div v-if="event.location" class="flex items-center gap-2 text-gray-700 dark:text-gray-300">
          <i class="fa-solid fa-building w-4 text-gray-400 dark:text-gray-500"></i>
          <span class="text-sm">{{ event.location }}</span>
        </div>
        <div v-if="event.meeting_url" class="flex items-center gap-2">
          <i class="fa-solid fa-video w-4 text-gray-400 dark:text-gray-500"></i>
          <a
            :href="event.meeting_url"
            target="_blank"
            class="text-sm text-orga-600 dark:text-orga-400 hover:underline flex items-center gap-1"
          >
            {{ __('Join Meeting') }}
            <i class="fa-solid fa-external-link text-xs"></i>
          </a>
        </div>
      </div>
    </div>

    <!-- Project & Task Links -->
    <div v-if="event.project || event.task">
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-folder text-orga-500"></i>
        {{ __('Related') }}
      </h5>
      <div class="space-y-2">
        <div v-if="event.project" class="flex items-center gap-2">
          <i class="fa-solid fa-folder-open w-4 text-gray-400 dark:text-gray-500"></i>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ event.project_name || event.project }}</span>
        </div>
        <div v-if="event.task" class="flex items-center gap-2">
          <i class="fa-solid fa-check-square w-4 text-gray-400 dark:text-gray-500"></i>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ event.task_subject || event.task }}</span>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div v-if="event.description">
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-file-lines text-orga-500"></i>
        {{ __('Description') }}
      </h5>
      <div class="text-sm text-gray-700 dark:text-gray-300 prose prose-sm dark:prose-invert max-w-none" v-html="sanitizeHtml(event.description)"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'
import type { OrgaEvent, EventStatus } from '@/types/orga'

interface Props {
  event: OrgaEvent
}

const props = defineProps<Props>()

const statusColors: Record<EventStatus, string> = {
  'Scheduled': 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400',
  'Completed': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400',
  'Cancelled': 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
}

const eventTypeColors: Record<string, string> = {
  'Meeting': 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-400',
  'Deadline': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400',
  'Review': 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400',
  'Milestone': 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400',
  'Other': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

const eventTypeIcons: Record<string, string> = {
  'Meeting': 'fa-users',
  'Deadline': 'fa-flag',
  'Review': 'fa-clipboard-check',
  'Milestone': 'fa-trophy',
  'Other': 'fa-calendar'
}

const formattedDate = computed<string>(() => {
  if (!props.event?.start_datetime) return ''
  const start = new Date(props.event.start_datetime)
  return start.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

const formattedTime = computed<string>(() => {
  if (!props.event?.start_datetime) return ''
  if (props.event.all_day) return __('All day')

  const start = new Date(props.event.start_datetime)
  const startTime = start.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

  if (props.event.end_datetime) {
    const end = new Date(props.event.end_datetime)
    const endTime = end.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    return `${startTime} - ${endTime}`
  }

  return startTime
})

const formattedDuration = computed<string | null>(() => {
  const appt = props.event as Record<string, unknown>
  const minutes = appt.duration_minutes as number | undefined
  if (!minutes) return null
  if (minutes < 60) return __("{0} min", [minutes])
  const hours = Math.floor(minutes / 60)
  const remainingMins = minutes % 60
  if (remainingMins === 0) return __("{0}h", [hours])
  return __("{0}h {1}m", [hours, remainingMins])
})
</script>
