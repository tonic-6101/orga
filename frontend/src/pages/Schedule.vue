<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useEventApi, useProjectApi } from '../composables/useApi'
import CreateEventModal from '../components/CreateEventModal.vue'
import EventPanel from '../components/EventPanel.vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaProject, OrgaEvent, CalendarEvent, EventType } from '@/types/orga'

const eventApi = useEventApi()
const projectApi = useProjectApi()

// Calendar day structure
interface CalendarDay {
  day: number
  date: Date
  otherMonth: boolean
  today?: boolean
  events: CalendarEvent[]
}

// State
const currentDate = ref<Date>(new Date())
const events = ref<CalendarEvent[]>([])
const projects = ref<OrgaProject[]>([])
const loading = ref<boolean>(false)
const error = ref<string | null>(null)

// Filters
const selectedProject = ref<string>('')
const selectedEventType = ref<EventType | ''>('')

// Modal state
const showCreateModal = ref<boolean>(false)
const selectedEvent = ref<OrgaEvent | null>(null)
const showPanel = ref<boolean>(false)
// Computed
const weekdays: string[] = [__('Mon'), __('Tue'), __('Wed'), __('Thu'), __('Fri'), __('Sat'), __('Sun')]

const currentMonth = computed<string>(() => {
  return currentDate.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const calendarDays = computed<CalendarDay[]>(() => {
  const days: CalendarDay[] = []
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  // First day of the month
  const firstDay = new Date(year, month, 1)
  // Last day of the month
  const lastDay = new Date(year, month + 1, 0)

  // Get the day of week for the first day (0 = Sunday, convert to Monday-based)
  let startDayOfWeek = firstDay.getDay() - 1
  if (startDayOfWeek < 0) startDayOfWeek = 6

  // Previous month days
  const prevMonth = new Date(year, month, 0)
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    days.push({
      day: prevMonth.getDate() - i,
      date: new Date(year, month - 1, prevMonth.getDate() - i),
      otherMonth: true,
      events: []
    })
  }

  // Current month days
  const today = new Date()
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month, i)
    const isToday = date.toDateString() === today.toDateString()
    const dateStr = formatDate(date)
    const dayEvents = events.value.filter((e: CalendarEvent) => {
      const eventDate = e.start.split(' ')[0]
      return eventDate === dateStr
    })

    days.push({
      day: i,
      date: date,
      today: isToday,
      otherMonth: false,
      events: dayEvents
    })
  }

  // Next month days to fill remaining grid
  const remainingDays = 42 - days.length // 6 rows x 7 days
  for (let i = 1; i <= remainingDays; i++) {
    days.push({
      day: i,
      date: new Date(year, month + 1, i),
      otherMonth: true,
      events: []
    })
  }

  return days
})

const eventTypeColors: Record<string, string> = {
  Meeting: 'bg-purple-500/20 text-purple-700 dark:text-purple-300',
  Deadline: 'bg-red-500/20 text-red-700 dark:text-red-300',
  Review: 'bg-blue-500/20 text-blue-700 dark:text-blue-300',
  Milestone: 'bg-amber-500/20 text-amber-700 dark:text-amber-300',
  Other: 'bg-gray-500/20 text-gray-700 dark:text-gray-300'
}

interface LegendItem {
  type: string
  label: string
  color: string
}

const legendItems: LegendItem[] = [
  { type: 'Meeting', label: __('Meetings'), color: 'bg-purple-500' },
  { type: 'Deadline', label: __('Deadlines'), color: 'bg-red-500' },
  { type: 'Review', label: __('Reviews'), color: 'bg-blue-500' },
  { type: 'Milestone', label: __('Milestones'), color: 'bg-amber-500' }
]

const eventTypes: string[] = ['Meeting', 'Deadline', 'Review', 'Milestone', 'Other']

// Methods
function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

interface DateRange {
  start: string
  end: string
}

