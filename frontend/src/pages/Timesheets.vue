<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useTimeLogApi, useProjectApi } from '../composables/useApi'
import { useCurrency } from '../composables/useCurrency'
import { useTimer } from '../composables/useTimer'
import ManualTimeEntryModal from '../components/ManualTimeEntryModal.vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaProject, OrgaTimeLog, TodayTimeSummary, TrackingContext } from '@/types/orga'

const timeLogApi = useTimeLogApi()
const projectApi = useProjectApi()
const { currencyIcon } = useCurrency()
const { timerState, formattedTime, stopTimer: stopActiveTimer } = useTimer()

// State
const todaySummary = ref<TodayTimeSummary | null>(null)
const loadingToday = ref(false)
const timeLogs = ref<OrgaTimeLog[]>([])
const totalLogs = ref(0)
const loadingLogs = ref(false)
const projects = ref<OrgaProject[]>([])
const showManualTimeEntry = ref(false)

// Week navigation
const weekOffset = ref(0) // 0 = this week, -1 = last week, etc.

// Filters
const filterProject = ref('')
const filterContext = ref<TrackingContext | ''>('')

// Pagination
const pageSize = 50

// Computed: week date range
const weekRange = computed(() => {
  const now = new Date()
  const dayOfWeek = now.getDay() // 0=Sun, 1=Mon...
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek
  const monday = new Date(now)
  monday.setDate(now.getDate() + mondayOffset + weekOffset.value * 7)
  monday.setHours(0, 0, 0, 0)

  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  sunday.setHours(23, 59, 59, 999)

  return { start: monday, end: sunday }
})

const weekLabel = computed(() => {
  if (weekOffset.value === 0) return __('This Week')
  if (weekOffset.value === -1) return __('Last Week')
  if (weekOffset.value === 1) return __('Next Week')
  const { start, end } = weekRange.value
  return `${formatDateShort(start)} - ${formatDateShort(end)}`
})

const weekTotalHours = computed(() => {
  return timeLogs.value.reduce((sum, log) => sum + (log.hours || 0), 0)
})

// Group logs by day
interface DayGroup {
  date: string
  dateLabel: string
  logs: OrgaTimeLog[]
  totalHours: number
}

const groupedLogs = computed<DayGroup[]>(() => {
  const groups = new Map<string, OrgaTimeLog[]>()

  for (const log of timeLogs.value) {
    const date = log.log_date || ''
    if (!groups.has(date)) {
      groups.set(date, [])
    }
    groups.get(date)!.push(log)
  }

  // Sort by date descending
  const sorted = [...groups.entries()].sort((a, b) => b[0].localeCompare(a[0]))

  return sorted.map(([date, logs]) => ({
    date,
    dateLabel: formatDayHeader(date),
    logs,
    totalHours: logs.reduce((sum, l) => sum + (l.hours || 0), 0)
  }))
})

// Helper functions
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatDateShort(date: Date): string {
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatDayHeader(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)

  if (dateStr === formatDate(today)) return __('Today')
  if (dateStr === formatDate(yesterday)) return __('Yesterday')

  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
}

function formatTimeHours(h: number): string {
  if (h >= 1) return `${h.toFixed(1)}h`
  const mins = Math.round(h * 60)
  return mins > 0 ? `${mins}m` : (h > 0 ? '< 1m' : '0m')
}

function getContextIcon(ctx: string): string {
  switch (ctx) {
    case 'task': return 'fa-check-square'
    case 'event': return 'fa-calendar'
    case 'project': return 'fa-folder'
    default: return 'fa-clock'
  }
}

function getContextIconColor(ctx: string): string {
  switch (ctx) {
    case 'task': return 'text-orga-500'
    case 'event': return 'text-purple-500'
    case 'project': return 'text-blue-500'
    default: return 'text-gray-400'
  }
}

function getContextLabel(log: OrgaTimeLog): string {
  if (log.task_subject) return log.task_subject
  if (log.event_subject) return log.event_subject
  if (log.project_name) return log.project_name
  return log.description || __('Standalone')
}

// Data loading
async function loadTodaySummary(): Promise<void> {
  loadingToday.value = true
  try {
    todaySummary.value = await timeLogApi.getTodaySummary()
  } catch (e) {
    console.error('Failed to load today summary:', e)
  } finally {
    loadingToday.value = false
  }
}

