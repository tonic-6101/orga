<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskApi, useProjectApi } from '@/composables/useApi'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Skeleton from '@/components/common/Skeleton.vue'
import TaskManager from '@/components/TaskManager.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { __ } from '@/composables/useTranslate'
import { Loader2, TriangleAlert, Plus, Search, ListIcon, Columns3, CircleCheck, ArrowUpNarrowWide, ArrowDownWideNarrow, ArrowUp, ArrowDown, ArrowUpDown, User } from 'lucide-vue-next'
import type { OrgaTask, OrgaProject, TaskStatus, TaskPriority, MentionUser } from '@/types/orga'

// KanbanColumn interface (same as TaskManager/ProjectDetail)
interface KanbanColumn {
  id: TaskStatus
  title: string
  color?: string
}

const router = useRouter()
const { loading, error } = useTaskApi()
const taskApi = useTaskApi()
const projectApi = useProjectApi()
const { isOrgaManager, isSystemManager } = useAuth()
const { success: showSuccess, error: showError } = useToast()

// View mode
type ViewMode = 'list' | 'board'
const viewMode = ref<ViewMode>(
  (localStorage.getItem('orga_mytasks_view') as ViewMode) || 'list'
)

watch(viewMode, (mode) => {
  localStorage.setItem('orga_mytasks_view', mode)
  if (mode === 'board') {
    loadBoardTasks()
  } else {
    loadTasks()
  }
})

// Data
const tasks = ref<OrgaTask[]>([])
const totalTasks = ref(0)
const projects = ref<OrgaProject[]>([])
const isLoading = ref(true)
const loadError = ref<string | null>(null)

// Board data
const boardTasks = ref<Record<string, OrgaTask[]>>({
  'Open': [],
  'In Progress': [],
  'Review': [],
  'Completed': [],
})
const isBoardLoading = ref(false)

// Quick-add
const quickAddInput = ref('')
const quickAddRef = ref<HTMLInputElement | null>(null)
const isCreating = ref(false)

// Scope
type TaskScope = 'assigned' | 'my_projects' | 'all'
const scopeFilter = ref<TaskScope>('assigned')

const canViewAll = computed(() => isOrgaManager.value || isSystemManager.value)

const scopeOptions = computed(() => {
  const options: { value: TaskScope; label: string }[] = [
    { value: 'assigned', label: __('Assigned to Me') },
    { value: 'my_projects', label: __('My Projects') },
  ]
  if (canViewAll.value) {
    options.push({ value: 'all', label: __('All Tasks') })
  }
  return options
})

const subtitleText = computed(() => {
  switch (scopeFilter.value) {
    case 'my_projects':
      return __('Tasks from projects you manage.')
    case 'all':
      return __('All tasks across all projects.')
    default:
      return __('Tasks assigned to you across all projects.')
  }
})

// Filters
const statusFilter = ref<string>('')
const priorityFilter = ref<string>('')
const projectFilter = ref<string>('')
const assignedToFilter = ref<string>('')
const searchQuery = ref('')

// Sort state
type SortField = 'subject' | 'project' | 'priority' | 'status' | 'due_date'
const sortField = ref<SortField>('due_date')
const sortDir = ref<'asc' | 'desc'>('asc')

// Restore sort from localStorage
const savedSort = localStorage.getItem('orga_mytasks_sort')
if (savedSort) {
  try {
    const parsed = JSON.parse(savedSort)
    if (parsed.field && ['subject', 'project', 'priority', 'status', 'due_date'].includes(parsed.field)) {
      sortField.value = parsed.field
    }
    if (parsed.dir === 'asc' || parsed.dir === 'desc') {
      sortDir.value = parsed.dir
    }
  } catch {
    // Ignore invalid stored value
  }
}

// Sort field labels for dropdown
const sortOptions: { value: SortField; label: string }[] = [
  { value: 'due_date', label: __('Sort: Due Date') },
  { value: 'subject', label: __('Sort: Task') },
  { value: 'project', label: __('Sort: Project') },
  { value: 'priority', label: __('Sort: Priority') },
  { value: 'status', label: __('Sort: Status') },
]

// Natural default sort direction per field
const defaultSortDir: Record<SortField, 'asc' | 'desc'> = {
  due_date: 'asc',
  subject: 'asc',
  project: 'asc',
  priority: 'desc',
  status: 'asc',
}

