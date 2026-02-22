<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ContactDetail.vue - Comprehensive contact detail page with tabs
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContactApi, useDefectApi, useAssignmentApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'
import { useCurrency } from '@/composables/useCurrency'
import { useToast } from '@/composables/useToast'
import CreateDefectModal from '@/components/contact/CreateDefectModal.vue'
import type {
  OrgaContact,
  OrgaDefect,
  OrgaAssignment,
  ContactStats,
  OrgaContactSkill,
  ProficiencyLevel
} from '@/types/orga'

const route = useRoute()
const router = useRouter()
const contactApi = useContactApi()
const defectApi = useDefectApi()
const assignmentApi = useAssignmentApi()
const { success: showSuccess, error: showError } = useToast()
const { formatCurrency } = useCurrency()

const contactId = computed(() => route.params.id as string)

// Data refs
const contact = ref<OrgaContact | null>(null)
const stats = ref<ContactStats | null>(null)
const defects = ref<OrgaDefect[]>([])
const assignments = ref<OrgaAssignment[]>([])
const isLoading = ref(true)
const loadError = ref<string | null>(null)
const activeTab = ref('overview')

// Modal state
const showDefectModal = ref(false)
const showDeleteConfirm = ref(false)
const showAddSkillForm = ref(false)

// Add skill form
const newSkillName = ref('')
const newSkillProficiency = ref<ProficiencyLevel>('Intermediate')
const isAddingSkill = ref(false)

// Tab-specific loading flags
const defectsLoaded = ref(false)
const assignmentsLoaded = ref(false)

// Inline editing state
const editingField = ref<string | null>(null)
const editValue = ref<string | number | null>(null)
const isSavingField = ref(false)
const editInputRef = ref<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null>(null)

function startEdit(field: string, currentValue: unknown): void {
  editingField.value = field
  editValue.value = currentValue as string | number | null
  nextTick(() => editInputRef.value?.focus())
}

function cancelEdit(): void {
  editingField.value = null
  editValue.value = null
}

async function saveField(field: string): Promise<void> {
  if (!contact.value || isSavingField.value) return
  const currentVal = (contact.value as Record<string, unknown>)[field]
  if (editValue.value === currentVal) {
    cancelEdit()
    return
  }
  isSavingField.value = true
  try {
    await contactApi.updateContact(contact.value.name, { [field]: editValue.value } as Partial<OrgaContact>)
    ;(contact.value as Record<string, unknown>)[field] = editValue.value
    cancelEdit()
    showSuccess(__('Updated successfully'))
  } catch (e) {
    showError(__('Update failed'), (e as Error).message)
  } finally {
    isSavingField.value = false
  }
}

// Tabs definition
const tabs = computed(() => [
  { id: 'overview', label: __('Overview') },
  { id: 'skills', label: __('Skills') },
  { id: 'assignments', label: __('Assignments') },
  { id: 'defects', label: __('Defects') },
  { id: 'financial', label: __('Financial') }
])

