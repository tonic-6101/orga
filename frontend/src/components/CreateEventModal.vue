<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useEventApi, useProjectApi, useContactApi } from '../composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { OrgaProject, OrgaContact, OrgaEvent, EventType } from '@/types/orga'

interface Props {
  show: boolean
  initialDate?: string | null
}

interface AttendeeForm {
  resource: string
  required: boolean
}

interface EventForm {
  title: string
  event_type: EventType
  all_day: boolean
  start_datetime: string
  end_datetime: string
  project: string
  location: string
  meeting_url: string
  description: string
  attendees: AttendeeForm[]
  send_invitations: boolean
}

interface SelectedAttendee extends OrgaContact {
  required: boolean
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  initialDate: null
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', event: OrgaEvent): void
}>()

const eventApi = useEventApi()
const projectApi = useProjectApi()
const contactApi = useContactApi()

// Form state
const form = ref<EventForm>({
  title: '',
  event_type: 'Meeting',
  all_day: false,
  start_datetime: '',
  end_datetime: '',
  project: '',
  location: '',
  meeting_url: '',
  description: '',
  attendees: [],
  send_invitations: true
})

const saving = ref<boolean>(false)
const error = ref<string | null>(null)
const projects = ref<OrgaProject[]>([])
const contacts = ref<OrgaContact[]>([])
const searchQuery = ref<string>('')
const showAttendeeSearch = ref<boolean>(false)

const eventTypes: EventType[] = ['Meeting', 'Deadline', 'Review', 'Milestone', 'Other']

// Computed
const filteredContacts = computed<OrgaContact[]>(() => {
  if (!searchQuery.value) return contacts.value
  const query = searchQuery.value.toLowerCase()
  return contacts.value.filter((r: OrgaContact) =>
    r.resource_name.toLowerCase().includes(query) ||
    (r.email && r.email.toLowerCase().includes(query))
  )
})

const selectedAttendees = computed<SelectedAttendee[]>(() => {
  return form.value.attendees.map((att: AttendeeForm) => {
    const resource = contacts.value.find((r: OrgaContact) => r.name === att.resource)
    return resource ? { ...resource, required: att.required } : null
  }).filter((item): item is SelectedAttendee => item !== null)
})

