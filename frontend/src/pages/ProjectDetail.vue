<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectApi, useTaskApi, useMilestoneApi, useGanttApi, useApi, useContactApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'
import { useProjectShortcuts } from '@/composables/useProjectShortcuts'
import { useToast } from '@/composables/useToast'
import { useCurrency } from '@/composables/useCurrency'
import TaskManager from '@/components/TaskManager.vue'
import GanttChart from '@/components/gantt/GanttChart.vue'
// GanttFocusPanel replaced by unified TaskManager with viewType='gantt'
import CreateTaskModal from '@/components/project/CreateTaskModal.vue'
import CreateMilestoneModal from '@/components/project/CreateMilestoneModal.vue'
import DeleteProjectModal from '@/components/project/DeleteProjectModal.vue'
import SaveAsTemplateModal from '@/components/project/SaveAsTemplateModal.vue'
// KanbanColumnQuickAdd removed - use top bar "+ Add Task" button instead
import StatusBadge from '@/components/common/StatusBadge.vue'
import Breadcrumb from '@/components/common/Breadcrumb.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { OrgaProject, OrgaTask, OrgaMilestone, OrgaContact, TaskStatus, TaskPriority, GanttTask, GanttItem, GanttMilestone, CascadeChange, ProjectDependencyEdge, TaskDependencyInfo, DependencyType } from '@/types/orga'

const route = useRoute()
const router = useRouter()
const { getProject, updateProject, getCriticalPath } = useProjectApi()
const { getTasksByStatus, updateStatus, updateTask, applyCascade, addDependency } = useTaskApi()
const { call: apiCall } = useApi()
const { updateMilestone } = useMilestoneApi()
const { reorderItem } = useGanttApi()
const { getContacts } = useContactApi()
const { success: showSuccess, error: showError } = useToast()
const { formatCurrency, currencySymbol } = useCurrency()

// Kanban column definition
interface KanbanColumn {
  id: TaskStatus
  title: string
  color: string
}

// View state
const view = ref<'kanban' | 'list' | 'gantt'>('gantt')
const showDetails = ref<boolean>(true)
const showManager = ref<boolean>(true)
const selectedTask = ref<OrgaTask | GanttTask | null>(null)
const selectedMilestone = ref<GanttMilestone | null>(null)
const isLoading = ref<boolean>(true)
const loadError = ref<string | null>(null)

// Drag-and-drop state
const draggedTask = ref<OrgaTask | null>(null)
const dragOverColumn = ref<TaskStatus | null>(null)
const justDroppedTask = ref<string | null>(null)
const justReorderedTaskId = ref<string | null>(null)

// Modal state
const isTaskModalOpen = ref<boolean>(false)
const isMilestoneModalOpen = ref<boolean>(false)
const isDeleteModalOpen = ref<boolean>(false)
const isSaveTemplateModalOpen = ref<boolean>(false)
const showSettingsMenu = ref<boolean>(false)
const initialTaskStatus = ref<string>('Open')

// Team member and document types
interface TeamMember {
  user: string
  full_name: string
  user_image?: string
  is_manager?: boolean
  source?: 'user' | 'resource'
}

interface ProjectDocument {
  name: string
  file_name: string
  file_url: string
  file_size: number
  file_type?: string
  attached_to_name?: string
  is_private?: number
  creation?: string
  owner?: string
}

// Data
const project = ref<OrgaProject | null>(null)
const tasks = ref<OrgaTask[]>([])
const milestones = ref<OrgaMilestone[]>([])
const teamMembers = ref<TeamMember[]>([])
const contacts = ref<OrgaContact[]>([])
const documents = ref<ProjectDocument[]>([])
const taskAttachments = ref<ProjectDocument[]>([])
const tasksByStatus = ref<Record<TaskStatus, OrgaTask[]>>({} as Record<TaskStatus, OrgaTask[]>)
const projectDependencies = ref<ProjectDependencyEdge[]>([])
const criticalPathTasks = ref<string[]>([])

// Document drawer state
const isDocDrawerOpen = ref(false)
const isUploadingProjectFile = ref(false)
const projectUploadProgress = ref(0)

// Kanban columns mapping with improved color scheme
const columns = computed<KanbanColumn[]>(() => [
  { id: 'Open', title: __('Open'), color: 'column-open' },
  { id: 'In Progress', title: __('In Progress'), color: 'column-in-progress' },
  { id: 'Review', title: __('Review'), color: 'column-review' },
  { id: 'Completed', title: __('Completed'), color: 'column-completed' }
])

// Colors now handled by StatusBadge component

// Computed
const projectId = computed<string>(() => route.params.id as string)

const totalTasks = computed<number>(() => {
  let count = 0
  for (const status in tasksByStatus.value) {
    count += tasksByStatus.value[status as TaskStatus]?.length || 0
  }
  return count
})

const completedTasks = computed<number>(() => tasksByStatus.value['Completed']?.length || 0)

const progressPercentage = computed<number>(() => {
  if (tasks.value.length === 0) return 0
  const total = tasks.value.reduce((sum, t) => {
    // Completed tasks always count as 100%, even if progress field wasn't updated
    if (t.status === 'Completed') return sum + 100
    return sum + (t.progress || 0)
  }, 0)
  return Math.round(total / tasks.value.length)
})


const budgetSpentPercent = computed<number>(() => {
  const b = project.value?.budget
  const s = project.value?.spent
  if (!b || b <= 0) return 0
  return Math.min(100, Math.round(((s || 0) / b) * 100))
})

const budgetEstimatedPercent = computed<number>(() => {
  const b = project.value?.budget
  const e = project.value?.estimated_cost
  if (!b || b <= 0) return 0
  return Math.min(100, Math.round(((e || 0) / b) * 100))
})

const costVariance = computed<number | null>(() => {
  const e = project.value?.estimated_cost
  const s = project.value?.spent
  if (!e && !s) return null
  return (e || 0) - (s || 0)
})

const costVariancePercent = computed<number>(() => {
  const e = project.value?.estimated_cost
  if (!e || e <= 0) return 0
  return Math.round(((costVariance.value || 0) / e) * 100)
})

// Available task groups (computed from loaded tasks)
const availableTaskGroups = computed<string[]>(() => {
  const groups = new Set<string>()
  for (const task of tasks.value) {
    if (task.task_group) groups.add(task.task_group)
  }
  return [...groups].sort()
})

// Project duration calculation
const projectDuration = computed<{ total: number; elapsed: number; remaining: number; label: string } | null>(() => {
  if (!project.value?.start_date) return null
  const start = new Date(project.value.start_date)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  start.setHours(0, 0, 0, 0)

  const end = project.value.end_date ? new Date(project.value.end_date) : null
  if (end) end.setHours(0, 0, 0, 0)

  const msPerDay = 1000 * 60 * 60 * 24
  const totalDays = end ? Math.ceil((end.getTime() - start.getTime()) / msPerDay) + 1 : 0
  const elapsedDays = Math.max(0, Math.ceil((today.getTime() - start.getTime()) / msPerDay) + 1)
  const remainingDays = end ? Math.max(0, Math.ceil((end.getTime() - today.getTime()) / msPerDay)) : 0

  // Format label
  let label: string
  if (totalDays <= 0 && !end) {
    label = __('{0}d elapsed', [elapsedDays])
  } else if (totalDays < 30) {
    label = __('{0}d', [totalDays])
  } else if (totalDays < 365) {
    const months = Math.round(totalDays / 30.44)
    label = months === 1 ? __('1 month') : __('{0} months', [months])
  } else {
    const years = (totalDays / 365.25).toFixed(1)
    label = __('{0}y', [years])
  }

  return { total: totalDays, elapsed: elapsedDays, remaining: remainingDays, label }
})

// Duration progress percentage (how much time has elapsed)
const durationProgress = computed<number>(() => {
  if (!projectDuration.value || projectDuration.value.total <= 0) return 0
  return Math.min(100, Math.round((projectDuration.value.elapsed / projectDuration.value.total) * 100))
})

// Get tasks for a column
function getColumnTasks(status: TaskStatus): OrgaTask[] {
  return tasksByStatus.value[status] || []
}

