<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityPanel.vue - Activity Manager Panel with 3-tab layout

  Displays activity management with type-adaptive tabs:
  - Overview: Type-specific properties, quick actions, related docs (replaces Details + Actions)
  - Discussion: Unified comments + notes stream with filter (replaces Comments + Notes)
  - History: Version history with field-level changes (unchanged)
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { ActivityItem, ActivityNote, ActivityChange, ManagerTab } from '@/types/orga'

// Shared Manager Components
import ManagerTabs from '@/components/manager/ManagerTabs.vue'
import ManagerTabContent from '@/components/manager/ManagerTabContent.vue'

// Tab Content Components
import ActivityOverviewTab from '@/components/manager/tabs/ActivityOverviewTab.vue'
import ActivityDiscussionTab from '@/components/manager/tabs/ActivityDiscussionTab.vue'
import ActivityChangesTab from '@/components/manager/tabs/ActivityChangesTab.vue'

interface Props {
  activity: ActivityItem | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  update: []
  pin: [isPinned: boolean]
  archive: [isArchived: boolean]
  delete: []
}>()

const router = useRouter()
const {
  getActivityDetails,
  addActivityNote,
  deleteActivityNote,
  toggleActivityPin,
  toggleActivityArchive,
  deleteActivity
} = useActivityApi()

// Tab configuration — 3 tabs
const activityTabs: ManagerTab[] = [
  { id: 'overview', icon: 'fa-circle-info', label: __('Overview') },
  { id: 'discussion', icon: 'fa-comments', label: __('Discussion') },
  { id: 'history', icon: 'fa-clock-rotate-left', label: __('History') }
]

const activeTab = ref('overview')

// Activity state (from API)
const activityState = ref<{
  is_pinned: boolean
  is_archived: boolean
  can_delete: boolean
}>({
  is_pinned: false,
  is_archived: false,
  can_delete: false
})

// Data
const notes = ref<ActivityNote[]>([])
const changes = ref<ActivityChange[]>([])

// Loading states
const isLoadingDetails = ref(false)
const isLoadingNotes = ref(false)
const isLoadingChanges = ref(false)
const isAddingNote = ref(false)

/**
 * Get doctype and docname from activity
 */
function getActivityRef(activity: ActivityItem | null): { doctype: string; docname: string } | null {
  if (!activity) return null

  const doctype = activity.reference_doctype || activity.doctype
  const docname = activity.reference_name || activity.name

  if (!doctype || !docname) return null
  return { doctype, docname }
}

/**
 * Load activity details from backend
 */
async function loadActivityDetails(doctype: string, docname: string) {
  isLoadingDetails.value = true
  isLoadingChanges.value = true
  isLoadingNotes.value = true

  try {
    const details = await getActivityDetails(doctype, docname)
    activityState.value = {
      is_pinned: details.is_pinned || false,
      is_archived: details.is_archived || false,
      can_delete: details.can_delete || false
    }
    changes.value = details.changes || []
    notes.value = details.notes || []
  } catch (e) {
    console.error('Failed to load activity details:', e)
    activityState.value = { is_pinned: false, is_archived: false, can_delete: false }
    changes.value = []
    notes.value = []
  } finally {
    isLoadingDetails.value = false
    isLoadingChanges.value = false
    isLoadingNotes.value = false
  }
}

// Load activity details when activity changes
watch(() => props.activity, async (newActivity) => {
  // Reset to overview tab when activity changes
  activeTab.value = 'overview'

  const ref = getActivityRef(newActivity)
  if (ref) {
    await loadActivityDetails(ref.doctype, ref.docname)
  } else {
    activityState.value = { is_pinned: false, is_archived: false, can_delete: false }
    changes.value = []
    notes.value = []
  }
}, { immediate: true })

// ============================================
// Action Handlers
// ============================================

async function handleTogglePin() {
  const ref = getActivityRef(props.activity)
  if (!ref) return

  try {
    const result = await toggleActivityPin(ref.doctype, ref.docname)
    activityState.value.is_pinned = result.is_pinned
    emit('pin', result.is_pinned)
    emit('update')
  } catch (e) {
    console.error('Failed to toggle pin:', e)
  }
}

