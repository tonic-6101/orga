<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityOverviewTab.vue - Type-adaptive Overview tab for Activity Manager

  Replaces the old Details + Actions tabs with a single, type-aware view
  that shows inline-editable properties and quick actions for each activity type:
  - Task: status buttons, priority, assignee, due date, progress, checklist
  - Milestone: status, target date, task completion progress
  - Appointment: RSVP, attendees, event details
  - Project: status, progress, budget, team, task stats
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useActivityApi } from '@/composables/useApi'
import { useCurrency } from '@/composables/useCurrency'
import { __ } from '@/composables/useTranslate'
import type { ActivityItem } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'
import RelatedDocumentsSection from '@/components/manager/RelatedDocumentsSection.vue'

interface Props {
  activity: ActivityItem
  state: {
    is_pinned: boolean
    is_archived: boolean
    can_delete: boolean
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'toggle-pin': []
  'toggle-archive': []
  'delete': []
  'navigate': []
}>()

const router = useRouter()
const { getSourceDocumentInfo } = useActivityApi()
const { formatCurrency, currencySymbol } = useCurrency()

// Source document data
const sourceDoc = ref<Record<string, unknown> | null>(null)
const isLoading = ref(false)
const loadErrorMsg = ref<string | null>(null)

// Detect the activity type
const activityType = computed<string>(() => {
  const doctype = props.activity.reference_doctype || props.activity.doctype || ''
  if (doctype.includes('Task')) return 'task'
  if (doctype.includes('Milestone')) return 'milestone'
  if (doctype.includes('Appointment')) return 'appointment'
  if (doctype.includes('Project')) return 'project'
  return props.activity.type || 'unknown'
})

/**
 * Load source document info when activity changes
 */
async function loadSourceDoc() {
  const doctype = props.activity.reference_doctype || props.activity.doctype
  const docname = props.activity.reference_name || props.activity.name
  if (!doctype || !docname) {
    sourceDoc.value = null
    return
  }

  isLoading.value = true
  loadErrorMsg.value = null
  try {
    const data = await getSourceDocumentInfo(doctype, docname)
    if (data?.exists && !data?.error) {
      sourceDoc.value = data
    } else {
      sourceDoc.value = null
      loadErrorMsg.value = (data?.error as string)
        || __("{0} \"{1}\" was not found. It may have been deleted.", [doctype, docname])
    }
  } catch (e) {
    console.error('Failed to load source document info:', e)
    sourceDoc.value = null
    loadErrorMsg.value = __("Failed to load {0} \"{1}\": {2}", [doctype, docname, (e as Error).message || __('Unknown error')])
  } finally {
    isLoading.value = false
  }
}

watch(() => [props.activity.reference_name, props.activity.name], loadSourceDoc, { immediate: true })

// ============================================
// Helpers
// ============================================

function getTypeBadgeClass(type: string): string {
  const classes: Record<string, string> = {
    task: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    milestone: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    appointment: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    project: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
  }
  return classes[type] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
}

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    task: 'fa-list-check',
    milestone: 'fa-flag',
    appointment: 'fa-calendar-check',
    project: 'fa-folder'
  }
  return icons[type] || 'fa-circle'
}

function getStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'Open': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'Working': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'Completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'Cancelled': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    'Planning': 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    'In Progress': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'On Hold': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'Pending': 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    'Reached': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'Overdue': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
  return classes[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
}

function getPriorityClass(priority: string): string {
  const classes: Record<string, string> = {
    'Urgent': 'text-red-600 dark:text-red-400',
    'High': 'text-orange-600 dark:text-orange-400',
    'Medium': 'text-yellow-600 dark:text-yellow-400',
    'Low': 'text-green-600 dark:text-green-400'
  }
  return classes[priority] || 'text-gray-600 dark:text-gray-400'
}

function getPriorityIcon(priority: string): string {
  const icons: Record<string, string> = {
    'Urgent': 'fa-circle-exclamation',
    'High': 'fa-arrow-up',
    'Medium': 'fa-minus',
    'Low': 'fa-arrow-down'
  }
  return icons[priority] || 'fa-minus'
}

function getRsvpClass(status: string): string {
  const classes: Record<string, string> = {
    'Accepted': 'bg-green-500 text-white',
    'Declined': 'bg-red-500 text-white',
    'Tentative': 'bg-yellow-500 text-white',
    'Pending': 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
  return classes[status] || 'bg-gray-200 text-gray-700'
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return __('Not set')
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return __('Not set')
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit'
  })
}

function formatDoctype(doctype?: string): string {
  if (!doctype) return __('Document')
  return doctype.replace('Orga ', '')
}

