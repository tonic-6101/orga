<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useProjectApi, useTemplateApi } from '@/composables/useApi'
import { useCurrency } from '@/composables/useCurrency'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaProject, OrgaProjectTemplate, ProjectStatus, ProjectType } from '@/types/orga'

const { getProjects, createProject, loading, error } = useProjectApi()
const { getTemplates: fetchTemplates, applyTemplate } = useTemplateApi()
const { currencySymbol } = useCurrency()

// New project form data structure
interface NewProjectForm {
  project_name: string
  description: string
  project_type: ProjectType
  start_date: string
  end_date: string
  project_manager: string
  budget?: number | null
}

// Data refs
const projects = ref<OrgaProject[]>([])
const totalProjects = ref<number>(0)
const isLoading = ref<boolean>(true)
const isLoadingMore = ref<boolean>(false)
const loadError = ref<string | null>(null)
const showNewProjectModal = ref<boolean>(false)

// Pagination
const perPage = ref<number>(20)
const perPageOptions = [20, 50, 100]

// Sorting
const sortBy = ref<string>('modified desc')
const sortOptions = [
  { value: 'modified desc', label: __('Last Updated') },
  { value: 'creation desc', label: __('Newest First') },
  { value: 'creation asc', label: __('Oldest First') },
  { value: 'project_name asc', label: __('Name (A-Z)') },
  { value: 'project_name desc', label: __('Name (Z-A)') },
  { value: 'start_date asc', label: __('Start Date (Earliest)') },
  { value: 'end_date asc', label: __('Due Date (Earliest)') },
  { value: 'progress desc', label: __('Progress (High-Low)') },
  { value: 'progress asc', label: __('Progress (Low-High)') },
  { value: 'status asc', label: __('Status') },
]

// Filters
const statusFilter = ref<ProjectStatus | ''>('')
const typeFilter = ref<ProjectType | ''>('')

// Computed
const hasMore = computed(() => projects.value.length < totalProjects.value)

// New project form
const newProject = ref<NewProjectForm>({
  project_name: '',
  description: '',
  project_type: 'Internal',
  start_date: '',
  end_date: '',
  project_manager: '',
  budget: null
})
const isCreating = ref<boolean>(false)
const createError = ref<string | null>(null)

// Template selection for new project
const availableTemplates = ref<OrgaProjectTemplate[]>([])
const selectedTemplate = ref<string>('')