async function handleToggleArchive() {
  const ref = getActivityRef(props.activity)
  if (!ref) return

  try {
    const result = await toggleActivityArchive(ref.doctype, ref.docname)
    activityState.value.is_archived = result.is_archived
    emit('archive', result.is_archived)
    emit('update')
  } catch (e) {
    console.error('Failed to toggle archive:', e)
  }
}

async function handleDelete() {
  const ref = getActivityRef(props.activity)
  if (!ref || !activityState.value.can_delete) return

  try {
    await deleteActivity(ref.doctype, ref.docname)
    emit('delete')
    emit('close')
  } catch (e) {
    console.error('Failed to delete activity:', e)
  }
}

async function handleAddNote(content: string) {
  if (!content.trim() || isAddingNote.value) return

  const ref = getActivityRef(props.activity)
  if (!ref) return

  isAddingNote.value = true
  try {
    const note = await addActivityNote(ref.doctype, ref.docname, content)
    notes.value.unshift(note)
  } catch (e) {
    console.error('Failed to add note:', e)
  } finally {
    isAddingNote.value = false
  }
}

async function handleDeleteNote(noteName: string) {
  try {
    await deleteActivityNote(noteName)
    notes.value = notes.value.filter(n => n.name !== noteName)
  } catch (e) {
    console.error('Failed to delete note:', e)
  }
}

function navigateToReference() {
  if (!props.activity) return

  const doctype = props.activity.reference_doctype || props.activity.doctype
  const docname = props.activity.reference_name || props.activity.name

  const routes: Record<string, string> = {
    'Orga Task': '/orga/tasks',
    'Orga Project': '/orga/projects',
    'Orga Resource': '/orga/contacts',
    'Orga Appointment': '/orga/schedule',
    'Orga Milestone': '/orga/projects'
  }

  const basePath = routes[doctype] || '/orga'

  if (doctype === 'Orga Task' && props.activity.project) {
    router.push({ path: `/orga/projects/${props.activity.project}`, query: { task: docname } })
  } else if (doctype === 'Orga Milestone' && props.activity.project) {
    router.push({ path: `/orga/projects/${props.activity.project}`, query: { milestone: docname } })
  } else {
    router.push(`${basePath}/${docname}`)
  }

  emit('close')
}
</script>

<template>
  <div v-if="activity" class="h-full flex flex-col bg-white dark:bg-gray-900 transition-colors">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
      <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
        <i class="fa-solid fa-sliders text-orga-500"></i>
        <span>{{ __('Manager') }}</span>
      </h3>
      <div class="flex items-center gap-2">
        <!-- Close -->
        <button
          @click="emit('close')"
          class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          :title="__('Close')"
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </div>

    <!-- Tab Navigation -->
    <ManagerTabs
      :tabs="activityTabs"
      storage-key="activity-manager"
      section-label="ACTIVITY"
      @change="activeTab = $event"
    />

    <!-- Tab Content -->
    <ManagerTabContent :active-tab="activeTab" :tabs="activityTabs" class="flex-1">
      <!-- Overview Tab (replaces Details + Actions) -->
      <template #overview>
        <ActivityOverviewTab
          :activity="activity"
          :state="activityState"
          @toggle-pin="handleTogglePin"
          @toggle-archive="handleToggleArchive"
          @delete="handleDelete"
          @navigate="navigateToReference"
        />
      </template>

      <!-- Discussion Tab (replaces Comments + Notes) -->
      <template #discussion>
        <ActivityDiscussionTab
          v-if="getActivityRef(activity)"
          :doctype="getActivityRef(activity)!.doctype"
          :docname="getActivityRef(activity)!.docname"
          :notes="notes"
          :is-loading-notes="isLoadingNotes"
          :is-adding-note="isAddingNote"
          @note-add="handleAddNote"
          @note-delete="handleDeleteNote"
        />
      </template>

      <!-- History Tab (unchanged Changes tab) -->
      <template #history>
        <ActivityChangesTab
          :changes="changes"
          :is-loading="isLoadingChanges"
        />
      </template>
    </ManagerTabContent>
  </div>
</template>
