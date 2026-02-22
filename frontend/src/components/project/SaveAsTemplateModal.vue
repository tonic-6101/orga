<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  SaveAsTemplateModal.vue - Save project structure as a reusable template
-->
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useTemplateApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import type { TemplateCategory } from '@/types/orga'

interface Props {
  isOpen: boolean
  projectName: string
  projectLabel: string
  taskCount: number
  milestoneCount: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  saved: [name: string]
}>()

const { createFromProject } = useTemplateApi()
const { success: showSuccess, error: showError } = useToast()

const templateName = ref('')
const description = ref('')
const category = ref<TemplateCategory>('General')
const isSaving = ref(false)
const nameInputRef = ref<HTMLInputElement | null>(null)

const categories: TemplateCategory[] = ['General', 'Marketing', 'Engineering', 'Operations', 'Other']

watch(() => props.isOpen, (open) => {
  if (open) {
    templateName.value = `${props.projectLabel} Template`
    description.value = ''
    category.value = 'General'
    isSaving.value = false
    nextTick(() => nameInputRef.value?.focus())
  }
})

async function handleSave(): Promise<void> {
  if (!templateName.value.trim() || isSaving.value) return

  isSaving.value = true
  try {
    const result = await createFromProject(
      props.projectName,
      templateName.value.trim(),
      description.value.trim() || undefined,
      category.value
    )
    showSuccess(
      __('Template saved'),
      __('"{0}" created with {1} tasks and {2} milestones.', [templateName.value, result.task_count, result.milestone_count])
    )
    emit('saved', result.name)
    emit('close')
  } catch (e) {
    console.error('Failed to save template:', e)
    showError(__('Save failed'), (e as Error).message || __('Could not save the template. Please try again.'))
    isSaving.value = false
  }
}

function handleClose(): void {
  if (!isSaving.value) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/60"
        @click="handleClose"
      ></div>

      <!-- Modal -->
      <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-gray-700">
        <!-- Header -->
        <div class="flex items-center gap-3 p-5 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div class="w-10 h-10 rounded-full bg-orga-100 dark:bg-orga-900/50 flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-copy text-orga-600 dark:text-orga-400 text-lg"></i>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Save as Template') }}</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-0.5">{{ __('Capture project structure for reuse') }}</p>
          </div>
          <button
            @click="handleClose"
            :disabled="isSaving"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- Body -->
        <form @submit.prevent="handleSave" class="p-5 space-y-4">
          <!-- Preview -->
          <div class="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 space-y-1.5">
            <p class="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider m-0">{{ __('Will capture:') }}</p>
            <ul class="list-none p-0 m-0 space-y-1">
              <li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <i class="fa-solid fa-list-check text-xs w-4 text-center text-orga-500"></i>
                {{ taskCount }} {{ taskCount === 1 ? __('task') : __('tasks') }} {{ __('with checklist items') }}
              </li>
              <li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <i class="fa-solid fa-flag text-xs w-4 text-center text-orga-500"></i>
                {{ milestoneCount }} {{ milestoneCount === 1 ? __('milestone') : __('milestones') }}
              </li>
              <li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <i class="fa-solid fa-link text-xs w-4 text-center text-orga-500"></i>
                {{ __('All task dependencies & relative dates') }}
              </li>
            </ul>
          </div>

          <!-- Template Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Template Name') }} *</label>
            <input
              ref="nameInputRef"
              v-model="templateName"
              type="text"
              required
              :disabled="isSaving"
              class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 border-gray-300 dark:border-gray-600 focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 focus:outline-none disabled:opacity-50"
              :placeholder="__('Enter template name')"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Description') }}</label>
            <textarea
              v-model="description"
              rows="2"
              :disabled="isSaving"
              class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 border-gray-300 dark:border-gray-600 focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 focus:outline-none disabled:opacity-50"
              :placeholder="__('Brief description of this template')"
            ></textarea>
          </div>

          <!-- Category -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Category') }}</label>
            <select
              v-model="category"
              :disabled="isSaving"
              class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 focus:outline-none disabled:opacity-50"
            >
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              @click="handleClose"
              :disabled="isSaving"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {{ __('Cancel') }}
            </button>
            <button
              type="submit"
              :disabled="!templateName.trim() || isSaving"
              class="px-4 py-2 text-sm font-medium text-white bg-orga-500 rounded-lg hover:bg-orga-600 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <i v-if="isSaving" class="fa-solid fa-spinner fa-spin"></i>
              <i v-else class="fa-solid fa-copy"></i>
              {{ isSaving ? __('Saving...') : __('Save Template') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