function handleDelete() {
  if (confirm(__('Are you sure you want to delete this activity data? This cannot be undone.'))) {
    emit('delete')
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Quick Actions Bar -->
    <div class="flex items-center gap-2 flex-wrap">
      <!-- Type Badge -->
      <span :class="['px-2.5 py-1 rounded-full text-xs font-medium', getTypeBadgeClass(activityType)]">
        <i :class="['fa-solid mr-1', getTypeIcon(activityType)]"></i>
        {{ activityType.charAt(0).toUpperCase() + activityType.slice(1) }}
      </span>

      <div class="flex-1"></div>

      <!-- Pin -->
      <button
        @click="emit('toggle-pin')"
        :class="[
          'p-1.5 rounded transition-colors text-xs',
          state.is_pinned
            ? 'text-amber-500 bg-amber-50 dark:bg-amber-900/30'
            : 'text-gray-400 hover:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/30'
        ]"
        :title="state.is_pinned ? __('Unpin') : __('Pin')"
      >
        <i class="fa-solid fa-thumbtack"></i>
      </button>

      <!-- Archive -->
      <button
        @click="emit('toggle-archive')"
        :class="[
          'p-1.5 rounded transition-colors text-xs',
          state.is_archived
            ? 'text-orga-500 bg-orga-50 dark:bg-orga-900/30'
            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
        ]"
        :title="state.is_archived ? __('Unarchive') : __('Archive')"
      >
        <i :class="['fa-solid', state.is_archived ? 'fa-box-open' : 'fa-archive']"></i>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 text-xl"></i>
      <p class="text-sm text-gray-400 mt-2">{{ __('Loading details...') }}</p>
    </div>

    <!-- Source document not found (e.g. deleted or permission error) -->
    <div v-else-if="!sourceDoc" class="text-center py-6">
      <i class="fa-solid fa-circle-xmark text-gray-300 dark:text-gray-600 text-2xl mb-2 block"></i>
      <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('Could not load document details.') }}</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ loadErrorMsg || __('The source document may have been deleted.') }}</p>
    </div>

    <!-- ============================================ -->
    <!-- TASK OVERVIEW -->
    <!-- ============================================ -->
    <template v-else-if="activityType === 'task'">
      <!-- Title -->
      <div>
        <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
          {{ sourceDoc.subject || activity.title }}
        </p>
      </div>

      <!-- Status & Priority -->
      <div class="flex items-center gap-2 flex-wrap">
        <span :class="['px-2.5 py-1 rounded-full text-xs font-medium', getStatusClass(String(sourceDoc.status || ''))]">
          {{ sourceDoc.status }}
        </span>
        <span v-if="sourceDoc.priority" :class="['flex items-center gap-1 text-xs font-medium', getPriorityClass(String(sourceDoc.priority))]">
          <i :class="['fa-solid', getPriorityIcon(String(sourceDoc.priority))]"></i>
          {{ sourceDoc.priority }}
        </span>
      </div>

      <!-- Properties -->
      <div class="space-y-3">
        <!-- Assignee -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Assigned to') }}</span>
          <div v-if="sourceDoc.assigned_to" class="flex items-center gap-2">
            <UserAvatar
              :name="String(sourceDoc.assigned_user_name || sourceDoc.assigned_to)"
              :image="sourceDoc.assigned_user_image as string | undefined"
              size="xs"
              color="orga"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ sourceDoc.assigned_user_name || sourceDoc.assigned_to }}
            </span>
          </div>
          <span v-else class="text-sm text-gray-400 dark:text-gray-500">{{ __('Unassigned') }}</span>
        </div>

        <!-- Due Date -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Due Date') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(sourceDoc.due_date as string) }}
          </span>
        </div>

        <!-- Project -->
        <div v-if="sourceDoc.project" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Project') }}</span>
          <router-link
            :to="{ path: `/orga/projects/${sourceDoc.project}`, query: { task: activity.reference_name || activity.name } }"
            class="text-sm text-orga-500 hover:text-orga-600 no-underline"
          >
            {{ sourceDoc.project_name || sourceDoc.project }}
          </router-link>
        </div>

        <!-- Progress -->
        <div v-if="Number(sourceDoc.progress) > 0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Progress') }}</span>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ sourceDoc.progress }}%</span>
          </div>
          <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-orga-500 rounded-full transition-all"
              :style="{ width: `${sourceDoc.progress}%` }"
            ></div>
          </div>
        </div>

        <!-- Checklist -->
        <div v-if="Number(sourceDoc.checklist_total) > 0" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Checklist') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ __("{0}/{1} done", [sourceDoc.checklist_done, sourceDoc.checklist_total]) }}
          </span>
        </div>

        <!-- Hours -->
        <div v-if="Number(sourceDoc.estimated_hours) > 0 || Number(sourceDoc.actual_hours) > 0"
             class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Hours') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ __("{0}h / {1}h est.", [sourceDoc.actual_hours, sourceDoc.estimated_hours]) }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <div v-if="sourceDoc.description" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{{ __('Description') }}</p>
        <p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap break-words line-clamp-3">
          {{ sourceDoc.description }}
        </p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- MILESTONE OVERVIEW -->
    <!-- ============================================ -->
    <template v-else-if="activityType === 'milestone'">
      <!-- Title -->
      <div>
        <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
          {{ sourceDoc.milestone_name || activity.title }}
        </p>
      </div>

      <!-- Status -->
      <div class="flex items-center gap-2">
        <span :class="['px-2.5 py-1 rounded-full text-xs font-medium', getStatusClass(String(sourceDoc.status || 'Pending'))]">
          {{ sourceDoc.status || 'Pending' }}
        </span>
      </div>

      <!-- Properties -->
      <div class="space-y-3">
        <!-- Target Date -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Target Date') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(sourceDoc.due_date as string) }}
          </span>
        </div>

        <!-- Project -->
        <div v-if="sourceDoc.project" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Project') }}</span>
          <router-link
            :to="{ path: `/orga/projects/${sourceDoc.project}`, query: { milestone: activity.reference_name || activity.name } }"
            class="text-sm text-orga-500 hover:text-orga-600 no-underline"
          >
            {{ sourceDoc.project_name || sourceDoc.project }}
          </router-link>
        </div>

        <!-- Task Completion -->
        <div v-if="Number(sourceDoc.task_total) > 0">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Tasks') }}</span>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">
              {{ __("{0}/{1} completed", [sourceDoc.task_done, sourceDoc.task_total]) }}
            </span>
          </div>
          <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-green-500 rounded-full transition-all"
              :style="{ width: `${Number(sourceDoc.task_total) > 0 ? Math.round(Number(sourceDoc.task_done) / Number(sourceDoc.task_total) * 100) : 0}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="sourceDoc.description" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{{ __('Description') }}</p>
        <p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap break-words line-clamp-3">
          {{ sourceDoc.description }}
        </p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- APPOINTMENT OVERVIEW -->
    <!-- ============================================ -->
    <template v-else-if="activityType === 'appointment'">
      <!-- Title -->
      <div>
        <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
          {{ sourceDoc.subject || activity.title }}
        </p>
      </div>

      <!-- Event Type -->
      <div v-if="sourceDoc.event_type" class="flex items-center gap-2">
        <span class="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
          <i class="fa-solid fa-tag mr-1"></i>{{ sourceDoc.event_type }}
        </span>
      </div>

      <!-- Properties -->
      <div class="space-y-3">
        <!-- Date/Time -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('When') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDateTime(sourceDoc.start_datetime as string) }}
          </span>
        </div>

        <!-- End Time -->
        <div v-if="sourceDoc.end_datetime" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Until') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDateTime(sourceDoc.end_datetime as string) }}
          </span>
        </div>

        <!-- Location -->
        <div v-if="sourceDoc.location" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Location') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ sourceDoc.location }}</span>
        </div>

        <!-- Project -->
        <div v-if="sourceDoc.project" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Project') }}</span>
          <router-link
            :to="`/orga/projects/${sourceDoc.project}`"
            class="text-sm text-orga-500 hover:text-orga-600 no-underline"
          >
            {{ sourceDoc.project_name || sourceDoc.project }}
          </router-link>
        </div>
      </div>

      <!-- RSVP -->
      <div v-if="sourceDoc.user_rsvp_status" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">{{ __('Your RSVP') }}</p>
        <span :class="['px-3 py-1 rounded-full text-xs font-medium', getRsvpClass(String(sourceDoc.user_rsvp_status))]">
          {{ sourceDoc.user_rsvp_status }}
        </span>
      </div>

      <!-- Attendees -->
      <div v-if="(sourceDoc.attendees as unknown[])?.length" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Attendees') }}</p>
          <span class="text-xs text-gray-400">
            {{ __("{0}/{1} accepted", [(sourceDoc.attendee_stats as Record<string, number>)?.accepted || 0, (sourceDoc.attendee_stats as Record<string, number>)?.total || 0]) }}
          </span>
        </div>
        <div class="space-y-2">
          <div
            v-for="att in (sourceDoc.attendees as Array<Record<string, string>>)"
            :key="att.user"
            class="flex items-center gap-2"
          >
            <UserAvatar
              :name="att.full_name || att.user"
              :image="att.user_image"
              size="xs"
              color="orga"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300 flex-1 truncate">
              {{ att.full_name || att.user }}
            </span>
            <span :class="['px-1.5 py-0.5 rounded text-[10px] font-medium', getRsvpClass(att.rsvp_status || 'Pending')]">
              {{ att.rsvp_status || 'Pending' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="sourceDoc.description" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{{ __('Description') }}</p>
        <p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap break-words line-clamp-3">
          {{ sourceDoc.description }}
        </p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- PROJECT OVERVIEW -->
    <!-- ============================================ -->
    <template v-else-if="activityType === 'project'">
      <!-- Title -->
      <div>
        <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">
          {{ sourceDoc.project_name || activity.title }}
        </p>
      </div>

      <!-- Status -->
      <div class="flex items-center gap-2">
        <span :class="['px-2.5 py-1 rounded-full text-xs font-medium', getStatusClass(String(sourceDoc.status || ''))]">
          {{ sourceDoc.status }}
        </span>
      </div>

      <!-- Progress -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Progress') }}</span>
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ sourceDoc.progress }}%</span>
        </div>
        <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-orga-500 rounded-full transition-all"
            :style="{ width: `${sourceDoc.progress}%` }"
          ></div>
        </div>
      </div>

      <!-- Properties -->
      <div class="space-y-3">
        <!-- Dates -->
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Timeline') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(sourceDoc.start_date as string) }} — {{ formatDate(sourceDoc.end_date as string) }}
          </span>
        </div>

        <!-- Budget -->
        <div v-if="Number(sourceDoc.budget) > 0" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Budget') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatCurrency(Number(sourceDoc.budget)) }}
          </span>
        </div>

        <!-- Team -->
        <div v-if="Number(sourceDoc.team_count) > 0" class="flex items-center justify-between">
          <span class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ __('Team') }}</span>
          <span class="text-sm text-gray-700 dark:text-gray-300">
            <i class="fa-solid fa-users text-xs mr-1 text-gray-400"></i>{{ Number(sourceDoc.team_count) === 1 ? __('1 member') : __("{0} members", [sourceDoc.team_count]) }}
          </span>
        </div>
      </div>

      <!-- Task Stats -->
      <div class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">{{ __('Tasks') }}</p>
        <div class="grid grid-cols-3 gap-2 text-center">
          <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2">
            <p class="text-lg font-bold text-blue-700 dark:text-blue-400">{{ sourceDoc.task_open }}</p>
            <p class="text-[10px] text-blue-600 dark:text-blue-500 uppercase">{{ __('Open') }}</p>
          </div>
          <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-2">
            <p class="text-lg font-bold text-green-700 dark:text-green-400">{{ sourceDoc.task_done }}</p>
            <p class="text-[10px] text-green-600 dark:text-green-500 uppercase">{{ __('Done') }}</p>
          </div>
          <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-2">
            <p class="text-lg font-bold text-red-700 dark:text-red-400">{{ sourceDoc.task_overdue }}</p>
            <p class="text-[10px] text-red-600 dark:text-red-500 uppercase">{{ __('Overdue') }}</p>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div v-if="sourceDoc.description" class="pt-3 border-t border-gray-100 dark:border-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{{ __('Description') }}</p>
        <p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap break-words line-clamp-3">
          {{ sourceDoc.description }}
        </p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- UNKNOWN TYPE FALLBACK -->
    <!-- ============================================ -->
    <template v-else>
      <div>
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Title') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ activity.title || activity.subject || activity.name }}</p>
      </div>
      <div v-if="activity.status">
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Status') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ activity.status }}</p>
      </div>
    </template>

    <!-- ============================================ -->
    <!-- FOOTER: Navigate, Related Docs, Danger Zone -->
    <!-- ============================================ -->
    <div class="pt-3 border-t border-gray-100 dark:border-gray-800 space-y-3">
      <!-- Navigate to Source -->
      <button
        v-if="activity.reference_doctype && activity.reference_name"
        @click="emit('navigate')"
        class="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-left"
      >
        <i class="fa-solid fa-external-link-alt text-orga-500 w-5"></i>
        <span>{{ __("Open {0}", [formatDoctype(activity.reference_doctype)]) }}</span>
        <i class="fa-solid fa-chevron-right ml-auto text-gray-400 dark:text-gray-500"></i>
      </button>

      <!-- Related Documents -->
      <RelatedDocumentsSection
        v-if="activity.reference_doctype && activity.reference_name"
        :doctype="activity.reference_doctype"
        :docname="activity.reference_name"
        :activity="activity"
      />

      <!-- Danger Zone -->
      <div v-if="state.can_delete" class="pt-3 border-t border-gray-200 dark:border-gray-700">
        <button
          @click="handleDelete"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 rounded-lg transition-colors text-left"
        >
          <i class="fa-solid fa-trash w-5"></i>
          <span>{{ __('Delete Activity Data') }}</span>
        </button>
        <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1.5">
          {{ __('Deletes notes and preferences. Source document is not affected.') }}
        </p>
      </div>
    </div>
  </div>
</template>
