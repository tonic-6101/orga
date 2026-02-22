<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ProposeTimeModal.vue - Modal for proposing alternative meeting times

  Features:
  - Date/time pickers for proposed start and end
  - Optional note field
  - Shows current time for reference
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEventApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { AttendeeStats } from '@/types/orga'

interface Props {
  event: string
  currentStart?: string
  currentEnd?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  proposed: [result: { status: string; attendee_stats: AttendeeStats }]
}>()

const { proposeNewTime } = useEventApi()

const proposedStart = ref('')
const proposedEnd = ref('')
const note = ref('')
const isSubmitting = ref(false)
const error = ref<string | null>(null)

const currentStartFormatted = computed(() => {
  if (!props.currentStart) return __('Not specified')
  const date = new Date(props.currentStart)
  return date.toLocaleString('en', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
})

const currentEndFormatted = computed(() => {
  if (!props.currentEnd) return null
  const date = new Date(props.currentEnd)
  return date.toLocaleString('en', {
    hour: 'numeric',
    minute: '2-digit'
  })
})

const canSubmit = computed(() => {
  return proposedStart.value && proposedEnd.value && !isSubmitting.value
})

onMounted(() => {
  // Pre-fill with current times as starting point
  if (props.currentStart) {
    const start = new Date(props.currentStart)
    // Add 1 day as default proposal
    start.setDate(start.getDate() + 1)
    proposedStart.value = formatDateTimeLocal(start)
  } else {
    // Default to tomorrow at 10:00
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(10, 0, 0, 0)
    proposedStart.value = formatDateTimeLocal(tomorrow)
  }

  if (props.currentEnd && props.currentStart) {
    const start = new Date(props.currentStart)
    const end = new Date(props.currentEnd)
    const duration = end.getTime() - start.getTime()

    const proposedEndDate = new Date(proposedStart.value)
    proposedEndDate.setTime(proposedEndDate.getTime() + duration)
    proposedEnd.value = formatDateTimeLocal(proposedEndDate)
  } else {
    // Default 1 hour duration
    const endDate = new Date(proposedStart.value)
    endDate.setHours(endDate.getHours() + 1)
    proposedEnd.value = formatDateTimeLocal(endDate)
  }
})

function formatDateTimeLocal(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function handleStartChange() {
  // Auto-adjust end time to maintain duration
  if (proposedStart.value && proposedEnd.value) {
    const start = new Date(proposedStart.value)
    const end = new Date(proposedEnd.value)

    // If end is before or equal to start, add 1 hour
    if (end <= start) {
      const newEnd = new Date(start)
      newEnd.setHours(newEnd.getHours() + 1)
      proposedEnd.value = formatDateTimeLocal(newEnd)
    }
  }
}

async function handleSubmit() {
  if (!canSubmit.value) return

  error.value = null
  isSubmitting.value = true

  try {
    // Convert to ISO format
    const startISO = new Date(proposedStart.value).toISOString()
    const endISO = new Date(proposedEnd.value).toISOString()

    const result = await proposeNewTime(
      props.event,
      startISO,
      endISO,
      note.value || undefined
    )

    emit('proposed', {
      status: result.status,
      attendee_stats: result.attendee_stats
    })
  } catch (e) {
    error.value = (e as Error).message || __('Failed to propose new time')
    console.error('Failed to propose time:', e)
  } finally {
    isSubmitting.value = false
  }
}

function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="handleBackdropClick"
    >
      <div
        class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 m-0">
            {{ __('Propose New Time') }}
          </h3>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- Content -->
        <div class="p-4 space-y-4">
          <!-- Current Time Reference -->
          <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{{ __('Current scheduled time:') }}</div>
            <div class="text-sm text-gray-700 dark:text-gray-300">
              {{ currentStartFormatted }}
              <span v-if="currentEndFormatted"> - {{ currentEndFormatted }}</span>
            </div>
          </div>

          <!-- Proposed Start -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Proposed Start') }}
            </label>
            <input
              v-model="proposedStart"
              @change="handleStartChange"
              type="datetime-local"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                     focus:border-orga-500 focus:outline-none"
            />
          </div>

          <!-- Proposed End -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Proposed End') }}
            </label>
            <input
              v-model="proposedEnd"
              type="datetime-local"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                     focus:border-orga-500 focus:outline-none"
            />
          </div>

          <!-- Note -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Note (optional)') }}
            </label>
            <textarea
              v-model="note"
              rows="2"
              :placeholder="__('Explain why you are proposing a different time...')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                     focus:border-orga-500 focus:outline-none resize-none
                     placeholder-gray-400 dark:placeholder-gray-500"
            ></textarea>
          </div>

          <!-- Error -->
          <div v-if="error" class="text-sm text-red-500 dark:text-red-400">
            {{ error }}
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleSubmit"
            :disabled="!canSubmit"
            class="px-4 py-2 text-sm bg-orga-500 text-white rounded-lg hover:bg-orga-600
                   disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i v-if="isSubmitting" class="fa-solid fa-spinner fa-spin mr-1"></i>
            <i v-else class="fa-solid fa-paper-plane mr-1"></i>
            {{ __('Propose Time') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
