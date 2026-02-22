<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventPanel.vue - Tabbed Event Manager panel

  Features:
  - Details: Subject, status/type badges, date/time, location, project/task, description
  - Attendees: RSVP summary, attendee list, response buttons
  - Actions: Status change, edit, send invitations, open in Desk, delete
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useEventApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { OrgaEvent, EventStatus, RsvpStatus, ManagerTab } from '@/types/orga'

// Shared Manager Components
import ManagerTabs from '@/components/manager/ManagerTabs.vue'
import ManagerTabContent from '@/components/manager/ManagerTabContent.vue'

// Tab Content Components
import EventDetailsTab from '@/components/manager/tabs/EventDetailsTab.vue'
import EventAttendeesTab from '@/components/manager/tabs/EventAttendeesTab.vue'
import EventActionsTab from '@/components/manager/tabs/EventActionsTab.vue'
import EventTimeTab from '@/components/manager/tabs/EventTimeTab.vue'
import ManualTimeEntryModal from '@/components/ManualTimeEntryModal.vue'

interface Props {
  event: OrgaEvent
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update', event?: OrgaEvent): void
  (e: 'delete', eventName: string): void
}>()

const { getEvent, updateRsvp, deleteEvent } = useEventApi()

// Tab configuration
const eventTabs: ManagerTab[] = [
  { id: 'details', icon: 'fa-file-alt', label: __('Details') },
  { id: 'attendees', icon: 'fa-users', label: __('Attendees') },
  { id: 'time', icon: 'fa-stopwatch', label: __('Time') },
  { id: 'actions', icon: 'fa-bolt', label: __('Actions') }
]

const showManualTimeEntry = ref(false)

const activeTab = ref('details')

// Local state
const eventDetail = ref<OrgaEvent | null>(null)
const isLoading = ref<boolean>(true)
const isDeleting = ref<boolean>(false)
const rsvpLoading = ref<boolean>(false)

// Methods
async function loadEvent(): Promise<void> {
  if (!props.event?.name) return
  isLoading.value = true
  try {
    eventDetail.value = await getEvent(props.event.name)
  } catch (e) {
    console.error('Failed to load event:', e)
    eventDetail.value = props.event
  } finally {
    isLoading.value = false
  }
}

async function handleRsvp(status: RsvpStatus): Promise<void> {
  if (!eventDetail.value?.name) return
  rsvpLoading.value = true
  try {
    await updateRsvp(eventDetail.value.name, status)
    await loadEvent()
    emit('update')
  } catch (e) {
    console.error('Failed to update RSVP:', e)
  } finally {
    rsvpLoading.value = false
  }
}

async function handleDelete(): Promise<void> {
  if (!eventDetail.value?.name) return
  isDeleting.value = true
  try {
    await deleteEvent(eventDetail.value.name)
    emit('delete', eventDetail.value.name)
    emit('close')
  } catch (e) {
    console.error('Failed to delete event:', e)
  } finally {
    isDeleting.value = false
  }
}

function handleEdit(): void {
  emit('update', eventDetail.value || undefined)
}

function handleSendInvitations(): void {
  if (!eventDetail.value?.name) return
  window.open(`/app/orga-appointment/${eventDetail.value.name}?action=send_invitations`, '_blank')
}

function handleStatusChange(status: EventStatus): void {
  if (!eventDetail.value?.name) return
  // Update via the Desk form API
  window.open(`/app/orga-appointment/${eventDetail.value.name}`, '_blank')
}

function handleOpenDesk(): void {
  if (!eventDetail.value?.name) return
  window.open(`/app/orga-appointment/${eventDetail.value.name}`, '_blank')
}

// Watch for event changes — reset tab and reload
watch(() => props.event?.name, (newVal) => {
  if (newVal) {
    activeTab.value = 'details'
    loadEvent()
  }
}, { immediate: true })
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900 transition-colors">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
      <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
        <i class="fa-solid fa-sliders text-orga-500"></i>
        <span>{{ __('Manager') }}</span>
      </h3>
      <button
        @click="emit('close')"
        class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :title="__('Close')"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <!-- Tab Navigation -->
    <ManagerTabs
      :tabs="eventTabs"
      :default-tab="activeTab"
      storage-key="event-manager"
      section-label="EVENT"
      @change="activeTab = $event"
    />

    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <i class="fa-solid fa-spinner fa-spin text-2xl text-orga-500"></i>
    </div>

    <!-- Tab Content -->
    <ManagerTabContent v-else-if="eventDetail" :active-tab="activeTab" :tabs="eventTabs" class="flex-1">
      <!-- Details Tab -->
      <template #details>
        <EventDetailsTab :event="eventDetail" />
      </template>

      <!-- Attendees Tab -->
      <template #attendees>
        <EventAttendeesTab
          :attendees="eventDetail.attendees || []"
          :rsvp-loading="rsvpLoading"
          @rsvp="handleRsvp"
        />
      </template>

      <!-- Time Tab -->
      <template #time>
        <EventTimeTab
          :event="eventDetail"
          @update="loadEvent()"
          @open-manual-entry="showManualTimeEntry = true"
        />
      </template>

      <!-- Actions Tab -->
      <template #actions>
        <EventActionsTab
          :event="eventDetail"
          :is-deleting="isDeleting"
          @edit="handleEdit"
          @send-invitations="handleSendInvitations"
          @status-change="handleStatusChange"
          @open-desk="handleOpenDesk"
          @delete="handleDelete"
        />
      </template>
    </ManagerTabContent>

    <!-- Manual Time Entry Modal -->
    <ManualTimeEntryModal
      :show="showManualTimeEntry"
      default-context="event"
      :default-event="eventDetail?.name || ''"
      @close="showManualTimeEntry = false"
      @created="loadEvent()"
    />
  </div>
</template>
