<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventTimeTab.vue - Time tracking tab for Event Panel
  Shows timer control, scheduled vs actual time, and time log list.
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { __ } from '@/composables/useTranslate'
import { useTimer } from '@/composables/useTimer'
import { useTimeLogApi } from '@/composables/useApi'
import type { OrgaEvent, OrgaTimeLog } from '@/types/orga'

interface Props {
  event: OrgaEvent
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update'): void
  (e: 'open-manual-entry'): void
}>()

const { timerState, formattedTime, startTimer, stopTimer, isTrackingEvent, loading: timerLoading } = useTimer()
const api = useTimeLogApi()

const timeLogs = ref<OrgaTimeLog[]>([])
const totalHours = ref(0)
const logCount = ref(0)
const isLoading = ref(false)
const timerDescription = ref('')

const isCurrentEvent = computed(() => isTrackingEvent(props.event.name))
const isOtherRunning = computed(() => timerState.value.isRunning && !isCurrentEvent.value)

const scheduledDuration = computed(() => {
  if (!props.event.start_datetime || !props.event.end_datetime) return null
  const start = new Date(props.event.start_datetime).getTime()
  const end = new Date(props.event.end_datetime).getTime()
  const hours = (end - start) / (1000 * 60 * 60)
  return Math.max(0, Math.round(hours * 10) / 10)
})

async function loadTimeLogs(): Promise<void> {
  isLoading.value = true
  try {
    const result = await api.getTimeLogs({ event: props.event.name, limit: 20 })
    timeLogs.value = result.logs || []
    totalHours.value = (result.logs || []).reduce((sum: number, l: OrgaTimeLog) => sum + (l.hours || 0), 0)
    logCount.value = result.total || 0
  } catch {
    timeLogs.value = []
  } finally {
    isLoading.value = false
  }
}

async function handleStartTimer(): Promise<void> {
  try {
    await startTimer({
      trackingContext: 'event',
      event: props.event.name
    })
  } catch (e) {
    console.error('Failed to start timer:', e)
  }
}

async function handleStopTimer(): Promise<void> {
  try {
    const result = await stopTimer()
    if (timerDescription.value.trim() && result?.name) {
      await api.updateTimeLog(result.name, { description: timerDescription.value.trim() })
    }
    timerDescription.value = ''
    await loadTimeLogs()
    emit('update')
  } catch (e) {
    console.error('Failed to stop timer:', e)
  }
}

async function handleDeleteLog(name: string): Promise<void> {
  try {
    await api.deleteTimeLog(name)
    await loadTimeLogs()
    emit('update')
  } catch (e) {
    console.error('Failed to delete time log:', e)
  }
}

function formatHours(h: number): string {
  if (h >= 1) return __("{0}h", [h.toFixed(1)])
  const mins = Math.round(h * 60)
  return mins > 0 ? __("{0}m", [mins]) : (h > 0 ? __('< 1m') : __('0m'))
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

watch(() => props.event.name, () => {
  loadTimeLogs()
})

onMounted(() => {
  loadTimeLogs()
})
</script>

<template>
  <div class="space-y-5">
    <!-- Timer Control -->
    <div class="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/20 rounded-lg p-4">
      <!-- Active on this event -->
      <div v-if="isCurrentEvent" class="text-center space-y-3">
        <div class="flex items-center justify-center gap-2 text-xs text-purple-600 dark:text-purple-400 uppercase font-semibold">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
          </span>
          {{ __('Timer Running') }}
        </div>
        <p class="text-3xl font-mono font-bold text-purple-700 dark:text-purple-300 m-0 tabular-nums">{{ formattedTime }}</p>
        <input
          v-model="timerDescription"
          type="text"
          :placeholder="__('What are you working on?')"
          class="w-full px-3 py-1.5 text-sm text-center bg-white/60 dark:bg-gray-800/60 border border-purple-200 dark:border-purple-700 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:border-purple-400 dark:focus:border-purple-500"
        />
        <button
          @click="handleStopTimer"
          :disabled="timerLoading"
          class="px-6 py-2 bg-purple-500 text-white text-sm font-medium rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors inline-flex items-center gap-2"
        >
          <i class="fa-solid fa-stop text-xs"></i>
          {{ __('Stop & Save') }}
        </button>
      </div>

      <!-- Timer active on something else -->
      <div v-else-if="isOtherRunning" class="text-center space-y-2">
        <p class="text-xs text-gray-500 dark:text-gray-400 m-0">{{ __('Timer active on') }}</p>
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300 m-0">{{ timerState.contextLabel }}</p>
        <button
          @click="handleStartTimer"
          :disabled="timerLoading"
          class="mt-2 px-4 py-1.5 bg-purple-500 text-white text-xs font-medium rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5"
          :title="__('Stops current timer and starts for this event')"
        >
          <i class="fa-solid fa-play text-[10px]"></i>
          {{ __('Switch to this event') }}
        </button>
      </div>

      <!-- Idle -->
      <div v-else class="text-center">
        <button
          @click="handleStartTimer"
          :disabled="timerLoading"
          class="px-6 py-2 bg-purple-500 text-white text-sm font-medium rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors inline-flex items-center gap-2"
        >
          <i class="fa-solid fa-play text-xs"></i>
          {{ __('Start Timer') }}
        </button>
      </div>
    </div>

    <!-- Duration Summary -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-chart-bar text-purple-500"></i>
        {{ __('Duration Summary') }}
      </h5>
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase m-0">{{ __('Scheduled') }}</p>
          <p class="text-lg font-semibold text-gray-800 dark:text-gray-200 m-0">
            {{ scheduledDuration !== null ? __("{0}h", [scheduledDuration]) : '—' }}
          </p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase m-0">{{ __('Tracked') }}</p>
          <p class="text-lg font-semibold text-gray-800 dark:text-gray-200 m-0">
            {{ formatHours(totalHours) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Time Log List -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider m-0 flex items-center gap-2">
          <i class="fa-solid fa-list text-purple-500"></i>
          {{ __('Time Logs') }}
          <span v-if="logCount > 0" class="text-gray-400">({{ logCount }})</span>
        </h5>
        <button
          @click="emit('open-manual-entry')"
          class="text-xs text-purple-500 dark:text-purple-400 hover:text-purple-600 dark:hover:text-purple-300 font-medium"
        >
          {{ __('+ Log Time') }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="text-center py-4">
        <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
      </div>

      <!-- Empty state -->
      <div v-else-if="timeLogs.length === 0" class="text-center py-6">
        <i class="fa-regular fa-clock text-2xl text-gray-300 dark:text-gray-600 mb-2"></i>
        <p class="text-sm text-gray-400 dark:text-gray-500 m-0">{{ __('No time logged yet') }}</p>
      </div>

      <!-- Entries -->
      <div v-else class="space-y-2 max-h-[300px] overflow-y-auto">
        <div
          v-for="log in timeLogs"
          :key="log.name"
          class="flex items-center justify-between p-2.5 bg-gray-50 dark:bg-gray-800 rounded-lg group"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
                {{ formatHours(log.hours) }}
              </span>
              <span class="text-xs text-gray-400 dark:text-gray-500">
                {{ formatDate(log.log_date) }}
              </span>
            </div>
            <p v-if="log.description" class="text-xs text-gray-500 dark:text-gray-400 truncate m-0 mt-0.5">
              {{ log.description }}
            </p>
          </div>
          <button
            @click="handleDeleteLog(log.name)"
            class="p-1 text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
            :title="__('Delete')"
          >
            <i class="fa-solid fa-trash-can text-xs"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
