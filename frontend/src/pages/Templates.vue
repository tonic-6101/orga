<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTemplateApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import ApplyTemplateModal from '@/components/project/ApplyTemplateModal.vue'
import type { OrgaProjectTemplate, TemplateCategory } from '@/types/orga'

const { getTemplates, deleteTemplate, exportTemplate, importTemplate, updateTemplate } = useTemplateApi()
const { success: showSuccess, error: showError } = useToast()

const templates = ref<OrgaProjectTemplate[]>([])
const isLoading = ref(true)
const loadError = ref<string | null>(null)

// Filters
const categoryFilter = ref<TemplateCategory | ''>('')

// Apply modal state
const isApplyModalOpen = ref(false)
const selectedTemplateName = ref<string | undefined>(undefined)

// Edit state
const editingTemplate = ref<string | null>(null)
const editName = ref('')
const editDescription = ref('')
const editCategory = ref<TemplateCategory>('General')
const isSavingEdit = ref(false)

// Import state
const fileInputRef = ref<HTMLInputElement | null>(null)
const isImporting = ref(false)

const categories: TemplateCategory[] = ['General', 'Marketing', 'Engineering', 'Operations', 'Other']

function getCategoryClass(category: string): string {
  const classes: Record<string, string> = {
    'General': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
    'Marketing': 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    'Engineering': 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    'Operations': 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-400',
    'Other': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
  }
  return classes[category] || classes['Other']
}

function formatDate(date: string | null | undefined): string {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadTemplates(): Promise<void> {
  isLoading.value = true
  loadError.value = null
  try {
    const filters: Record<string, string> = {}
    if (categoryFilter.value) filters.category = categoryFilter.value
    const response = await getTemplates(filters)
    templates.value = response.templates || []
  } catch (e) {
    console.error('Failed to load templates:', e)
    loadError.value = (e as Error).message || 'Failed to load templates'
  } finally {
    isLoading.value = false
  }
}

async function handleExport(tpl: OrgaProjectTemplate): Promise<void> {
  try {
    const data = await exportTemplate(tpl.name)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${tpl.template_name.replace(/\s+/g, '_').toLowerCase()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showSuccess(__('Exported'), __('Template "{0}" downloaded as JSON.', [tpl.template_name]))
  } catch (e) {
    console.error('Failed to export template:', e)
    showError(__('Export failed'), (e as Error).message || __('Could not export the template.'))
  }
}

async function handleDelete(tpl: OrgaProjectTemplate): Promise<void> {
  if (!confirm(`Delete template "${tpl.template_name}"? This cannot be undone.`)) return
  try {
    await deleteTemplate(tpl.name)
    showSuccess(__('Deleted'), __('Template "{0}" has been deleted.', [tpl.template_name]))
    await loadTemplates()
  } catch (e) {
    console.error('Failed to delete template:', e)
    showError(__('Delete failed'), (e as Error).message || __('Could not delete the template.'))
  }
}

function handleApply(tpl: OrgaProjectTemplate): void {
  selectedTemplateName.value = tpl.name
  isApplyModalOpen.value = true
}

function startEdit(tpl: OrgaProjectTemplate): void {
  editingTemplate.value = tpl.name
  editName.value = tpl.template_name
  editDescription.value = tpl.description || ''
  editCategory.value = tpl.category
}

function cancelEdit(): void {
  editingTemplate.value = null
}

async function saveEdit(): Promise<void> {
  if (!editingTemplate.value || !editName.value.trim()) return
  isSavingEdit.value = true
  try {
    await updateTemplate(editingTemplate.value, {
      template_name: editName.value.trim(),
      description: editDescription.value.trim(),
      category: editCategory.value,
    } as Partial<OrgaProjectTemplate>)
    showSuccess(__('Updated'), __('Template updated successfully.'))
    editingTemplate.value = null
    await loadTemplates()
  } catch (e) {
    console.error('Failed to update template:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not update the template.'))
  } finally {
    isSavingEdit.value = false
  }
}

function triggerImport(): void {
  fileInputRef.value?.click()
}

async function handleImportFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isImporting.value = true
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    const result = await importTemplate(data)
    showSuccess(__('Imported'), __('Template "{0}" imported with {1} tasks.', [result.template_name, result.task_count]))
    await loadTemplates()
  } catch (e) {
    console.error('Failed to import template:', e)
    showError(__('Import failed'), (e as Error).message || __('Could not import the template. Please check the file format.'))
  } finally {
    isImporting.value = false
    // Reset file input
    if (input) input.value = ''
  }
}

function handleApplied(): void {
  isApplyModalOpen.value = false
  showSuccess(__('Template applied'), __('Tasks, milestones, and dependencies have been created.'))
}

onMounted(loadTemplates)
</script>

