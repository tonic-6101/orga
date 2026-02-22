<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  CreateMilestoneModal.vue - Modal for creating new milestones in a project
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMilestoneApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import FormField from '@/components/common/FormField.vue'
import type { MilestoneStatus } from '@/types/orga'

interface Props {
  isOpen: boolean
  projectId: string
}

interface MilestoneFormData {
  milestone_name: string
  description: string
  due_date: string | null
  status: MilestoneStatus
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [milestone: { name: string; milestone_name: string }]
}>()

const { createMilestone } = useMilestoneApi()
const { error: showError } = useToast()

// Form state
const formData = ref<MilestoneFormData>({
  milestone_name: '',
  description: '',
  due_date: null,
  status: 'Upcoming'
})

const isSubmitting = ref(false)
const errors = ref<Record<string, string>>({})
const touched = ref<Record<string, boolean>>({})

// Validation
const isValid = computed(() => {
  return formData.value.milestone_name.trim().length > 0
})

// Mark field as touched
function touch(field: string): void {
  touched.value[field] = true
  validateField(field)
}

// Validate single field (real-time)
function validateField(field: string): void {
  if (field === 'milestone_name') {
    if (!formData.value.milestone_name.trim()) {
      errors.value.milestone_name = __('Milestone name is required')
    } else if (formData.value.milestone_name.length > 255) {
      errors.value.milestone_name = __('Name cannot exceed 255 characters')
    } else {
      delete errors.value.milestone_name
    }
  }
}

function validate(): boolean {
  errors.value = {}

  if (!formData.value.milestone_name.trim()) {
    errors.value.milestone_name = __('Milestone name is required')
  }

  if (formData.value.milestone_name.length > 255) {
    errors.value.milestone_name = __('Name cannot exceed 255 characters')
  }

  return Object.keys(errors.value).length === 0
}

// Submit handler
async function handleSubmit() {
  // Mark all fields as touched on submit
  touched.value = { milestone_name: true }

  if (!validate()) return

  isSubmitting.value = true

  try {
    const result = await createMilestone({
      project: props.projectId,
      milestone_name: formData.value.milestone_name,
      description: formData.value.description || undefined,
      due_date: formData.value.due_date || undefined,
      status: formData.value.status
    })

    emit('created', { name: result.name, milestone_name: result.milestone_name })
    resetForm()
    emit('close')
  } catch (e) {
    errors.value.submit = (e as Error).message || __('Failed to create milestone')
    showError(__('Failed to create milestone'), errors.value.submit)
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  formData.value = {
    milestone_name: '',
    description: '',
    due_date: null,
    status: 'Upcoming'
  }
  errors.value = {}
  touched.value = {}
}

function handleClose() {
  resetForm()
  emit('close')
}

// Reset form when modal closes
watch(() => props.isOpen, (open) => {
  if (!open) {
    resetForm()
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
            {{ __('Create New Milestone') }}
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
          <!-- Milestone Name -->
          <FormField
            :label="__('Milestone Name')"
            :required="true"
            :error="errors.milestone_name"
            :touched="touched.milestone_name"
            :max-length="255"
            :current-length="formData.milestone_name.length"
            :show-success="formData.milestone_name.trim().length > 0"
            :hint="__('A key deliverable or checkpoint for the project')"
          >
            <template #default="{ id, hasError, isValid }">
              <input
                :id="id"
                v-model="formData.milestone_name"
                type="text"
                maxlength="255"
                :placeholder="__('Enter milestone name...')"
                @blur="touch('milestone_name')"
                @input="touched.milestone_name && validateField('milestone_name')"
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
            :hint="__('Add details or acceptance criteria for this milestone')"
          >
            <template #default="{ id }">
              <textarea
                :id="id"
                v-model="formData.description"
                rows="3"
                :placeholder="__('Add details about this milestone...')"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-orga-500/20 focus:border-orga-500 transition-colors"
              ></textarea>
            </template>
          </FormField>

          <!-- Two columns: Due Date + Status -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Target Date') }}
              </label>
              <input
                v-model="formData.due_date"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Status') }}
              </label>
              <select
                v-model="formData.status"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="Upcoming">{{ __('Upcoming') }}</option>
                <option value="In Progress">{{ __('In Progress') }}</option>
                <option value="Completed">{{ __('Completed') }}</option>
                <option value="Missed">{{ __('Missed') }}</option>
              </select>
            </div>
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
            {{ isSubmitting ? __('Creating...') : __('Create Milestone') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
