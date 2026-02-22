<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventActivityContent.vue - Event-specific content for activity cards

  Features:
  - Date box display
  - RSVP buttons (Accept/Decline/Propose)
  - Attendee summary with avatars
  - Inline time proposal
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEventApi } from '@/composables/useApi'
import type { ActivityItem, AttendeeStats, EventAttendee } from '@/types/orga'
import ProposeTimeModal from './ProposeTimeModal.vue'

interface Props {
  activity: ActivityItem
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'rsvp-updated': [status: string, stats: AttendeeStats]
}>()

const { updateRsvpEnhanced } = useEventApi()

const isUpdating = ref(false)
const showProposeModal = ref(false)
const currentStatus = ref(props.activity.user_rsvp_status || 'Pending')
const stats = ref<AttendeeStats>(props.activity.attendee_stats || {
  total: 0,
  accepted: 0,
  declined: 0,
  tentative: 0,
  pending: 0
})

const eventName = computed(() => props.activity.reference_name || props.activity.name)

const startDate = computed(() => {
  if (!props.activity.start_datetime) return null
  return new Date(props.activity.start_datetime)
})

const dayOfWeek = computed(() => {
  if (!startDate.value) return ''
  return startDate.value.toLocaleDateString('en', { weekday: 'short' })
})

const dayNumber = computed(() => {
  if (!startDate.value) return ''
  return startDate.value.getDate()
})

const month = computed(() => {
  if (!startDate.value) return ''
  return startDate.value.toLocaleDateString('en', { month: 'short' })
})

const formattedTime = computed(() => {
  if (!startDate.value) return ''
  return startDate.value.toLocaleTimeString('en', { hour: 'numeric', minute: '2-digit' })
})

const formattedEndTime = computed(() => {
  if (!props.activity.end_datetime) return null
  const endDate = new Date(props.activity.end_datetime)
  return endDate.toLocaleTimeString('en', { hour: 'numeric', minute: '2-digit' })
})

const isAttendee = computed(() => props.activity.is_attendee ?? false)

const acceptedAttendees = computed(() => {
  return (props.activity.attendees || []).filter(a => a.rsvp_status === 'Accepted')
})

function getInitials(name: string): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
  }
  return name.charAt(0).toUpperCase()
}

async function handleRSVP(status: string) {
  if (isUpdating.value || !eventName.value) return

  isUpdating.value = true
  const previousStatus = currentStatus.value

  // Optimistic update
  currentStatus.value = status

  try {
    const result = await updateRsvpEnhanced(eventName.value, status)
    currentStatus.value = result.status
    stats.value = result.attendee_stats
    emit('rsvp-updated', result.status, result.attendee_stats)
  } catch (e) {
    // Revert on error
    currentStatus.value = previousStatus
    console.error('Failed to update RSVP:', e)
  } finally {
    isUpdating.value = false
  }
}

function handleTimeProposed(result: { status: string; attendee_stats: AttendeeStats }) {
  currentStatus.value = result.status
  stats.value = result.attendee_stats
  showProposeModal.value = false
  emit('rsvp-updated', result.status, result.attendee_stats)
}
</script>

<template>
  <div class="event-activity-content">
    <!-- Event Info Row -->
    <div class="flex gap-3 items-start">
      <!-- Date Box -->
      <div class="w-14 h-14 bg-orga-50 dark:bg-orga-900/30 rounded-lg flex flex-col items-center justify-center shrink-0 border border-orga-100 dark:border-orga-800">
        <span class="text-[10px] text-orga-500 dark:text-orga-400 font-medium uppercase">{{ dayOfWeek }}</span>
        <span class="text-xl font-bold text-orga-700 dark:text-orga-300 leading-none">{{ dayNumber }}</span>
        <span class="text-[10px] text-orga-500 dark:text-orga-400 uppercase">{{ month }}</span>
      </div>

      <!-- Details -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ formattedTime }}
            <span v-if="formattedEndTime"> - {{ formattedEndTime }}</span>
          </span>
          <span
            v-if="activity.event_type"
            class="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400"
          >
            {{ activity.event_type }}
          </span>
        </div>

        <p v-if="activity.location" class="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 mt-1">
          <i class="fa-solid fa-location-dot"></i>
          {{ activity.location }}
        </p>

        <!-- Attendee Summary -->
        <div v-if="stats.total > 0" class="flex items-center gap-2 mt-2">
          <div class="flex -space-x-1.5">
            <div
              v-for="(attendee, idx) in acceptedAttendees.slice(0, 4)"
              :key="idx"
              class="w-5 h-5 rounded-full bg-green-500 border-2 border-white dark:border-gray-800 flex items-center justify-center text-white text-[8px] font-medium"
              :title="attendee.name"
            >
              {{ getInitials(attendee.name) }}
            </div>
            <div
              v-if="acceptedAttendees.length > 4"
              class="w-5 h-5 rounded-full bg-gray-400 dark:bg-gray-600 border-2 border-white dark:border-gray-800 flex items-center justify-center text-white text-[8px]"
            >
              +{{ acceptedAttendees.length - 4 }}
            </div>
          </div>
          <span class="text-[10px] text-gray-500 dark:text-gray-400">
            {{ __("{0}/{1} accepted", [stats.accepted, stats.total]) }}
          </span>
        </div>
      </div>
    </div>

    <!-- RSVP Actions (only for attendees) -->
    <div v-if="isAttendee" class="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <span class="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Your Response') }}</span>
        <div class="flex items-center gap-1.5">
          <button
            @click.stop="handleRSVP('Accepted')"
            :disabled="isUpdating"
            :class="[
              'px-2.5 py-1 text-xs rounded-lg transition-all disabled:opacity-50',
              currentStatus === 'Accepted'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-green-100 dark:hover:bg-green-900/30 hover:text-green-700 dark:hover:text-green-400'
            ]"
          >
            <i class="fa-solid fa-check mr-1"></i>{{ __('Accept') }}
          </button>

          <button
            @click.stop="handleRSVP('Declined')"
            :disabled="isUpdating"
            :class="[
              'px-2.5 py-1 text-xs rounded-lg transition-all disabled:opacity-50',
              currentStatus === 'Declined'
                ? 'bg-red-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-700 dark:hover:text-red-400'
            ]"
          >
            <i class="fa-solid fa-xmark mr-1"></i>{{ __('Decline') }}
          </button>

          <button
            @click.stop="showProposeModal = true"
            :disabled="isUpdating"
            :class="[
              'px-2.5 py-1 text-xs rounded-lg transition-all disabled:opacity-50',
              currentStatus === 'Tentative'
                ? 'bg-amber-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-amber-100 dark:hover:bg-amber-900/30 hover:text-amber-700 dark:hover:text-amber-400'
            ]"
          >
            <i class="fa-solid fa-clock-rotate-left mr-1"></i>{{ __('Propose') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Propose Time Modal -->
    <ProposeTimeModal
      v-if="showProposeModal"
      :event="eventName"
      :current-start="activity.start_datetime"
      :current-end="activity.end_datetime"
      @close="showProposeModal = false"
      @proposed="handleTimeProposed"
    />
  </div>
</template>