function toggleSort(field: SortField): void {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDir.value = defaultSortDir[field]
  }
}

// Users for filter dropdown
const users = ref<MentionUser[]>([])

// Pagination (load-more style)
const perPage = 20
const loadedCount = ref(0)
const isLoadingMore = ref(false)

// Status options for filter dropdown
const statusOptions: { value: string; label: string }[] = [
  { value: '', label: __('All Active') },
  { value: 'Open', label: __('Open') },
  { value: 'In Progress', label: __('In Progress') },
  { value: 'Review', label: __('Review') },
  { value: 'Completed', label: __('Completed') },
  { value: 'Cancelled', label: __('Cancelled') },
]

const priorityOptions: { value: string; label: string }[] = [
  { value: '', label: __('All Priorities') },
  { value: 'Urgent', label: __('Urgent') },
  { value: 'High', label: __('High') },
  { value: 'Medium', label: __('Medium') },
  { value: 'Low', label: __('Low') },
]

const taskStatusOptions: TaskStatus[] = ['Open', 'In Progress', 'Review', 'Completed', 'Cancelled']

// Computed
const hasMore = computed(() => loadedCount.value < totalTasks.value)

// Debounce timer for search
let searchTimer: ReturnType<typeof setTimeout> | null = null

// Priority badge classes
function getPriorityClass(priority: string): string {
  const classes: Record<string, string> = {
    'Urgent': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    'High': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    'Medium': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'Low': 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  }
  return classes[priority] || 'bg-gray-100 text-gray-600'
}

// Due date formatting
interface BadgeDisplay {
  text: string
  class: string
}