// Status badge colors
function getStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'Active': 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    'Inactive': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
    'On Leave': 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400'
  }
  return classes[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

function getTypeClass(type: string): string {
  const classes: Record<string, string> = {
    'Employee': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    'Contractor': 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    'External': 'bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400'
  }
  return classes[type] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

function getProficiencyClass(level: string): string {
  const classes: Record<string, string> = {
    'Beginner': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
    'Intermediate': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    'Advanced': 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    'Expert': 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400'
  }
  return classes[level] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

function getSeverityClass(severity: string): string {
  const classes: Record<string, string> = {
    'Low': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    'Medium': 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-600 dark:text-yellow-400',
    'High': 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    'Critical': 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400'
  }
  return classes[severity] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

function getDefectStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'Open': 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400',
    'In Progress': 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-600 dark:text-yellow-400',
    'Resolved': 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    'Closed': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  }
  return classes[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

function getAssignmentStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'Assigned': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    'In Progress': 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-600 dark:text-yellow-400',
    'Completed': 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400',
    'Cancelled': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
  }
  return classes[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
}

// Utilities
function getInitials(name: string): string {
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}


function formatDate(date: string | null | undefined): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Utilization color
const utilizationColorClass = computed(() => {
  const pct = stats.value?.assignments.active
    ? (contact.value?.utilization_percent || 0)
    : 0
  if (pct > 100) return 'text-red-600 dark:text-red-400'
  if (pct > 80) return 'text-orange-600 dark:text-orange-400'
  if (pct > 50) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
})

// Load data
async function loadContact(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const [contactData, statsData] = await Promise.all([
      contactApi.getContact(contactId.value),
      contactApi.getContactStats(contactId.value)
    ])

    contact.value = contactData
    stats.value = statsData
  } catch (e) {
    loadError.value = (e as Error).message || __('Failed to load contact')
  } finally {
    isLoading.value = false
  }
}

async function loadDefects(): Promise<void> {
  if (defectsLoaded.value) return
  try {
    const result = await defectApi.getDefects({ contact: contactId.value, limit: 100 })
    defects.value = result.defects
    defectsLoaded.value = true
  } catch (e) {
    showError(__('Failed to load defects'), (e as Error).message)
  }
}

async function loadAssignments(): Promise<void> {
  if (assignmentsLoaded.value) return
  try {
    const result = await contactApi.getContactTimeline(contactId.value, 50)
    assignments.value = result.timeline
    assignmentsLoaded.value = true
  } catch (e) {
    showError(__('Failed to load assignments'), (e as Error).message)
  }
}

// Tab change handler
watch(activeTab, (tab) => {
  if (tab === 'defects') loadDefects()
  if (tab === 'assignments') loadAssignments()
})

// Skills management
async function addSkill(): Promise<void> {
  if (!newSkillName.value.trim()) return
  isAddingSkill.value = true

  try {
    await contactApi.addSkill(contactId.value, newSkillName.value, newSkillProficiency.value)
    showSuccess(__('Skill added'))
    newSkillName.value = ''
    newSkillProficiency.value = 'Intermediate'
    showAddSkillForm.value = false
    await loadContact()
  } catch (e) {
    showError(__('Failed to add skill'), (e as Error).message)
  } finally {
    isAddingSkill.value = false
  }
}

async function removeSkill(skillName: string): Promise<void> {
  try {
    await contactApi.removeSkill(contactId.value, skillName)
    showSuccess(__('Skill removed'))
    await loadContact()
  } catch (e) {
    showError(__('Failed to remove skill'), (e as Error).message)
  }
}

// Delete contact
async function deleteContact(): Promise<void> {
  try {
    await contactApi.deleteContact(contactId.value)
    showSuccess(__('Contact deleted'))
    router.push('/orga/contacts')
  } catch (e) {
    showError(__('Failed to delete contact'), (e as Error).message)
  }
}

// Defect created handler
function onDefectCreated(): void {
  defectsLoaded.value = false
  loadDefects()
  // Refresh stats
  contactApi.getContactStats(contactId.value).then(s => { stats.value = s })
}

onMounted(() => {
  loadContact()
})

// Watch for route param changes
watch(contactId, () => {
  defectsLoaded.value = false
  assignmentsLoaded.value = false
  loadContact()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Loading state -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('Loading contact...') }}</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="loadError" class="flex items-center justify-center py-20">
      <div class="text-center">
        <i class="fa-solid fa-exclamation-circle text-3xl text-red-400 mb-3"></i>
        <p class="text-sm text-red-500 mb-4">{{ loadError }}</p>
        <button
          @click="loadContact"
          class="px-4 py-2 text-sm bg-orga-500 text-white rounded-lg hover:bg-orga-600"
        >
          {{ __('Retry') }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <template v-else-if="contact">
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div class="flex items-center gap-4">
          <button
            @click="router.push('/orga/contacts')"
            class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <i class="fa-solid fa-arrow-left"></i>
          </button>

          <div class="w-14 h-14 rounded-full bg-teal-500 text-white text-xl font-semibold flex items-center justify-center flex-shrink-0">
            {{ contact.initials || getInitials(contact.resource_name) }}
          </div>

          <div>
            <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100">
              {{ contact.resource_name }}
            </h1>
            <p v-if="contact.designation" class="text-sm text-gray-500 dark:text-gray-400">
              {{ contact.designation }}
              <span v-if="contact.department"> &middot; {{ contact.department }}</span>
            </p>
            <div class="flex gap-2 mt-1">
              <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getStatusClass(contact.status)]">
                {{ contact.status }}
              </span>
              <span v-if="contact.resource_type" :class="['px-2 py-0.5 rounded-full text-xs font-medium', getTypeClass(contact.resource_type)]">
                {{ contact.resource_type }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <button
            @click="showDeleteConfirm = true"
            class="px-3 py-2 text-sm text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <i class="fa-solid fa-trash-can mr-1"></i> {{ __('Delete') }}
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ __('Active Assignments') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 mt-1">{{ stats.assignments.active }}</p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('{0} total', [stats.assignments.total]) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ __('Utilization') }}</p>
          <p :class="['text-2xl font-bold mt-1', utilizationColorClass]">
            {{ Math.round(contact.utilization_percent || 0) }}%
          </p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('{0}h/week capacity', [contact.weekly_capacity]) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ __('Hours Logged') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 mt-1">{{ Math.round(stats.time_logs.total_hours) }}</p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('{0}h billable', [Math.round(stats.time_logs.billable_hours)]) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ __('Projects') }}</p>
          <p class="text-2xl font-bold text-gray-800 dark:text-gray-100 mt-1">{{ stats.projects.total }}</p>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('{0} active', [stats.projects.active_count]) }}</p>
        </div>
      </div>

      <!-- Tab Bar -->
      <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
        <div class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === tab.id
                ? 'border-orga-500 text-orga-600 dark:text-orga-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
            ]"
          >
            {{ tab.label }}
            <span
              v-if="tab.id === 'defects' && stats && stats.defects.open > 0"
              class="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400"
            >
              {{ stats.defects.open }}
            </span>
          </button>
        </div>
      </div>

      <!-- Tab Content -->

      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'" class="space-y-6">
        <!-- Contact Information -->
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{{ __('Contact Information') }}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4">

            <!-- Email (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Email') }}</p>
              <template v-if="editingField === 'email'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="email"
                    @keydown.enter="saveField('email')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('email')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('email', contact.email)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.email || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Phone (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Phone') }}</p>
              <template v-if="editingField === 'phone'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="tel"
                    @keydown.enter="saveField('phone')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('phone')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('phone', contact.phone)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.phone || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Mobile (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Mobile') }}</p>
              <template v-if="editingField === 'mobile_no'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="tel"
                    @keydown.enter="saveField('mobile_no')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('mobile_no')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('mobile_no', contact.mobile_no)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.mobile_no || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Department (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Department') }}</p>
              <template v-if="editingField === 'department'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="text"
                    @keydown.enter="saveField('department')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('department')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('department', contact.department)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.department || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Designation (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Designation') }}</p>
              <template v-if="editingField === 'designation'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="text"
                    @keydown.enter="saveField('designation')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('designation')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('designation', contact.designation)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.designation || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Company (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Company') }}</p>
              <template v-if="editingField === 'company'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="text"
                    @keydown.enter="saveField('company')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('company')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('company', contact.company)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.company || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Reports To (read-only display) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Reports To') }}</p>
              <p class="text-sm text-gray-800 dark:text-gray-200">{{ contact.reports_to_name || contact.reports_to || '-' }}</p>
            </div>

            <!-- Date of Joining (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Date of Joining') }}</p>
              <template v-if="editingField === 'date_of_joining'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model="editValue"
                    type="date"
                    @keydown.enter="saveField('date_of_joining')"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('date_of_joining')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('date_of_joining', contact.date_of_joining)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ formatDate(contact.date_of_joining) }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Address (editable, spans full width) -->
            <div class="md:col-span-2 lg:col-span-3">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Address') }}</p>
              <template v-if="editingField === 'address'">
                <div class="flex items-start gap-1">
                  <textarea
                    ref="editInputRef"
                    v-model="editValue"
                    rows="2"
                    @keydown.escape="cancelEdit"
                    class="flex-1 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500 resize-y"
                  ></textarea>
                  <div class="flex flex-col gap-1">
                    <button @click="saveField('address')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                    <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                  </div>
                </div>
              </template>
              <p v-else @click="startEdit('address', contact.address)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group whitespace-pre-line">
                {{ contact.address || '-' }}
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>
          </div>
        </div>

        <!-- Capacity & Rates -->
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{{ __('Capacity & Rates') }}</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-4">

            <!-- Daily Availability (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Daily Availability') }}</p>
              <template v-if="editingField === 'availability_hours'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model.number="editValue"
                    type="number"
                    step="0.5"
                    min="0"
                    max="24"
                    @keydown.enter="saveField('availability_hours')"
                    @keydown.escape="cancelEdit"
                    class="w-20 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <span class="text-xs text-gray-400">h/day</span>
                  <button @click="saveField('availability_hours')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('availability_hours', contact.availability_hours)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.availability_hours ?? 8 }}h/day
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Weekly Capacity (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Weekly Capacity') }}</p>
              <template v-if="editingField === 'weekly_capacity'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model.number="editValue"
                    type="number"
                    step="1"
                    min="0"
                    max="168"
                    @keydown.enter="saveField('weekly_capacity')"
                    @keydown.escape="cancelEdit"
                    class="w-20 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <span class="text-xs text-gray-400">h/week</span>
                  <button @click="saveField('weekly_capacity')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('weekly_capacity', contact.weekly_capacity)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ contact.weekly_capacity }}h/week
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Hourly Cost (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Hourly Cost') }}</p>
              <template v-if="editingField === 'hourly_cost'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model.number="editValue"
                    type="number"
                    step="0.01"
                    min="0"
                    @keydown.enter="saveField('hourly_cost')"
                    @keydown.escape="cancelEdit"
                    class="w-24 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('hourly_cost')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('hourly_cost', contact.hourly_cost)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ formatCurrency(contact.hourly_cost) }}/hr
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>

            <!-- Billable Rate (editable) -->
            <div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{{ __('Billable Rate') }}</p>
              <template v-if="editingField === 'billable_rate'">
                <div class="flex items-center gap-1">
                  <input
                    ref="editInputRef"
                    v-model.number="editValue"
                    type="number"
                    step="0.01"
                    min="0"
                    @keydown.enter="saveField('billable_rate')"
                    @keydown.escape="cancelEdit"
                    class="w-24 px-2 py-1 text-sm border border-orga-400 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500"
                  />
                  <button @click="saveField('billable_rate')" class="text-green-500 hover:text-green-600 text-xs p-1"><i class="fa-solid fa-check"></i></button>
                  <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-xs p-1"><i class="fa-solid fa-xmark"></i></button>
                </div>
              </template>
              <p v-else @click="startEdit('billable_rate', contact.billable_rate)" class="text-sm text-gray-800 dark:text-gray-200 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 group">
                {{ formatCurrency(contact.billable_rate) }}/hr
                <i class="fa-solid fa-pen text-[10px] text-gray-300 dark:text-gray-600 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
              </p>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3">{{ __('Notes') }}</h3>
          <template v-if="editingField === 'notes'">
            <textarea
              ref="editInputRef"
              v-model="editValue"
              rows="4"
              @keydown.escape="cancelEdit"
              class="w-full px-3 py-2 text-sm border border-orga-400 rounded-lg bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-orga-500 resize-y"
              :placeholder="__('Add notes about this contact...')"
            ></textarea>
            <div class="flex justify-end gap-2 mt-2">
              <button @click="cancelEdit" class="px-3 py-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">{{ __('Cancel') }}</button>
              <button @click="saveField('notes')" class="px-3 py-1 text-xs bg-orga-500 text-white rounded hover:bg-orga-600">{{ __('Save') }}</button>
            </div>
          </template>
          <div v-else @click="startEdit('notes', contact.notes)" class="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 rounded p-2 -m-2 group">
            <p v-if="contact.notes" class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line" v-html="sanitizeHtml(contact.notes)"></p>
            <p v-else class="text-sm text-gray-400 dark:text-gray-500 italic">{{ __('Click to add notes...') }}
              <i class="fa-solid fa-pen text-[10px] ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
            </p>
          </div>
        </div>

        <!-- Quick Stats Summary -->
        <div v-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">{{ __('Assignments') }}</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Completed') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ stats.assignments.completed }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Active') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ stats.assignments.active }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Cancelled') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ stats.assignments.cancelled }}</span>
              </div>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">{{ __('Time Tracking') }}</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Total Hours') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ Math.round(stats.time_logs.total_hours) }}h</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Billable') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ Math.round(stats.time_logs.billable_hours) }}h</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Time Entries') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ stats.time_logs.log_count }}</span>
              </div>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">{{ __('Defects') }}</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Total') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ stats.defects.total }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Open') }}</span>
                <span :class="['font-medium', stats.defects.open > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100']">{{ stats.defects.open }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ __('Cost Impact') }}</span>
                <span class="font-medium text-gray-800 dark:text-gray-100">{{ formatCurrency(stats.defects.total_cost) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Skills Tab -->
      <div v-if="activeTab === 'skills'" class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ __('Skills & Competencies') }}</h3>
          <button
            @click="showAddSkillForm = !showAddSkillForm"
            class="px-3 py-1.5 text-sm bg-orga-500 text-white rounded-lg hover:bg-orga-600"
          >
            <i class="fa-solid fa-plus mr-1"></i> {{ __('Add Skill') }}
          </button>
        </div>

        <!-- Add Skill Form -->
        <div v-if="showAddSkillForm" class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <form @submit.prevent="addSkill" class="flex gap-3 items-end">
            <div class="flex-1">
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Skill Name') }}</label>
              <input
                v-model="newSkillName"
                type="text"
                :placeholder="__('e.g. Electrical, Plumbing...')"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Proficiency') }}</label>
              <select
                v-model="newSkillProficiency"
                class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="Beginner">{{ __('Beginner') }}</option>
                <option value="Intermediate">{{ __('Intermediate') }}</option>
                <option value="Advanced">{{ __('Advanced') }}</option>
                <option value="Expert">{{ __('Expert') }}</option>
              </select>
            </div>
            <button
              type="submit"
              :disabled="isAddingSkill || !newSkillName.trim()"
              class="px-4 py-2 text-sm bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50"
            >
              {{ isAddingSkill ? __('Adding...') : __('Add') }}
            </button>
            <button
              type="button"
              @click="showAddSkillForm = false"
              class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              {{ __('Cancel') }}
            </button>
          </form>
        </div>

        <!-- Skills List -->
        <div v-if="contact.skills && contact.skills.length > 0" class="space-y-2">
          <div
            v-for="skill in (contact.skills as OrgaContactSkill[])"
            :key="skill.skill_name"
            class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between"
          >
            <div class="flex items-center gap-3">
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ skill.skill_name }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getProficiencyClass(skill.proficiency)]">
                    {{ skill.proficiency }}
                  </span>
                  <span v-if="skill.years_experience" class="text-xs text-gray-400 dark:text-gray-500">
                    {{ skill.years_experience }} yr{{ skill.years_experience !== 1 ? 's' : '' }}
                  </span>
                </div>
              </div>
            </div>
            <button
              @click="removeSkill(skill.skill_name)"
              class="p-1.5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 rounded"
              :title="__('Remove skill')"
            >
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>

        <div v-else class="text-center py-10 text-gray-400 dark:text-gray-500">
          <i class="fa-solid fa-star text-3xl mb-3 block"></i>
          <p class="text-sm">{{ __('No skills recorded yet') }}</p>
        </div>
      </div>

      <!-- Assignments Tab -->
      <div v-if="activeTab === 'assignments'" class="space-y-4">
        <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ __('Assignment History') }}</h3>

        <div v-if="assignments.length > 0" class="space-y-2">
          <div
            v-for="assignment in assignments"
            :key="assignment.name"
            class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
                  {{ (assignment as Record<string, unknown>).task_subject || assignment.task }}
                </p>
                <p v-if="(assignment as Record<string, unknown>).project_name" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {{ (assignment as Record<string, unknown>).project_name }}
                </p>
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-400 dark:text-gray-500">
                  <span v-if="assignment.start_date">{{ formatDate(assignment.start_date) }}</span>
                  <span v-if="assignment.start_date && assignment.end_date">&rarr;</span>
                  <span v-if="assignment.end_date">{{ formatDate(assignment.end_date) }}</span>
                  <span v-if="assignment.allocated_hours">{{ assignment.allocated_hours }}h allocated</span>
                  <span v-if="assignment.actual_hours">{{ assignment.actual_hours }}h actual</span>
                </div>
              </div>
              <span :class="['px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0', getAssignmentStatusClass(assignment.status)]">
                {{ assignment.status }}
              </span>
            </div>
          </div>
        </div>

        <div v-else-if="assignmentsLoaded" class="text-center py-10 text-gray-400 dark:text-gray-500">
          <i class="fa-solid fa-clipboard-list text-3xl mb-3 block"></i>
          <p class="text-sm">{{ __('No assignments found') }}</p>
        </div>

        <div v-else class="text-center py-10">
          <i class="fa-solid fa-spinner fa-spin text-xl text-gray-400"></i>
        </div>
      </div>

      <!-- Defects Tab -->
      <div v-if="activeTab === 'defects'" class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ __('Defects & Issues') }}</h3>
          <button
            @click="showDefectModal = true"
            class="px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            <i class="fa-solid fa-plus mr-1"></i> {{ __('Report Defect') }}
          </button>
        </div>

        <!-- Defect Summary -->
        <div v-if="stats && stats.defects.total > 0" class="grid grid-cols-3 gap-4">
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-center">
            <p class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ stats.defects.total }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Total') }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-center">
            <p :class="['text-lg font-bold', stats.defects.open > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100']">{{ stats.defects.open }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Open') }}</p>
          </div>
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-center">
            <p class="text-lg font-bold text-gray-800 dark:text-gray-100">{{ formatCurrency(stats.defects.total_cost) }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Total Cost') }}</p>
          </div>
        </div>

        <!-- Defects List -->
        <div v-if="defects.length > 0" class="space-y-2">
          <div
            v-for="defect in defects"
            :key="defect.name"
            class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ defect.title }}</p>
                <div class="flex items-center gap-2 mt-1.5">
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getDefectStatusClass(defect.status)]">
                    {{ defect.status }}
                  </span>
                  <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', getSeverityClass(defect.severity)]">
                    {{ defect.severity }}
                  </span>
                  <span class="text-xs text-gray-400 dark:text-gray-500">{{ defect.defect_type }}</span>
                </div>
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-400 dark:text-gray-500">
                  <span v-if="defect.project_name">{{ defect.project_name }}</span>
                  <span>{{ __('Reported {0}', [formatDate(defect.reported_date)]) }}</span>
                  <span v-if="defect.actual_cost">{{ __('Cost: {0}', [formatCurrency(defect.actual_cost)]) }}</span>
                  <span v-else-if="defect.cost_estimate">{{ __('Est: {0}', [formatCurrency(defect.cost_estimate)]) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else-if="defectsLoaded" class="text-center py-10 text-gray-400 dark:text-gray-500">
          <i class="fa-solid fa-check-circle text-3xl mb-3 block text-green-400"></i>
          <p class="text-sm">{{ __('No defects reported') }}</p>
        </div>

        <div v-else class="text-center py-10">
          <i class="fa-solid fa-spinner fa-spin text-xl text-gray-400"></i>
        </div>
      </div>

      <!-- Financial Tab -->
      <div v-if="activeTab === 'financial'" class="space-y-6">
        <div v-if="stats" class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Rates -->
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{{ __('Rates') }}</h3>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Hourly Cost') }}</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ formatCurrency(stats.financial.hourly_cost) }}/hr</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Billable Rate') }}</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ formatCurrency(stats.financial.billable_rate) }}/hr</span>
              </div>
              <div class="flex justify-between" v-if="stats.financial.billable_rate && stats.financial.hourly_cost">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Margin') }}</span>
                <span class="text-sm font-medium text-green-600 dark:text-green-400">
                  {{ formatCurrency(stats.financial.billable_rate - stats.financial.hourly_cost) }}/hr
                </span>
              </div>
            </div>
          </div>

          <!-- Time & Revenue -->
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{{ __('Time & Revenue') }}</h3>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Total Hours Logged') }}</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ Math.round(stats.time_logs.total_hours) }}h</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Billable Hours') }}</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ Math.round(stats.financial.total_billed_hours) }}h</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-300">{{ __('Total Cost to Org') }}</span>
                <span class="text-sm font-medium text-gray-800 dark:text-gray-100">{{ formatCurrency(stats.financial.total_cost_to_org) }}</span>
              </div>
            </div>
          </div>

          <!-- Defect Impact -->
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 md:col-span-2">
            <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">{{ __('Defect Cost Impact') }}</h3>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Total Defect Cost') }}</p>
                <p :class="['text-lg font-bold mt-1', stats.financial.defect_cost > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100']">
                  {{ formatCurrency(stats.financial.defect_cost) }}
                </p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Estimated Cost') }}</p>
                <p class="text-lg font-bold text-gray-800 dark:text-gray-100 mt-1">{{ formatCurrency(stats.defects.total_estimate) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Defects Resolved') }}</p>
                <p class="text-lg font-bold text-gray-800 dark:text-gray-100 mt-1">
                  {{ stats.defects.resolved }} / {{ stats.defects.total }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation -->
      <Teleport to="body">
        <div
          v-if="showDeleteConfirm"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showDeleteConfirm = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4 p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">{{ __('Delete Contact') }}</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {{ __('Are you sure you want to delete {0}? This action cannot be undone.', [contact.resource_name]) }}
            </p>
            <div class="flex justify-end gap-3">
              <button
                @click="showDeleteConfirm = false"
                class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {{ __('Cancel') }}
              </button>
              <button
                @click="deleteContact"
                class="px-4 py-2 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600"
              >
                {{ __('Delete') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Create Defect Modal -->
      <CreateDefectModal
        :is-open="showDefectModal"
        :contact-name="contactId"
        @close="showDefectModal = false"
        @created="onDefectCreated"
      />
    </template>
  </div>
</template>