function getMonthRange(): DateRange {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  // Start from beginning of first week shown
  const firstDay = new Date(year, month, 1)
  let startDayOfWeek = firstDay.getDay() - 1
  if (startDayOfWeek < 0) startDayOfWeek = 6
  const startDate = new Date(year, month, 1 - startDayOfWeek)

  // End at end of last week shown
  const endDate = new Date(year, month + 1, 7)

  return {
    start: formatDate(startDate),
    end: formatDate(endDate)
  }
}

async function loadEvents(): Promise<void> {
  loading.value = true
  error.value = null

  try {
    const { start, end } = getMonthRange()
    const filters: Record<string, string> = {}

    if (selectedProject.value) {
      filters.project = selectedProject.value
    }
    if (selectedEventType.value) {
      filters.event_type = selectedEventType.value
    }

    const result = await eventApi.getCalendarEvents(start, end, filters)
    events.value = result || []
  } catch (e) {
    events.value = []
    // Check if it's a "DocType not found" error
    const errorMsg = (e as Error).message || String(e)
    if (errorMsg.includes('not found') || errorMsg.includes('does not exist')) {
      error.value = __('Events not available. Please run: bench --site orga.localhost migrate')
    } else {
      error.value = errorMsg || __('Failed to load events')
    }
    console.error('Failed to load events:', e)
  } finally {
    loading.value = false
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

function prevMonth(): void {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(newDate.getMonth() - 1)
  currentDate.value = newDate
}

function nextMonth(): void {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(newDate.getMonth() + 1)
  currentDate.value = newDate
}

function goToToday(): void {
  currentDate.value = new Date()
}

function getEventColor(event: CalendarEvent): string {
  if (event.color) {
    return `background-color: ${event.color}20; color: ${event.color};`
  }
  const type = event.extendedProps?.event_type || 'Other'
  return eventTypeColors[type] || eventTypeColors.Other
}

function onEventClick(event: CalendarEvent): void {
  // Convert calendar event to event format for the panel
  selectedEvent.value = {
    name: event.id,
    title: event.title,
    event_type: event.extendedProps?.event_type as EventType,
    status: event.extendedProps?.status,
    start_datetime: event.start,
    end_datetime: event.end,
    all_day: event.allDay ? 1 : 0,
    location: event.extendedProps?.location,
    meeting_url: event.extendedProps?.meeting_url,
    project: event.extendedProps?.project,
    project_name: event.extendedProps?.project_name
  }
  showPanel.value = true
}

function closeEventPanel(): void {
  showPanel.value = false
  selectedEvent.value = null
}

function onEventUpdate(): void {
  loadEvents()
}

function onEventDelete(_eventName: string): void {
  loadEvents()
  closeEventPanel()
}

function openCreateModal(): void {
  showCreateModal.value = true
}

function closeCreateModal(): void {
  showCreateModal.value = false
}

function onEventCreated(_event: OrgaEvent): void {
  // Reload events to show the new event
  loadEvents()
}

function formatTime(datetime: string | null | undefined): string {
  if (!datetime) return ''
  const date = new Date(datetime)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

// Watchers
watch(currentDate, () => {
  loadEvents()
})

watch([selectedProject, selectedEventType], () => {
  loadEvents()
})

// Lifecycle
onMounted(() => {
  loadProjects()
  loadEvents()
})
</script>

<template>
  <div class="p-6 bg-white dark:bg-gray-950 min-h-full">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Schedule') }}</h1>

      <div class="flex items-center gap-4">
        <!-- Filters -->
        <select
          v-model="selectedProject"
          class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
        >
          <option value="">{{ __('All Projects') }}</option>
          <option v-for="project in projects" :key="project.name" :value="project.name">
            {{ project.project_name }}
          </option>
        </select>

        <select
          v-model="selectedEventType"
          class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500"
        >
          <option value="">{{ __('All Types') }}</option>
          <option v-for="type in eventTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>

        <!-- Month Navigation -->
        <div class="flex items-center gap-2">
          <button
            @click="prevMonth"
            class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <i class="fa-solid fa-chevron-left"></i>
          </button>
          <button
            @click="goToToday"
            class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
          >
            {{ __('Today') }}
          </button>
          <span class="text-lg font-semibold text-gray-800 dark:text-gray-100 min-w-[180px] text-center">
            {{ currentMonth }}
          </span>
          <button
            @click="nextMonth"
            class="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <i class="fa-solid fa-chevron-right"></i>
          </button>
        </div>

        <!-- New Event Button -->
        <button
          @click="openCreateModal"
          class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2"
        >
          <i class="fa-solid fa-plus"></i> {{ __('New Event') }}
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center justify-between">
      <span class="text-red-700 dark:text-red-300">{{ error }}</span>
      <button @click="loadEvents" class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 text-sm font-medium">
        {{ __('Retry') }}
      </button>
    </div>

    <!-- Calendar -->
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden relative">
      <!-- Loading Overlay -->
      <div v-if="loading" class="absolute inset-0 bg-white/70 dark:bg-gray-900/70 flex items-center justify-center z-10">
        <div class="flex items-center gap-2 text-gray-600 dark:text-gray-300">
          <i class="fa-solid fa-spinner fa-spin"></i>
          <span>{{ __('Loading events...') }}</span>
        </div>
      </div>

      <!-- Weekdays -->
      <div class="grid grid-cols-7 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <div
          v-for="day in weekdays"
          :key="day"
          class="p-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase"
        >
          {{ day }}
        </div>
      </div>

      <!-- Days Grid -->
      <div class="grid grid-cols-7">
        <div
          v-for="(day, index) in calendarDays"
          :key="index"
          :class="[
            'min-h-[100px] p-2 border-r border-b border-gray-200 dark:border-gray-700',
            'last:border-r-0 [&:nth-child(7n)]:border-r-0',
            day.otherMonth && 'bg-gray-50 dark:bg-gray-800/50 opacity-50',
            day.today && 'bg-green-50 dark:bg-green-950/20'
          ]"
        >
          <div
            :class="[
              'text-sm font-medium mb-1',
              day.today && 'w-6 h-6 bg-green-600 dark:bg-green-500 text-white rounded-full flex items-center justify-center'
            ]"
          >
            {{ day.day }}
          </div>
          <div class="flex flex-col gap-0.5">
            <div
              v-for="event in day.events.slice(0, 3)"
              :key="event.id"
              @click="onEventClick(event)"
              :class="[
                'px-1.5 py-0.5 rounded text-xs truncate cursor-pointer hover:opacity-80',
                typeof getEventColor(event) === 'string' && !getEventColor(event).startsWith('background')
                  ? getEventColor(event)
                  : ''
              ]"
              :style="getEventColor(event).startsWith('background') ? getEventColor(event) : ''"
            >
              {{ event.title }}
            </div>
            <div
              v-if="day.events.length > 3"
              class="text-xs text-gray-500 dark:text-gray-400 pl-1"
            >
              {{ __('+{0} more', [day.events.length - 3]) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex gap-5 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
        <div
          v-for="item in legendItems"
          :key="item.type"
          class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400"
        >
          <div :class="['w-2.5 h-2.5 rounded-sm', item.color]"></div>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </div>

    <!-- Event Detail Panel -->
    <div
      v-if="showPanel && selectedEvent"
      class="fixed inset-0 z-50 flex justify-end"
      @click.self="closeEventPanel"
    >
      <div class="absolute inset-0 bg-black/20 dark:bg-black/50" @click="closeEventPanel"></div>
      <div class="relative w-[420px] bg-white dark:bg-gray-800 shadow-xl dark:shadow-gray-950/50 h-full">
        <EventPanel
          :event="selectedEvent"
          @close="closeEventPanel"
          @update="onEventUpdate"
          @delete="onEventDelete"
        />
      </div>
    </div>

    <!-- Create Event Modal -->
    <CreateEventModal
      :show="showCreateModal"
      @close="closeCreateModal"
      @created="onEventCreated"
    />

  </div>
</template>