function formatDueDate(dueDate: string | null | undefined): BadgeDisplay {
  if (!dueDate) return { text: __('No due date'), class: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400' }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)

  const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { text: __('{0}d overdue', [Math.abs(diffDays)]), class: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' }
  } else if (diffDays === 0) {
    return { text: __('Today'), class: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400' }
  } else if (diffDays === 1) {
    return { text: __('Tomorrow'), class: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
  } else if (diffDays <= 7) {
    return { text: __('{0} days', [diffDays]), class: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' }
  } else {
    return {
      text: due.toLocaleDateString('de-DE', { month: 'short', day: 'numeric' }),
      class: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
    }
  }
}

// Quick-add task
async function handleQuickAdd(): Promise<void> {
  const subject = quickAddInput.value.trim()
  if (!subject || isCreating.value) return

  isCreating.value = true
  try {
    await taskApi.createTask({ subject })
    quickAddInput.value = ''
    showSuccess(__('Task created'), subject)
    if (viewMode.value === 'board') {
      await loadBoardTasks()
    } else {
      await loadTasks()
    }
    await nextTick()
    quickAddRef.value?.focus()
  } catch (e) {
    showError(__('Failed to create task'), (e as Error).message || __('Could not create task'))
  } finally {
    isCreating.value = false
  }
}

// Load tasks (resets list)
async function loadTasks(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const includeCompleted = statusFilter.value === 'Completed' || statusFilter.value === 'Cancelled'
    const result = await taskApi.call<{ tasks: OrgaTask[]; total: number }>(
      'orga.orga.api.task.get_my_tasks',
      {
        status: statusFilter.value || null,
        priority: priorityFilter.value || null,
        project: projectFilter.value || null,
        assigned_to: assignedToFilter.value || null,
        search: searchQuery.value.trim() || null,
        limit: perPage,
        offset: 0,
        include_completed: includeCompleted,
        scope: scopeFilter.value,
        sort_by: sortField.value,
        sort_dir: sortDir.value,
      }
    )
    tasks.value = result.tasks || []
    totalTasks.value = result.total || 0
    loadedCount.value = tasks.value.length
  } catch (e) {
    console.error('Failed to load tasks:', e)
    loadError.value = (e as Error).message || __('Failed to load tasks')
  } finally {
    isLoading.value = false
  }
}

// Load more tasks (appends to list)
async function loadMore(): Promise<void> {
  if (!hasMore.value || isLoadingMore.value) return
  isLoadingMore.value = true

  try {
    const includeCompleted = statusFilter.value === 'Completed' || statusFilter.value === 'Cancelled'
    const result = await taskApi.call<{ tasks: OrgaTask[]; total: number }>(
      'orga.orga.api.task.get_my_tasks',
      {
        status: statusFilter.value || null,
        priority: priorityFilter.value || null,
        project: projectFilter.value || null,
        assigned_to: assignedToFilter.value || null,
        search: searchQuery.value.trim() || null,
        limit: perPage,
        offset: loadedCount.value,
        include_completed: includeCompleted,
        scope: scopeFilter.value,
        sort_by: sortField.value,
        sort_dir: sortDir.value,
      }
    )
    const newTasks = result.tasks || []
    tasks.value = [...tasks.value, ...newTasks]
    totalTasks.value = result.total || 0
    loadedCount.value = tasks.value.length
  } catch (e) {
    console.error('Failed to load more tasks:', e)
  } finally {
    isLoadingMore.value = false
  }
}

// Load board tasks (grouped by status)
async function loadBoardTasks(): Promise<void> {
  isBoardLoading.value = true
  loadError.value = null

  try {
    const result = await taskApi.getMyTasksByStatus({
      priority: priorityFilter.value || null,
      project: projectFilter.value || null,
      assigned_to: assignedToFilter.value || null,
      search: searchQuery.value.trim() || null,
      scope: scopeFilter.value,
    })
    boardTasks.value = {
      'Open': result['Open'] || [],
      'In Progress': result['In Progress'] || [],
      'Review': result['Review'] || [],
      'Completed': result['Completed'] || [],
    }
  } catch (e) {
    console.error('Failed to load board tasks:', e)
    loadError.value = (e as Error).message || __('Failed to load tasks')
  } finally {
    isBoardLoading.value = false
  }
}

// Load projects for filter dropdown
async function loadProjects(): Promise<void> {
  try {
    const result = await projectApi.getProjects({ status: 'Active', limit: 200 })
    projects.value = result.projects || []
  } catch {
    // Non-critical
  }
}

// Load users for assigned-to filter dropdown
async function loadUsers(): Promise<void> {
  try {
    users.value = await taskApi.getAssignableUsers({ limit: 200 })
  } catch {
    // Non-critical
  }
}

// Quick status change (inline dropdown)
async function handleStatusChange(task: OrgaTask, newStatus: string): Promise<void> {
  const oldStatus = task.status
  task.status = newStatus as TaskStatus
  try {
    await taskApi.updateStatus(task.name, newStatus)
    showSuccess(__('Status updated'), __('{0} is now {1}', [task.subject, newStatus]))
    // Refresh the panel if this task is selected
    if (selectedTask.value?.name === task.name) {
      selectedTask.value = { ...selectedTask.value, status: newStatus as TaskStatus }
    }
    // Reload if completed/cancelled and not showing those
    if ((newStatus === 'Completed' || newStatus === 'Cancelled') && !statusFilter.value) {
      if (viewMode.value === 'board') {
        await loadBoardTasks()
      } else {
        await loadTasks()
      }
    }
  } catch (e) {
    task.status = oldStatus as TaskStatus
    showError(__('Update failed'), (e as Error).message || __('Could not update task status'))
  }
}

// Navigate to project detail
function navigateToProject(task: OrgaTask): void {
  if (task.project) {
    router.push(`/orga/projects/${task.project}`)
  }
}

// --- Kanban Board Drag & Drop ---
const draggedTask = ref<OrgaTask | null>(null)
const dragOverColumn = ref<string | null>(null)

function onDragStart(event: DragEvent, task: OrgaTask): void {
  draggedTask.value = task
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', task.name)
  }
  ;(event.target as HTMLElement).classList.add('opacity-50')
}

function onDragEnd(event: DragEvent): void {
  ;(event.target as HTMLElement).classList.remove('opacity-50')
  draggedTask.value = null
  dragOverColumn.value = null
}

function onDragOver(event: DragEvent, columnId: string): void {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverColumn.value = columnId
}

function onDragLeave(_event: DragEvent, columnId: string): void {
  if (dragOverColumn.value === columnId) {
    dragOverColumn.value = null
  }
}

async function onDrop(_event: DragEvent, columnId: string): Promise<void> {
  dragOverColumn.value = null
  const task = draggedTask.value
  draggedTask.value = null

  if (!task || task.status === columnId) return

  // Optimistic update
  const oldStatus = task.status
  const sourceColumn = boardTasks.value[oldStatus]
  const targetColumn = boardTasks.value[columnId]
  if (sourceColumn && targetColumn) {
    const idx = sourceColumn.findIndex(t => t.name === task.name)
    if (idx !== -1) {
      sourceColumn.splice(idx, 1)
      task.status = columnId as TaskStatus
      targetColumn.unshift(task)
    }
  }

  try {
    await taskApi.updateStatus(task.name, columnId)
    showSuccess(__('Status updated'), __('{0} is now {1}', [task.subject, columnId]))
    if (selectedTask.value?.name === task.name) {
      selectedTask.value = { ...selectedTask.value, status: columnId as TaskStatus }
    }
  } catch (e) {
    // Revert optimistic update
    showError(__('Update failed'), (e as Error).message || __('Could not update task status'))
    await loadBoardTasks()
  }
}

// --- TaskManager Panel ---
const columns: KanbanColumn[] = [
  { id: 'Open', title: __('Open'), color: 'column-open' },
  { id: 'In Progress', title: __('In Progress'), color: 'column-in-progress' },
  { id: 'Review', title: __('Review'), color: 'column-review' },
  { id: 'Completed', title: __('Completed'), color: 'column-completed' },
]

const selectedTask = ref<OrgaTask | null>(null)
const showManager = ref(false)
const isLoadingTask = ref(false)

async function selectTask(task: OrgaTask): Promise<void> {
  // If clicking the already-selected task, just ensure panel is open
  if (selectedTask.value?.name === task.name) {
    showManager.value = true
    return
  }
  isLoadingTask.value = true
  showManager.value = true
  try {
    const fullTask = await taskApi.getTask(task.name)
    selectedTask.value = fullTask
  } catch (e) {
    console.error('Failed to load task details:', e)
    showError(__('Load failed'), (e as Error).message || __('Could not load task details'))
    showManager.value = false
  } finally {
    isLoadingTask.value = false
  }
}

async function handleTaskUpdate(): Promise<void> {
  // Refresh task detail + task list
  if (selectedTask.value) {
    try {
      const refreshed = await taskApi.getTask(selectedTask.value.name)
      selectedTask.value = refreshed
    } catch {
      // Task may have been deleted
      selectedTask.value = null
      showManager.value = false
    }
  }
  if (viewMode.value === 'board') {
    await loadBoardTasks()
  } else {
    await loadTasks()
  }
}

// Handle field updates from TaskManager (e.g. project change, description, dates)
async function handleFieldUpdate(payload: { field: string; value: unknown; task_id: string }): Promise<void> {
  try {
    await taskApi.updateTask(payload.task_id, { [payload.field]: payload.value })
    await handleTaskUpdate()
  } catch (e) {
    showError(__('Update failed'), (e as Error).message || __('Could not update task'))
  }
}

async function handleStatusChangeFromManager(task: OrgaTask, newStatus: TaskStatus): Promise<void> {
  try {
    await taskApi.updateStatus(task.name, newStatus)
    showSuccess(__('Status updated'), __('{0} is now {1}', [task.subject, newStatus]))
    // Refresh detail + list
    await handleTaskUpdate()
  } catch (e) {
    showError(__('Update failed'), (e as Error).message || __('Could not update task status'))
  }
}

// Keyboard navigation
function handleKeydown(e: KeyboardEvent): void {
  // Don't intercept when typing in inputs
  const tag = (e.target as HTMLElement).tagName
  if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA' || (e.target as HTMLElement).isContentEditable) return

  if (e.key === 'Escape' && showManager.value) {
    showManager.value = false
    return
  }

  if (!showManager.value || !selectedTask.value || tasks.value.length === 0) return

  const currentIdx = tasks.value.findIndex(t => t.name === selectedTask.value?.name)
  if (currentIdx === -1) return

  if ((e.key === 'j' || e.key === 'ArrowDown') && currentIdx < tasks.value.length - 1) {
    e.preventDefault()
    selectTask(tasks.value[currentIdx + 1])
  } else if ((e.key === 'k' || e.key === 'ArrowUp') && currentIdx > 0) {
    e.preventDefault()
    selectTask(tasks.value[currentIdx - 1])
  }
}

// Watch filters to reload (resets list)
watch([scopeFilter, statusFilter, priorityFilter, projectFilter, assignedToFilter], () => {
  if (viewMode.value === 'board') {
    loadBoardTasks()
  } else {
    loadTasks()
  }
})

// Watch sort changes — persist to localStorage + reload
watch([sortField, sortDir], () => {
  localStorage.setItem('orga_mytasks_sort', JSON.stringify({ field: sortField.value, dir: sortDir.value }))
  if (viewMode.value === 'list') {
    loadTasks()
  }
})

// Debounced search — waits 300ms after typing stops, then reloads
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    if (viewMode.value === 'board') {
      loadBoardTasks()
    } else {
      loadTasks()
    }
  }, 300)
})

