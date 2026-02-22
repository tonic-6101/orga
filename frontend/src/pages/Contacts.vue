<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useContactApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { OrgaContact, ContactStatus, ContactType } from '@/types/orga'

const router = useRouter()
const { getContacts, createContact, loading, error } = useContactApi()

// New contact form data structure
interface NewContactForm {
  resource_name: string
  email: string
  resource_type: ContactType
  status: ContactStatus
  designation: string
  weekly_capacity: number
  availability_hours: number
}

// State
const contacts = ref<OrgaContact[]>([])
const isLoading = ref<boolean>(true)
const loadError = ref<string | null>(null)
const searchQuery = ref<string>('')
const statusFilter = ref<ContactStatus | ''>('')
const departmentFilter = ref<string>('')

// Panel state (kept for backward compat, unused since navigation to detail page)
const selectedContact = ref<OrgaContact | null>(null)
const showPanel = ref<boolean>(false)

// Create modal state
const showCreateModal = ref<boolean>(false)
const isCreating = ref<boolean>(false)
const createError = ref<string | null>(null)
const newContact = ref<NewContactForm>({
  resource_name: '',
  email: '',
  resource_type: 'Employee',
  status: 'Active',
  designation: '',
  weekly_capacity: 40,
  availability_hours: 8
})

// Computed
const filteredContacts = computed<OrgaContact[]>(() => {
  let result = contacts.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter((r: OrgaContact) =>
      r.resource_name.toLowerCase().includes(query) ||
      r.email?.toLowerCase().includes(query) ||
      r.skills?.some(s => s.skill_name.toLowerCase().includes(query))
    )
  }

  return result
})

// Load contacts
async function loadContacts(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const filters: Record<string, string> = {}
    if (statusFilter.value) filters.status = statusFilter.value
    if (departmentFilter.value) filters.department = departmentFilter.value

    const data = await getContacts(filters)
    contacts.value = data.resources || []
  } catch (e) {
    console.error('Failed to load contacts:', e)
    loadError.value = (e as Error).message || 'Failed to load contacts'
  } finally {
    isLoading.value = false
  }
}

// Navigate to contact detail page
function selectContact(contact: OrgaContact): void {
  router.push(`/orga/contacts/${contact.name}`)
}

// Open create modal
function openCreateModal(): void {
  newContact.value = {
    resource_name: '',
    email: '',
    resource_type: 'Employee',
    status: 'Active',
    designation: '',
    weekly_capacity: 40,
    availability_hours: 8
  }
  createError.value = null
  showCreateModal.value = true
}

// Close create modal
function closeCreateModal(): void {
  showCreateModal.value = false
  createError.value = null
}

// Handle create contact
async function handleCreateContact(): Promise<void> {
  if (!newContact.value.resource_name.trim()) {
    createError.value = __('Contact name is required')
    return
  }

  isCreating.value = true
  createError.value = null

  try {
    await createContact(newContact.value)
    closeCreateModal()
    await loadContacts()
  } catch (e) {
    console.error('Failed to create contact:', e)
    createError.value = (e as Error).message || 'Failed to create contact'
  } finally {
    isCreating.value = false
  }
}

// Get availability class based on status and workload
function getAvailabilityClass(contact: OrgaContact): string {
  if (contact.status === 'On Leave') return 'bg-red-500'
  if (contact.status === 'Inactive') return 'bg-gray-400'
  if (contact.workload_status === 'overallocated') return 'bg-red-500'
  if (contact.workload_status === 'busy') return 'bg-orange-500'
  if (contact.workload_status === 'moderate') return 'bg-yellow-500'
  return 'bg-green-500'
}

function getAvailabilityText(contact: OrgaContact): string {
  if (contact.status === 'On Leave') return __('On Leave')
  if (contact.status === 'Inactive') return __('Inactive')
  if (contact.workload_status === 'overallocated') return __('Overallocated')
  if (contact.workload_status === 'busy') return __('Busy')
  if (contact.workload_status === 'moderate') return __('Moderate')
  return __('Available')
}

