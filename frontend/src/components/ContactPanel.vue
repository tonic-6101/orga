<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useContactApi, useAssignmentApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { OrgaContact, OrgaAssignment, ContactStatus, ContactType, SkillProficiency } from '@/types/orga'

interface Props {
  contact: OrgaContact
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update'): void
}>()

const { getContact } = useContactApi()
const { getResourceAssignments } = useAssignmentApi()

// Local state
const contactDetail = ref<OrgaContact | null>(null)
const assignments = ref<OrgaAssignment[]>([])
const isLoading = ref<boolean>(true)
const isLoadingAssignments = ref<boolean>(false)

// Status colors
const statusColors: Record<ContactStatus, string> = {
  'Active': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400',
  'Inactive': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  'On Leave': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
}

const typeColors: Record<ContactType, string> = {
  'Employee': 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400',
  'Contractor': 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-400',
  'External': 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-400'
}

const proficiencyColors: Record<SkillProficiency, string> = {
  'Beginner': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  'Intermediate': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
  'Advanced': 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
  'Expert': 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400'
}

const taskStatusColors: Record<string, string> = {
  'Open': 'text-gray-500 dark:text-gray-400',
  'In Progress': 'text-yellow-600 dark:text-yellow-400',
  'Review': 'text-blue-600 dark:text-blue-400',
  'Completed': 'text-green-600 dark:text-green-400',
  'Cancelled': 'text-red-500 dark:text-red-400'
}

// Computed
const workloadPercent = computed<number>(() => {
  if (!contactDetail.value) return 0
  return contactDetail.value.workload?.utilization_percent || 0
})

const workloadBarClass = computed<string>(() => {
  const util = workloadPercent.value
  if (util > 100) return 'bg-red-500'
  if (util > 80) return 'bg-orange-500'
  if (util > 50) return 'bg-yellow-500'
  return 'bg-green-500'
})

const workloadStatus = computed<string>(() => {
  const util = workloadPercent.value
  if (util > 100) return __('Overallocated')
  if (util > 80) return __('Busy')
  if (util > 50) return __('Moderate')
  return __('Available')
})

// Load contact details
async function loadContact(): Promise<void> {
  if (!props.contact?.name) return
  isLoading.value = true
  try {
    contactDetail.value = await getContact(props.contact.name)
  } catch (e) {
    console.error('Failed to load contact:', e)
    contactDetail.value = props.contact
  } finally {
    isLoading.value = false
  }
}

// Load assignments
async function loadAssignments(): Promise<void> {
  if (!props.contact?.name) return
  isLoadingAssignments.value = true
  try {
    assignments.value = await getResourceAssignments(props.contact.name) || []
  } catch (e) {
    console.error('Failed to load assignments:', e)
    assignments.value = []
  } finally {
    isLoadingAssignments.value = false
  }
}

