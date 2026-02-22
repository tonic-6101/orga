<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskTimeTab.vue - Time tracking tab for Task Manager
  Shows timer control, time summary, and time log list.
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useTimer } from '@/composables/useTimer'
import { useTimeLogApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { OrgaTask, OrgaTimeLog } from '@/types/orga'

interface Props {
  task: OrgaTask
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update'): void
  (e: 'open-manual-entry'): void
}>()

const { timerState, formattedTime, startTimer, stopTimer, isTrackingTask, loading: timerLoading } = useTimer()
const api = useTimeLogApi()

const timeLogs = ref<OrgaTimeLog[]>([])
const totalHours = ref(0)
const logCount = ref(0)
const isLoading = ref(false)
const timerDescription = ref('')

const isCurrentTask = computed(() => isTrackingTask(props.task.name))
const isOtherRunning = computed(() => timerState.value.isRunning && !isCurrentTask.value)

const progressPercent = computed(() => {
  if (!props.task.estimated_hours || props.task.estimated_hours <= 0) return 0
  return Math.min(100, Math.round(((props.task.actual_hours || 0) / props.task.estimated_hours) * 100))
})

const isOverEstimate = computed(() => {
  return (props.task.actual_hours || 0) > (props.task.estimated_hours || 0) && (props.task.estimated_hours || 0) > 0
})

async function loadTimeLogs(): Promise<void> {
  isLoading.value = true
  try {
    const result = await api.getTimeLogs({ task: props.task.name, limit: 20 })
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
      trackingContext: 'task',
      task: props.task.name
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
  if (h >= 1) return `${h.toFixed(1)}h`
  const mins = Math.round(h * 60)
  return mins > 0 ? `${mins}m` : (h > 0 ? '< 1m' : '0m')
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

watch(() => props.task.name, () => {
  loadTimeLogs()
})

onMounted(() => {
  loadTimeLogs()
})
</script>

<template>
  <div class="space-y-5">
    <!-- Timer Control -->
    <div class="bg-gradient-to-br from-orga-50 to-orga-100 dark:from-orga-900/30 dark:to-orga-800/20 rounded-lg p-4">
      <!-- Active on this task -->
      <div v-if="isCurrentTask" class="text-center space-y-3">
        <div class="flex items-center justify-center gap-2 text-xs text-orga-600 dark:text-orga-400 uppercase font-semibold">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-orga-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-orga-500"></span>
          </span>
          {{ __('Timer Running') }}
        </div>
        <p class="text-3xl font-mono font-bold text-orga-700 dark:text-orga-300 m-0 tabular-nums">{{ formattedTime }}</p>
        <input
          v-model="timerDescription"
          type="text"
          :placeholder="__('What are you working on?')"
          class="w-full px-3 py-1.5 text-sm text-center bg-white/60 dark:bg-gray-800/60 border border-orga-200 dark:border-orga-700 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:border-orga-400 dark:focus:border-orga-500"
        />
        <button
          @click="handleStopTimer"
          :disabled="timerLoading"
          class="px-6 py-2 bg-orga-500 text-white text-sm font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors inline-flex items-center gap-2"
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
          class="mt-2 px-4 py-1.5 bg-orga-500 text-white text-xs font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5"
          :title="__('Stops current timer and starts for this task')"
        >
          <i class="fa-solid fa-play text-[10px]"></i>
          {{ __('Switch to this task') }}
        </button>
      </div>

      <!-- Idle -->
      <div v-else class="text-center">
        <button
          @click="handleStartTimer"
          :disabled="timerLoading"
          class="px-6 py-2 bg-orga-500 text-white text-sm font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors inline-flex items-center gap-2"
        >
          <i class="fa-solid fa-play text-xs"></i>
          {{ __('Start Timer') }}
        </button>
      </div>
    </div>

    <!-- Hours Summary -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-chart-bar text-orga-500"></i>
        {{ __('Time Summary') }}
      </h5>
      <div class="grid grid-cols-2 gap-3">
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase m-0">{{ __('Estimated') }}</p>
          <p class="text-lg font-semibold text-gray-800 dark:text-gray-200 m-0">
            {{ task.estimated_hours ? `${task.estimated_hours}h` : '—' }}
          </p>
        </div>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase m-0">{{ __('Actual') }}</p>
          <p :class="['text-lg font-semibold m-0', isOverEstimate ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-200']">
            {{ formatHours(task.actual_hours || 0) }}
          </p>
        </div>
      </div>

      <!-- Progress bar -->
      <div v-if="task.estimated_hours" class="mt-3">
        <div class="flex justify-between text-[10px] text-gray-500 dark:text-gray-400 mb-1">
          <span>{{ __("{0} entries", [logCount]) }}</span>
          <span>{{ progressPercent }}%</span>
        </div>
        <div class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            :class="['h-full rounded-full transition-all', isOverEstimate ? 'bg-red-500' : 'bg-orga-500']"
            :style="{ width: `${Math.min(progressPercent, 100)}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Time Log List -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider m-0 flex items-center gap-2">
          <i class="fa-solid fa-list text-orga-500"></i>
          {{ __('Time Logs') }}
        </h5>
        <button
          @click="emit('open-manual-entry')"
          class="text-xs text-orga-500 dark:text-orga-400 hover:text-orga-600 dark:hover:text-orga-300 font-medium"
        >
          + {{ __('Log Time') }}
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
