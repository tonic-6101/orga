<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  CreateTaskModal.vue - Modal for creating new tasks in a project
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTaskApi, useUserApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import FormField from '@/components/common/FormField.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { MentionUser, TaskType } from '@/types/orga'

interface Props {
  isOpen: boolean
  projectId: string
  initialStatus?: string
  autoTrailDefault?: boolean
}

interface TaskFormData {
  subject: string
  description: string
  assigned_to: string | null
  task_type: TaskType
  priority: 'Low' | 'Medium' | 'High' | 'Urgent'
  status: string
  start_date: string | null
  due_date: string | null
  estimated_cost: number | null
  auto_trail_start: boolean
}

const props = withDefaults(defineProps<Props>(), {
  initialStatus: 'Open',
  autoTrailDefault: false
})

const emit = defineEmits<{
  close: []
  created: [task: { name: string; subject: string }]
}>()

const { createTask } = useTaskApi()
const { getAssignableUsers } = useUserApi()
const { success: showSuccess, error: showError } = useToast()

// Form state
const formData = ref<TaskFormData>({
  subject: '',
  description: '',
  assigned_to: null,
  task_type: '',
  priority: 'Medium',
  status: props.initialStatus,
  start_date: null,
  due_date: null,
  estimated_cost: null,
  auto_trail_start: false
})

const isSubmitting = ref(false)
const errors = ref<Record<string, string>>({})
const touched = ref<Record<string, boolean>>({})
const users = ref<MentionUser[]>([])
const isAssignDropdownOpen = ref(false)

// Selected user for avatar display in assign dropdown
const selectedUser = computed(() => {
  if (!formData.value.assigned_to) return null
  return users.value.find(u => u.name === formData.value.assigned_to) || null
})

// Mark field as touched
function touch(field: string): void {
  touched.value[field] = true
  validateField(field)
}

// Validate single field (real-time)
function validateField(field: string): void {
  if (field === 'subject') {
    if (!formData.value.subject.trim()) {
      errors.value.subject = __('Task subject is required')
    } else if (formData.value.subject.length > 255) {
      errors.value.subject = __('Subject cannot exceed 255 characters')
    } else {
      delete errors.value.subject
    }
  }

  if (field === 'dates' || field === 'start_date' || field === 'due_date') {
    if (formData.value.start_date && formData.value.due_date) {
      if (new Date(formData.value.due_date) < new Date(formData.value.start_date)) {
        errors.value.dates = __('End date cannot be before start date')
      } else {
        delete errors.value.dates
      }
    } else {
      delete errors.value.dates
    }
  }
}

// Load users for assignment dropdown (meta-driven: reads field def to determine target DocType)
async function loadUsers() {
  try {
    const result = await getAssignableUsers({ limit: 100 })
    users.value = Array.isArray(result) ? result : []
  } catch (e) {
    console.error('Failed to load assignable users:', e)
  }
}

// Validation
const isValid = computed(() => {
  return formData.value.subject.trim().length > 0
})

function validate(): boolean {
  errors.value = {}

  if (!formData.value.subject.trim()) {
    errors.value.subject = __('Task subject is required')
  }

  if (formData.value.subject.length > 255) {
    errors.value.subject = __('Subject cannot exceed 255 characters')
  }

  if (formData.value.start_date && formData.value.due_date) {
    if (new Date(formData.value.due_date) < new Date(formData.value.start_date)) {
      errors.value.dates = __('End date cannot be before start date')
    }
  }

  return Object.keys(errors.value).length === 0
}