<template>
  <div class="p-6 bg-white dark:bg-gray-950 min-h-full">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Templates') }}</h1>
        <span
          v-if="templates.length > 0"
          class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full text-xs font-medium"
        >{{ templates.length }}</span>
      </div>
      <button
        @click="triggerImport"
        :disabled="isImporting"
        class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2 disabled:opacity-50"
      >
        <i v-if="isImporting" class="fa-solid fa-spinner fa-spin"></i>
        <i v-else class="fa-solid fa-file-import"></i>
        {{ __('Import Template') }}
      </button>
      <input
        ref="fileInputRef"
        type="file"
        accept=".json"
        class="hidden"
        @change="handleImportFile"
      />
    </div>

    <!-- Filters -->
    <div class="flex gap-4 mb-6">
      <select
        v-model="categoryFilter"
        @change="loadTemplates"
        class="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      >
        <option value="">{{ __('All Categories') }}</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-500 dark:text-gray-400">{{ __('Loading templates...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-xl"></i>
        <div>
          <h3 class="text-red-800 dark:text-red-300 font-medium">{{ __('Error loading templates') }}</h3>
          <p class="text-red-600 dark:text-red-400 text-sm">{{ loadError }}</p>
        </div>
      </div>
      <button
        @click="loadTemplates"
        class="mt-4 px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60"
      >
        {{ __('Try Again') }}
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="templates.length === 0" class="text-center py-12">
      <i class="fa-solid fa-copy text-5xl text-gray-300 dark:text-gray-600 mb-4"></i>
      <h3 class="text-lg font-medium text-gray-800 dark:text-gray-100 mb-2">{{ __('No templates yet') }}</h3>
      <p class="text-gray-500 dark:text-gray-400 mb-4">{{ __('Save a project as a template, or import one from a JSON file.') }}</p>
      <button
        @click="triggerImport"
        class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600"
      >
        <i class="fa-solid fa-file-import mr-2"></i> {{ __('Import Template') }}
      </button>
    </div>

    <!-- Templates Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="tpl in templates"
        :key="tpl.name"
        class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:shadow-lg dark:hover:shadow-gray-950/50 transition-shadow"
      >
        <!-- Edit mode -->
        <div v-if="editingTemplate === tpl.name" class="space-y-3">
          <input
            v-model="editName"
            type="text"
            class="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
            :placeholder="__('Template name')"
          />
          <textarea
            v-model="editDescription"
            rows="2"
            class="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
            :placeholder="__('Description')"
          ></textarea>
          <select
            v-model="editCategory"
            class="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:border-orga-500 focus:outline-none"
          >
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <div class="flex justify-end gap-2">
            <button
              @click="cancelEdit"
              :disabled="isSavingEdit"
              class="px-3 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >{{ __('Cancel') }}</button>
            <button
              @click="saveEdit"
              :disabled="!editName.trim() || isSavingEdit"
              class="px-3 py-1 text-xs bg-orga-500 text-white rounded hover:bg-orga-600 disabled:opacity-50"
            >
              <i v-if="isSavingEdit" class="fa-solid fa-spinner fa-spin mr-1"></i>
              {{ __('Save') }}
            </button>
          </div>
        </div>

        <!-- View mode -->
        <template v-else>
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-base font-semibold text-gray-800 dark:text-gray-100 m-0 truncate flex-1 mr-2">
              {{ tpl.template_name }}
            </h3>
            <span :class="['px-2 py-1 rounded-xl text-xs font-medium whitespace-nowrap', getCategoryClass(tpl.category)]">
              {{ tpl.category }}
            </span>
          </div>

          <p v-if="tpl.description" class="text-sm text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
            {{ tpl.description }}
          </p>

          <!-- Counts -->
          <div class="flex gap-4 mb-3 text-sm text-gray-600 dark:text-gray-300">
            <span class="flex items-center gap-1">
              <i class="fa-solid fa-list-check text-xs text-gray-400"></i>
              {{ tpl.task_count === 1 ? __('1 task') : __('{0} tasks', [tpl.task_count]) }}
            </span>
            <span class="flex items-center gap-1">
              <i class="fa-solid fa-flag text-xs text-gray-400"></i>
              {{ tpl.milestone_count === 1 ? __('1 milestone') : __('{0} milestones', [tpl.milestone_count]) }}
            </span>
          </div>

          <div v-if="tpl.dependency_count" class="text-xs text-gray-500 dark:text-gray-400 mb-3">
            <i class="fa-solid fa-link text-xs mr-1"></i>
            {{ tpl.dependency_count === 1 ? __('1 dependency') : __('{0} dependencies', [tpl.dependency_count]) }}
          </div>

          <!-- Source & Date -->
          <div class="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-4">
            <span v-if="tpl.source_project_name">
              {{ __('From: {0}', [tpl.source_project_name]) }}
            </span>
            <span v-else>&nbsp;</span>
            <span>{{ formatDate(tpl.modified) }}</span>
          </div>

          <!-- Actions -->
          <div class="flex justify-between items-center pt-3 border-t border-gray-200 dark:border-gray-700">
            <button
              @click="handleApply(tpl)"
              class="px-3 py-1.5 text-xs font-medium bg-orga-500 text-white rounded hover:bg-orga-600 transition-colors flex items-center gap-1"
            >
              <i class="fa-solid fa-play text-[10px]"></i> {{ __('Apply') }}
            </button>
            <div class="flex gap-1">
              <button
                @click="handleExport(tpl)"
                class="p-1.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                :title="__('Export JSON')"
              >
                <i class="fa-solid fa-download text-sm"></i>
              </button>
              <button
                @click="startEdit(tpl)"
                class="p-1.5 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                :title="__('Edit')"
              >
                <i class="fa-solid fa-pen text-sm"></i>
              </button>
              <button
                @click="handleDelete(tpl)"
                class="p-1.5 text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                :title="__('Delete')"
              >
                <i class="fa-solid fa-trash text-sm"></i>
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Apply Template Modal -->
    <ApplyTemplateModal
      :is-open="isApplyModalOpen"
      :template-name="selectedTemplateName"
      @close="isApplyModalOpen = false"
      @applied="handleApplied"
    />
  </div>
</template>
