<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ApplyTemplateModal.vue - Apply a project template to a target project
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useTemplateApi, useProjectApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import type { OrgaProjectTemplate, OrgaProject } from '@/types/orga'

interface Props {
  isOpen: boolean
  templateName?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  applied: []
}>()

const { getTemplates, applyTemplate } = useTemplateApi()
const { getProjects } = useProjectApi()
const { success: showSuccess, error: showError } = useToast()

const templates = ref<OrgaProjectTemplate[]>([])
const projects = ref<OrgaProject[]>([])
const selectedTemplate = ref('')
const selectedProject = ref('')
const isApplying = ref(false)
const isLoadingData = ref(false)

const selectedTemplateData = computed(() =>
  templates.value.find(t => t.name === selectedTemplate.value)
)

const canApply = computed(() =>
  selectedTemplate.value && selectedProject.value && !isApplying.value
)

watch(() => props.isOpen, async (open) => {
  if (open) {
    selectedTemplate.value = props.templateName || ''
    selectedProject.value = ''
    isApplying.value = false
    await loadData()
  }
})

async function loadData(): Promise<void> {
  isLoadingData.value = true
  try {
    const [tplResponse, projResponse] = await Promise.all([
      getTemplates({ limit: 100 }),
      getProjects({ status: 'Planning', limit: 100 } as Record<string, unknown>)
    ])
    templates.value = tplResponse.templates || []
    // Also include Active projects
    const activeResponse = await getProjects({ status: 'Active', limit: 100 } as Record<string, unknown>)
    projects.value = [
      ...(projResponse.projects || []),
      ...(activeResponse.projects || [])
    ]
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    isLoadingData.value = false
  }
}

async function handleApply(): Promise<void> {
  if (!canApply.value) return

  isApplying.value = true
  try {
    const result = await applyTemplate(selectedProject.value, selectedTemplate.value)
    showSuccess(
      __('Template applied'),
      __('Created {0} tasks, {1} milestones, and {2} dependencies.', [result.tasks_created, result.milestones_created, result.dependencies_created])
    )
    emit('applied')
  } catch (e) {
    console.error('Failed to apply template:', e)
    showError(__('Apply failed'), (e as Error).message || __('Could not apply the template. Please try again.'))
    isApplying.value = false
  }
}

function handleClose(): void {
  if (!isApplying.value) {
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
            <i class="fa-solid fa-play text-orga-600 dark:text-orga-400 text-lg"></i>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Apply Template') }}</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-0.5">{{ __('Create tasks and milestones from a template') }}</p>
          </div>
          <button
            @click="handleClose"
            :disabled="isApplying"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="p-5 space-y-4">
          <!-- Loading -->
          <div v-if="isLoadingData" class="text-center py-4">
            <i class="fa-solid fa-spinner fa-spin text-orga-500 text-xl"></i>
          </div>

          <template v-else>
            <!-- Template selector -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Template') }} *</label>
              <select
                v-model="selectedTemplate"
                :disabled="isApplying"
                class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 focus:outline-none disabled:opacity-50"
              >
                <option value="">{{ __('Select a template...') }}</option>
                <option v-for="tpl in templates" :key="tpl.name" :value="tpl.name">
                  {{ tpl.template_name }} ({{ tpl.task_count }} tasks)
                </option>
              </select>
            </div>

            <!-- Template preview -->
            <div v-if="selectedTemplateData" class="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 space-y-1">
              <p class="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider m-0">{{ __('Will create:') }}</p>
              <ul class="list-none p-0 m-0 space-y-1">
                <li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <i class="fa-solid fa-list-check text-xs w-4 text-center text-orga-500"></i>
                  {{ selectedTemplateData.task_count }} {{ selectedTemplateData.task_count === 1 ? __('task') : __('tasks') }}
                </li>
                <li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <i class="fa-solid fa-flag text-xs w-4 text-center text-orga-500"></i>
                  {{ selectedTemplateData.milestone_count }} {{ selectedTemplateData.milestone_count === 1 ? __('milestone') : __('milestones') }}
                </li>
                <li v-if="selectedTemplateData.dependency_count" class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <i class="fa-solid fa-link text-xs w-4 text-center text-orga-500"></i>
                  {{ selectedTemplateData.dependency_count }} {{ selectedTemplateData.dependency_count === 1 ? __('dependency') : __('dependencies') }}
                </li>
              </ul>
            </div>

            <!-- Project selector -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Target Project') }} *</label>
              <select
                v-model="selectedProject"
                :disabled="isApplying"
                class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 focus:outline-none disabled:opacity-50"
              >
                <option value="">{{ __('Select a project...') }}</option>
                <option v-for="proj in projects" :key="proj.name" :value="proj.name">
                  {{ proj.project_name }} ({{ proj.status }})
                </option>
              </select>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {{ __("Dates will be relative to the project's start date.") }}
              </p>
            </div>
          </template>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 p-5 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="handleClose"
            :disabled="isApplying"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleApply"
            :disabled="!canApply"
            class="px-4 py-2 text-sm font-medium text-white bg-orga-500 rounded-lg hover:bg-orga-600 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <i v-if="isApplying" class="fa-solid fa-spinner fa-spin"></i>
            <i v-else class="fa-solid fa-play"></i>
            {{ isApplying ? __('Applying...') : __('Apply Template') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