// Methods
function formatDatetimeLocal(date: Date | string): string {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function setDefaultDates(): void {
  const now = new Date()
  if (props.initialDate) {
    const date = new Date(props.initialDate)
    date.setHours(now.getHours(), 0, 0, 0)
    form.value.start_datetime = formatDatetimeLocal(date)
    date.setHours(date.getHours() + 1)
    form.value.end_datetime = formatDatetimeLocal(date)
  } else {
    now.setMinutes(0, 0, 0)
    form.value.start_datetime = formatDatetimeLocal(now)
    now.setHours(now.getHours() + 1)
    form.value.end_datetime = formatDatetimeLocal(now)
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

async function loadContacts(): Promise<void> {
  try {
    const result = await contactApi.getContacts({ status: 'Active', limit: 100 })
    contacts.value = result?.resources || []
  } catch (e) {
    console.error('Failed to load contacts:', e)
  }
}

function toggleAttendee(resourceName: string): void {
  const idx = form.value.attendees.findIndex((a: AttendeeForm) => a.resource === resourceName)
  if (idx >= 0) {
    form.value.attendees.splice(idx, 1)
  } else {
    form.value.attendees.push({ resource: resourceName, required: true })
  }
}

function removeAttendee(resourceName: string): void {
  const idx = form.value.attendees.findIndex((a: AttendeeForm) => a.resource === resourceName)
  if (idx >= 0) {
    form.value.attendees.splice(idx, 1)
  }
}

function toggleRequired(resourceName: string): void {
  const attendee = form.value.attendees.find((a: AttendeeForm) => a.resource === resourceName)
  if (attendee) {
    attendee.required = !attendee.required
  }
}

function isAttendeeSelected(resourceName: string): boolean {
  return form.value.attendees.some((a: AttendeeForm) => a.resource === resourceName)
}

function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

async function handleSubmit(): Promise<void> {
  error.value = null

  if (!form.value.title.trim()) {
    error.value = __('Title is required')
    return
  }

  if (!form.value.start_datetime) {
    error.value = __('Start date/time is required')
    return
  }

  saving.value = true

  try {
    const data = {
      title: form.value.title,
      event_type: form.value.event_type,
      all_day: form.value.all_day ? 1 : 0,
      start_datetime: form.value.start_datetime.replace('T', ' '),
      end_datetime: form.value.end_datetime ? form.value.end_datetime.replace('T', ' ') : null,
      project: form.value.project || null,
      location: form.value.location || null,
      meeting_url: form.value.meeting_url || null,
      description: form.value.description || null,
      attendees: form.value.attendees.map((a: AttendeeForm) => ({
        resource: a.resource,
        required: a.required ? 1 : 0
      }))
    }

    // Use the endpoint that can send invitations
    const result = await eventApi.createEventWithInvitations(data, form.value.send_invitations)
    emit('created', result)
    resetForm()
    emit('close')
  } catch (e) {
    error.value = (e as Error).message || __('Failed to create event')
    console.error('Failed to create event:', e)
  } finally {
    saving.value = false
  }
}

function resetForm(): void {
  form.value = {
    title: '',
    event_type: 'Meeting',
    all_day: false,
    start_datetime: '',
    end_datetime: '',
    project: '',
    location: '',
    meeting_url: '',
    description: '',
    attendees: [],
    send_invitations: true
  }
  setDefaultDates()
  error.value = null
  searchQuery.value = ''
  showAttendeeSearch.value = false
}

function handleClose(): void {
  resetForm()
  emit('close')
}

// Watchers
watch(() => props.show, (newVal) => {
  if (newVal) {
    setDefaultDates()
  }
})

// Auto-correct end datetime when start changes
watch(() => form.value.start_datetime, (newStart, oldStart) => {
  if (!newStart || !oldStart || !form.value.end_datetime) return

  const startMs = new Date(newStart).getTime()
  const endMs = new Date(form.value.end_datetime).getTime()
  const oldStartMs = new Date(oldStart).getTime()

  // If new start is at or after current end, update end to preserve duration
  if (startMs >= endMs) {
    const originalDuration = endMs - oldStartMs // Original duration in ms
    const duration = originalDuration > 0 ? originalDuration : 3600000 // Default 1 hour if invalid
    const newEnd = new Date(startMs + duration)
    form.value.end_datetime = formatDatetimeLocal(newEnd)
  }
})

// Lifecycle
onMounted(() => {
  loadProjects()
  loadContacts()
  setDefaultDates()
})
</script>

<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center"
    @click.self="handleClose"
  >
    <div class="absolute inset-0 bg-black/30 dark:bg-black/70" @click="handleClose"></div>
    <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl dark:shadow-gray-950/50 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
      <form @submit.prevent="handleSubmit" class="p-6">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-100">{{ __('New Event') }}</h2>
          <button
            type="button"
            @click="handleClose"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <i class="fa-solid fa-times"></i>
          </button>
        </div>

        <!-- Error -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-300 text-sm">
          {{ error }}
        </div>

        <!-- Form Fields -->
        <div class="space-y-4">
          <!-- Title -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Title') }} *</label>
            <input
              v-model="form.title"
              type="text"
              :placeholder="__('Meeting title')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
            />
          </div>

          <!-- Event Type & All Day -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Event Type') }}</label>
              <select
                v-model="form.event_type"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              >
                <option v-for="type in eventTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.all_day"
                  type="checkbox"
                  class="w-4 h-4 text-orga-500 border-gray-300 rounded focus:ring-orga-500"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('All day event') }}</span>
              </label>
            </div>
          </div>

          <!-- Date/Time -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Start') }} *</label>
              <input
                v-model="form.start_datetime"
                :type="form.all_day ? 'date' : 'datetime-local'"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('End') }}</label>
              <input
                v-model="form.end_datetime"
                :type="form.all_day ? 'date' : 'datetime-local'"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              />
            </div>
          </div>

          <!-- Project -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Project') }}</label>
            <select
              v-model="form.project"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
            >
              <option value="">{{ __('No project') }}</option>
              <option v-for="project in projects" :key="project.name" :value="project.name">
                {{ project.project_name }}
              </option>
            </select>
          </div>

          <!-- Location & Meeting URL -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Location') }}</label>
              <input
                v-model="form.location"
                type="text"
                :placeholder="__('Room or address')"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Meeting URL') }}</label>
              <input
                v-model="form.meeting_url"
                type="url"
                placeholder="https://..."
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              />
            </div>
          </div>

          <!-- Attendees -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Invite People') }}</label>

            <!-- Selected Attendees -->
            <div v-if="selectedAttendees.length > 0" class="space-y-2 mb-3">
              <div
                v-for="attendee in selectedAttendees"
                :key="attendee.name"
                class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded border border-gray-200 dark:border-gray-600"
              >
                <div class="flex items-center gap-2">
                  <span
                    class="w-8 h-8 bg-teal-500 text-white rounded-full text-sm flex items-center justify-center font-medium"
                  >
                    {{ getInitials(attendee.resource_name) }}
                  </span>
                  <div>
                    <div class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ attendee.resource_name }}</div>
                    <div v-if="attendee.email" class="text-xs text-gray-500 dark:text-gray-400">{{ attendee.email }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    @click="toggleRequired(attendee.name)"
                    :class="[
                      'text-xs px-2 py-1 rounded transition-colors',
                      attendee.required
                        ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/60'
                        : 'bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-500'
                    ]"
                  >
                    {{ attendee.required ? __('Required') : __('Optional') }}
                  </button>
                  <button
                    type="button"
                    @click="removeAttendee(attendee.name)"
                    class="text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 p-1"
                  >
                    <i class="fa-solid fa-times"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Add Attendee -->
            <div class="relative">
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="__('Search for people to invite...')"
                @focus="showAttendeeSearch = true"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500"
              />

              <!-- Dropdown -->
              <div
                v-if="showAttendeeSearch && filteredContacts.length > 0"
                class="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded shadow-lg dark:shadow-gray-950/50 max-h-48 overflow-y-auto"
              >
                <div
                  v-for="contact in filteredContacts"
                  :key="contact.name"
                  @click="toggleAttendee(contact.name)"
                  class="px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-600 cursor-pointer flex items-center justify-between"
                >
                  <div class="flex items-center gap-2">
                    <span
                      class="w-6 h-6 bg-gray-200 dark:bg-gray-500 text-gray-600 dark:text-gray-200 rounded-full text-xs flex items-center justify-center"
                    >
                      {{ getInitials(contact.resource_name) }}
                    </span>
                    <div>
                      <div class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ contact.resource_name }}</div>
                      <div v-if="contact.email" class="text-xs text-gray-500 dark:text-gray-400">{{ contact.email }}</div>
                    </div>
                  </div>
                  <i
                    v-if="isAttendeeSelected(contact.name)"
                    class="fa-solid fa-check text-orga-500"
                  ></i>
                </div>
              </div>
            </div>

            <!-- Close dropdown on click outside -->
            <div
              v-if="showAttendeeSearch"
              class="fixed inset-0 z-0"
              @click="showAttendeeSearch = false"
            ></div>

            <!-- Send invitations checkbox -->
            <div v-if="selectedAttendees.length > 0" class="mt-3">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.send_invitations"
                  type="checkbox"
                  class="w-4 h-4 text-orga-500 border-gray-300 rounded focus:ring-orga-500"
                />
                <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Send email invitations to attendees') }}</span>
              </label>
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Description') }}</label>
            <textarea
              v-model="form.description"
              rows="3"
              :placeholder="__('Add details about this event...')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-orga-500 resize-none dark:caret-gray-100"
            ></textarea>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            @click="handleClose"
            class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            :disabled="saving"
          >
            {{ __('Cancel') }}
          </button>
          <button
            type="submit"
            class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2"
            :disabled="saving"
          >
            <i v-if="saving" class="fa-solid fa-spinner fa-spin"></i>
            <span>{{ saving ? __('Creating...') : __('Create Event') }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