// Submit handler
async function handleSubmit() {
  // Mark all fields as touched on submit
  touched.value = { subject: true }

  if (!validate()) return

  isSubmitting.value = true

  try {
    const result = await createTask({
      project: props.projectId,
      subject: formData.value.subject,
      description: formData.value.description || undefined,
      assigned_to: formData.value.assigned_to || undefined,
      task_type: formData.value.task_type || undefined,
      priority: formData.value.priority,
      status: formData.value.status,
      start_date: formData.value.start_date || undefined,
      due_date: formData.value.due_date || undefined,
      estimated_cost: formData.value.estimated_cost || undefined,
      auto_trail_start: formData.value.auto_trail_start ? 1 : undefined
    })

    emit('created', { name: result.name, subject: formData.value.subject })
    resetForm()
    emit('close')
  } catch (e) {
    errors.value.submit = (e as Error).message || __('Failed to create task')
    showError(__('Failed to create task'), errors.value.submit)
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  formData.value = {
    subject: '',
    description: '',
    assigned_to: null,
    task_type: '',
    priority: 'Medium',
    status: props.initialStatus,
    start_date: null,
    due_date: null,
    estimated_cost: null,
    auto_trail_start: false
  }
  errors.value = {}
  touched.value = {}
  isAssignDropdownOpen.value = false
}

function handleClose() {
  resetForm()
  emit('close')
}

// Load users when modal opens
watch(() => props.isOpen, (open) => {
  if (open) {
    loadUsers()
    // Reset status to initialStatus when opening
    formData.value.status = props.initialStatus
    // Apply project's auto-trail default
    formData.value.auto_trail_start = props.autoTrailDefault
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="handleClose"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
            {{ __('Create New Task') }}
          </h2>
          <button
            @click="handleClose"
            class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
          >
            <i class="fa-solid fa-xmark text-xl"></i>
          </button>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="p-4 space-y-4">
          <!-- Subject -->
          <FormField
            :label="__('Task Subject')"
            :required="true"
            :error="errors.subject"
            :touched="touched.subject"
            :max-length="255"
            :current-length="formData.subject.length"
            :show-success="formData.subject.trim().length > 0"
            :hint="__('A clear, actionable title for the task')"
          >
            <template #default="{ id, hasError, isValid }">
              <input
                :id="id"
                v-model="formData.subject"
                type="text"
                maxlength="255"
                :placeholder="__('Enter task title...')"
                @blur="touch('subject')"
                @input="touched.subject && validateField('subject')"
                :class="[
                  'w-full px-3 py-2 border rounded-lg text-sm transition-colors',
                  'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100',
                  'focus:outline-none focus:ring-2',
                  hasError
                    ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500'
                    : isValid
                    ? 'border-green-500 focus:ring-green-500/20 focus:border-green-500'
                    : 'border-gray-300 dark:border-gray-600 focus:ring-orga-500/20 focus:border-orga-500'
                ]"
              />
            </template>
          </FormField>

          <!-- Description -->
          <FormField
            :label="__('Description')"
            :hint="__('Add details, context, or acceptance criteria')"
          >
            <template #default="{ id }">
              <textarea
                :id="id"
                v-model="formData.description"
                rows="3"
                :placeholder="__('Add details about this task...')"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-orga-500/20 focus:border-orga-500 transition-colors"
              ></textarea>
            </template>
          </FormField>

          <!-- Three columns: Assign To + Task Type + Priority -->
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Assign To') }}
              </label>
              <div class="relative">
                <button
                  type="button"
                  @click="isAssignDropdownOpen = !isAssignDropdownOpen"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 flex items-center gap-2 text-left"
                >
                  <template v-if="selectedUser">
                    <UserAvatar :name="selectedUser.full_name" :image="selectedUser.user_image" size="xs" color="orga" class="!w-5 !h-5 !text-[10px]" />
                    <span class="truncate flex-1">{{ selectedUser.full_name || selectedUser.name }}</span>
                  </template>
                  <span v-else class="text-gray-400 dark:text-gray-500 flex-1">{{ __('Unassigned') }}</span>
                  <i class="fa-solid fa-chevron-down text-[10px] text-gray-400 shrink-0"></i>
                </button>
                <div
                  v-if="isAssignDropdownOpen"
                  class="absolute left-0 top-full mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 py-1 max-h-48 overflow-y-auto"
                >
                  <button
                    type="button"
                    @click="formData.assigned_to = null; isAssignDropdownOpen = false"
                    class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                  >
                    {{ __('Unassigned') }}
                  </button>
                  <button
                    v-for="user in users"
                    :key="user.name"
                    type="button"
                    @click="formData.assigned_to = user.name; isAssignDropdownOpen = false"
                    :class="[
                      'w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors text-left',
                      formData.assigned_to === user.name
                        ? 'bg-orga-50 dark:bg-orga-900/20 text-orga-700 dark:text-orga-300'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    ]"
                  >
                    <UserAvatar :name="user.full_name" :image="user.user_image" size="xs" color="orga" class="!w-5 !h-5 !text-[10px]" />
                    <span class="truncate">{{ user.full_name || user.name }}</span>
                  </button>
                </div>
                <div
                  v-if="isAssignDropdownOpen"
                  class="fixed inset-0 z-40"
                  @click="isAssignDropdownOpen = false"
                ></div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Task Type') }}
              </label>
              <select
                v-model="formData.task_type"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="">{{ __('None') }}</option>
                <option value="Task">{{ __('Task') }}</option>
                <option value="Bug">{{ __('Bug') }}</option>
                <option value="Feature">{{ __('Feature') }}</option>
                <option value="Research">{{ __('Research') }}</option>
                <option value="Meeting">{{ __('Meeting') }}</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Priority') }}
              </label>
              <select
                v-model="formData.priority"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="Low">{{ __('Low') }}</option>
                <option value="Medium">{{ __('Medium') }}</option>
                <option value="High">{{ __('High') }}</option>
                <option value="Urgent">{{ __('Urgent') }}</option>
              </select>
            </div>
          </div>

          <!-- Status -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Status') }}
            </label>
            <select
              v-model="formData.status"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
            >
              <option value="Open">{{ __('Open') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Review">{{ __('Review') }}</option>
              <option value="Completed">{{ __('Completed') }}</option>
            </select>
          </div>

          <!-- Two columns: Start Date + End Date (required for Gantt chart) -->
          <div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {{ __('Start Date') }}
                </label>
                <input
                  v-model="formData.start_date"
                  type="date"
                  @change="validateField('dates')"
                  :class="[
                    'w-full px-3 py-2 border rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100',
                    errors.dates ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  ]"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ __('When work begins') }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {{ __('End Date') }}
                </label>
                <input
                  v-model="formData.due_date"
                  type="date"
                  @change="validateField('dates')"
                  :class="[
                    'w-full px-3 py-2 border rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100',
                    errors.dates ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                  ]"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ __('When work is due') }}</p>
              </div>
            </div>
            <p v-if="errors.dates" class="text-xs text-red-500 mt-1">{{ errors.dates }}</p>
            <p v-else class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              <i class="fa-solid fa-circle-info mr-1"></i>
              {{ __('Both dates are needed to display task as a bar in Gantt chart') }}
            </p>
          </div>

          <!-- Auto-Trail Start -->
          <label class="flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition-colors"
            :class="formData.auto_trail_start
              ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
              : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700'"
          >
            <input
              type="checkbox"
              v-model="formData.auto_trail_start"
              class="w-3.5 h-3.5 rounded accent-blue-500 cursor-pointer flex-shrink-0"
            />
            <span class="text-xs text-gray-600 dark:text-gray-400 leading-tight">
              {{ __('Auto-Trail Start') }}
              <span class="text-gray-400 dark:text-gray-500"> — {{ __('trails to today while Open at 0%') }}</span>
            </span>
          </label>

          <!-- Estimated Cost -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Estimated Cost (€)') }}
            </label>
            <input
              v-model.number="formData.estimated_cost"
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-orga-500/20 focus:border-orga-500 transition-colors"
            />
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ __('Planned budget for this task') }}</p>
          </div>

          <!-- Error message -->
          <div v-if="errors.submit" class="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-sm text-red-600 dark:text-red-400">{{ errors.submit }}</p>
          </div>
        </form>

        <!-- Footer -->
        <div class="flex justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <button
            type="button"
            @click="handleClose"
            :disabled="isSubmitting"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {{ __('Cancel') }}
          </button>
          <button
            type="submit"
            @click="handleSubmit"
            :disabled="isSubmitting || !isValid"
            class="px-4 py-2 text-sm font-medium text-white bg-orga-500 rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <i v-if="isSubmitting" class="fa-solid fa-spinner fa-spin"></i>
            {{ isSubmitting ? __('Creating...') : __('Create Task') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