// Format date
function formatDate(date: string | null | undefined): string {
  if (!date) return __('Not set')
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Get initials
function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Watch for contact changes
watch(() => props.contact?.name, (newVal) => {
  if (newVal) {
    loadContact()
    loadAssignments()
  }
}, { immediate: true })
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
        <i class="fa-solid fa-user text-orga-500"></i> {{ __('Contact Details') }}
      </h3>
      <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <i class="fa-solid fa-spinner fa-spin text-2xl text-orga-500"></i>
    </div>

    <!-- Contact Content -->
    <div v-else class="flex-1 overflow-auto">
      <!-- Contact Header -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 text-center">
        <div class="w-20 h-20 rounded-full bg-teal-500 text-white text-3xl font-semibold flex items-center justify-center mx-auto mb-3">
          {{ contactDetail?.initials || getInitials(contactDetail?.resource_name) }}
        </div>
        <h4 class="text-xl font-semibold text-gray-800 dark:text-gray-100 m-0 mb-1">{{ contactDetail?.resource_name }}</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 m-0 mb-3">{{ contactDetail?.designation || contactDetail?.resource_type }}</p>
        <div class="flex items-center justify-center gap-2">
          <span :class="['text-xs px-2 py-1 rounded-full', statusColors[contactDetail?.status]]">
            {{ contactDetail?.status }}
          </span>
          <span :class="['text-xs px-2 py-1 rounded-full', typeColors[contactDetail?.resource_type]]">
            {{ contactDetail?.resource_type }}
          </span>
        </div>
      </div>

      <!-- Contact Info -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
        <div v-if="contactDetail?.email" class="flex items-center gap-3">
          <i class="fa-solid fa-envelope text-gray-400 dark:text-gray-500 w-4"></i>
          <a :href="`mailto:${contactDetail.email}`" class="text-sm text-orga-600 dark:text-orga-400 hover:underline">
            {{ contactDetail.email }}
          </a>
        </div>
        <div v-if="contactDetail?.department" class="flex items-center gap-3">
          <i class="fa-solid fa-building text-gray-400 dark:text-gray-500 w-4"></i>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ contactDetail.department }}</span>
        </div>
        <div class="flex items-center gap-3">
          <i class="fa-solid fa-clock text-gray-400 dark:text-gray-500 w-4"></i>
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ contactDetail?.weekly_capacity || 40 }}h {{ __('weekly capacity') }}</span>
        </div>
      </div>

      <!-- Workload Section -->
      <div v-if="contactDetail?.status === 'Active'" class="p-4 border-b border-gray-200 dark:border-gray-700">
        <h5 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-chart-pie text-orga-500"></i> {{ __('Workload') }}
        </h5>
        <div class="mb-2">
          <div class="flex items-center justify-between text-sm mb-1">
            <span class="text-gray-600 dark:text-gray-400">{{ workloadStatus }}</span>
            <span :class="[
              'font-medium',
              workloadPercent > 100 ? 'text-red-600 dark:text-red-400' : workloadPercent > 80 ? 'text-orange-600 dark:text-orange-400' : 'text-gray-700 dark:text-gray-300'
            ]">
              {{ workloadPercent }}%
            </span>
          </div>
          <div class="h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              :class="['h-full rounded-full transition-all', workloadBarClass]"
              :style="{ width: Math.min(workloadPercent, 100) + '%' }"
            ></div>
          </div>
        </div>
        <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{{ contactDetail?.workload?.allocated_hours || 0 }}h {{ __('allocated') }}</span>
          <span>{{ contactDetail?.weekly_capacity || 40 }}h {{ __('capacity') }}</span>
        </div>
      </div>

      <!-- Skills Section -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <h5 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-star text-orga-500"></i> {{ __('Skills') }}
          <span v-if="contactDetail?.skills?.length" class="text-xs font-normal text-gray-400 dark:text-gray-500">
            ({{ contactDetail.skills.length }})
          </span>
        </h5>

        <div v-if="contactDetail?.skills?.length" class="space-y-2">
          <div
            v-for="skill in contactDetail.skills"
            :key="skill.skill_name"
            class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div>
              <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ skill.skill_name }}</span>
              <span v-if="skill.years_experience" class="text-xs text-gray-400 dark:text-gray-500 ml-2">
                {{ skill.years_experience }}y exp
              </span>
            </div>
            <span :class="['text-xs px-2 py-0.5 rounded-full', proficiencyColors[skill.proficiency]]">
              {{ skill.proficiency }}
            </span>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-3">
          {{ __('No skills listed') }}
        </div>
      </div>

      <!-- Current Assignments -->
      <div class="p-4">
        <h5 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
          <i class="fa-solid fa-tasks text-orga-500"></i> {{ __('Current Assignments') }}
          <span v-if="assignments.length" class="text-xs font-normal text-gray-400 dark:text-gray-500">
            ({{ assignments.length }})
          </span>
        </h5>

        <!-- Loading -->
        <div v-if="isLoadingAssignments" class="text-center py-3">
          <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
        </div>

        <!-- Assignments list -->
        <div v-else-if="assignments.length" class="space-y-2">
          <div
            v-for="assignment in assignments"
            :key="assignment.name"
            class="p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-orga-300 dark:hover:border-orga-700 transition-colors"
          >
            <div class="flex items-start justify-between mb-1">
              <span class="text-sm font-medium text-gray-800 dark:text-gray-100 flex-1">{{ assignment.task_subject }}</span>
              <span :class="['text-xs', taskStatusColors[assignment.task_status]]">
                {{ assignment.task_status }}
              </span>
            </div>
            <div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span v-if="assignment.project_name" class="flex items-center gap-1">
                <i class="fa-solid fa-folder"></i>
                {{ assignment.project_name }}
              </span>
              <span v-if="assignment.allocated_hours" class="flex items-center gap-1">
                <i class="fa-solid fa-clock"></i>
                {{ assignment.allocated_hours }}h
              </span>
              <span v-if="assignment.task_due_date" class="flex items-center gap-1">
                <i class="fa-solid fa-calendar"></i>
                {{ formatDate(assignment.task_due_date) }}
              </span>
            </div>
            <div v-if="assignment.role" class="mt-1">
              <span class="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded">
                {{ assignment.role }}
              </span>
            </div>
          </div>
        </div>

        <div v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-3">
          {{ __('No active assignments') }}
        </div>
      </div>
    </div>
  </div>
</template>
