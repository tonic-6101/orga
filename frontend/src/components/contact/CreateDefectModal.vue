<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  CreateDefectModal.vue - Modal for creating new defects linked to a contact
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useDefectApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import FormField from '@/components/common/FormField.vue'
import type { DefectType, DefectSeverity } from '@/types/orga'

interface Props {
  isOpen: boolean
  contactName: string
  projectName?: string
}

interface DefectFormData {
  title: string
  defect_type: DefectType
  severity: DefectSeverity
  project: string
  task: string
  cost_estimate: string
  description: string
  reported_date: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [defect: { name: string; title: string }]
}>()

const { createDefect } = useDefectApi()
const { error: showError } = useToast()

const today = new Date().toISOString().split('T')[0]

const formData = ref<DefectFormData>({
  title: '',
  defect_type: 'Workmanship',
  severity: 'Medium',
  project: props.projectName || '',
  task: '',
  cost_estimate: '',
  description: '',
  reported_date: today
})

const isSubmitting = ref(false)
const errors = ref<Record<string, string>>({})
const touched = ref<Record<string, boolean>>({})

const isValid = computed(() => {
  return formData.value.title.trim().length > 0
})

function touch(field: string): void {
  touched.value[field] = true
  validateField(field)
}

function validateField(field: string): void {
  if (field === 'title') {
    if (!formData.value.title.trim()) {
      errors.value.title = __('Title is required')
    } else if (formData.value.title.length > 255) {
      errors.value.title = __('Title cannot exceed 255 characters')
    } else {
      delete errors.value.title
    }
  }
  if (field === 'cost_estimate') {
    const val = formData.value.cost_estimate
    if (val && (isNaN(Number(val)) || Number(val) < 0)) {
      errors.value.cost_estimate = __('Must be a positive number')
    } else {
      delete errors.value.cost_estimate
    }
  }
}

function validate(): boolean {
  errors.value = {}

  if (!formData.value.title.trim()) {
    errors.value.title = __('Title is required')
  }

  const cost = formData.value.cost_estimate
  if (cost && (isNaN(Number(cost)) || Number(cost) < 0)) {
    errors.value.cost_estimate = __('Must be a positive number')
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  touched.value = { title: true, cost_estimate: true }

  if (!validate()) return

  isSubmitting.value = true

  try {
    const data: Record<string, unknown> = {
      title: formData.value.title,
      contact: props.contactName,
      defect_type: formData.value.defect_type,
      severity: formData.value.severity,
      reported_date: formData.value.reported_date
    }

    if (formData.value.project) data.project = formData.value.project
    if (formData.value.task) data.task = formData.value.task
    if (formData.value.cost_estimate) data.cost_estimate = Number(formData.value.cost_estimate)
    if (formData.value.description) data.description = formData.value.description

    const result = await createDefect(data)

    emit('created', { name: result.name, title: result.title })
    resetForm()
    emit('close')
  } catch (e) {
    errors.value.submit = (e as Error).message || __('Failed to create defect')
    showError(__('Failed to create defect'), errors.value.submit)
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  formData.value = {
    title: '',
    defect_type: 'Workmanship',
    severity: 'Medium',
    project: props.projectName || '',
    task: '',
    cost_estimate: '',
    description: '',
    reported_date: today
  }
  errors.value = {}
  touched.value = {}
}

function handleClose() {
  resetForm()
  emit('close')
}

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
            {{ __('Report Defect') }}
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
          <!-- Title -->
          <FormField
            :label="__('Title')"
            :required="true"
            :error="errors.title"
            :touched="touched.title"
            :max-length="255"
            :current-length="formData.title.length"
            :show-success="formData.title.trim().length > 0"
            :hint="__('Brief description of the defect or damage')"
          >
            <template #default="{ id, hasError, isValid: fieldValid }">
              <input
                :id="id"
                v-model="formData.title"
                type="text"
                maxlength="255"
                :placeholder="__('e.g. Cracked wall finish in bathroom...')"
                @blur="touch('title')"
                @input="touched.title && validateField('title')"
                :class="[
                  'w-full px-3 py-2 border rounded-lg text-sm transition-colors',
                  'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100',
                  'focus:outline-none focus:ring-2',
                  hasError
                    ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500'
                    : fieldValid
                    ? 'border-green-500 focus:ring-green-500/20 focus:border-green-500'
                    : 'border-gray-300 dark:border-gray-600 focus:ring-orga-500/20 focus:border-orga-500'
                ]"
              />
            </template>
          </FormField>

          <!-- Two columns: Type + Severity -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Defect Type') }}
              </label>
              <select
                v-model="formData.defect_type"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="Workmanship">{{ __('Workmanship') }}</option>
                <option value="Material">{{ __('Material') }}</option>
                <option value="Safety">{{ __('Safety') }}</option>
                <option value="Compliance">{{ __('Compliance') }}</option>
                <option value="Other">{{ __('Other') }}</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Severity') }}
              </label>
              <select
                v-model="formData.severity"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              >
                <option value="Low">{{ __('Low') }}</option>
                <option value="Medium">{{ __('Medium') }}</option>
                <option value="High">{{ __('High') }}</option>
                <option value="Critical">{{ __('Critical') }}</option>
              </select>
            </div>
          </div>

          <!-- Two columns: Project + Estimated Cost -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {{ __('Project') }}
              </label>
              <input
                v-model="formData.project"
                type="text"
                :placeholder="__('Project code (e.g. ORG-2026-0001)')"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
              />
            </div>

            <FormField
              :label="__('Estimated Cost')"
              :error="errors.cost_estimate"
              :touched="touched.cost_estimate"
            >
              <template #default="{ id, hasError }">
                <input
                  :id="id"
                  v-model="formData.cost_estimate"
                  type="text"
                  inputmode="decimal"
                  placeholder="0.00"
                  @blur="touch('cost_estimate')"
                  @input="touched.cost_estimate && validateField('cost_estimate')"
                  :class="[
                    'w-full px-3 py-2 border rounded-lg text-sm transition-colors',
                    'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100',
                    'focus:outline-none focus:ring-2',
                    hasError
                      ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-orga-500/20 focus:border-orga-500'
                  ]"
                />
              </template>
            </FormField>
          </div>

          <!-- Reported Date -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Reported Date') }}
            </label>
            <input
              v-model="formData.reported_date"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100"
            />
          </div>

          <!-- Description -->
          <FormField
            :label="__('Description')"
            :hint="__('Detailed description of the defect, location, and impact')"
          >
            <template #default="{ id }">
              <textarea
                :id="id"
                v-model="formData.description"
                rows="3"
                :placeholder="__('Describe the defect in detail...')"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-orga-500/20 focus:border-orga-500 transition-colors"
              ></textarea>
            </template>
          </FormField>

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
            {{ isSubmitting ? __('Creating...') : __('Report Defect') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