// Status colors
function getStatusClass(status: string): string {
  const classes: Record<string, string> = {
    'Planning': 'bg-blue-100 text-blue-600',
    'Active': 'bg-green-100 text-green-600',
    'On Hold': 'bg-orange-100 text-orange-600',
    'Completed': 'bg-gray-100 text-gray-600',
    'Cancelled': 'bg-red-100 text-red-600'
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

// Format date
function formatDate(date: string | null | undefined): string {
  if (!date) return __('TBD')
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Get initials from name
function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Build filter params
function buildFilters(offset: number = 0): Record<string, unknown> {
  const filters: Record<string, unknown> = {
    limit: perPage.value,
    offset,
    order_by: sortBy.value
  }
  if (statusFilter.value) filters.status = statusFilter.value
  if (typeFilter.value) filters.project_type = typeFilter.value
  return filters
}

// Load projects (initial / reset)
async function loadProjects(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const response = await getProjects(buildFilters(0))
    projects.value = response.projects || []
    totalProjects.value = response.total || projects.value.length
  } catch (e) {
    console.error('Failed to load projects:', e)
    loadError.value = (e as Error).message || __('Failed to load projects')
  } finally {
    isLoading.value = false
  }
}

// Load more projects (append)
async function loadMore(): Promise<void> {
  if (isLoadingMore.value || !hasMore.value) return
  isLoadingMore.value = true

  try {
    const response = await getProjects(buildFilters(projects.value.length))
    projects.value = [...projects.value, ...(response.projects || [])]
    totalProjects.value = response.total || totalProjects.value
  } catch (e) {
    console.error('Failed to load more projects:', e)
  } finally {
    isLoadingMore.value = false
  }
}

// Handle per-page change
function handlePerPageChange(): void {
  loadProjects()
}

// Load available templates for the create modal
async function loadAvailableTemplates(): Promise<void> {
  try {
    const response = await fetchTemplates({ limit: 100 })
    availableTemplates.value = response.templates || []
  } catch (e) {
    console.error('Failed to load templates:', e)
  }
}

// Handle new project
async function handleCreateProject(): Promise<void> {
  isCreating.value = true
  createError.value = null

  try {
    // Get current user as project manager if not set
    if (!newProject.value.project_manager) {
      const frappeWindow = window as Window & { frappe?: { session?: { user?: string } } }
      newProject.value.project_manager = frappeWindow.frappe?.session?.user || 'Administrator'
    }

    const result = await createProject(newProject.value)

    // Apply template if one was selected
    if (selectedTemplate.value && result?.name) {
      try {
        await applyTemplate(result.name, selectedTemplate.value)
      } catch (e) {
        console.error('Failed to apply template:', e)
        // Project was created but template failed - don't block
      }
    }

    showNewProjectModal.value = false

    // Reset form
    newProject.value = {
      project_name: '',
      description: '',
      project_type: 'Internal',
      start_date: '',
      end_date: '',
      project_manager: '',
      budget: null
    }
    selectedTemplate.value = ''

    // Reload projects
    await loadProjects()
  } catch (e) {
    console.error('Failed to create project:', e)
    createError.value = (e as Error).message || __('Failed to create project')
  } finally {
    isCreating.value = false
  }
}

// Watch filters — reset to first page
function applyFilters(): void {
  loadProjects()
}

onMounted(() => {
  loadProjects()
  loadAvailableTemplates()
})
</script>

<template>
  <div class="p-6 bg-gray-50 dark:bg-gray-900 min-h-full">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Projects') }}</h1>
        <span v-if="!isLoading && totalProjects > 0" class="px-2 py-0.5 text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
          {{ totalProjects }}
        </span>
      </div>
      <button
        @click="showNewProjectModal = true"
        class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 flex items-center gap-2"
      >
        <i class="fa-solid fa-plus"></i> {{ __('New Project') }}
      </button>
    </div>

    <!-- Filters -->
    <div class="flex items-center gap-4 mb-6">
      <select
        v-model="statusFilter"
        @change="applyFilters"
        class="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
      >
        <option value="">{{ __('All Statuses') }}</option>
        <option value="Planning">{{ __('Planning') }}</option>
        <option value="Active">{{ __('Active') }}</option>
        <option value="On Hold">{{ __('On Hold') }}</option>
        <option value="Completed">{{ __('Completed') }}</option>
        <option value="Cancelled">{{ __('Cancelled') }}</option>
      </select>

      <select
        v-model="typeFilter"
        @change="applyFilters"
        class="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
      >
        <option value="">{{ __('All Types') }}</option>
        <option value="Internal">{{ __('Internal') }}</option>
        <option value="Client">{{ __('Client') }}</option>
        <option value="Mixed">{{ __('Mixed') }}</option>
      </select>

      <!-- Sort -->
      <div class="flex items-center gap-2">
        <i class="fa-solid fa-arrow-down-wide-short text-xs text-gray-400 dark:text-gray-500"></i>
        <select
          v-model="sortBy"
          @change="applyFilters"
          class="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <!-- Per Page selector -->
      <div class="ml-auto flex items-center gap-2">
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Show') }}</span>
        <select
          v-model.number="perPage"
          @change="handlePerPageChange"
          class="px-2 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
        >
          <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
        </select>
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('per page') }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-600 dark:text-gray-400">{{ __('Loading projects...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-xl"></i>
        <div>
          <h3 class="text-red-800 font-medium">{{ __('Error loading projects') }}</h3>
          <p class="text-red-600 text-sm">{{ loadError }}</p>
        </div>
      </div>
      <button
        @click="loadProjects"
        class="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
      >
        {{ __('Try Again') }}
      </button>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else-if="projects.length === 0"
      icon="fa-folder-open"
      :title="__('No projects found')"
      :description="__('Create your first project to get started.')"
      :action-label="__('New Project')"
      @action="showNewProjectModal = true"
    />

    <!-- Projects Grid + Load More -->
    <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <router-link
          v-for="project in projects"
          :key="project.name"
          :to="`/orga/projects/${project.name}`"
          class="project-card bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:shadow-lg transition-shadow no-underline"
        >
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-base font-semibold text-gray-800 dark:text-gray-100 m-0 truncate flex-1 mr-2">
              {{ project.project_name }}
            </h3>
            <StatusBadge :status="project.status" type="project" size="sm" />
          </div>

          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed line-clamp-2">
            {{ project.project_code }} · {{ project.project_type }}
          </p>

          <!-- Progress -->
          <div class="mb-4">
            <div class="h-1.5 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden">
              <div
                class="h-full bg-orga-500 rounded transition-all"
                :style="{ width: `${project.progress || 0}%` }"
              ></div>
            </div>
            <div class="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
              <span>{{ __('{0} / {1} tasks', [project.completed_tasks || 0, project.task_count || 0]) }}</span>
              <span>{{ Math.round(project.progress || 0) }}%</span>
            </div>
          </div>

          <!-- Meta -->
          <div class="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700">
            <div class="flex items-center">
              <div
                v-if="project.project_manager_name"
                class="w-7 h-7 rounded-full bg-orga-500 text-white text-[10px] flex items-center justify-center font-semibold"
                :title="project.project_manager_name"
              >
                {{ getInitials(project.project_manager_name) }}
              </div>
            </div>
            <span class="text-xs text-gray-600 dark:text-gray-400">{{ __('Due:') }} {{ formatDate(project.end_date) }}</span>
          </div>
        </router-link>
      </div>

      <!-- Pagination footer -->
      <div class="mt-6 flex items-center justify-between">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ __('Showing {0} of {1} projects', [projects.length, totalProjects]) }}
        </p>
        <button
          v-if="hasMore"
          @click="loadMore"
          :disabled="isLoadingMore"
          class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors text-sm flex items-center gap-2"
        >
          <i v-if="isLoadingMore" class="fa-solid fa-spinner fa-spin"></i>
          <template v-else>
            <i class="fa-solid fa-arrow-down"></i>
            {{ __('Load More') }}
          </template>
        </button>
      </div>
    </template>

    <!-- New Project Modal -->
    <div
      v-if="showNewProjectModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showNewProjectModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg mx-4">
        <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100">{{ __('New Project') }}</h2>
          <button
            @click="showNewProjectModal = false"
            class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            <i class="fa-solid fa-xmark text-xl"></i>
          </button>
        </div>

        <form @submit.prevent="handleCreateProject" class="p-4 space-y-4">
          <div v-if="createError" class="bg-red-50 border border-red-200 rounded p-3 text-red-600 text-sm">
            {{ createError }}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Project Name') }} *</label>
            <input
              v-model="newProject.project_name"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
              :placeholder="__('Enter project name')"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Description') }}</label>
            <textarea
              v-model="newProject.description"
              rows="3"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
              :placeholder="__('Brief project description')"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Start Date') }} *</label>
              <input
                v-model="newProject.start_date"
                type="date"
                required
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('End Date') }} *</label>
              <input
                v-model="newProject.end_date"
                type="date"
                required
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Project Type') }}</label>
            <select
              v-model="newProject.project_type"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
            >
              <option value="Internal">{{ __('Internal') }}</option>
              <option value="Client">{{ __('Client') }}</option>
              <option value="Mixed">{{ __('Mixed') }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Budget') }}</label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 text-sm">{{ currencySymbol }}</span>
              <input
                v-model.number="newProject.budget"
                type="number"
                min="0"
                step="100"
                class="w-full pl-7 pr-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
                placeholder="0"
              />
            </div>
          </div>

          <!-- From Template (optional) -->
          <div v-if="availableTemplates.length > 0">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('From Template') }}
              <span class="text-xs text-gray-400 dark:text-gray-500 font-normal ml-1">({{ __('optional') }})</span>
            </label>
            <select
              v-model="selectedTemplate"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20"
            >
              <option value="">{{ __('No template') }}</option>
              <option v-for="tpl in availableTemplates" :key="tpl.name" :value="tpl.name">
                {{ tpl.template_name }} ({{ __('{0} tasks, {1} milestones', [tpl.task_count, tpl.milestone_count]) }})
              </option>
            </select>
            <p v-if="selectedTemplate" class="text-xs text-orga-600 dark:text-orga-400 mt-1">
              <i class="fa-solid fa-info-circle mr-1"></i>
              {{ __('Tasks and milestones will be created with dates relative to the project start date.') }}
            </p>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              @click="showNewProjectModal = false"
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              {{ __('Cancel') }}
            </button>
            <button
              type="submit"
              :disabled="isCreating"
              class="px-4 py-2 bg-orga-500 text-white rounded hover:bg-orga-600 disabled:opacity-50"
            >
              <i v-if="isCreating" class="fa-solid fa-spinner fa-spin mr-2"></i>
              {{ isCreating ? __('Creating...') : __('Create Project') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