// Board column count helper
function getColumnCount(columnId: string): number {
  return (boardTasks.value[columnId] || []).length
}

onMounted(() => {
  if (viewMode.value === 'board') {
    loadBoardTasks()
  } else {
    loadTasks()
  }
  loadProjects()
  loadUsers()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="flex h-full overflow-hidden">
  <!-- Task List (left side) -->
  <div class="flex-1 overflow-auto p-6">
    <!-- Header -->
    <div class="mb-6 flex items-start justify-between">
      <div>
        <h1 class="text-h1 text-gray-800 dark:text-gray-100 m-0">{{ __('My Tasks') }}</h1>
        <p class="text-body text-gray-600 dark:text-gray-400 mt-1">
          {{ subtitleText }}
        </p>
      </div>
      <!-- View Toggle -->
      <div class="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
        <button
          @click="viewMode = 'list'"
          :class="[
            'px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-1.5',
            viewMode === 'list'
              ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          :title="__('List view')"
        >
          <ListIcon class="w-3 h-3" aria-hidden="true" />
          {{ __('List') }}
        </button>
        <button
          @click="viewMode = 'board'"
          :class="[
            'px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-1.5',
            viewMode === 'board'
              ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          :title="__('Board view')"
        >
          <Columns3 class="w-3 h-3" aria-hidden="true" />
          {{ __('Board') }}
        </button>
      </div>
    </div>

    <!-- Quick Add -->
    <div class="mb-4">
      <form @submit.prevent="handleQuickAdd" class="flex items-center gap-2">
        <div class="relative flex-1">
          <Plus class="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            ref="quickAddRef"
            v-model="quickAddInput"
            type="text"
            :placeholder="__('Add a task... (press Enter)')"
            :disabled="isCreating"
            class="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50 transition-colors"
          />
        </div>
        <button
          v-if="quickAddInput.trim()"
          type="submit"
          :disabled="isCreating"
          class="px-4 py-2.5 text-sm font-medium bg-accent-500 text-white rounded-lg hover:bg-accent-600 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          <Loader2 v-if="isCreating" class="w-3.5 h-3.5 animate-spin inline mr-1" aria-hidden="true" />
          {{ __('Add') }}
        </button>
      </form>
    </div>

    <!-- Scope Toggle -->
    <div class="flex items-center gap-1 mb-4 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg w-fit">
      <button
        v-for="opt in scopeOptions"
        :key="opt.value"
        @click="scopeFilter = opt.value"
        :class="[
          'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
          scopeFilter === opt.value
            ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
        ]"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-6">
      <!-- Status Filter (list view only) -->
      <select
        v-if="viewMode === 'list'"
        v-model="statusFilter"
        class="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20"
      >
        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>

      <!-- Priority Filter -->
      <select
        v-model="priorityFilter"
        class="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20"
      >
        <option v-for="opt in priorityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>

      <!-- Project Filter -->
      <select
        v-model="projectFilter"
        class="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20"
      >
        <option value="">{{ __('All Projects') }}</option>
        <option v-for="p in projects" :key="p.name" :value="p.name">{{ p.project_name }}</option>
      </select>

      <!-- Assigned To Filter -->
      <select
        v-model="assignedToFilter"
        class="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20"
      >
        <option value="">{{ __('All Assignees') }}</option>
        <option v-for="u in users" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
      </select>

      <!-- Search -->
      <div class="relative flex-1 min-w-[200px] max-w-sm">
        <Search class="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="__('Search tasks...')"
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20 placeholder-gray-400 dark:placeholder-gray-500"
        />
      </div>

      <!-- Sort (list view only) -->
      <template v-if="viewMode === 'list'">
        <select
          v-model="sortField"
          class="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <button
          @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
          :title="sortDir === 'asc' ? __('Ascending — click to reverse') : __('Descending — click to reverse')"
          class="px-2.5 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20 transition-colors"
        >
          <ArrowUpNarrowWide v-if="sortDir === 'asc'" class="w-4 h-4" aria-hidden="true" /><ArrowDownWideNarrow v-else class="w-4 h-4" aria-hidden="true" />
        </button>
      </template>

      <!-- Count -->
      <span v-if="viewMode === 'list'" class="text-sm text-gray-500 dark:text-gray-400 ml-auto">
        {{ totalTasks }} task{{ totalTasks !== 1 ? 's' : '' }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="(viewMode === 'list' && isLoading) || (viewMode === 'board' && isBoardLoading)">
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <Skeleton type="card" :count="5" />
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <TriangleAlert class="w-5 h-5 text-red-500" aria-hidden="true" />
        <div>
          <h3 class="text-red-800 dark:text-red-300 font-medium">{{ __('Error loading tasks') }}</h3>
          <p class="text-red-600 dark:text-red-400 text-sm">{{ loadError }}</p>
        </div>
      </div>
      <button
        @click="viewMode === 'board' ? loadBoardTasks() : loadTasks()"
        class="mt-4 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/50"
      >
        {{ __('Try Again') }}
      </button>
    </div>

    <!-- ================ LIST VIEW ================ -->
    <template v-else-if="viewMode === 'list'">
      <!-- Empty State -->
      <div v-if="tasks.length === 0" class="text-center py-16">
        <CircleCheck class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4 mx-auto" aria-hidden="true" />
        <h3 class="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
          {{ statusFilter || priorityFilter || projectFilter || searchQuery ? __('No matching tasks') : __('All caught up!') }}
        </h3>
        <p class="text-gray-500 dark:text-gray-400">
          {{ statusFilter || priorityFilter || projectFilter || searchQuery
            ? __('Try adjusting your filters.')
            : __('You have no tasks assigned to you right now.') }}
        </p>
      </div>

      <!-- Task List -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- Table Header -->
        <div
          class="hidden sm:grid gap-2 px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 text-xs font-semibold uppercase tracking-wide sm:grid-cols-[1fr_130px_44px_100px_100px_120px_130px]"
        >
          <button
            @click="toggleSort('subject')"
            :aria-sort="sortField === 'subject' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            :class="['flex items-center gap-1 text-left', sortField === 'subject' ? 'text-accent-600 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
          >
            {{ __('Task') }}
            <ArrowUp v-if="sortField === 'subject' && sortDir === 'asc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowDown v-else-if="sortField === 'subject' && sortDir === 'desc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowUpDown v-else class="w-2.5 h-2.5 opacity-40" aria-hidden="true" />
          </button>
          <button
            @click="toggleSort('project')"
            :aria-sort="sortField === 'project' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            :class="['flex items-center gap-1 text-left', sortField === 'project' ? 'text-accent-600 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
          >
            {{ __('Project') }}
            <ArrowUp v-if="sortField === 'project' && sortDir === 'asc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowDown v-else-if="sortField === 'project' && sortDir === 'desc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowUpDown v-else class="w-2.5 h-2.5 opacity-40" aria-hidden="true" />
          </button>
          <span></span>
          <button
            @click="toggleSort('priority')"
            :aria-sort="sortField === 'priority' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            :class="['flex items-center gap-1 text-left', sortField === 'priority' ? 'text-accent-600 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
          >
            {{ __('Priority') }}
            <ArrowUp v-if="sortField === 'priority' && sortDir === 'asc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowDown v-else-if="sortField === 'priority' && sortDir === 'desc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowUpDown v-else class="w-2.5 h-2.5 opacity-40" aria-hidden="true" />
          </button>
          <button
            @click="toggleSort('status')"
            :aria-sort="sortField === 'status' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            :class="['flex items-center gap-1 text-left', sortField === 'status' ? 'text-accent-600 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
          >
            {{ __('Status') }}
            <ArrowUp v-if="sortField === 'status' && sortDir === 'asc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowDown v-else-if="sortField === 'status' && sortDir === 'desc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowUpDown v-else class="w-2.5 h-2.5 opacity-40" aria-hidden="true" />
          </button>
          <button
            @click="toggleSort('due_date')"
            :aria-sort="sortField === 'due_date' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            :class="['flex items-center gap-1 text-left', sortField === 'due_date' ? 'text-accent-600 dark:text-accent-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300']"
          >
            {{ __('Due Date') }}
            <ArrowUp v-if="sortField === 'due_date' && sortDir === 'asc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowDown v-else-if="sortField === 'due_date' && sortDir === 'desc'" class="w-2.5 h-2.5" aria-hidden="true" /><ArrowUpDown v-else class="w-2.5 h-2.5 opacity-40" aria-hidden="true" />
          </button>
          <span class="text-gray-500 dark:text-gray-400">{{ __('Quick Action') }}</span>
        </div>

        <!-- Task Rows -->
        <div
          v-for="task in tasks"
          :key="task.name"
          @click="selectTask(task)"
          :class="[
            'grid grid-cols-1 gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors items-center cursor-pointer',
            selectedTask?.name === task.name ? 'bg-accent-50 dark:bg-accent-900/20 ring-1 ring-inset ring-accent-200 dark:ring-accent-800' : '',
            'sm:grid-cols-[1fr_130px_44px_100px_100px_120px_130px]'
          ]"
        >
          <!-- Task Subject -->
          <div class="min-w-0">
            <span
              class="text-sm font-medium text-gray-800 dark:text-gray-200 hover:text-accent-500 dark:hover:text-accent-400 truncate block text-left w-full transition-colors"
              :title="task.subject"
            >
              {{ task.subject }}
            </span>
          </div>

          <!-- Project (navigates to ProjectDetail) -->
          <div class="min-w-0">
            <button
              v-if="task.project"
              @click.stop="navigateToProject(task)"
              class="text-xs text-gray-500 dark:text-gray-400 hover:text-accent-500 truncate block text-left w-full transition-colors"
              :title="task.project_name || task.project"
            >
              {{ task.project_name || task.project }}
            </button>
            <span v-else class="text-xs text-gray-400 dark:text-gray-500">&mdash;</span>
          </div>

          <!-- Assigned To (avatar) -->
          <div class="flex justify-center">
            <UserAvatar
              v-if="task.assigned_to_name"
              :name="task.assigned_to_name"
              :image="task.assigned_to_image"
              size="xs"
              color="orga"
              class="!w-6 !h-6 !text-[10px]"
              :title="task.assigned_to_name"
            />
            <span v-else class="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400 dark:text-gray-500 text-[10px]">
              <User class="w-2.5 h-2.5" aria-hidden="true" />
            </span>
          </div>

          <!-- Priority Badge -->
          <div>
            <span :class="['text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap', getPriorityClass(task.priority)]">
              {{ task.priority }}
            </span>
          </div>

          <!-- Status Badge -->
          <div>
            <StatusBadge :status="task.status" type="task" size="sm" />
          </div>

          <!-- Due Date -->
          <div>
            <span :class="['text-xs px-2 py-1 rounded whitespace-nowrap', formatDueDate(task.due_date).class]">
              {{ formatDueDate(task.due_date).text }}
            </span>
          </div>

          <!-- Quick Status Change -->
          <div @click.stop>
            <select
              :value="task.status"
              @change="handleStatusChange(task, ($event.target as HTMLSelectElement).value)"
              class="text-xs px-2 py-1.5 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20 w-full"
            >
              <option v-for="s in taskStatusOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Load More -->
      <div v-if="hasMore && !isLoading" class="flex flex-col items-center gap-2 mt-4">
        <button
          @click="loadMore"
          :disabled="isLoadingMore"
          class="px-5 py-2 text-sm font-medium border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <template v-if="isLoadingMore">
            <Loader2 class="w-3.5 h-3.5 animate-spin inline mr-1.5" aria-hidden="true" /> {{ __('Loading...') }}
          </template>
          <template v-else>
            {{ __('Load More') }} ({{ __('{0} remaining', [totalTasks - loadedCount]) }})
          </template>
        </button>
        <span class="text-xs text-gray-400 dark:text-gray-500">
          {{ __('Showing {0} of {1}', [loadedCount, totalTasks]) }}
        </span>
      </div>
    </template>

    <!-- ================ BOARD VIEW ================ -->
    <template v-else-if="viewMode === 'board'">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="col in columns"
          :key="col.id"
          @dragover="onDragOver($event, col.id)"
          @dragleave="onDragLeave($event, col.id)"
          @drop="onDrop($event, col.id)"
          :class="[
            'flex flex-col rounded-lg border min-h-[200px] transition-colors',
            dragOverColumn === col.id
              ? 'border-accent-400 dark:border-accent-500 bg-accent-50/50 dark:bg-accent-900/20'
              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50'
          ]"
        >
          <!-- Column Header -->
          <div class="flex items-center justify-between px-3 py-2.5 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-2">
              <StatusBadge :status="col.id" type="task" size="sm" />
              <span class="text-xs font-medium text-gray-500 dark:text-gray-400">
                {{ getColumnCount(col.id) }}
              </span>
            </div>
          </div>

          <!-- Column Body -->
          <div class="flex-1 overflow-y-auto p-2 space-y-2">
            <!-- Empty column -->
            <div
              v-if="getColumnCount(col.id) === 0"
              class="flex items-center justify-center h-24 text-xs text-gray-400 dark:text-gray-500"
            >
              {{ __('No tasks') }}
            </div>

            <!-- Task Cards -->
            <div
              v-for="task in boardTasks[col.id]"
              :key="task.name"
              draggable="true"
              @dragstart="onDragStart($event, task)"
              @dragend="onDragEnd"
              @click="selectTask(task)"
              :class="[
                'bg-white dark:bg-gray-800 rounded-lg border p-3 cursor-pointer hover:shadow-sm transition-all',
                selectedTask?.name === task.name
                  ? 'border-accent-300 dark:border-accent-600 ring-1 ring-accent-200 dark:ring-accent-800'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              ]"
            >
              <!-- Subject -->
              <p class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 line-clamp-2">
                {{ task.subject }}
              </p>

              <!-- Meta row -->
              <div class="flex items-center gap-2 flex-wrap">
                <!-- Project badge -->
                <button
                  v-if="task.project"
                  @click.stop="navigateToProject(task)"
                  class="text-[11px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded hover:text-accent-500 transition-colors truncate max-w-[120px]"
                  :title="task.project_name || task.project"
                >
                  {{ task.project_name || task.project }}
                </button>

                <!-- Priority -->
                <span :class="['text-[11px] px-1.5 py-0.5 rounded-full font-medium', getPriorityClass(task.priority)]">
                  {{ task.priority }}
                </span>

                <!-- Due date -->
                <span
                  v-if="task.due_date"
                  :class="['text-[11px] px-1.5 py-0.5 rounded', formatDueDate(task.due_date).class]"
                >
                  {{ formatDueDate(task.due_date).text }}
                </span>

                <!-- Spacer -->
                <span class="flex-1"></span>

                <!-- Assignee avatar -->
                <UserAvatar
                  v-if="task.assigned_to_name"
                  :name="task.assigned_to_name"
                  :image="task.assigned_to_image"
                  size="xs"
                  color="orga"
                  class="!w-5 !h-5 !text-[9px]"
                  :title="task.assigned_to_name"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div><!-- end task list left side -->

  <!-- Mobile Manager Panel Backdrop -->
  <div
    v-if="showManager"
    class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    @click="showManager = false"
  ></div>

  <!-- Task Manager Panel (right side) -->
  <aside
    v-if="showManager && selectedTask"
    class="fixed inset-y-0 right-0 w-full max-w-md z-50 lg:relative lg:z-auto lg:w-96 lg:max-w-none bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 overflow-hidden transition-all"
  >
    <TaskManager
      :task="selectedTask"
      :columns="columns"
      view-type="list"
      @update="handleTaskUpdate"
      @close="showManager = false"
      @status-change="handleStatusChangeFromManager"
      @field-update="handleFieldUpdate"
    />
  </aside>

  <!-- Loading indicator when fetching task detail -->
  <aside
    v-else-if="showManager && isLoadingTask"
    class="fixed inset-y-0 right-0 w-full max-w-md z-50 lg:relative lg:z-auto lg:w-96 lg:max-w-none bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 items-center justify-center"
  >
    <Loader2 class="w-6 h-6 text-gray-400 animate-spin" aria-hidden="true" />
    <p class="text-sm text-gray-500 mt-2">{{ __('Loading task...') }}</p>
  </aside>
  </div><!-- end flex container -->
</template>