// Format date
function formatDate(date: string | null | undefined): string {
  if (!date) return __('N/A')
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Get initials
function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Get blocking predecessor tasks for a given task (uses already-loaded projectDependencies)
function getBlockingTasks(taskName: string): { name: string; subject: string }[] {
  return projectDependencies.value
    .filter(edge =>
      edge.task === taskName &&
      edge.dependency_type === 'Finish to Start' &&
      edge.depends_on_status !== 'Completed'
    )
    .map(edge => ({ name: edge.depends_on, subject: edge.depends_on_subject }))
}

function getBlockedByTooltip(taskName: string): string {
  const blockers = getBlockingTasks(taskName)
  if (blockers.length === 0) return __('Blocked')
  return __('Blocked by: {0}', [blockers.map(b => b.subject).join(', ')])
}

// Format file size
function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let size = bytes
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(size < 10 ? 1 : 0)} ${units[unitIndex]}`
}

// Select task for focus panel
function selectTask(task: OrgaTask): void {
  selectedTask.value = task
  showManager.value = true
}

// Refresh selectedTask with latest data from tasks array (call after loadProject)
function refreshSelectedTask(taskId?: string): void {
  const targetId = taskId || selectedTask.value?.name
  if (!targetId) return

  const updatedTask = tasks.value.find(t => t.name === targetId)
  if (updatedTask) {
    selectedTask.value = updatedTask
  }
}

// Refresh selectedMilestone with latest data from ganttMilestones (call after loadProject)
function refreshSelectedMilestone(): void {
  if (!selectedMilestone.value) return
  const updated = ganttMilestones.value.find(m => m.name === selectedMilestone.value?.name)
  if (updated) selectedMilestone.value = updated
}

// Handle Gantt item selection (task or milestone)
function handleGanttSelect(item: GanttItem): void {
  if (item.type === 'milestone') {
    // Open milestone detail panel
    selectedMilestone.value = item as GanttMilestone
    selectedTask.value = null
    isEditingMilestoneDesc.value = false
    isLinkingTask.value = false
    linkTaskSearch.value = ''
    if (!showManager.value) {
      showManager.value = true
    }
    return
  }
  // It's a task - use unified selectedTask and showManager state
  selectedMilestone.value = null
  selectedTask.value = item as GanttTask
  // Only open manager if not already open (same behavior as Kanban)
  if (!showManager.value) {
    showManager.value = true
  }
}

// Handle drag-to-create dependency on Gantt
async function handleCreateDependency(payload: { fromTask: string; toTask: string; type: 'FS' }): Promise<void> {
  try {
    await addDependency(payload.toTask, payload.fromTask, payload.type)
    showSuccess(__('Dependency created'), __('Added Finish-to-Start dependency'))
    await loadProject()
  } catch (e) {
    showError(__('Failed to create dependency'), (e as Error).message || __('Unknown error'))
  }
}

// Handle Gantt drag-and-drop date updates (with cascade support)
async function handleGanttDatesUpdate(payload: { taskId: string; startDate: string; endDate: string }): Promise<void> {
  try {
    // update_task backend now handles cascade based on project dependency_mode:
    // - Strict: auto-applies cascade, returns _cascade.updated_tasks
    // - Flexible: returns _cascade.cascade_preview for user confirmation
    // - Off: no cascade
    const result = await updateTask(payload.taskId, {
      start_date: payload.startDate,
      due_date: payload.endDate
    })

    const cascade = (result as Record<string, unknown>)?._cascade as {
      mode?: string
      cascade_preview?: Array<{ task_id: string; task_name: string; days_shift: number }>
      total_affected?: number
      updated_tasks?: string[]
      total_updated?: number
    } | undefined

    if (cascade?.mode === 'Flexible' && cascade.cascade_preview?.length) {
      // Show confirmation for Flexible mode
      const affected = cascade.cascade_preview
      const msg = affected.map(t => `${t.task_name}: ${t.days_shift > 0 ? '+' : ''}${t.days_shift} ${__('days')}`).join('\n')
      const confirmed = window.confirm(
        __('This change affects {0} dependent task(s):', [cascade.total_affected]) + `\n\n${msg}\n\n` + __('Apply cascade?')
      )
      if (confirmed) {
        await applyCascade(payload.taskId, payload.startDate, payload.endDate)
      }
    }

    if (cascade?.mode === 'Strict' && cascade.total_updated && cascade.total_updated > 0) {
      showSuccess(__('Dates cascaded'), __('Updated {0} dependent task(s)', [cascade.total_updated]))
    } else {
      showSuccess(__('Task moved'), __('Dates updated to {0} - {1}', [payload.startDate, payload.endDate]))
    }

    await loadProject()
    refreshSelectedTask(payload.taskId)
  } catch (e) {
    console.error('Failed to update task dates:', e)
    showError(__('Move failed'), __('Could not update task dates'))
  }
}

// Handle Gantt milestone date update (drag diamond to change due_date)
async function handleMilestoneDateUpdate(payload: { milestoneId: string; dueDate: string }): Promise<void> {
  try {
    await updateMilestone(payload.milestoneId, { due_date: payload.dueDate })
    await loadProject()
    showSuccess(__('Milestone moved'), __('Due date updated to {0}', [payload.dueDate]))
  } catch (e) {
    console.error('Failed to update milestone date:', e)
    showError(__('Move failed'), __('Could not update milestone date'))
  }
}

// Handle milestone field update from detail panel
async function handleMilestoneFieldUpdate(payload: { field: string; value: unknown }): Promise<void> {
  if (!selectedMilestone.value) return
  try {
    await updateMilestone(selectedMilestone.value.name, { [payload.field]: payload.value })
    await loadProject()
    refreshSelectedMilestone()
    showSuccess(__('Milestone updated'), __('Field has been updated'))
  } catch (e) {
    console.error('Failed to update milestone:', e)
    showError(__('Update failed'), __('Could not save changes to the milestone'))
  }
}

// Handle unified Gantt item reorder using float sort_order (backend is source of truth).
// GanttChart emits the neighbour IDs at the drop position.
// We call the backend to set a new sort_order = midpoint(prev, next), then reload data.
async function handleItemReorder(payload: {
  itemId: string
  itemType: 'task' | 'milestone'
  prevItemId: string | null
  nextItemId: string | null
  prevItemType: 'task' | 'milestone' | null
  nextItemType: 'task' | 'milestone' | null
}): Promise<void> {
  const { itemId, itemType, prevItemId, nextItemId, prevItemType, nextItemType } = payload

  // Trigger highlight animation
  justReorderedTaskId.value = itemId
  setTimeout(() => { justReorderedTaskId.value = null }, 1500)

  try {
    const result = await reorderItem({
      item_id: itemId,
      item_type: itemType,
      project: projectId.value,
      prev_item_id: prevItemId,
      next_item_id: nextItemId,
      prev_item_type: prevItemType,
      next_item_type: nextItemType
    })

    if (result.success === false) {
      // Migration not run yet — silently ignore
      return
    }

    // Reload data so sort_order values from backend are reflected
    await loadProject()
  } catch {
    // Backend call failed — data stays as-is
  }
}

// Handle task field update (used by all views for date changes, etc.)
async function handleGanttUpdate(payload: { field: string; value: unknown; task_id: string }): Promise<void> {
  try {
    // Call API to update task field
    await updateTask(payload.task_id, { [payload.field]: payload.value })
    await loadProject()
    refreshSelectedTask(payload.task_id)
    refreshSelectedMilestone()

    // Show success feedback for field changes
    if (payload.field === 'start_date' || payload.field === 'due_date') {
      const fieldLabel = payload.field === 'start_date' ? __('Start date') : __('Due date')
      if (payload.value) {
        showSuccess(__('Date updated'), __('{0} set to {1}', [fieldLabel, new Date(payload.value as string).toLocaleDateString()]))
      } else {
        showSuccess(__('Date cleared'), __('{0} has been cleared', [fieldLabel]))
      }
    } else if (payload.field === 'progress') {
      showSuccess(__('Progress updated'), __('Progress set to {0}%', [payload.value]))
    } else if (payload.field === 'description') {
      showSuccess(__('Description updated'), __('Task description has been saved.'))
    } else if (payload.field === 'task_group') {
      if (payload.value) {
        showSuccess(__('Group updated'), __('Task moved to group "{0}"', [payload.value]))
      } else {
        showSuccess(__('Group removed'), __('Task removed from group'))
      }
    } else if (payload.field === 'depends_on_group') {
      if (payload.value) {
        showSuccess(__('Group dependency set'), __('Task blocked until all "{0}" tasks complete', [payload.value]))
      } else {
        showSuccess(__('Group dependency removed'), __('Task is no longer blocked by a group'))
      }
    }
  } catch (e) {
    console.error('Failed to update task:', e)
    const errMsg = (e as Error)?.message || (e as Record<string, unknown>)?.exc || __('Could not save changes to the task')
    showError(__('Update failed'), String(errMsg))
  }
}

// Handle cascade preview
function handleCascadePreview(payload: { changes: CascadeChange[] }): void {
  // Preview is handled by the UI — no action needed here
}

// Handle cascade apply
async function handleCascadeApply(payload: { task_id: string; changes: CascadeChange[] }): Promise<void> {
  try {
    // Apply all cascade changes via batch update
    const updates = payload.changes.map(change => ({
      task_name: change.task_id,
      [change.field === 'start_date' ? 'start_date' : 'due_date']: change.new_value
    }))

    await apiCall<{ success: boolean }>('orga.orga.api.task.batch_update_task_dates', { updates: JSON.stringify(updates) })
    await loadProject()
  } catch (e) {
    console.error('Failed to apply cascade:', e)
  }
}

// Handle navigate to another task in Gantt
function handleGanttNavigate(payload: { task_id: string }): void {
  const task = tasks.value.find(t => t.name === payload.task_id) as GanttTask | undefined
  if (task) {
    selectedTask.value = task
  }
}

// Convert tasks to GanttTask format with dependency info
const ganttTasks = computed<GanttTask[]>(() => {
  const deps = projectDependencies.value

  return tasks.value.map(task => {
    // Predecessors: edges where this task depends_on something (task field = this task's name)
    // means: "this task" has a row in depends_on child table pointing to another task
    // In the SQL: td.parent = this task, td.depends_on = predecessor
    const predecessors: TaskDependencyInfo[] = deps
      .filter(d => d.task === task.name)
      .map(d => ({
        task_id: d.depends_on,
        task_name: d.depends_on_subject,
        type: toShortDependencyType(d.dependency_type),
        lag: d.lag_days || 0,
        status: d.depends_on_status
      }))

    // Successors: edges where another task depends on this one
    const successors: TaskDependencyInfo[] = deps
      .filter(d => d.depends_on === task.name)
      .map(d => ({
        task_id: d.task,
        task_name: d.task_subject,
        type: toShortDependencyType(d.dependency_type),
        lag: d.lag_days || 0,
        status: d.task_status
      }))

    return {
      ...task,
      type: 'task' as const,
      duration: task.start_date && task.due_date
        ? Math.ceil((new Date(task.due_date).getTime() - new Date(task.start_date).getTime()) / (1000 * 60 * 60 * 24)) + 1
        : undefined,
      dependencies_info: predecessors,
      dependents_info: successors,
      is_blocked: predecessors.some(p => p.status !== 'Completed')
    }
  }) as GanttTask[]
})

// Convert milestones to GanttMilestone format for Gantt chart
const ganttMilestones = computed<GanttMilestone[]>(() => {
  return milestones.value
    .filter(m => m.due_date) // Only include milestones with dates
    .map(milestone => ({
      name: milestone.name,
      subject: milestone.milestone_name,
      type: 'milestone' as const,
      status: milestone.status,
      start_date: milestone.due_date,
      due_date: milestone.due_date,
      progress: milestone.completion_percentage ?? (milestone.status === 'Completed' ? 100 : 0),
      project: milestone.project,
      description: milestone.description,
      completed_date: milestone.completed_date,
      sort_order: milestone.sort_order || 0,
      task_count: milestone.task_count ?? 0
    }))
})

// Combined Gantt items (tasks + milestones) — passed to GanttChart which sorts by sort_order.
// Backend float sort_order is the single source of truth for ordering.
const ganttItems = computed<GanttItem[]>(() => {
  return [...ganttTasks.value, ...ganttMilestones.value]
})

// Handle status change (via click or drag-drop)
async function changeTaskStatus(task: OrgaTask, newStatus: TaskStatus): Promise<void> {
  try {
    await updateStatus(task.name, newStatus)
    await loadProject()
    refreshSelectedMilestone()
    showSuccess(__('Task updated'), __('"{0}" moved to {1}', [task.subject, newStatus]))
  } catch (e) {
    console.error('Failed to update task status:', e)
    showError(__('Failed to update task'), __('Could not change task status'))
  }
}

// Handle priority change
async function changeTaskPriority(task: OrgaTask, newPriority: TaskPriority): Promise<void> {
  try {
    await updateTask(task.name, { priority: newPriority })
    await loadProject()
    showSuccess(__('Priority updated'), __('"{0}" set to {1}', [task.subject, newPriority]))
  } catch (e) {
    console.error('Failed to update task priority:', e)
    showError(__('Failed to update priority'), __('Could not change task priority'))
  }
}

// Drag-and-drop handlers
function onDragStart(event: DragEvent, task: OrgaTask): void {
  draggedTask.value = task
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', task.name)
  }
  // Add visual feedback class
  const element = event.target as HTMLElement
  element.classList.add('dragging')
}

function onDragEnd(event: DragEvent): void {
  draggedTask.value = null
  dragOverColumn.value = null
  // Remove visual feedback class
  const element = event.target as HTMLElement
  element.classList.remove('dragging')
}

function onDragOver(event: DragEvent, columnId: TaskStatus): void {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverColumn.value = columnId
}

function onDragLeave(event: DragEvent, columnId: TaskStatus): void {
  // Only clear if leaving the column entirely
  const currentTarget = event.currentTarget as HTMLElement
  if (!currentTarget.contains(event.relatedTarget as Node)) {
    if (dragOverColumn.value === columnId) {
      dragOverColumn.value = null
    }
  }
}

async function onDrop(event: DragEvent, newStatus: TaskStatus): Promise<void> {
  event.preventDefault()
  dragOverColumn.value = null

  if (!draggedTask.value) return
  if (draggedTask.value.status === newStatus) {
    draggedTask.value = null
    return
  }

  const taskName = draggedTask.value.name
  const taskSubject = draggedTask.value.subject
  try {
    await updateStatus(taskName, newStatus)
    await loadProject()
    refreshSelectedMilestone()

    // Trigger just-dropped animation
    justDroppedTask.value = taskName
    setTimeout(() => {
      justDroppedTask.value = null
    }, 300) // Match animation duration

    showSuccess(__('Task moved'), __('"{0}" moved to {1}', [taskSubject, newStatus]))
  } catch (e) {
    console.error('Failed to update task status:', e)
    showError(__('Failed to move task'), __('Could not change task status'))
  }

  draggedTask.value = null
}

// Handle task created from modal
function handleTaskCreated(task: { name: string; subject: string }): void {
  loadProject()
  showSuccess(__('Task created'), __('"{0}" has been added', [task.subject]))
}

// Handle milestone created from modal
function handleMilestoneCreated(milestone: { name: string; milestone_name: string }): void {
  loadProject()
  showSuccess(__('Milestone created'), __('"{0}" has been added', [milestone.milestone_name]))
}

// Handle project deleted
function handleProjectDeleted(): void {
  isDeleteModalOpen.value = false
  router.push('/orga/projects')
}

// Inline description editing
const isEditingDescription = ref(false)
const editDescription = ref('')
const isSavingDescription = ref(false)

function startEditDescription(): void {
  editDescription.value = project.value?.description || ''
  isEditingDescription.value = true
}

function cancelEditDescription(): void {
  isEditingDescription.value = false
}

async function saveDescription(): Promise<void> {
  if (!project.value || isSavingDescription.value) return
  isSavingDescription.value = true
  try {
    await updateProject(project.value.name, { description: editDescription.value })
    project.value.description = editDescription.value
    isEditingDescription.value = false
    showSuccess(__('Description updated'), __('Project description has been saved.'))
  } catch (e) {
    console.error('Failed to update description:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save description.'))
  } finally {
    isSavingDescription.value = false
  }
}

// Inline project title editing
const isEditingTitle = ref(false)
const editTitle = ref('')
const isSavingTitle = ref(false)
const titleInputRef = ref<HTMLInputElement | null>(null)

function startEditTitle(): void {
  editTitle.value = project.value?.project_name || ''
  isEditingTitle.value = true
  nextTick(() => titleInputRef.value?.focus())
}

function cancelEditTitle(): void {
  isEditingTitle.value = false
}

async function saveTitle(): Promise<void> {
  if (!project.value || isSavingTitle.value) return
  const trimmed = editTitle.value.trim()
  if (!trimmed) return cancelEditTitle()
  if (trimmed === project.value.project_name) return cancelEditTitle()
  isSavingTitle.value = true
  try {
    await updateProject(project.value.name, { project_name: trimmed })
    project.value.project_name = trimmed
    isEditingTitle.value = false
    showSuccess(__('Title updated'), __('Project title has been saved.'))
  } catch (e) {
    console.error('Failed to update title:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save title.'))
  } finally {
    isSavingTitle.value = false
  }
}

// Inline budget editing
const isEditingBudget = ref(false)
const editBudget = ref<number | null>(null)
const isSavingBudget = ref(false)
const budgetInputRef = ref<HTMLInputElement | null>(null)

function startEditBudget(): void {
  editBudget.value = project.value?.budget ?? null
  isEditingBudget.value = true
  nextTick(() => budgetInputRef.value?.focus())
}

function cancelEditBudget(): void {
  isEditingBudget.value = false
}

async function saveBudget(): Promise<void> {
  if (!project.value || isSavingBudget.value) return
  const val = editBudget.value && editBudget.value > 0 ? editBudget.value : 0
  if (val === (project.value.budget || 0)) return cancelEditBudget()
  isSavingBudget.value = true
  try {
    await updateProject(project.value.name, { budget: val })
    project.value.budget = val
    isEditingBudget.value = false
    showSuccess(__('Budget updated'), __('Project budget has been saved.'))
  } catch (e) {
    console.error('Failed to update budget:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save budget.'))
  } finally {
    isSavingBudget.value = false
  }
}

// Inline project date editing
const isEditingStartDate = ref(false)
const editStartDate = ref('')
const isSavingStartDate = ref(false)
const startDateInputRef = ref<HTMLInputElement | null>(null)

const isEditingEndDate = ref(false)
const editEndDate = ref('')
const isSavingEndDate = ref(false)
const endDateInputRef = ref<HTMLInputElement | null>(null)

function startEditStartDate(): void {
  editStartDate.value = project.value?.start_date || ''
  isEditingStartDate.value = true
  nextTick(() => startDateInputRef.value?.focus())
}

function cancelEditStartDate(): void {
  isEditingStartDate.value = false
}

async function saveStartDate(): Promise<void> {
  if (!project.value || isSavingStartDate.value) return
  if (editStartDate.value === (project.value.start_date || '')) return cancelEditStartDate()
  isSavingStartDate.value = true
  try {
    await updateProject(project.value.name, { start_date: editStartDate.value || null } as Partial<OrgaProject>)
    project.value.start_date = editStartDate.value || undefined
    isEditingStartDate.value = false
    showSuccess(__('Start date updated'), __('Project start date has been saved.'))
  } catch (e) {
    console.error('Failed to update start date:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save start date.'))
  } finally {
    isSavingStartDate.value = false
  }
}

function startEditEndDate(): void {
  editEndDate.value = project.value?.end_date || ''
  isEditingEndDate.value = true
  nextTick(() => endDateInputRef.value?.focus())
}

function cancelEditEndDate(): void {
  isEditingEndDate.value = false
}

async function saveEndDate(): Promise<void> {
  if (!project.value || isSavingEndDate.value) return
  if (editEndDate.value === (project.value.end_date || '')) return cancelEditEndDate()
  isSavingEndDate.value = true
  try {
    await updateProject(project.value.name, { end_date: editEndDate.value || null } as Partial<OrgaProject>)
    project.value.end_date = editEndDate.value || undefined
    isEditingEndDate.value = false
    showSuccess(__('End date updated'), __('Project end date has been saved.'))
  } catch (e) {
    console.error('Failed to update end date:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save end date.'))
  } finally {
    isSavingEndDate.value = false
  }
}

// Inline status editing
const showStatusDropdown = ref(false)
const isSavingStatus = ref(false)
const statusDropdownRef = ref<HTMLElement | null>(null)

const projectStatusOptions: Array<{ value: string; icon: string; color: string }> = [
  { value: 'Planning', icon: 'fa-compass-drafting', color: 'text-slate-600 dark:text-slate-400' },
  { value: 'Active', icon: 'fa-play', color: 'text-green-600 dark:text-green-400' },
  { value: 'On Hold', icon: 'fa-pause', color: 'text-yellow-600 dark:text-yellow-400' },
  { value: 'Completed', icon: 'fa-circle-check', color: 'text-green-600 dark:text-green-400' },
  { value: 'Cancelled', icon: 'fa-ban', color: 'text-gray-500 dark:text-gray-400' }
]

function toggleStatusDropdown(): void {
  showStatusDropdown.value = !showStatusDropdown.value
}

async function changeProjectStatus(newStatus: string): Promise<void> {
  if (!project.value || isSavingStatus.value || newStatus === project.value.status) {
    showStatusDropdown.value = false
    return
  }
  isSavingStatus.value = true
  try {
    await updateProject(project.value.name, { status: newStatus } as Partial<OrgaProject>)
    project.value.status = newStatus as OrgaProject['status']
    showStatusDropdown.value = false
    showSuccess(__('Status updated'), __('Project status changed to {0}.', [newStatus]))
  } catch (e) {
    console.error('Failed to update status:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not update project status.'))
  } finally {
    isSavingStatus.value = false
  }
}

function handleStatusClickOutside(e: MouseEvent): void {
  if (statusDropdownRef.value && !statusDropdownRef.value.contains(e.target as Node)) {
    showStatusDropdown.value = false
  }
  if (typeDropdownRef.value && !typeDropdownRef.value.contains(e.target as Node)) {
    showTypeDropdown.value = false
  }
  if (depModeDropdownRef.value && !depModeDropdownRef.value.contains(e.target as Node)) {
    showDepModeDropdown.value = false
  }
}

// Inline project type editing
const showTypeDropdown = ref(false)
const isSavingType = ref(false)
const typeDropdownRef = ref<HTMLElement | null>(null)

const projectTypeOptions: Array<{ value: string; icon: string; color: string }> = [
  { value: 'Internal', icon: 'fa-building', color: 'text-blue-600 dark:text-blue-400' },
  { value: 'External', icon: 'fa-arrow-up-right-from-square', color: 'text-green-600 dark:text-green-400' },
  { value: 'Maintenance', icon: 'fa-wrench', color: 'text-yellow-600 dark:text-yellow-400' },
  { value: 'Research', icon: 'fa-flask', color: 'text-purple-600 dark:text-purple-400' }
]

function toggleTypeDropdown(): void {
  showTypeDropdown.value = !showTypeDropdown.value
}

async function changeProjectType(newType: string): Promise<void> {
  if (!project.value || isSavingType.value || newType === project.value.project_type) {
    showTypeDropdown.value = false
    return
  }
  isSavingType.value = true
  try {
    await updateProject(project.value.name, { project_type: newType } as Partial<OrgaProject>)
    project.value.project_type = newType as OrgaProject['project_type']
    showTypeDropdown.value = false
    showSuccess(__('Type updated'), __('Project type changed to {0}.', [newType]))
  } catch (e) {
    console.error('Failed to update type:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not update project type.'))
  } finally {
    isSavingType.value = false
  }
}

// Dependency mode
const showDepModeDropdown = ref(false)
const isSavingDepMode = ref(false)
const depModeDropdownRef = ref<HTMLElement | null>(null)

const dependencyModeOptions = computed<Array<{ value: string; icon: string; description: string }>>(() => [
  { value: 'Strict', icon: 'fa-link', description: __('Auto-shift dependents when dates change') },
  { value: 'Flexible', icon: 'fa-arrows-left-right', description: __('Preview cascade before applying') },
  { value: 'Off', icon: 'fa-link-slash', description: __('Dependencies are informational only') }
])

const currentDepMode = computed(() => project.value?.dependency_mode || 'Flexible')

const depModeIcon = computed(() => {
  const opt = dependencyModeOptions.value.find(o => o.value === currentDepMode.value)
  return opt?.icon || 'fa-arrows-left-right'
})

async function changeDependencyMode(mode: string): Promise<void> {
  if (!project.value || isSavingDepMode.value || mode === currentDepMode.value) {
    showDepModeDropdown.value = false
    return
  }
  isSavingDepMode.value = true
  try {
    await updateProject(project.value.name, { dependency_mode: mode } as Partial<OrgaProject>)
    project.value.dependency_mode = mode as OrgaProject['dependency_mode']
    showDepModeDropdown.value = false
    showSuccess(__('Dependency mode updated'), __('Scheduling set to {0}.', [mode]))
  } catch (e) {
    console.error('Failed to update dependency mode:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not update dependency mode.'))
  } finally {
    isSavingDepMode.value = false
  }
}

// Auto-Trail Start default toggle
const isSavingAutoTrail = ref(false)
const autoTrailDefault = computed(() => !!project.value?.auto_trail_start_default)

async function toggleAutoTrailDefault(): Promise<void> {
  if (!project.value || isSavingAutoTrail.value) return
  isSavingAutoTrail.value = true
  const newVal = autoTrailDefault.value ? 0 : 1
  try {
    await updateProject(project.value.name, { auto_trail_start_default: newVal } as Partial<OrgaProject>)
    project.value.auto_trail_start_default = newVal
    showSuccess(__('Auto-Trail updated'), newVal ? __('New tasks will auto-trail by default.') : __('Auto-trail default disabled.'))
  } catch (e) {
    console.error('Failed to update auto-trail default:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not update setting.'))
  } finally {
    isSavingAutoTrail.value = false
  }
}

// Inline milestone name editing
const isEditingMilestoneName = ref(false)
const editMilestoneName = ref('')
const isSavingMilestoneName = ref(false)

function startEditMilestoneName(): void {
  editMilestoneName.value = selectedMilestone.value?.subject || ''
  isEditingMilestoneName.value = true
}

function cancelEditMilestoneName(): void {
  isEditingMilestoneName.value = false
}

async function saveMilestoneName(): Promise<void> {
  if (!selectedMilestone.value || isSavingMilestoneName.value) return
  const trimmed = editMilestoneName.value.trim()
  if (!trimmed) return
  isSavingMilestoneName.value = true
  try {
    await updateMilestone(selectedMilestone.value.name, { milestone_name: trimmed })
    await loadProject()
    refreshSelectedMilestone()
    isEditingMilestoneName.value = false
    showSuccess(__('Milestone updated'), __('Milestone name has been saved.'))
  } catch (e) {
    console.error('Failed to update milestone name:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save milestone name.'))
  } finally {
    isSavingMilestoneName.value = false
  }
}

// Inline milestone description editing
const isEditingMilestoneDesc = ref(false)
const editMilestoneDesc = ref('')
const isSavingMilestoneDesc = ref(false)

function startEditMilestoneDesc(): void {
  editMilestoneDesc.value = selectedMilestone.value?.description || ''
  isEditingMilestoneDesc.value = true
}

function cancelEditMilestoneDesc(): void {
  isEditingMilestoneDesc.value = false
}

async function saveMilestoneDesc(): Promise<void> {
  if (!selectedMilestone.value || isSavingMilestoneDesc.value) return
  isSavingMilestoneDesc.value = true
  try {
    await updateMilestone(selectedMilestone.value.name, { description: editMilestoneDesc.value })
    await loadProject()
    refreshSelectedMilestone()
    isEditingMilestoneDesc.value = false
    showSuccess(__('Description updated'), __('Milestone description has been saved.'))
  } catch (e) {
    console.error('Failed to update milestone description:', e)
    showError(__('Update failed'), (e as Error).message || __('Could not save description.'))
  } finally {
    isSavingMilestoneDesc.value = false
  }
}

// Milestone task linking
const isLinkingTask = ref(false)
const linkTaskSearch = ref('')

// Tasks available to link (not already linked to this milestone)
const linkableTasks = computed<OrgaTask[]>(() => {
  if (!selectedMilestone.value) return []
  const search = linkTaskSearch.value.toLowerCase()
  return tasks.value.filter(t =>
    t.milestone !== selectedMilestone.value?.name &&
    t.status !== 'Cancelled' &&
    (!search || t.subject.toLowerCase().includes(search))
  )
})

async function linkTaskToMilestone(task: OrgaTask): Promise<void> {
  if (!selectedMilestone.value) return
  try {
    await updateTask(task.name, { milestone: selectedMilestone.value.name })
    await loadProject()
    refreshSelectedMilestone()
    isLinkingTask.value = false
    linkTaskSearch.value = ''
    showSuccess(__('Task linked'), __('"{0}" linked to milestone', [task.subject]))
  } catch (e) {
    console.error('Failed to link task:', e)
    showError(__('Link failed'), __('Could not link task to milestone'))
  }
}

async function unlinkTaskFromMilestone(task: OrgaTask): Promise<void> {
  if (!selectedMilestone.value) return
  try {
    await updateTask(task.name, { milestone: '' })
    await loadProject()
    refreshSelectedMilestone()
    showSuccess(__('Task unlinked'), __('"{0}" removed from milestone', [task.subject]))
  } catch (e) {
    console.error('Failed to unlink task:', e)
    showError(__('Unlink failed'), __('Could not remove task from milestone'))
  }
}

// Quick-add from Kanban columns removed - users should use the top bar "+ Add Task" button

// Convert dependency type from full form to short form
function toShortDependencyType(fullType: string): DependencyType {
  const map: Record<string, DependencyType> = {
    'Finish to Start': 'FS',
    'Start to Start': 'SS',
    'Finish to Finish': 'FF',
    'Start to Finish': 'SF'
  }
  return map[fullType] || 'FS'
}

// Grouped documents: project-level + task-level
const groupedDocuments = computed(() => {
  const projectFiles = documents.value
  const byTask: Record<string, { taskSubject: string; files: ProjectDocument[] }> = {}

  for (const file of taskAttachments.value) {
    const taskName = file.attached_to_name
    if (!taskName) continue
    if (!byTask[taskName]) {
      const task = tasks.value.find(t => t.name === taskName)
      byTask[taskName] = {
        taskSubject: task?.subject || taskName,
        files: []
      }
    }
    byTask[taskName].files.push(file)
  }

  return {
    project: projectFiles,
    byTask,
    totalCount: projectFiles.length + taskAttachments.value.length
  }
})

const documentSummary = computed(() => {
  const pCount = groupedDocuments.value.project.length
  const tCount = taskAttachments.value.length
  const parts: string[] = []
  if (pCount > 0) parts.push(__('{0} project', [pCount]))
  if (tCount > 0) parts.push(__('{0} task', [tCount]))
  const total = pCount + tCount
  if (parts.length === 0) return ''
  return parts.join(', ') + ' ' + (total === 1 ? __('file') : __('files'))
})

function getDocIcon(doc: ProjectDocument): string {
  const name = doc.file_name || ''
  const type = doc.file_type || ''
  if (type.includes('pdf') || name.endsWith('.pdf')) return 'fa-file-pdf text-red-500'
  if (type.includes('image') || /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(name)) return 'fa-file-image text-blue-500'
  if (type.includes('word') || /\.(doc|docx)$/i.test(name)) return 'fa-file-word text-blue-600'
  if (type.includes('excel') || /\.(xls|xlsx|csv)$/i.test(name)) return 'fa-file-excel text-green-600'
  if (/\.(dwg|dxf)$/i.test(name)) return 'fa-drafting-compass text-orange-500'
  if (/\.(zip|rar|7z|tar|gz)$/i.test(name)) return 'fa-file-zipper text-yellow-600'
  return 'fa-file text-gray-400'
}

function toggleDocDrawer(): void {
  isDocDrawerOpen.value = !isDocDrawerOpen.value
}

async function handleProjectFileUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  if (!input.files?.length || !project.value) return

  isUploadingProjectFile.value = true
  projectUploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', input.files[0])
    formData.append('doctype', 'Orga Project')
    formData.append('docname', project.value.name)
    formData.append('is_private', '0')

    const xhr = new XMLHttpRequest()
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        projectUploadProgress.value = Math.round((e.loaded / e.total) * 100)
      }
    })

    await new Promise<void>((resolve, reject) => {
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      }
      xhr.onerror = () => reject(new Error('Upload failed'))
      xhr.open('POST', '/api/method/upload_file')
      xhr.setRequestHeader('X-Frappe-CSRF-Token', (window as unknown as { frappe?: { csrf_token?: string } }).frappe?.csrf_token || '')
      xhr.send(formData)
    })

    await loadProject()
    showSuccess(__('File uploaded'), __('Document attached to project'))
  } catch (e) {
    console.error('Failed to upload project file:', e)
    showError(__('Upload failed'), __('Could not attach file to project'))
  } finally {
    isUploadingProjectFile.value = false
    projectUploadProgress.value = 0
    input.value = ''
  }
}

// Load project data
// Only show full-page loading spinner on initial load, not on data refreshes.
// Showing the spinner on refresh destroys the TaskManager (via v-if/v-else-if),
// which resets tab state and other component state.
async function loadProject(): Promise<void> {
  const isInitialLoad = !project.value
  if (isInitialLoad) {
    isLoading.value = true
  }
  loadError.value = null

  try {
    const [projectData, kanbanData, depsData, contactData] = await Promise.all([
      getProject(projectId.value),
      getTasksByStatus(projectId.value),
      apiCall<ProjectDependencyEdge[]>('orga.orga.api.project.get_project_dependencies', { project_name: projectId.value }),
      getContacts({ status: 'Active' })
    ])

    project.value = projectData.project
    tasks.value = projectData.tasks || []
    milestones.value = projectData.milestones || []
    teamMembers.value = projectData.team_members || []
    contacts.value = (contactData as { resources: OrgaContact[]; total: number })?.resources || []
    documents.value = projectData.documents || []
    taskAttachments.value = projectData.task_attachments || []
    tasksByStatus.value = kanbanData || {}
    projectDependencies.value = depsData || []

    // Load critical path data (non-blocking — don't hold up the main load)
    getCriticalPath(projectId.value)
      .then(cpData => { criticalPathTasks.value = cpData?.critical_tasks || [] })
      .catch(() => { criticalPathTasks.value = [] })

    // After data refresh, update selectedTask with the fresh object from the new tasks array
    // so the TaskManager receives updated props without remounting
    refreshSelectedTask()

  } catch (e) {
    console.error('Failed to load project:', e)
    loadError.value = (e as Error).message || __('Failed to load project')
  } finally {
    isLoading.value = false
  }
}

// Watch for route changes
watch(() => route.params.id, () => {
  if (route.params.id) {
    loadProject()
  }
})

// Watch for query param changes (e.g. navigating from Activity page to select a task/milestone)
watch(() => route.query, (newQuery) => {
  if (!newQuery) return
  const taskQuery = newQuery.task as string | undefined
  const milestoneQuery = newQuery.milestone as string | undefined
  if (taskQuery) {
    const task = ganttTasks.value.find(t => t.name === taskQuery) || tasks.value.find(t => t.name === taskQuery)
    if (task) {
      selectedTask.value = task
      selectedMilestone.value = null
      showManager.value = true
      view.value = 'gantt'
    }
    router.replace({ path: route.path, query: {} })
  } else if (milestoneQuery) {
    const milestone = ganttMilestones.value.find(m => m.name === milestoneQuery)
    if (milestone) {
      selectedMilestone.value = milestone
      selectedTask.value = null
      showManager.value = true
      view.value = 'gantt'
    }
    router.replace({ path: route.path, query: {} })
  }
})

// Register keyboard shortcuts
useProjectShortcuts({
  onAddTask: () => {
    initialTaskStatus.value = 'Open'
    isTaskModalOpen.value = true
  },
  onAddMilestone: () => {
    isMilestoneModalOpen.value = true
  }
})

onMounted(async () => {
  await loadProject()
  // Auto-select task or milestone from query params (e.g. navigated from Activity page)
  const taskQuery = route.query.task as string | undefined
  const milestoneQuery = route.query.milestone as string | undefined
  if (taskQuery) {
    const task = ganttTasks.value.find(t => t.name === taskQuery) || tasks.value.find(t => t.name === taskQuery)
    if (task) {
      selectedTask.value = task
      selectedMilestone.value = null
      showManager.value = true
      view.value = 'gantt'
    }
    // Clear query param to avoid re-selecting on subsequent navigations
    router.replace({ path: route.path, query: {} })
  } else if (milestoneQuery) {
    const milestone = ganttMilestones.value.find(m => m.name === milestoneQuery)
    if (milestone) {
      selectedMilestone.value = milestone
      selectedTask.value = null
      showManager.value = true
      view.value = 'gantt'
    }
    router.replace({ path: route.path, query: {} })
  }
  document.addEventListener('click', handleStatusClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleStatusClickOutside)
})
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-600 dark:text-gray-400">{{ __('Loading project...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="flex-1 flex items-center justify-center p-6">
      <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center">
        <i class="fa-solid fa-exclamation-triangle text-red-500 dark:text-red-400 text-3xl mb-3"></i>
        <h3 class="text-red-800 dark:text-red-200 font-medium mb-2">{{ __('Error loading project') }}</h3>
        <p class="text-red-600 dark:text-red-400 text-sm mb-4">{{ loadError }}</p>
        <button
          @click="loadProject"
          class="px-4 py-2 bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/70"
        >
          {{ __('Try Again') }}
        </button>
      </div>
    </div>

    <!-- Project Content -->
    <template v-else-if="project">
      <!-- Top Header -->
      <div class="flex-shrink-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <!-- Breadcrumb - Hidden on mobile -->
        <div class="hidden sm:block px-4 pt-3 pb-2 border-b border-gray-100 dark:border-gray-800">
          <Breadcrumb
            :items="[
              { label: __('Projects'), to: '/orga/projects' },
              { label: project.project_name, current: true }
            ]"
          />
        </div>

        <!-- Header Row - Stack on mobile -->
        <div class="p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div class="flex items-center gap-3 sm:gap-4">
            <button
              @click="router.back()"
              class="min-h-[44px] min-w-[44px] flex items-center justify-center text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              :title="__('Go back')"
            >
              <i class="fa-solid fa-arrow-left text-lg"></i>
            </button>
            <div class="min-w-0 flex-1">
              <input
                v-if="isEditingTitle"
                v-model="editTitle"
                @keydown.enter="saveTitle"
                @keydown.escape="cancelEditTitle"
                @blur="saveTitle"
                ref="titleInputRef"
                class="text-h3 sm:text-h2 text-gray-800 dark:text-gray-100 m-0 w-full bg-transparent border-b-2 border-orga-500 outline-none"
                :disabled="isSavingTitle"
              />
              <h1
                v-else
                @click="startEditTitle"
                class="text-h3 sm:text-h2 text-gray-800 dark:text-gray-100 m-0 truncate cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
                :title="__('Click to edit title')"
              >{{ project.project_name }}</h1>
              <p class="text-caption sm:text-body text-gray-600 dark:text-gray-400 m-0 truncate">{{ project.project_code }} · {{ project.project_type }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <!-- View Toggle - Icons only on mobile -->
            <div class="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
              <button
                @click="view = 'gantt'"
                :class="[
                  'min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2',
                  view === 'gantt' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                ]"
                :title="__('Gantt View')"
              >
                <i class="fa-solid fa-bars-progress"></i>
                <span class="hidden sm:inline">{{ __('Gantt') }}</span>
              </button>
              <button
                @click="view = 'kanban'"
                :class="[
                  'min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2',
                  view === 'kanban' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                ]"
                :title="__('Kanban View')"
              >
                <i class="fa-solid fa-table-columns"></i>
                <span class="hidden sm:inline">{{ __('Kanban') }}</span>
              </button>
              <button
                @click="view = 'list'"
                :class="[
                  'min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2',
                  view === 'list' ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                ]"
                :title="__('List View')"
              >
                <i class="fa-solid fa-list"></i>
                <span class="hidden sm:inline">{{ __('List') }}</span>
              </button>
            </div>

            <!-- Action Buttons - Icons only on mobile -->
            <div class="flex gap-2 ml-2 sm:ml-4">
              <button
                @click="isTaskModalOpen = true"
                class="min-h-[44px] min-w-[44px] sm:min-w-0 px-3 py-2 sm:py-1.5 text-sm font-medium text-white bg-orga-500 rounded-lg hover:bg-orga-600 flex items-center justify-center gap-2"
                :title="__('Add Task (Shift+T)')"
              >
                <i class="fa-solid fa-plus"></i>
                <span class="hidden sm:inline">{{ __('Add Task') }}</span>
              </button>
              <button
                @click="isMilestoneModalOpen = true"
                class="min-h-[44px] min-w-[44px] sm:min-w-0 px-3 py-2 sm:py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center gap-2"
                :title="__('Add Milestone (Shift+M)')"
              >
                <i class="fa-solid fa-flag"></i>
                <span class="hidden md:inline">{{ __('Add Milestone') }}</span>
              </button>
            </div>

            <!-- Dependency Mode Selector -->
            <div ref="depModeDropdownRef" class="relative ml-2 sm:ml-4">
              <button
                @click="showDepModeDropdown = !showDepModeDropdown"
                class="min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 border bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                :title="__('Dependency Mode: {0}', [currentDepMode])"
              >
                <i :class="['fa-solid', depModeIcon]"></i>
                <span class="hidden lg:inline">{{ currentDepMode }}</span>
              </button>
              <div
                v-if="showDepModeDropdown"
                class="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-gray-950/50 z-50 py-1"
              >
                <button
                  v-for="opt in dependencyModeOptions"
                  :key="opt.value"
                  @click="changeDependencyMode(opt.value)"
                  :class="[
                    'w-full text-left px-3 py-2 text-sm flex items-start gap-2 transition-colors',
                    opt.value === currentDepMode
                      ? 'bg-orga-50 dark:bg-orga-900/20 text-orga-700 dark:text-orga-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  ]"
                >
                  <i :class="['fa-solid', opt.icon, 'mt-0.5 w-4 text-center']"></i>
                  <div>
                    <div class="font-medium">{{ opt.value }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ opt.description }}</div>
                  </div>
                  <i v-if="opt.value === currentDepMode" class="fa-solid fa-check ml-auto mt-0.5 text-orga-500"></i>
                </button>
              </div>
            </div>

            <!-- Panel Toggles - Icons only on mobile -->
            <div class="flex gap-1 ml-2 sm:ml-4">
              <button
                @click="showDetails = !showDetails"
                :class="[
                  'min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 border',
                  showDetails
                    ? 'bg-orga-500 text-white border-orga-500'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                ]"
                :title="__('Toggle Details Panel')"
              >
                <i class="fa-solid fa-circle-info"></i>
                <span class="hidden lg:inline">{{ __('Details') }}</span>
              </button>
              <button
                @click="showManager = !showManager"
                :class="[
                  'min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 border',
                  showManager
                    ? 'bg-orga-500 text-white border-orga-500'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                ]"
                :title="__('Toggle Manager Panel')"
              >
                <i class="fa-solid fa-sliders"></i>
                <span class="hidden lg:inline">{{ __('Manager') }}</span>
              </button>
            </div>

            <!-- Settings Menu -->
            <div class="relative ml-2 sm:ml-4">
              <button
                @click="showSettingsMenu = !showSettingsMenu"
                class="min-h-[44px] min-w-[44px] sm:min-w-0 px-2 sm:px-3 py-2 sm:py-1.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center border bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                :title="__('Project settings')"
              >
                <i class="fa-solid fa-gear"></i>
              </button>
              <!-- Dropdown -->
              <div
                v-if="showSettingsMenu"
                class="absolute right-0 top-full mt-1 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 py-1"
              >
                <!-- Auto-Trail Start Default -->
                <button
                  @click="toggleAutoTrailDefault"
                  :disabled="isSavingAutoTrail"
                  class="w-full flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                  :class="autoTrailDefault
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300'"
                >
                  <i class="fa-solid fa-forward text-xs w-4 text-center"></i>
                  {{ __('Auto-Trail Start') }}
                  <i v-if="autoTrailDefault" class="fa-solid fa-check ml-auto text-xs text-blue-500"></i>
                </button>
                <div class="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                <button
                  @click="showSettingsMenu = false; isSaveTemplateModalOpen = true"
                  class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                >
                  <i class="fa-solid fa-copy text-xs w-4 text-center"></i>
                  {{ __('Save as Template') }}
                </button>
                <div class="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                <button
                  @click="showSettingsMenu = false; isDeleteModalOpen = true"
                  class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors text-left"
                >
                  <i class="fa-solid fa-trash text-xs w-4 text-center"></i>
                  {{ __('Delete Project') }}
                </button>
              </div>
              <!-- Click-outside overlay -->
              <div
                v-if="showSettingsMenu"
                class="fixed inset-0 z-40"
                @click="showSettingsMenu = false"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Main Content (Kanban/List) -->
        <div class="flex-1 overflow-auto p-4">
          <!-- Kanban View - Responsive: 1 col mobile, 2 cols tablet, 4 cols desktop -->
          <div v-if="view === 'kanban'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div
              v-for="column in columns"
              :key="column.id"
              :class="[
                'kanban-column rounded-xl p-4 min-h-[400px] transition-all duration-200',
                'border border-gray-200 dark:border-gray-700',
                'bg-white dark:bg-gray-800',
                'shadow-sm dark:shadow-lg dark:shadow-black/30',
                column.color,
                dragOverColumn === column.id && draggedTask && draggedTask.status !== column.id && 'drop-target'
              ]"
              @dragover="onDragOver($event, column.id)"
              @dragleave="onDragLeave($event, column.id)"
              @drop="onDrop($event, column.id)"
            >
              <div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
                <h3 class="font-semibold text-gray-900 dark:text-gray-100 m-0 text-sm">{{ column.title }}</h3>
                <span class="bg-gray-100 dark:bg-gray-700 px-2.5 py-1 rounded-full text-xs font-semibold text-gray-700 dark:text-gray-200">
                  {{ getColumnTasks(column.id).length }}
                </span>
              </div>
              <div class="space-y-2">
                <div
                  v-for="task in getColumnTasks(column.id)"
                  :key="task.name"
                  draggable="true"
                  tabindex="0"
                  @dragstart="onDragStart($event, task)"
                  @dragend="onDragEnd"
                  @click="selectTask(task)"
                  @keydown.enter="selectTask(task)"
                  @keydown.space.prevent="selectTask(task)"
                  :class="[
                    'kanban-card rounded-lg p-3 cursor-grab transition-all duration-200',
                    'bg-white dark:bg-gray-700',
                    'border border-gray-200 dark:border-gray-600',
                    'hover:shadow-md dark:hover:shadow-lg dark:hover:shadow-black/30',
                    'hover:border-gray-300 dark:hover:border-gray-600',
                    selectedTask?.name === task.name
                      ? 'ring-2 ring-orga-300 card-selected'
                      : task.status === 'Open' ? 'card-open'
                      : task.status === 'In Progress' ? 'card-in-progress'
                      : task.status === 'Review' ? 'card-review'
                      : task.status === 'Completed' ? 'card-completed'
                      : 'border-l-4 border-l-gray-300',
                    draggedTask?.name === task.name && 'dragging',
                    justDroppedTask === task.name && 'just-dropped',
                    task.is_blocked && 'opacity-60'
                  ]"
                  :title="task.is_blocked ? getBlockedByTooltip(task.name) : undefined"
                >
                  <div class="flex items-start justify-between mb-2">
                    <h4 class="font-medium text-gray-900 dark:text-gray-100 text-sm leading-tight m-0 pr-2">{{ task.subject }}</h4>
                    <div class="flex items-center gap-1 shrink-0">
                      <StatusBadge v-if="task.is_blocked" status="Blocked" type="blocked" size="sm" :title="getBlockedByTooltip(task.name)" />
                      <StatusBadge :status="task.priority" type="priority" size="sm" :show-icon="false" />
                    </div>
                  </div>
                  <div v-if="task.due_date" class="text-xs text-gray-600 dark:text-gray-300 mb-2">
                    <i class="fa-regular fa-calendar mr-1 text-gray-500 dark:text-gray-400"></i>
                    {{ formatDate(task.due_date) }}
                  </div>
                  <div class="flex items-center justify-between">
                    <div v-if="task.assigned_to_name" class="flex items-center gap-1">
                      <UserAvatar :name="task.assigned_to_name" :image="task.assigned_to_image" size="xs" color="orga" />
                      <span class="text-[10px] text-gray-600 dark:text-gray-400">{{ task.assigned_to_name }}</span>
                    </div>
                    <div v-else class="text-[10px] text-gray-600 dark:text-gray-400">{{ __('Unassigned') }}</div>
                    <div v-if="task.progress" class="text-[10px] text-gray-600 dark:text-gray-400">{{ task.progress }}%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- List View - Responsive with horizontal scroll on mobile -->
          <div v-if="view === 'list'" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 max-h-[calc(100vh-280px)] overflow-auto">
            <table class="w-full min-w-[600px]">
              <thead class="bg-gray-50 dark:bg-gray-900 list-header">
                <tr>
                  <th class="text-left p-3 text-overline text-gray-600 dark:text-gray-400">{{ __('Task') }}</th>
                  <th class="text-left p-3 text-overline text-gray-600 dark:text-gray-400">{{ __('Status') }}</th>
                  <th class="text-left p-3 text-overline text-gray-600 dark:text-gray-400 hidden sm:table-cell">{{ __('Priority') }}</th>
                  <th class="text-left p-3 text-overline text-gray-600 dark:text-gray-400 hidden md:table-cell">{{ __('Assignee') }}</th>
                  <th class="text-left p-3 text-overline text-gray-600 dark:text-gray-400">{{ __('Due Date') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="task in tasks"
                  :key="task.name"
                  @click="selectTask(task)"
                  tabindex="0"
                  :class="[
                    'task-row border-b border-gray-100 dark:border-gray-700',
                    selectedTask?.name === task.name ? 'bg-orga-50 dark:bg-orga-900/20' : '',
                    task.is_blocked && 'opacity-60'
                  ]"
                  :title="task.is_blocked ? getBlockedByTooltip(task.name) : undefined"
                  @keydown.enter="selectTask(task)"
                  @keydown.space.prevent="selectTask(task)"
                >
                  <td class="p-3">
                    <div class="text-subtitle text-gray-800 dark:text-gray-100">{{ task.subject }}</div>
                    <div class="text-caption text-gray-600 dark:text-gray-400">{{ task.name }}</div>
                  </td>
                  <td class="p-3">
                    <div class="flex items-center gap-1.5">
                      <StatusBadge :status="task.status" type="task" size="sm" />
                      <StatusBadge v-if="task.is_blocked" status="Blocked" type="blocked" size="sm" :title="getBlockedByTooltip(task.name)" />
                    </div>
                  </td>
                  <td class="p-3 hidden sm:table-cell">
                    <StatusBadge :status="task.priority" type="priority" size="sm" />
                  </td>
                  <td class="p-3 hidden md:table-cell">
                    <div v-if="task.assigned_to_name" class="flex items-center gap-2">
                      <UserAvatar :name="task.assigned_to_name" :image="task.assigned_to_image" size="xs" color="orga" />
                      <span class="text-sm text-gray-700 dark:text-gray-300">{{ task.assigned_to_name }}</span>
                    </div>
                    <span v-else class="text-gray-600 dark:text-gray-400 text-sm">{{ __('Unassigned') }}</span>
                  </td>
                  <td class="p-3 text-sm text-gray-700 dark:text-gray-300">
                    {{ task.due_date ? formatDate(task.due_date) : '-' }}
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Empty State for List View -->
            <EmptyState
              v-if="tasks.length === 0"
              icon="fa-list-check"
              :title="__('No tasks yet')"
              :description="__('Create your first task to start tracking work on this project.')"
              :action-label="__('+ Create Task')"
              @action="isTaskModalOpen = true"
              size="md"
            />
          </div>

          <!-- Gantt View -->
          <div v-if="view === 'gantt'" class="h-full">
            <GanttChart
              :tasks="ganttItems"
              :start-date="project?.start_date"
              :end-date="project?.end_date"
              :selected-task-id="selectedTask?.name"
              :just-reordered-id="justReorderedTaskId"
              :critical-path-tasks="criticalPathTasks"
              @select="handleGanttSelect"
              @update-dates="handleGanttDatesUpdate"
              @reorder-item="handleItemReorder"
              @update-milestone-date="handleMilestoneDateUpdate"
              @create-dependency="handleCreateDependency"
            />
          </div>
        </div>

        <!-- Mobile Manager Panel Backdrop -->
        <div
          v-if="showManager"
          class="fixed inset-0 bg-black/50 z-40 lg:hidden"
          @click="showManager = false"
        ></div>

        <!-- Right Sidebar: Manager Panel - Modal on mobile, sidebar on desktop -->
        <!-- Unified for all views (Kanban, List, Gantt) -->
        <aside
          v-if="showManager"
          class="fixed inset-y-0 right-0 w-full max-w-sm z-50 lg:relative lg:z-auto lg:w-80 lg:max-w-none bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col flex-shrink-0 overflow-hidden transition-all"
        >
          <TaskManager
            v-if="selectedTask"
            :task="selectedTask"
            :columns="columns"
            :all-tasks="view === 'gantt' ? ganttTasks : tasks"
            :contacts="contacts"
            :available-groups="availableTaskGroups"
            :view-type="view"
            :project="view === 'gantt' ? project : undefined"
            :show-cascade-preview="view === 'gantt'"
            @update="loadProject"
            @close="showManager = false"
            @status-change="changeTaskStatus"
            @priority-change="changeTaskPriority"
            @field-update="handleGanttUpdate"
            @navigate="handleGanttNavigate"
            @preview-cascade="handleCascadePreview"
            @apply-cascade="handleCascadeApply"
          />

          <!-- Milestone Detail Panel -->
          <div v-else-if="selectedMilestone" class="flex-1 flex flex-col overflow-hidden">
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
                <i class="fa-solid fa-flag text-indigo-500"></i> {{ __('Milestone') }}
              </h3>
              <button @click="showManager = false; selectedMilestone = null" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4">
              <!-- Title -->
              <div>
                <div v-if="isEditingMilestoneName" class="flex items-center gap-2">
                  <input
                    v-model="editMilestoneName"
                    type="text"
                    maxlength="255"
                    class="flex-1 text-lg font-semibold px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400"
                    @keydown.enter="saveMilestoneName"
                    @keydown.escape="cancelEditMilestoneName"
                  />
                  <button
                    @click="saveMilestoneName"
                    :disabled="isSavingMilestoneName || !editMilestoneName.trim()"
                    class="p-1.5 text-xs text-white bg-orga-500 rounded hover:bg-orga-600 transition-colors disabled:opacity-50"
                  >
                    <i v-if="isSavingMilestoneName" class="fa-solid fa-spinner fa-spin"></i>
                    <i v-else class="fa-solid fa-check"></i>
                  </button>
                  <button
                    @click="cancelEditMilestoneName"
                    :disabled="isSavingMilestoneName"
                    class="p-1.5 text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                  >
                    <i class="fa-solid fa-xmark"></i>
                  </button>
                </div>
                <h4
                  v-else
                  @click="startEditMilestoneName"
                  class="text-lg font-semibold text-gray-800 dark:text-gray-100 cursor-pointer group hover:ring-1 hover:ring-orga-300 dark:hover:ring-orga-600 rounded px-1 -mx-1 transition-all"
                  :title="__('Click to edit milestone name')"
                >
                  {{ selectedMilestone.subject }}
                  <i class="fa-solid fa-pen-to-square text-[10px] text-gray-400 dark:text-gray-500 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
                </h4>
              </div>

              <!-- Status -->
              <div class="flex items-center gap-3">
                <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">{{ __('Status') }}</label>
                <select
                  :value="selectedMilestone.status"
                  @change="handleMilestoneFieldUpdate({ field: 'status', value: ($event.target as HTMLSelectElement).value })"
                  class="flex-1 px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                >
                  <option value="Upcoming">{{ __('Upcoming') }}</option>
                  <option value="In Progress">{{ __('In Progress') }}</option>
                  <option value="Completed">{{ __('Completed') }}</option>
                  <option value="Missed">{{ __('Missed') }}</option>
                </select>
              </div>

              <!-- Due Date -->
              <div class="flex items-center gap-3">
                <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">{{ __('Due Date') }}</label>
                <input
                  type="date"
                  :value="selectedMilestone.due_date"
                  @change="handleMilestoneFieldUpdate({ field: 'due_date', value: ($event.target as HTMLInputElement).value })"
                  class="flex-1 px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                />
              </div>

              <!-- Progress (calculated from linked tasks) -->
              <div>
                <div class="flex items-center gap-3">
                  <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">{{ __('Progress') }}</label>
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all"
                          :class="selectedMilestone.progress === 100 ? 'bg-emerald-500' : selectedMilestone.progress > 0 ? 'bg-indigo-500' : 'bg-gray-300 dark:bg-gray-600'"
                          :style="{ width: `${selectedMilestone.progress || 0}%` }"
                        ></div>
                      </div>
                      <span class="text-sm text-gray-600 dark:text-gray-400 w-10 text-right">{{ selectedMilestone.progress || 0 }}%</span>
                    </div>
                  </div>
                </div>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1 ml-[calc(5rem+0.75rem)]">
                  <template v-if="(selectedMilestone.task_count ?? 0) > 0">
                    {{ __('{0} of {1} linked tasks completed', [tasks.filter(t => t.milestone === selectedMilestone?.name && t.status === 'Completed').length, selectedMilestone.task_count]) }}
                  </template>
                  <template v-else>
                    {{ __('No tasks linked to this milestone') }}
                  </template>
                </p>
              </div>

              <!-- Description -->
              <div>
                <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-2">{{ __('Description') }}</label>
                <!-- Editing mode -->
                <div v-if="isEditingMilestoneDesc">
                  <textarea
                    v-model="editMilestoneDesc"
                    rows="3"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 resize-y"
                    :placeholder="__('Add a milestone description...')"
                    @keydown.escape="cancelEditMilestoneDesc"
                  ></textarea>
                  <div class="flex justify-end gap-2 mt-2">
                    <button
                      @click="cancelEditMilestoneDesc"
                      :disabled="isSavingMilestoneDesc"
                      class="px-2.5 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                    >
                      {{ __('Cancel') }}
                    </button>
                    <button
                      @click="saveMilestoneDesc"
                      :disabled="isSavingMilestoneDesc"
                      class="px-2.5 py-1 text-xs font-medium text-white bg-orga-500 rounded hover:bg-orga-600 transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                      <i v-if="isSavingMilestoneDesc" class="fa-solid fa-spinner fa-spin"></i>
                      {{ isSavingMilestoneDesc ? __('Saving...') : __('Save') }}
                    </button>
                  </div>
                </div>
                <!-- Display mode -->
                <div
                  v-else
                  @click="startEditMilestoneDesc"
                  class="cursor-pointer group"
                  :title="__('Click to edit description')"
                >
                  <p v-if="selectedMilestone.description" class="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 group-hover:ring-1 group-hover:ring-orga-300 dark:group-hover:ring-orga-600 transition-all">
                    {{ selectedMilestone.description }}
                    <i class="fa-solid fa-pen-to-square text-[10px] text-gray-400 dark:text-gray-500 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
                  </p>
                  <p v-else class="text-sm text-gray-400 dark:text-gray-500 italic bg-gray-50 dark:bg-gray-800 rounded-lg p-3 group-hover:ring-1 group-hover:ring-orga-300 dark:group-hover:ring-orga-600 transition-all">
                    {{ __('Click to add description...') }}
                    <i class="fa-solid fa-pen-to-square text-[10px] ml-1 opacity-0 group-hover:opacity-100 transition-opacity"></i>
                  </p>
                </div>
              </div>

              <!-- Linked Tasks -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {{ __('Linked Tasks') }}
                  </label>
                  <button
                    v-if="!isLinkingTask"
                    @click="isLinkingTask = true; linkTaskSearch = ''"
                    class="text-xs text-orga-500 hover:text-orga-600 dark:text-orga-400 dark:hover:text-orga-300 font-medium flex items-center gap-1 transition-colors"
                  >
                    <i class="fa-solid fa-plus text-[10px]"></i> {{ __('Link Task') }}
                  </button>
                  <button
                    v-else
                    @click="isLinkingTask = false; linkTaskSearch = ''"
                    class="text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 font-medium transition-colors"
                  >
                    {{ __('Cancel') }}
                  </button>
                </div>

                <!-- Link task search dropdown -->
                <div v-if="isLinkingTask" class="mb-2">
                  <input
                    v-model="linkTaskSearch"
                    type="text"
                    :placeholder="__('Search tasks to link...')"
                    class="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400"
                  />
                  <div class="mt-1 max-h-40 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                    <div
                      v-for="task in linkableTasks.slice(0, 10)"
                      :key="task.name"
                      @click="linkTaskToMilestone(task)"
                      class="flex items-center gap-2 px-2.5 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                    >
                      <StatusBadge :status="task.status" size="sm" />
                      <span class="text-sm text-gray-700 dark:text-gray-300 truncate flex-1">{{ task.subject }}</span>
                    </div>
                    <p
                      v-if="linkableTasks.length === 0"
                      class="text-xs text-gray-400 dark:text-gray-500 text-center py-3"
                    >
                      {{ linkTaskSearch ? __('No matching tasks found') : __('All tasks are already linked') }}
                    </p>
                  </div>
                </div>

                <!-- Linked task list -->
                <div class="space-y-1">
                  <div
                    v-for="task in tasks.filter(t => t.milestone === selectedMilestone?.name)"
                    :key="task.name"
                    class="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 group transition-colors"
                  >
                    <StatusBadge :status="task.status" size="sm" />
                    <span
                      @click="selectedMilestone = null; selectTask(task)"
                      class="text-sm text-gray-700 dark:text-gray-300 truncate flex-1 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400"
                    >
                      {{ task.subject }}
                    </span>
                    <button
                      @click.stop="unlinkTaskFromMilestone(task)"
                      class="text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                      :title="__('Unlink task from milestone')"
                    >
                      <i class="fa-solid fa-xmark text-xs"></i>
                    </button>
                  </div>
                  <p
                    v-if="tasks.filter(t => t.milestone === selectedMilestone?.name).length === 0 && !isLinkingTask"
                    class="text-sm text-gray-400 dark:text-gray-500 text-center py-3"
                  >
                    {{ __('No tasks linked to this milestone') }}
                  </p>
                </div>
              </div>

              <!-- Completed Date (if completed) -->
              <div v-if="selectedMilestone.completed_date" class="flex items-center gap-3">
                <label class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">{{ __('Completed') }}</label>
                <span class="text-sm text-green-600 dark:text-green-400">{{ formatDate(selectedMilestone.completed_date) }}</span>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="flex-1 flex flex-col">
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
                <i class="fa-solid fa-sliders text-orga-500"></i> {{ __('Manager') }}
              </h3>
              <button @click="showManager = false" class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                <i class="fa-solid fa-xmark"></i>
              </button>
            </div>
            <div class="flex-1 flex items-center justify-center">
              <EmptyState
                icon="fa-hand-pointer"
                :title="__('No task selected')"
                :description="view === 'gantt'
                  ? __('Select a task from the Gantt chart to view and manage its details.')
                  : __('Select a task from the list or Kanban board to view and manage its details.')"
                size="sm"
              />
            </div>
          </div>
        </aside>
      </div>

      <!-- Bottom Bar: Details -->
      <div v-if="showDetails" class="flex-shrink-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <!-- Statistics Row -->
        <div class="flex items-center gap-4 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/50">
          <!-- Progress -->
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-md bg-orga-50 dark:bg-orga-900/30 flex items-center justify-center">
              <i class="fa-solid fa-chart-pie text-orga-500 text-xs"></i>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Progress') }}</span>
              <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ progressPercentage }}%</span>
            </div>
            <div class="w-20 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden hidden sm:block">
              <div class="h-full bg-orga-500 rounded-full transition-all" :style="{ width: `${progressPercentage}%` }"></div>
            </div>
          </div>

          <div class="w-px h-5 bg-gray-200 dark:bg-gray-700"></div>

          <!-- Tasks -->
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-md bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
              <i class="fa-solid fa-list-check text-blue-600 dark:text-blue-400 text-xs"></i>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Tasks') }}</span>
              <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ completedTasks }}/{{ totalTasks }}</span>
            </div>
          </div>

          <div class="w-px h-5 bg-gray-200 dark:bg-gray-700"></div>

          <!-- Milestones -->
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-md bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center">
              <i class="fa-solid fa-flag text-purple-600 dark:text-purple-400 text-xs"></i>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Milestones') }}</span>
              <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ milestones.length }}</span>
            </div>
          </div>

          <!-- Budget -->
          <template v-if="project.budget">
            <div class="w-px h-5 bg-gray-200 dark:bg-gray-700"></div>
            <div class="flex items-center gap-2.5">
              <div class="w-7 h-7 rounded-md bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
                <i class="fa-solid fa-wallet text-emerald-600 dark:text-emerald-400 text-xs"></i>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Budget') }}</span>
                <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ formatCurrency(project.spent) }} / {{ formatCurrency(project.budget) }}</span>
              </div>
              <div class="w-20 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden hidden sm:block">
                <div
                  class="h-full rounded-full transition-all"
                  :class="budgetSpentPercent >= 100 ? 'bg-red-500' : budgetSpentPercent >= 80 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: `${budgetSpentPercent}%` }"
                ></div>
              </div>
            </div>
          </template>

          <!-- Estimated Cost -->
          <template v-if="project.estimated_cost">
            <div class="w-px h-5 bg-gray-200 dark:bg-gray-700"></div>
            <div class="flex items-center gap-2.5">
              <div class="w-7 h-7 rounded-md bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                <i class="fa-solid fa-calculator text-blue-600 dark:text-blue-400 text-xs"></i>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Estimated') }}</span>
                <span class="text-sm font-semibold" :class="project.budget && budgetEstimatedPercent >= 100 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100'">{{ formatCurrency(project.estimated_cost) }}</span>
              </div>
            </div>
          </template>

          <!-- Duration -->
          <template v-if="projectDuration">
            <div class="w-px h-5 bg-gray-200 dark:bg-gray-700"></div>
            <div class="flex items-center gap-2.5">
              <div class="w-7 h-7 rounded-md bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                <i class="fa-solid fa-hourglass-half text-amber-600 dark:text-amber-400 text-xs"></i>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Duration') }}</span>
                <span class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ projectDuration.label }}</span>
              </div>
              <!-- Time elapsed bar (only when project has an end date) -->
              <div v-if="projectDuration.total > 0" class="w-20 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden hidden sm:block">
                <div
                  class="h-full rounded-full transition-all"
                  :class="durationProgress >= 100 ? 'bg-red-500' : durationProgress >= 80 ? 'bg-amber-500' : 'bg-amber-400'"
                  :style="{ width: `${durationProgress}%` }"
                ></div>
              </div>
              <span v-if="projectDuration.total > 0" class="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">
                {{ projectDuration.remaining > 0 ? __('{0}d left', [projectDuration.remaining]) : __('overdue') }}
              </span>
            </div>
          </template>
        </div>

        <!-- Detail Panels -->
        <div class="flex divide-x divide-gray-200 dark:divide-gray-700">
          <!-- Project Info -->
          <div class="flex-1 p-4">
            <h4 class="text-overline text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
              <i class="fa-solid fa-circle-info"></i> {{ __('Project Info') }}
            </h4>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div ref="statusDropdownRef" class="relative flex items-center gap-2">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Status:') }}</span>
                <button
                  @click.stop="toggleStatusDropdown"
                  class="cursor-pointer hover:ring-2 hover:ring-orga-300 dark:hover:ring-orga-600 rounded-full transition-all"
                  :title="__('Click to change status')"
                  :disabled="isSavingStatus"
                >
                  <StatusBadge :status="project.status" type="project" size="sm" />
                </button>
                <!-- Status dropdown -->
                <div
                  v-if="showStatusDropdown"
                  class="absolute left-0 top-full mt-1 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-gray-950/50 z-50 py-1"
                >
                  <button
                    v-for="opt in projectStatusOptions"
                    :key="opt.value"
                    @click="changeProjectStatus(opt.value)"
                    :class="[
                      'w-full text-left px-3 py-1.5 text-sm flex items-center gap-2 transition-colors',
                      opt.value === project.status
                        ? 'bg-orga-50 dark:bg-orga-900/30 font-medium'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    ]"
                  >
                    <i :class="['fa-solid', opt.icon, opt.color, 'w-4 text-center text-xs']"></i>
                    <span class="text-gray-700 dark:text-gray-200">{{ opt.value }}</span>
                    <i v-if="opt.value === project.status" class="fa-solid fa-check text-orga-500 text-xs ml-auto"></i>
                  </button>
                </div>
              </div>
              <div ref="typeDropdownRef" class="relative flex items-center gap-2">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Type:') }}</span>
                <button
                  @click.stop="toggleTypeDropdown"
                  class="ml-2 text-gray-800 dark:text-gray-100 cursor-pointer hover:text-orga-600 dark:hover:text-orga-400 transition-colors flex items-center gap-1"
                  :title="__('Click to change type')"
                  :disabled="isSavingType"
                >
                  <i :class="['fa-solid', projectTypeOptions.find(o => o.value === project?.project_type)?.icon || 'fa-folder', projectTypeOptions.find(o => o.value === project?.project_type)?.color || 'text-gray-500', 'text-xs']"></i>
                  {{ project?.project_type }}
                </button>
                <div
                  v-if="showTypeDropdown"
                  class="absolute left-0 top-full mt-1 w-44 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-gray-950/50 z-50 py-1"
                >
                  <button
                    v-for="opt in projectTypeOptions"
                    :key="opt.value"
                    @click="changeProjectType(opt.value)"
                    :class="[
                      'w-full text-left px-3 py-1.5 text-sm flex items-center gap-2 transition-colors',
                      opt.value === project.project_type
                        ? 'bg-orga-50 dark:bg-orga-900/30 font-medium'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                    ]"
                  >
                    <i :class="['fa-solid', opt.icon, opt.color, 'w-4 text-center text-xs']"></i>
                    <span class="text-gray-700 dark:text-gray-200">{{ opt.value }}</span>
                    <i v-if="opt.value === project.project_type" class="fa-solid fa-check text-orga-500 text-xs ml-auto"></i>
                  </button>
                </div>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">{{ __('Start:') }}</span>
                <template v-if="isEditingStartDate">
                  <input
                    ref="startDateInputRef"
                    v-model="editStartDate"
                    type="date"
                    @keydown.enter="saveStartDate"
                    @keydown.escape="cancelEditStartDate"
                    @blur="saveStartDate"
                    :disabled="isSavingStartDate"
                    class="ml-2 px-1.5 py-0.5 text-sm border-b-2 border-orga-500 bg-transparent outline-none text-gray-800 dark:text-gray-100 dark:[color-scheme:dark]"
                  />
                </template>
                <span
                  v-else
                  @click="startEditStartDate"
                  class="ml-2 text-gray-800 dark:text-gray-100 cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
                  :title="__('Click to edit start date')"
                >{{ formatDate(project.start_date) }}</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">{{ __('End:') }}</span>
                <template v-if="isEditingEndDate">
                  <input
                    ref="endDateInputRef"
                    v-model="editEndDate"
                    type="date"
                    @keydown.enter="saveEndDate"
                    @keydown.escape="cancelEditEndDate"
                    @blur="saveEndDate"
                    :disabled="isSavingEndDate"
                    class="ml-2 px-1.5 py-0.5 text-sm border-b-2 border-orga-500 bg-transparent outline-none text-gray-800 dark:text-gray-100 dark:[color-scheme:dark]"
                  />
                </template>
                <span
                  v-else
                  @click="startEditEndDate"
                  class="ml-2 text-gray-800 dark:text-gray-100 cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
                  :title="__('Click to edit end date')"
                >{{ formatDate(project.end_date) }}</span>
              </div>
              <div v-if="projectDuration" class="col-span-2 flex items-center gap-2">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Duration:') }}</span>
                <span class="ml-2 text-gray-800 dark:text-gray-100">
                  {{ projectDuration.label }}
                  <template v-if="projectDuration.total > 0 && projectDuration.remaining > 0">
                    <span class="text-gray-400 dark:text-gray-500">({{ __('{0}d remaining', [projectDuration.remaining]) }})</span>
                  </template>
                  <template v-else-if="projectDuration.total > 0 && projectDuration.remaining <= 0">
                    <span class="text-red-500 dark:text-red-400">({{ __('overdue') }})</span>
                  </template>
                </span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">{{ __('Budget:') }}</span>
                <template v-if="isEditingBudget">
                  <div class="inline-flex items-center ml-2 gap-1">
                    <span class="text-gray-400 text-sm">{{ currencySymbol }}</span>
                    <input
                      ref="budgetInputRef"
                      v-model.number="editBudget"
                      type="number"
                      min="0"
                      step="100"
                      @keydown.enter="saveBudget"
                      @keydown.escape="cancelEditBudget"
                      @blur="saveBudget"
                      :disabled="isSavingBudget"
                      class="w-28 px-1.5 py-0.5 text-sm border-b-2 border-orga-500 bg-transparent outline-none text-gray-800 dark:text-gray-100"
                    />
                  </div>
                </template>
                <span
                  v-else
                  @click="startEditBudget"
                  class="ml-2 text-gray-800 dark:text-gray-100 cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
                  :title="__('Click to edit budget')"
                >{{ project.budget ? formatCurrency(project.budget) : __('Not set') }}</span>
              </div>
              <div v-if="project.estimated_cost">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Estimated:') }}</span>
                <span class="ml-2" :class="project.budget && budgetEstimatedPercent >= 100 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100'">
                  {{ formatCurrency(project.estimated_cost) }}
                  <span v-if="project.budget" class="text-gray-400 dark:text-gray-500">({{ budgetEstimatedPercent }}%)</span>
                </span>
              </div>
              <div v-if="project.budget">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Spent:') }}</span>
                <span class="ml-2" :class="budgetSpentPercent >= 100 ? 'text-red-600 dark:text-red-400' : 'text-gray-800 dark:text-gray-100'">
                  {{ formatCurrency(project.spent) }}
                  <span class="text-gray-400 dark:text-gray-500">({{ budgetSpentPercent }}%)</span>
                </span>
              </div>
              <div v-if="costVariance !== null && project.estimated_cost">
                <span class="text-gray-600 dark:text-gray-400">{{ __('Variance:') }}</span>
                <span class="ml-2 font-medium" :class="costVariance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                  {{ costVariance >= 0 ? '+' : '' }}{{ formatCurrency(costVariance) }}
                  <span class="text-gray-400 dark:text-gray-500">({{ costVariancePercent }}%)</span>
                </span>
              </div>
            </div>
            <div class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
              <!-- Editing mode -->
              <div v-if="isEditingDescription">
                <textarea
                  v-model="editDescription"
                  rows="3"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 resize-y"
                  :placeholder="__('Add a project description...')"
                  @keydown.escape="cancelEditDescription"
                ></textarea>
                <div class="flex justify-end gap-2 mt-2">
                  <button
                    @click="cancelEditDescription"
                    :disabled="isSavingDescription"
                    class="px-2.5 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                  >
                    {{ __('Cancel') }}
                  </button>
                  <button
                    @click="saveDescription"
                    :disabled="isSavingDescription"
                    class="px-2.5 py-1 text-xs font-medium text-white bg-orga-500 rounded hover:bg-orga-600 transition-colors disabled:opacity-50 flex items-center gap-1"
                  >
                    <i v-if="isSavingDescription" class="fa-solid fa-spinner fa-spin"></i>
                    {{ isSavingDescription ? __('Saving...') : __('Save') }}
                  </button>
                </div>
              </div>
              <!-- Display mode -->
              <div
                v-else
                @click="startEditDescription"
                class="cursor-pointer group"
                :title="__('Click to edit description')"
              >
                <p
                  v-if="project.description"
                  class="text-sm text-gray-700 dark:text-gray-300 m-0 line-clamp-2 group-hover:text-orga-600 dark:group-hover:text-orga-400 transition-colors"
                  v-html="sanitizeHtml(project.description)"
                ></p>
                <p v-else class="text-sm text-gray-400 dark:text-gray-500 m-0 italic group-hover:text-orga-500 dark:group-hover:text-orga-400 transition-colors">
                  {{ __('Click to add description...') }}
                </p>
              </div>
            </div>
          </div>

          <!-- Team (Users assigned to project tasks) -->
          <div class="w-48 p-4">
            <h4 class="text-overline text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
              <i class="fa-solid fa-users"></i> {{ __('Team') }}
            </h4>
            <div v-if="teamMembers.length > 0" class="flex flex-wrap gap-1">
              <div
                v-for="member in teamMembers"
                :key="member.user"
                class="relative group"
                :title="member.full_name + (member.is_manager ? ' (' + __('Manager') + ')' : '')"
              >
                <img
                  v-if="member.user_image"
                  :src="member.user_image"
                  :alt="member.full_name"
                  class="w-8 h-8 rounded-full object-cover border-2"
                  :class="member.is_manager ? 'border-orga-500' : 'border-white dark:border-gray-700'"
                />
                <div
                  v-else
                  class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium text-white border-2"
                  :class="[
                    member.is_manager ? 'bg-orga-600 border-orga-500' : 'bg-gray-500 border-white dark:border-gray-700'
                  ]"
                >
                  {{ getInitials(member.full_name) }}
                </div>
                <div
                  v-if="member.is_manager"
                  class="absolute -top-1 -right-1 w-3 h-3 bg-orga-500 rounded-full flex items-center justify-center"
                >
                  <i class="fa-solid fa-star text-[6px] text-white"></i>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-gray-500 dark:text-gray-400">{{ __('No team members') }}</p>
          </div>

          <!-- Milestones -->
          <div class="flex-1 min-w-0 p-4">
            <h4 class="text-overline text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
              <i class="fa-solid fa-flag"></i> {{ __('Milestones') }}
            </h4>
            <div v-if="milestones.length > 0" class="space-y-1.5 max-h-20 overflow-auto">
              <div v-for="milestone in milestones" :key="milestone.name" class="flex items-center gap-2 text-sm">
                <StatusBadge :status="milestone.status" type="milestone" size="sm" />
                <span :class="[milestone.status === 'Completed' ? 'text-gray-500 dark:text-gray-500 line-through' : 'text-gray-800 dark:text-gray-200', 'truncate flex-1']">
                  {{ milestone.milestone_name }}
                </span>
                <span class="text-xs text-gray-600 dark:text-gray-400 ml-auto whitespace-nowrap">{{ formatDate(milestone.due_date) }}</span>
              </div>
            </div>
            <EmptyState
              v-else
              icon="fa-flag"
              :title="__('No milestones')"
              :description="__('Add milestones to track key deliverables.')"
              :action-label="__('+ Add Milestone')"
              @action="isMilestoneModalOpen = true"
              size="sm"
            />
          </div>

          <!-- Documents (expandable grouped drawer) -->
          <div class="w-64 p-4 relative">
            <h4 class="text-overline text-gray-600 dark:text-gray-400 mb-3 flex items-center gap-2">
              <i class="fa-solid fa-folder-open"></i> {{ __('Documents') }}
            </h4>

            <!-- Summary / Toggle -->
            <button
              v-if="groupedDocuments.totalCount > 0"
              @click="toggleDocDrawer"
              class="w-full text-left text-sm text-gray-700 dark:text-gray-300 hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
            >
              <span class="font-medium">{{ groupedDocuments.totalCount === 1 ? __('1 file') : __('{0} files', [groupedDocuments.totalCount]) }}</span>
              <span v-if="documentSummary" class="text-xs text-gray-500 dark:text-gray-400 ml-1">({{ documentSummary }})</span>
              <i :class="['fa-solid fa-chevron-up text-xs ml-1 transition-transform', isDocDrawerOpen ? '' : 'rotate-180']"></i>
            </button>
            <p v-else class="text-xs text-gray-500 dark:text-gray-400">{{ __('No documents attached') }}</p>

            <!-- Upload button (always visible) -->
            <label class="mt-2 flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 cursor-pointer transition-colors">
              <i class="fa-solid fa-cloud-arrow-up"></i>
              <span>{{ __('Upload to project') }}</span>
              <input type="file" class="hidden" @change="handleProjectFileUpload" :disabled="isUploadingProjectFile" />
            </label>
            <div v-if="isUploadingProjectFile" class="mt-1 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div class="h-full bg-orga-500 transition-all duration-300" :style="{ width: projectUploadProgress + '%' }"></div>
            </div>

            <!-- Expandable Document Drawer -->
            <div
              v-if="isDocDrawerOpen && groupedDocuments.totalCount > 0"
              class="absolute bottom-full left-0 mb-2 w-80 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 max-h-80 overflow-auto"
            >
              <!-- Project Files -->
              <div v-if="groupedDocuments.project.length > 0" class="p-3 border-b border-gray-100 dark:border-gray-800">
                <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  <i class="fa-solid fa-folder text-orga-500 mr-1"></i> {{ __('Project Files') }}
                </h5>
                <div class="space-y-1">
                  <a
                    v-for="doc in groupedDocuments.project"
                    :key="doc.name"
                    :href="doc.file_url"
                    target="_blank"
                    class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 hover:text-orga-600 dark:hover:text-orga-400 group"
                  >
                    <i :class="['fa-solid text-xs', getDocIcon(doc)]"></i>
                    <span class="truncate flex-1 group-hover:underline">{{ doc.file_name }}</span>
                    <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">{{ formatFileSize(doc.file_size) }}</span>
                  </a>
                </div>
              </div>

              <!-- Task Files (grouped by task) -->
              <div
                v-for="(group, taskName) in groupedDocuments.byTask"
                :key="taskName"
                class="p-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0"
              >
                <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  <i class="fa-solid fa-check-square text-blue-500 mr-1"></i> {{ group.taskSubject }}
                </h5>
                <div class="space-y-1">
                  <a
                    v-for="doc in group.files"
                    :key="doc.name"
                    :href="doc.file_url"
                    target="_blank"
                    class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 hover:text-orga-600 dark:hover:text-orga-400 group"
                  >
                    <i :class="['fa-solid text-xs', getDocIcon(doc)]"></i>
                    <span class="truncate flex-1 group-hover:underline">{{ doc.file_name }}</span>
                    <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">{{ formatFileSize(doc.file_size) }}</span>
                  </a>
                </div>
              </div>
            </div>

            <!-- Click-outside overlay to close drawer -->
            <div
              v-if="isDocDrawerOpen"
              class="fixed inset-0 z-10"
              @click="isDocDrawerOpen = false"
            ></div>
          </div>
        </div>
      </div>

      <!-- Modals -->
      <CreateTaskModal
        :is-open="isTaskModalOpen"
        :project-id="projectId"
        :initial-status="initialTaskStatus"
        :auto-trail-default="autoTrailDefault"
        @close="isTaskModalOpen = false; initialTaskStatus = 'Open'"
        @created="handleTaskCreated"
      />

      <CreateMilestoneModal
        :is-open="isMilestoneModalOpen"
        :project-id="projectId"
        @close="isMilestoneModalOpen = false"
        @created="handleMilestoneCreated"
      />

      <DeleteProjectModal
        :is-open="isDeleteModalOpen"
        :project-name="projectId"
        :project-label="project.project_name"
        :task-count="totalTasks"
        :milestone-count="milestones.length"
        @close="isDeleteModalOpen = false"
        @deleted="handleProjectDeleted"
      />

      <SaveAsTemplateModal
        :is-open="isSaveTemplateModalOpen"
        :project-name="projectId"
        :project-label="project.project_name"
        :task-count="totalTasks"
        :milestone-count="milestones.length"
        @close="isSaveTemplateModalOpen = false"
        @saved="isSaveTemplateModalOpen = false"
      />
    </template>
  </div>
</template>

<style scoped>
[draggable="true"] {
  cursor: grab;
}

[draggable="true"]:active {
  cursor: grabbing;
}

/* ========== KANBAN COLUMN COLORS ========== */
/* NOTE: Column backgrounds are handled by Tailwind (bg-white dark:bg-gray-800)
   and global dark rules in index.css. Light-mode gradients are set here
   but dark-mode overrides are in index.css (global) to avoid specificity issues. */

/* Open Status - Sky Blue */
.column-open {
  background: linear-gradient(180deg, #EEF4FF 0%, #F8FAFF 100%);
  border-top: 3px solid #0052CC;
}

/* In Progress Status - Warm Amber */
.column-in-progress {
  background: linear-gradient(180deg, #FFFBEB 0%, #FFFDF5 100%);
  border-top: 3px solid #B45309;
}

/* Review Status - Soft Purple */
.column-review {
  background: linear-gradient(180deg, #F5F3FF 0%, #FAF5FF 100%);
  border-top: 3px solid #7C3AED;
}

/* Completed Status - Mint Green */
.column-completed {
  background: linear-gradient(180deg, #ECFDF5 0%, #F0FDF9 100%);
  border-top: 3px solid #059669;
}

/* ========== KANBAN CARD STATUS BORDERS & SHADOWS ========== */
/* NOTE: background is handled by Tailwind (bg-white dark:bg-gray-700)
   and global dark rules in index.css. Do NOT set background here
   as scoped styles have higher specificity and break dark mode. */

/* Open Card */
.card-open {
  border-left: 4px solid #0052CC;
  box-shadow: 0 1px 3px rgba(0, 82, 204, 0.08);
}

.card-open:hover {
  box-shadow: 0 4px 12px rgba(0, 82, 204, 0.15);
}

/* In Progress Card */
.card-in-progress {
  border-left: 4px solid #B45309;
  box-shadow: 0 1px 3px rgba(180, 83, 9, 0.08);
}

.card-in-progress:hover {
  box-shadow: 0 4px 12px rgba(180, 83, 9, 0.15);
}

/* Review Card */
.card-review {
  border-left: 4px solid #7C3AED;
  box-shadow: 0 1px 3px rgba(124, 58, 237, 0.08);
}

.card-review:hover {
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.15);
}

/* Completed Card */
.card-completed {
  border-left: 4px solid #059669;
  box-shadow: 0 1px 3px rgba(5, 150, 105, 0.08);
  opacity: 0.9;
}

.card-completed:hover {
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.15);
  opacity: 1;
}

/* Selected Card */
.card-selected {
  border-left: 4px solid var(--orga-500, #6366f1);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

/* Dark mode styles moved to index.css for reliability
   (Vue scoped :global selectors can conflict with Tailwind dark: utilities) */
</style>