async function loadTimeLogs(): Promise<void> {
  loadingLogs.value = true
  try {
    const filters: Record<string, unknown> = {
      limit: pageSize,
      offset: 0
    }

    // Date range filter
    const { start, end } = weekRange.value
    filters.from_date = formatDate(start)
    filters.to_date = formatDate(end)

    if (filterProject.value) {
      filters.project = filterProject.value
    }
    if (filterContext.value) {
      filters.tracking_context = filterContext.value
    }

    const result = await timeLogApi.getTimeLogs(filters)
    timeLogs.value = result?.logs || []
    totalLogs.value = result?.total || 0
  } catch (e) {
    console.error('Failed to load time logs:', e)
    timeLogs.value = []
  } finally {
    loadingLogs.value = false
  }
}

async function loadProjects(): Promise<void> {
  try {
    const result = await projectApi.getProjects({ limit: 100 })
    projects.value = result?.projects || []
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
}

// Navigation
function prevWeek(): void {
  weekOffset.value--
}

function nextWeek(): void {
  weekOffset.value++
}

function goToThisWeek(): void {
  weekOffset.value = 0
}

// Timer actions
async function handleStopTimer(): Promise<void> {
  try {
    await stopActiveTimer()
    loadTodaySummary()
    loadTimeLogs()
  } catch (e) {
    console.error('Failed to stop timer:', e)
  }
}

function onTimeEntryCreated(): void {
  loadTodaySummary()
  loadTimeLogs()
}

// Watchers
watch(weekOffset, () => {
  loadTimeLogs()
})

watch([filterProject, filterContext], () => {
  loadTimeLogs()
})

// Lifecycle
onMounted(() => {
  loadProjects()
  loadTodaySummary()
  loadTimeLogs()
})
</script>

<template>
  <div class="p-6 bg-white dark:bg-gray-950 min-h-full">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-4">
        <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Timesheets') }}</h1>

        <!-- Active timer indicator -->
        <div
          v-if="timerState.isRunning"
          class="flex items-center gap-2 px-3 py-1.5 bg-orga-50 dark:bg-orga-950/30 border border-orga-200 dark:border-orga-800 rounded-lg"
        >
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-orga-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-orga-500"></span>
          </span>
          <span class="text-sm text-orga-700 dark:text-orga-300 font-medium">{{ timerState.contextLabel }}</span>
          <span class="text-sm text-orga-600 dark:text-orga-400 font-mono">{{ formattedTime }}</span>
          <button
            @click="handleStopTimer"
            class="ml-1 px-2 py-0.5 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
          >
            {{ __('Stop') }}
          </button>
        </div>
      </div>

      <button
        @click="showManualTimeEntry = true"
        class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2"
      >
        <i class="fa-solid fa-plus"></i> {{ __('Log Time') }}
      </button>
    </div>

    <!-- Today's Summary Strip -->
    <div class="mb-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-stopwatch text-orga-500"></i>
            <span class="font-semibold text-gray-800 dark:text-gray-100 text-sm">{{ __('Today') }}</span>
          </div>
          <div v-if="todaySummary && todaySummary.log_count > 0" class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
            <span class="font-medium text-gray-800 dark:text-gray-200">{{ formatTimeHours(todaySummary.total_hours) }}</span>
            <span>&middot; {{ todaySummary.log_count === 1 ? __('1 entry') : __('{0} entries', [todaySummary.log_count]) }}</span>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loadingToday" class="py-4 text-center">
          <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
        </div>

        <!-- Empty state -->
        <div v-else-if="!todaySummary || todaySummary.log_count === 0" class="py-4 text-center">
          <p class="text-sm text-gray-400 dark:text-gray-500 m-0">{{ __('No time logged today') }}</p>
          <button
            @click="showManualTimeEntry = true"
            class="mt-2 text-xs text-orga-500 dark:text-orga-400 hover:text-orga-600 dark:hover:text-orga-300 font-medium"
          >
            + {{ __('Log Time') }}
          </button>
        </div>

        <!-- Entries horizontal list -->
        <div v-else class="flex flex-wrap gap-2">
          <div
            v-for="log in todaySummary.logs"
            :key="log.name"
            class="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <i :class="['fa-solid text-xs w-3 text-center', getContextIcon(log.tracking_context), getContextIconColor(log.tracking_context)]"></i>
            <span class="text-sm text-gray-700 dark:text-gray-300 truncate max-w-[180px]">{{ getContextLabel(log) }}</span>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ formatTimeHours(log.hours) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Time Logs Table Section -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <!-- Table Header: Week nav + Filters -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <!-- Week Navigation -->
          <div class="flex items-center gap-2">
            <button
              @click="prevWeek"
              class="px-2.5 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm"
            >
              <i class="fa-solid fa-chevron-left text-xs"></i>
            </button>
            <button
              v-if="weekOffset !== 0"
              @click="goToThisWeek"
              class="px-2.5 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 text-xs"
            >
              {{ __('Today') }}
            </button>
            <span class="text-sm font-semibold text-gray-800 dark:text-gray-100 min-w-[140px] text-center">
              {{ weekLabel }}
            </span>
            <button
              @click="nextWeek"
              class="px-2.5 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 text-sm"
            >
              <i class="fa-solid fa-chevron-right text-xs"></i>
            </button>

            <!-- Weekly total -->
            <span class="ml-3 text-sm text-gray-500 dark:text-gray-400">
              {{ __('Total') }}: <span class="font-medium text-gray-700 dark:text-gray-300">{{ formatTimeHours(weekTotalHours) }}</span>
            </span>
          </div>

          <!-- Filters -->
          <div class="flex items-center gap-2">
            <select
              v-model="filterProject"
              class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
            >
              <option value="">{{ __('All Projects') }}</option>
              <option v-for="project in projects" :key="project.name" :value="project.name">
                {{ project.project_name }}
              </option>
            </select>

            <select
              v-model="filterContext"
              class="px-3 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
            >
              <option value="">{{ __('All Contexts') }}</option>
              <option value="task">{{ __('Task') }}</option>
              <option value="event">{{ __('Event') }}</option>
              <option value="project">{{ __('Project') }}</option>
              <option value="standalone">{{ __('Standalone') }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loadingLogs" class="p-8 text-center">
        <i class="fa-solid fa-spinner fa-spin text-gray-400 text-lg"></i>
        <p class="text-sm text-gray-400 mt-2 m-0">{{ __('Loading time logs...') }}</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="timeLogs.length === 0" class="p-8 text-center">
        <i class="fa-regular fa-clock text-3xl text-gray-300 dark:text-gray-600 mb-3"></i>
        <p class="text-gray-500 dark:text-gray-400 m-0">{{ __('No time logs for this period') }}</p>
        <button
          @click="showManualTimeEntry = true"
          class="mt-3 px-4 py-1.5 bg-orga-500 text-white text-xs font-medium rounded-lg hover:bg-orga-600 transition-colors inline-flex items-center gap-1.5"
        >
          <i class="fa-solid fa-plus text-[10px]"></i>
          {{ __('Log Time') }}
        </button>
      </div>

      <!-- Grouped time logs -->
      <div v-else>
        <div v-for="group in groupedLogs" :key="group.date">
          <!-- Day header -->
          <div class="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
            <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{{ group.dateLabel }}</span>
            <span class="text-xs font-medium text-gray-600 dark:text-gray-300">{{ formatTimeHours(group.totalHours) }}</span>
          </div>

          <!-- Rows -->
          <table class="w-full">
            <tbody>
              <tr
                v-for="log in group.logs"
                :key="log.name"
                class="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <!-- Context -->
                <td class="px-4 py-3 w-10">
                  <i :class="['fa-solid text-sm', getContextIcon(log.tracking_context), getContextIconColor(log.tracking_context)]"></i>
                </td>

                <!-- Label + description -->
                <td class="py-3 pr-4">
                  <p class="text-sm text-gray-800 dark:text-gray-200 m-0 truncate">{{ getContextLabel(log) }}</p>
                  <p v-if="log.description && log.description !== getContextLabel(log)" class="text-xs text-gray-500 dark:text-gray-400 m-0 truncate mt-0.5">
                    {{ log.description }}
                  </p>
                </td>

                <!-- Project -->
                <td class="py-3 pr-4 hidden md:table-cell">
                  <span v-if="log.project_name" class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ log.project_name }}</span>
                  <span v-else class="text-xs text-gray-300 dark:text-gray-600">-</span>
                </td>

                <!-- Hours -->
                <td class="py-3 pr-4 text-right w-20">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatTimeHours(log.hours) }}</span>
                </td>

                <!-- Billable indicator -->
                <td class="py-3 pr-4 w-8">
                  <span
                    v-if="log.billable"
                    class="text-xs text-green-600 dark:text-green-400"
                    :title="__('Billable')"
                  >
                    <i :class="currencyIcon"></i>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Manual Time Entry Modal -->
    <ManualTimeEntryModal
      :show="showManualTimeEntry"
      @close="showManualTimeEntry = false"
      @created="onTimeEntryCreated"
    />
  </div>
</template>