// Get workload bar color class
function getWorkloadBarClass(contact: OrgaContact): string {
  if (contact.status !== 'Active') return 'bg-gray-300 dark:bg-gray-600'
  const util = contact.utilization_percent || 0
  if (util > 100) return 'bg-red-500'
  if (util > 80) return 'bg-orange-500'
  if (util > 50) return 'bg-yellow-500'
  return 'bg-green-500'
}

// Get workload percentage capped at 100 for display
function getWorkloadWidth(contact: OrgaContact): number {
  const util = contact.utilization_percent || 0
  return Math.min(util, 100)
}

// Watch filters
watch([statusFilter, departmentFilter], () => {
  loadContacts()
})

onMounted(loadContacts)
</script>

<template>
  <div class="flex h-full bg-white dark:bg-gray-950">
    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Contacts') }}</h1>
        <button
          @click="openCreateModal"
          class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2"
        >
          <i class="fa-solid fa-plus"></i> {{ __('Add Contact') }}
        </button>
      </div>

      <!-- Filters -->
      <div class="flex gap-4 mb-6">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="__('Search by name, email, or skill...')"
          class="flex-1 px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:border-orga-500 focus:outline-none"
        />
        <select
          v-model="statusFilter"
          class="px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
        >
          <option value="">{{ __('All Status') }}</option>
          <option value="Active">{{ __('Active') }}</option>
          <option value="Inactive">{{ __('Inactive') }}</option>
          <option value="On Leave">{{ __('On Leave') }}</option>
        </select>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center py-12">
        <div class="text-center">
          <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
          <p class="text-gray-500 dark:text-gray-400">{{ __('Loading contacts...') }}</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="flex items-center justify-center py-12">
        <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center">
          <i class="fa-solid fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
          <h3 class="text-red-800 dark:text-red-300 font-medium mb-2">{{ __('Error loading contacts') }}</h3>
          <p class="text-red-600 dark:text-red-400 text-sm mb-4">{{ loadError }}</p>
          <button
            @click="loadContacts"
            class="px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60"
          >
            {{ __('Try Again') }}
          </button>
        </div>
      </div>

      <!-- Contacts Grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        <div
          v-for="contact in filteredContacts"
          :key="contact.name"
          @click="selectContact(contact)"
          :class="[
            'bg-white dark:bg-gray-800 border rounded-lg p-5 text-center hover:shadow-md dark:hover:shadow-gray-950/50 transition-all cursor-pointer',
            selectedContact?.name === contact.name ? 'border-orga-500 ring-2 ring-orga-100 dark:ring-orga-900/40' : 'border-gray-200 dark:border-gray-700'
          ]"
        >
          <!-- Avatar -->
          <div class="w-16 h-16 rounded-full bg-teal-500 text-white text-2xl font-semibold flex items-center justify-center mx-auto mb-3">
            {{ contact.initials }}
          </div>

          <h3 class="text-base font-semibold text-gray-800 dark:text-gray-100 m-0">{{ contact.resource_name }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">{{ contact.designation || contact.resource_type }}</p>

          <!-- Stats -->
          <div class="flex justify-center gap-6 py-3 border-t border-b border-gray-200 dark:border-gray-700 mb-4">
            <div class="text-center">
              <div class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ contact.active_assignments || 0 }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">{{ __('Tasks') }}</div>
            </div>
            <div class="text-center">
              <div class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ contact.weekly_capacity || 40 }}h</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">{{ __('Capacity') }}</div>
            </div>
          </div>

          <!-- Workload Bar -->
          <div
            v-if="contact.status === 'Active'"
            class="mb-4 group relative"
            :title="`${contact.allocated_hours || 0}h allocated of ${contact.weekly_capacity || 40}h capacity (${contact.utilization_percent || 0}%)`"
          >
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
              <span>{{ __('Workload') }}</span>
              <span :class="[
                contact.utilization_percent > 100 ? 'text-red-600 dark:text-red-400 font-medium' : '',
                contact.utilization_percent > 80 ? 'text-orange-600 dark:text-orange-400' : ''
              ]">
                {{ contact.utilization_percent || 0 }}%
              </span>
            </div>
            <div class="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all duration-300', getWorkloadBarClass(contact)]"
                :style="{ width: getWorkloadWidth(contact) + '%' }"
              ></div>
            </div>
            <!-- Tooltip on hover -->
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 dark:bg-gray-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
              {{ contact.allocated_hours || 0 }}h / {{ contact.weekly_capacity || 40 }}h allocated
              <div class="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800 dark:border-t-gray-700"></div>
            </div>
          </div>

          <!-- Availability -->
          <div class="flex items-center justify-center gap-2 text-sm mb-3">
            <span :class="['w-2 h-2 rounded-full', getAvailabilityClass(contact)]"></span>
            <span>{{ getAvailabilityText(contact) }}</span>
          </div>

          <!-- Skills -->
          <div class="flex flex-wrap gap-1.5 justify-center">
            <span
              v-for="skill in (contact.skills || []).slice(0, 3)"
              :key="skill.skill_name"
              class="px-2.5 py-1 bg-gray-100 dark:bg-gray-700 rounded-xl text-xs text-gray-500 dark:text-gray-400"
            >
              {{ skill.skill_name }}
            </span>
            <span
              v-if="contact.skills?.length > 3"
              class="px-2.5 py-1 bg-gray-100 dark:bg-gray-700 rounded-xl text-xs text-gray-400 dark:text-gray-500"
            >
              +{{ contact.skills.length - 3 }}
            </span>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="filteredContacts.length === 0"
          class="col-span-full text-center py-12"
        >
          <i class="fa-solid fa-users text-4xl text-gray-300 dark:text-gray-600 mb-3"></i>
          <p class="text-gray-500 dark:text-gray-400">{{ __('No contacts found') }}</p>
          <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">{{ __('Add contacts via the Desk interface or clear filters') }}</p>
        </div>
      </div>
    </div>

    <!-- Create Contact Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50"
      @click.self="closeCreateModal"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <!-- Modal Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Add New Contact') }}</h3>
          <button @click="closeCreateModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-4 space-y-4">
          <!-- Error message -->
          <div v-if="createError" class="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
            {{ createError }}
          </div>

          <!-- Contact Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Name') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="newContact.resource_name"
              type="text"
              :placeholder="__('Full name')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:border-orga-500 focus:outline-none"
            />
          </div>

          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Email') }}</label>
            <input
              v-model="newContact.email"
              type="email"
              placeholder="email@example.com"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:border-orga-500 focus:outline-none"
            />
          </div>

          <!-- Two columns -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Type -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Type') }}</label>
              <select
                v-model="newContact.resource_type"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
              >
                <option value="Employee">{{ __('Employee') }}</option>
                <option value="Contractor">{{ __('Contractor') }}</option>
                <option value="External">{{ __('External') }}</option>
              </select>
            </div>

            <!-- Status -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Status') }}</label>
              <select
                v-model="newContact.status"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
              >
                <option value="Active">{{ __('Active') }}</option>
                <option value="Inactive">{{ __('Inactive') }}</option>
                <option value="On Leave">{{ __('On Leave') }}</option>
              </select>
            </div>
          </div>

          <!-- Designation -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Designation') }}</label>
            <input
              v-model="newContact.designation"
              type="text"
              :placeholder="__('Job title or role')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:border-orga-500 focus:outline-none"
            />
          </div>

          <!-- Capacity -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Weekly Capacity (h)') }}</label>
              <input
                v-model.number="newContact.weekly_capacity"
                type="number"
                min="0"
                max="168"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Daily Hours') }}</label>
              <input
                v-model.number="newContact.availability_hours"
                type="number"
                min="0"
                max="24"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="flex items-center justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="closeCreateModal"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleCreateContact"
            :disabled="isCreating"
            class="px-4 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <i v-if="isCreating" class="fa-solid fa-spinner fa-spin"></i>
            <span>{{ isCreating ? __('Creating...') : __('Create Contact') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
