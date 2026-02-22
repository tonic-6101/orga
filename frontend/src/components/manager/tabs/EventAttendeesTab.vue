<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventAttendeesTab.vue - Attendees tab content for Event Manager
  Shows RSVP summary stats, attendee list with avatars and RSVP badges, user's RSVP buttons
-->
<template>
  <div class="space-y-4">
    <!-- RSVP Summary -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-users text-orga-500"></i>
        {{ __('Attendees') }}
        <span v-if="totalAttendees > 0" class="text-xs font-normal text-gray-400 dark:text-gray-500">
          ({{ __("{0}/{1} accepted", [acceptedCount, totalAttendees]) }})
        </span>
      </h5>

      <!-- Attendee List -->
      <div v-if="attendees.length" class="space-y-2">
        <div
          v-for="attendee in attendees"
          :key="attendee.name"
          class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
        >
          <div class="flex items-center gap-2">
            <span class="w-8 h-8 bg-teal-500 text-white rounded-full text-sm font-medium flex items-center justify-center">
              {{ attendee.initials || getInitials(attendee.resource_name) }}
            </span>
            <div>
              <div class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ attendee.resource_name }}</div>
              <div v-if="attendee.email" class="text-xs text-gray-500 dark:text-gray-400">{{ attendee.email }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="!attendee.required" class="text-xs text-gray-400 dark:text-gray-500">{{ __('Optional') }}</span>
            <span :class="['text-xs px-2 py-0.5 rounded-full', rsvpColors[attendee.rsvp_status]]">
              {{ __(attendee.rsvp_status) }}
            </span>
          </div>
        </div>
      </div>
      <div v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-3">
        {{ __('No attendees') }}
      </div>
    </div>

    <!-- RSVP Response Buttons -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-reply text-orga-500"></i>
        {{ __('Your Response') }}
      </h5>
      <div class="flex gap-2">
        <button
          @click="emit('rsvp', 'Accepted')"
          :disabled="rsvpLoading"
          class="flex-1 px-3 py-2 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-900/60 text-sm font-medium transition-colors flex items-center justify-center gap-1"
        >
          <i v-if="rsvpLoading" class="fa-solid fa-spinner fa-spin"></i>
          <i v-else class="fa-solid fa-check"></i>
          {{ __('Accept') }}
        </button>
        <button
          @click="emit('rsvp', 'Tentative')"
          :disabled="rsvpLoading"
          class="flex-1 px-3 py-2 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400 rounded hover:bg-yellow-200 dark:hover:bg-yellow-900/60 text-sm font-medium transition-colors flex items-center justify-center gap-1"
        >
          <i v-if="rsvpLoading" class="fa-solid fa-spinner fa-spin"></i>
          <i v-else class="fa-solid fa-question"></i>
          {{ __('Maybe') }}
        </button>
        <button
          @click="emit('rsvp', 'Declined')"
          :disabled="rsvpLoading"
          class="flex-1 px-3 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/60 text-sm font-medium transition-colors flex items-center justify-center gap-1"
        >
          <i v-if="rsvpLoading" class="fa-solid fa-spinner fa-spin"></i>
          <i v-else class="fa-solid fa-xmark"></i>
          {{ __('Decline') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaEventAttendee, RsvpStatus } from '@/types/orga'

interface Props {
  attendees: OrgaEventAttendee[]
  rsvpLoading: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  rsvp: [status: RsvpStatus]
}>()

const rsvpColors: Record<RsvpStatus, string> = {
  'Pending': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  'Accepted': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400',
  'Declined': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400',
  'Tentative': 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400'
}

const acceptedCount = computed<number>(() => {
  return props.attendees.filter(a => a.rsvp_status === 'Accepted').length
})

const totalAttendees = computed<number>(() => {
  return props.attendees.length
})

function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}
</script>
