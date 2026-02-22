<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskManager.vue - Unified Task Manager panel with tabbed interface

  Features:
  - Details: Task info, priority, status, assignee, dates
  - Dependencies: Predecessors/successors with FS/SS/FF/SF types
  - Finance: Cost tracking, billing, linked invoices
  - Checklist: Task checklist items with progress
  - Discussion: Threaded comments with rich text, @mentions, resolve, pin
  - Actions: Status changes, quick actions
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskApi, useAssignmentApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import type {
  OrgaTask,
  OrgaProject,
  OrgaContact,
  GanttTask,
  TaskChecklistItem,
  TaskStatus,
  TaskPriority,
  TaskDependency,
  TaskDependencyInfo,
  DependencyType,
  CascadeChange,
  ManagerTab,
  OrgaFileAttachment
} from '@/types/orga'

// Gantt-specific components
import DependencyChain from '@/components/gantt/DependencyChain.vue'
import CascadePreview from '@/components/gantt/CascadePreview.vue'
import BudgetBurnRate from '@/components/gantt/BudgetBurnRate.vue'

// Shared Manager Components
import ManagerTabs from '@/components/manager/ManagerTabs.vue'
import ManagerTabContent from '@/components/manager/ManagerTabContent.vue'

// Tab Content Components
import TaskDetailsTab from '@/components/manager/tabs/TaskDetailsTab.vue'
import TaskDependenciesTab from '@/components/manager/tabs/TaskDependenciesTab.vue'
import TaskFinanceTab from '@/components/manager/tabs/TaskFinanceTab.vue'
import TaskChecklistTab from '@/components/manager/tabs/TaskChecklistTab.vue'
import ActivityDiscussionTab from '@/components/manager/tabs/ActivityDiscussionTab.vue'
import TaskAttachmentsTab from '@/components/manager/tabs/TaskAttachmentsTab.vue'
import TaskActionsTab from '@/components/manager/tabs/TaskActionsTab.vue'
import TaskTimeTab from '@/components/manager/tabs/TaskTimeTab.vue'
import ManualTimeEntryModal from '@/components/ManualTimeEntryModal.vue'

// Kanban column interface
interface KanbanColumn {
  id: TaskStatus
  title: string
  color?: string
}

// View type for different contexts
type ViewType = 'kanban' | 'list' | 'gantt'

interface Props {
  task: OrgaTask | GanttTask
  columns?: KanbanColumn[]
  allTasks?: (OrgaTask | GanttTask)[]  // For dependency selection
  contacts?: OrgaContact[]  // For contact assignment picker
  availableGroups?: string[]  // For task group autocomplete
  // Gantt-specific props
  viewType?: ViewType
  project?: OrgaProject  // Required for Gantt context
  showCascadePreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  columns: () => [
    { id: 'Open', title: 'Open' },
    { id: 'In Progress', title: 'In Progress' },
    { id: 'Review', title: 'Review' },
    { id: 'Completed', title: 'Completed' }
  ],
  allTasks: () => [],
  contacts: () => [],
  availableGroups: () => [],
  viewType: 'kanban',
  showCascadePreview: false
})

const emit = defineEmits<{
  close: []
  update: []
  'status-change': [task: OrgaTask | GanttTask, newStatus: TaskStatus]
  'priority-change': [task: OrgaTask | GanttTask, newPriority: TaskPriority]
  // Gantt-specific emits
  'field-update': [payload: { field: string; value: unknown; task_id: string }]
  'navigate': [payload: { task_id: string }]
  'preview-cascade': [payload: { changes: CascadeChange[] }]
  'apply-cascade': [payload: { task_id: string; changes: CascadeChange[] }]
}>()

const router = useRouter()
const {
  getChecklist,
  addChecklistItem,
  toggleChecklistItem,
  deleteChecklistItem,
  promoteChecklistToTask,
  getDependencies,
  addDependency,
  updateDependency,
  removeDependency,
  getAttachments,
  deleteAttachment,
  updateTask,
  createTask,
  deleteTask
} = useTaskApi()
const {
  createAssignment,
  deleteAssignment,
  getTaskAssignments
} = useAssignmentApi()
const { success: showSuccess, error: showError } = useToast()

const showDeleteConfirm = ref(false)
const isDeleting = ref(false)

// Tab configuration - base tabs for all views
const baseTabs: ManagerTab[] = [
  { id: 'details', icon: 'fa-file-alt', label: __('Details') },
  { id: 'dependencies', icon: 'fa-project-diagram', label: __('Dependencies') },
  { id: 'time', icon: 'fa-stopwatch', label: __('Time') },
  { id: 'finance', icon: 'fa-euro-sign', label: __('Finance') },
  { id: 'checklist', icon: 'fa-list-check', label: __('Checklist') },
  { id: 'discussion', icon: 'fa-comments', label: __('Discussion') },
  { id: 'attachments', icon: 'fa-paperclip', label: __('Files') },
  { id: 'actions', icon: 'fa-bolt', label: __('Actions') }
]

const showManualTimeEntry = ref(false)
const timeTabKey = ref(0)

function loadTaskData(): void {
  // Increment key to force TaskTimeTab to remount and reload data
  timeTabKey.value++
  // Notify parent to refresh task data (actual_hours, progress, etc.)
  emit('update')
}

// Add cascade tab for Gantt view when task has dependents
const taskTabs = computed<ManagerTab[]>(() => {
  if (props.viewType === 'gantt' && hasDependents.value) {
    return [
      ...baseTabs.slice(0, 2),  // details, dependencies
      { id: 'cascade', icon: 'fa-sitemap', label: __('Cascade') },
      ...baseTabs.slice(2)  // time, financial, checklist, discussion, files, actions
    ]
  }
  return baseTabs
})

const activeTab = ref('details')

// Data
const checklist = ref<TaskChecklistItem[]>([])
const predecessors = ref<TaskDependency[]>([])
const successors = ref<TaskDependency[]>([])

// Gantt-specific state
const cascadeChanges = ref<CascadeChange[]>([])
const showCascade = ref(false)
const isSavingCascade = ref(false)

// Loading states
const isLoadingChecklist = ref(false)
const isLoadingDependencies = ref(false)
const isLoadingAttachments = ref(false)
const isAddingChecklistItem = ref(false)
const isUploadingAttachment = ref(false)
const uploadProgress = ref(0)

// Data - attachments
const attachments = ref<OrgaFileAttachment[]>([])

// ============================================
// Computed Properties
// ============================================

// Check if this is a Gantt view
const isGanttView = computed(() => props.viewType === 'gantt')

// Type guard for GanttTask
const ganttTask = computed<GanttTask | null>(() => {
  if (isGanttView.value && 'dependencies_info' in props.task) {
    return props.task as GanttTask
  }
  return null
})

// Gantt-specific computed: dependencies info from task
const dependenciesInfo = computed<TaskDependencyInfo[]>(() => {
  return ganttTask.value?.dependencies_info || []
})

// Gantt-specific computed: dependents info from task
const dependentsInfo = computed<TaskDependencyInfo[]>(() => {
  return ganttTask.value?.dependents_info || []
})

// Check if task has dependents (for cascade feature)
const hasDependents = computed(() => {
  return dependentsInfo.value.length > 0 || successors.value.length > 0
})

// Check if task is blocked by incomplete dependencies
const isBlocked = computed(() => {
  return ganttTask.value?.is_blocked || false
})

// Check if task has budget info
const hasBudget = computed(() => {
  const gt = ganttTask.value
  return gt && gt.budget !== undefined && gt.budget > 0
})

// Calculate task duration (for Gantt display)
const taskDuration = computed(() => {
  const task = props.task
  if (!task.start_date || !task.due_date) return null
  const start = new Date(task.start_date)
  const end = new Date(task.due_date)
  const diffTime = Math.abs(end.getTime() - start.getTime())
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
})

const availableTasksForDependency = computed(() => {
  // Exclude current task and tasks that are already dependencies
  const existingDeps = new Set([
    ...predecessors.value.map(d => d.depends_on),
    props.task.name
  ])
  return props.allTasks.filter(t => !existingDeps.has(t.name))
})

// ============================================
// Data Loading
// ============================================

async function loadChecklist(): Promise<void> {
  if (!props.task?.name) return
  isLoadingChecklist.value = true
  try {
    const data = await getChecklist(props.task.name)
    checklist.value = data || []
  } catch (e) {
    console.error('Failed to load checklist:', e)
    checklist.value = []
  } finally {
    isLoadingChecklist.value = false
  }
}

async function loadDependencies(): Promise<void> {
  if (!props.task?.name) return
  isLoadingDependencies.value = true
  try {
    const data = await getDependencies(props.task.name)
    predecessors.value = data?.predecessors || []
    successors.value = data?.successors || []
  } catch (e) {
    console.error('Failed to load dependencies:', e)
    predecessors.value = []
    successors.value = []
  } finally {
    isLoadingDependencies.value = false
  }
}

async function loadAttachments(): Promise<void> {
  if (!props.task?.name) return
  isLoadingAttachments.value = true
  try {
    const data = await getAttachments(props.task.name)
    attachments.value = data || []
  } catch (e) {
    console.error('Failed to load attachments:', e)
    attachments.value = []
  } finally {
    isLoadingAttachments.value = false
  }
}

// ============================================
// Checklist Handlers
// ============================================

async function handleAddChecklistItem(title: string): Promise<void> {
  if (!title.trim() || isAddingChecklistItem.value) return
  isAddingChecklistItem.value = true
  try {
    await addChecklistItem(props.task.name, title.trim())
    await loadChecklist()
    emit('update')
  } catch (e) {
    console.error('Failed to add checklist item:', e)
  } finally {
    isAddingChecklistItem.value = false
  }
}

async function handleToggleChecklistItem(item: TaskChecklistItem): Promise<void> {
  try {
    await toggleChecklistItem(props.task.name, item.name!)
    await loadChecklist()
    emit('update')
  } catch (e) {
    console.error('Failed to toggle checklist item:', e)
  }
}

async function handleDeleteChecklistItem(item: TaskChecklistItem): Promise<void> {
  try {
    await deleteChecklistItem(props.task.name, item.name!)
    await loadChecklist()
    emit('update')
  } catch (e) {
    console.error('Failed to delete checklist item:', e)
  }
}

async function handlePromoteChecklistItem(item: TaskChecklistItem): Promise<void> {
  try {
    const result = await promoteChecklistToTask(props.task.name, item.name!)
    await loadChecklist()
    showSuccess(__('Promoted to task'), __('"{0}" created as a new task.', [result.subject]))
    emit('update')
  } catch (e) {
    console.error('Failed to promote checklist item:', e)
    showError(__('Promote failed'), (e as Error).message || __('Could not promote checklist item to task.'))
  }
}

// ============================================
// Dependency Handlers
// ============================================

async function handleAddDependency(taskName: string, dependsOn: string, type: DependencyType): Promise<void> {
  try {
    await addDependency(taskName, dependsOn, type)
    await loadDependencies()
    emit('update')
  } catch (e) {
    console.error('Failed to add dependency:', e)
  }
}

async function handleUpdateDependency(dependencyName: string, type: DependencyType, lagDays: number): Promise<void> {
  try {
    await updateDependency(dependencyName, type, lagDays)
    await loadDependencies()
    emit('update')
  } catch (e) {
    console.error('Failed to update dependency:', e)
  }
}

async function handleRemoveDependency(dependencyName: string): Promise<void> {
  try {
    await removeDependency(dependencyName)
    await loadDependencies()
    emit('update')
  } catch (e) {
    console.error('Failed to remove dependency:', e)
  }
}

// ============================================
// Attachment Handlers
// ============================================

async function handleUploadFile(file: File): Promise<void> {
  if (!props.task?.name || isUploadingAttachment.value) return
  isUploadingAttachment.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doctype', 'Orga Task')
    formData.append('docname', props.task.name)
    formData.append('is_private', '0')

    const xhr = new XMLHttpRequest()
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadProgress.value = Math.round((e.loaded / e.total) * 100)
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

    await loadAttachments()
    emit('update')
  } catch (e) {
    console.error('Failed to upload file:', e)
  } finally {
    isUploadingAttachment.value = false
    uploadProgress.value = 0
  }
}

async function handleDeleteAttachment(attachment: OrgaFileAttachment): Promise<void> {
  try {
    await deleteAttachment(props.task.name, attachment.name)
    await loadAttachments()
    emit('update')
  } catch (e) {
    console.error('Failed to delete attachment:', e)
  }
}

// ============================================
// Gantt-Specific Handlers
// ============================================

// Navigate to another task (Gantt dependency chain)
function handleNavigateToTask(taskId: string): void {
  emit('navigate', { task_id: taskId })
}

// Handle field update (for Gantt inline editing)
function handleFieldUpdate(field: string, value: unknown): void {
  emit('field-update', { field, value, task_id: props.task.name })
}

// Handle date change from TaskDetailsTab
function handleTaskDateChange(field: 'start_date' | 'due_date', value: string): void {
  // Use the same field-update mechanism
  emit('field-update', { field, value: value || null, task_id: props.task.name })
}

// Handle progress change from TaskDetailsTab
function handleTaskProgressChange(value: number): void {
  // Use the same field-update mechanism
  emit('field-update', { field: 'progress', value, task_id: props.task.name })
}

// Handle description change from TaskDetailsTab
function handleTaskDescriptionChange(value: string): void {
  emit('field-update', { field: 'description', value, task_id: props.task.name })
}

// Handle subject change from TaskDetailsTab
async function handleTaskSubjectChange(value: string): Promise<void> {
  const oldValue = props.task.subject
  ;(props.task as Record<string, unknown>).subject = value
  try {
    await updateTask(props.task.name, { subject: value })
    emit('update')
  } catch (e) {
    ;(props.task as Record<string, unknown>).subject = oldValue
    console.error('Failed to update task subject:', e)
  }
}

// Handle task group change from TaskDetailsTab
function handleTaskGroupChange(value: string): void {
  emit('field-update', { field: 'task_group', value: value || '', task_id: props.task.name })
}

// Handle depends-on-group change from TaskDetailsTab
function handleDependsOnGroupChange(value: string): void {
  emit('field-update', { field: 'depends_on_group', value: value || '', task_id: props.task.name })
}

// Handle task type change from TaskDetailsTab
function handleTaskTypeChange(value: string): void {
  emit('field-update', { field: 'task_type', value: value || '', task_id: props.task.name })
}

// Handle auto-trail toggle from TaskDetailsTab
function handleAutoTrailChange(value: boolean): void {
  emit('field-update', { field: 'auto_trail_start', value: value ? 1 : 0, task_id: props.task.name })
}

// Handle contact assignment from TaskDetailsTab
async function handleAssignContact(contactName: string | null): Promise<void> {
  const oldAssigned = (props.task as Record<string, unknown>).assigned_to
  const oldName = (props.task as Record<string, unknown>).assigned_to_name
  const oldContactName = (props.task as Record<string, unknown>).assigned_resource_name

  if (!contactName) {
    // Unassign: clear task fields and remove any existing assignment
    ;(props.task as Record<string, unknown>).assigned_to = ''
    ;(props.task as Record<string, unknown>).assigned_to_name = ''
    ;(props.task as Record<string, unknown>).assigned_resource = ''
    ;(props.task as Record<string, unknown>).assigned_resource_name = ''
    try {
      await updateTask(props.task.name, { assigned_to: '' })
      // Remove existing assignments for this task
      const existing = await getTaskAssignments(props.task.name)
      for (const a of existing) {
        await deleteAssignment(a.name)
      }
      emit('update')
    } catch (e) {
      ;(props.task as Record<string, unknown>).assigned_to = oldAssigned
      ;(props.task as Record<string, unknown>).assigned_to_name = oldName
      ;(props.task as Record<string, unknown>).assigned_resource_name = oldContactName
      console.error('Failed to unassign contact:', e)
    }
    return
  }

  // Assign: find contact, create Orga Assignment, optionally set assigned_to
  const contact = props.contacts.find(r => r.name === contactName)
  if (!contact) return

  // Optimistic UI: show contact name immediately
  ;(props.task as Record<string, unknown>).assigned_resource = contactName
  ;(props.task as Record<string, unknown>).assigned_resource_name = contact.resource_name
  // Only set assigned_to if contact has a linked user
  if (contact.user) {
    ;(props.task as Record<string, unknown>).assigned_to = contact.user
    ;(props.task as Record<string, unknown>).assigned_to_name = contact.resource_name
  }
  try {
    // Update task's assigned_to if contact has a linked user
    if (contact.user) {
      await updateTask(props.task.name, { assigned_to: contact.user })
    }
    // Remove any existing assignments for this task, then create new one
    const existing = await getTaskAssignments(props.task.name)
    for (const a of existing) {
      await deleteAssignment(a.name)
    }
    await createAssignment(props.task.name, contactName)
    emit('update')
  } catch (e) {
    ;(props.task as Record<string, unknown>).assigned_to = oldAssigned
    ;(props.task as Record<string, unknown>).assigned_to_name = oldName
    ;(props.task as Record<string, unknown>).assigned_resource_name = oldContactName
    console.error('Failed to assign contact:', e)
  }
}

// Calculate cascade effect when dates change
function calculateCascade(dayShift: number): CascadeChange[] {
  const changes: CascadeChange[] = []
  const visited = new Set<string>()
  const allTasks = props.allTasks as GanttTask[]

  function findDependents(taskId: string, shift: number) {
    for (const t of allTasks) {
      if (visited.has(t.name)) continue

      const dep = t.dependencies_info?.find(d => d.task_id === taskId)
      if (!dep) continue

      visited.add(t.name)
      const effectiveShift = shift + (dep.lag || 0)

      if (t.start_date) {
        const oldDate = new Date(t.start_date)
        const newDate = new Date(oldDate.getTime() + effectiveShift * 24 * 60 * 60 * 1000)

        changes.push({
          task_id: t.name,
          task_name: t.subject,
          field: 'start_date',
          old_value: t.start_date,
          new_value: newDate.toISOString().split('T')[0],
          days_shift: effectiveShift
        })
      }

      // Recurse to find dependents of this task
      findDependents(t.name, effectiveShift)
    }
  }

  findDependents(props.task.name, dayShift)
  return changes
}

// Handle date change with cascade preview
function handleDateChange(field: 'start_date' | 'due_date', newValue: string): void {
  const oldValue = props.task[field]

  // Calculate cascade if there are dependents and dates changed
  if (hasDependents.value && oldValue !== newValue && oldValue) {
    const oldDate = new Date(oldValue)
    const newDate = new Date(newValue)
    const daysDiff = Math.ceil((newDate.getTime() - oldDate.getTime()) / (1000 * 60 * 60 * 24))

    if (daysDiff !== 0) {
      cascadeChanges.value = calculateCascade(daysDiff)
      showCascade.value = cascadeChanges.value.length > 0
    }
  }

  // Emit the field update
  handleFieldUpdate(field, newValue)
}

// Preview cascade changes
function handleCascadePreview(): void {
  emit('preview-cascade', { changes: cascadeChanges.value })
}

// Apply cascade changes
function handleCascadeApply(): void {
  isSavingCascade.value = true
  emit('apply-cascade', { task_id: props.task.name, changes: cascadeChanges.value })
  cascadeChanges.value = []
  showCascade.value = false
  isSavingCascade.value = false
}

// Cancel cascade changes
function handleCascadeCancel(): void {
  cascadeChanges.value = []
  showCascade.value = false
}

// ============================================
// Action Handlers
// ============================================

function handleStatusChange(newStatus: TaskStatus): void {
  emit('status-change', props.task, newStatus)
}

function handlePriorityChange(newPriority: TaskPriority): void {
  emit('priority-change', props.task, newPriority)
}

function handleNavigate(): void {
  // Open the Frappe Desk form for full task documentation (audit trail, version history, etc.)
  window.open(`/app/orga-task/${props.task.name}`, '_blank')
}

async function handleAssignToMe(): Promise<void> {
  try {
    const frappeWindow = window as unknown as { frappe?: { session?: { user?: string } } }
    const user = frappeWindow.frappe?.session?.user
    if (!user) return

    // Find the contact matching the current user
    const myContact = props.contacts.find(r => r.user === user)
    if (myContact) {
      await handleAssignContact(myContact.name)
    } else {
      // Fallback: assign directly if no contact record exists for the user
      await updateTask(props.task.name, { assigned_to: user })
      emit('update')
    }
  } catch (e) {
    console.error('Failed to assign task:', e)
  }
}

async function handleDuplicate(): Promise<void> {
  try {
    await createTask({
      subject: __("{0} (Copy)", [props.task.subject]),
      project: props.task.project,
      description: props.task.description,
      priority: props.task.priority,
      status: 'Open',
      estimated_hours: props.task.estimated_hours
    })
    showSuccess(__('Task duplicated'), __('A copy of "{0}" has been created.', [props.task.subject]))
    emit('update')
  } catch (e) {
    console.error('Failed to duplicate task:', e)
    showError(__('Duplicate failed'), (e as Error).message || __('Could not duplicate the task. Please try again.'))
  }
}

function handleDelete(): void {
  showDeleteConfirm.value = true
}

async function confirmAndDelete(): Promise<void> {
  if (isDeleting.value) return
  isDeleting.value = true
  try {
    await deleteTask(props.task.name)
    showDeleteConfirm.value = false
    showSuccess(__('Task deleted'), __('"{0}" has been permanently deleted.', [props.task.subject]))
    emit('close')
    emit('update')
  } catch (e) {
    console.error('Failed to delete task:', e)
    showError(__('Delete failed'), (e as Error).message || __('Could not delete the task. Please try again.'))
  } finally {
    isDeleting.value = false
  }
}

async function handleUpdateFinance(field: string, value: number | boolean): Promise<void> {
  // Optimistic update so the finance tab UI reflects the change immediately
  const oldValue = (props.task as Record<string, unknown>)[field]
  ;(props.task as Record<string, unknown>)[field] = value
  try {
    await updateTask(props.task.name, { [field]: value })
    // actual_cost changes affect project-level "spent" — refresh project data
    if (field === 'actual_cost') {
      emit('update')
    }
  } catch (e) {
    // Revert on failure
    ;(props.task as Record<string, unknown>)[field] = oldValue
    console.error('Failed to update finance field:', e)
  }
}

// ============================================
// Watch & Load
// ============================================

// UX pattern: Persist active tab across task switches (session-level persistence).
// SAP Fiori, Figma, and Xcode all keep the inspector tab when switching items.
// This supports "batch review" workflows (e.g. reviewing finance across multiple tasks).
// Tab state is managed by ManagerTabs via localStorage — we do NOT reset it here.
// On save/edit within a tab, the tab stays as-is (no reload destroys the component).

watch(() => props.task?.name, (newVal) => {
  if (newVal) {
    // Reload tab data for the new/refreshed task
    loadChecklist()
    loadDependencies()
    loadAttachments()
  }
}, { immediate: true })
</script>

<template>
  <div v-if="task" class="h-full flex flex-col bg-white dark:bg-gray-900 transition-colors">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between shrink-0">
      <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
        <i class="fa-solid fa-sliders text-orga-500"></i>
        <span>{{ __('Manager') }}</span>
      </h3>
      <button
        @click="emit('close')"
        class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :title="__('Close')"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <!-- Tab Navigation -->
    <ManagerTabs
      :tabs="taskTabs"
      :default-tab="activeTab"
      storage-key="task-manager"
      section-label="TASK"
      @change="activeTab = $event"
    />

    <!-- Tab Content -->
    <ManagerTabContent :active-tab="activeTab" :tabs="taskTabs" class="flex-1">
      <!-- Details Tab -->
      <template #details>
        <TaskDetailsTab
          :task="task"
          :contacts="contacts"
          :available-groups="availableGroups"
          @date-change="handleTaskDateChange"
          @progress-change="handleTaskProgressChange"
          @description-change="handleTaskDescriptionChange"
          @subject-change="handleTaskSubjectChange"
          @assign-contact="handleAssignContact"
          @task-group-change="handleTaskGroupChange"
          @task-type-change="handleTaskTypeChange"
          @depends-on-group-change="handleDependsOnGroupChange"
          @auto-trail-change="handleAutoTrailChange"
        />
      </template>

      <!-- Dependencies Tab -->
      <template #dependencies>
        <!-- Use visual DependencyChain for Gantt view -->
        <div v-if="isGanttView && ganttTask" class="p-4">
          <DependencyChain
            :task-id="task.name"
            :task-name="task.subject"
            :dependencies="dependenciesInfo"
            :dependents="dependentsInfo"
            :is-blocked="isBlocked"
            :available-tasks="availableTasksForDependency"
            @navigate="handleNavigateToTask"
            @add="handleAddDependency"
            @remove="(dependsOn) => handleRemoveDependency(dependsOn)"
          />
        </div>
        <!-- Standard dependency tab for Kanban/List -->
        <TaskDependenciesTab
          v-else
          :task="task"
          :predecessors="predecessors"
          :successors="successors"
          :available-tasks="availableTasksForDependency"
          :is-loading="isLoadingDependencies"
          @add-dependency="handleAddDependency"
          @update-dependency="handleUpdateDependency"
          @remove-dependency="handleRemoveDependency"
        />
      </template>

      <!-- Cascade Tab (Gantt only - shows when task has dependents) -->
      <template v-if="isGanttView && hasDependents" #cascade>
        <div class="p-4">
          <CascadePreview
            v-if="cascadeChanges.length > 0"
            :changes="cascadeChanges"
            :loading="isSavingCascade"
            @preview="handleCascadePreview"
            @apply="handleCascadeApply"
            @cancel="handleCascadeCancel"
          />
          <div v-else class="text-center py-8 text-gray-400">
            <i class="fa-solid fa-sitemap text-3xl mb-3 opacity-50"></i>
            <p class="text-sm">{{ __('No pending cascade changes') }}</p>
            <p class="text-xs mt-2">{{ __('Date changes on this task will show cascade impact here') }}</p>
          </div>
        </div>
      </template>

      <!-- Time Tab -->
      <template #time>
        <TaskTimeTab
          :key="timeTabKey"
          :task="task"
          @update="loadTaskData()"
          @open-manual-entry="showManualTimeEntry = true"
        />
      </template>

      <!-- Finance Tab -->
      <template #finance>
        <!-- Include BudgetBurnRate for Gantt view with budget -->
        <div v-if="isGanttView && hasBudget && ganttTask" class="p-4 border-b border-gray-200 dark:border-gray-700">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
            <i class="fa-solid fa-chart-line text-orga-500"></i>
            {{ __('Budget Burn Rate') }}
          </h5>
          <BudgetBurnRate
            :budget="ganttTask.budget || 0"
            :spent="ganttTask.spent || 0"
            :show-labels="true"
            size="md"
          />
        </div>
        <TaskFinanceTab :task="task" @update-finance="handleUpdateFinance" />
      </template>

      <!-- Checklist Tab -->
      <template #checklist>
        <TaskChecklistTab
          :checklist="checklist"
          :is-loading="isLoadingChecklist"
          :is-adding="isAddingChecklistItem"
          @add="handleAddChecklistItem"
          @toggle="handleToggleChecklistItem"
          @delete="handleDeleteChecklistItem"
          @promote="handlePromoteChecklistItem"
        />
      </template>

      <!-- Discussion Tab -->
      <template #discussion>
        <ActivityDiscussionTab
          doctype="Orga Task"
          :docname="task.name"
        />
      </template>

      <!-- Attachments Tab -->
      <template #attachments>
        <TaskAttachmentsTab
          :attachments="attachments"
          :is-loading="isLoadingAttachments"
          :is-uploading="isUploadingAttachment"
          :upload-progress="uploadProgress"
          @upload="handleUploadFile"
          @delete="handleDeleteAttachment"
        />
      </template>

      <!-- Actions Tab -->
      <template #actions>
        <TaskActionsTab
          :task="task"
          :columns="columns"
          @status-change="handleStatusChange"
          @priority-change="handlePriorityChange"
          @navigate="handleNavigate"
          @assign-to-me="handleAssignToMe"
          @duplicate="handleDuplicate"
          @delete="handleDelete"
        />
      </template>
    </ManagerTabContent>

    <!-- Manual Time Entry Modal -->
    <ManualTimeEntryModal
      :show="showManualTimeEntry"
      default-context="task"
      :default-task="task.name"
      @close="showManualTimeEntry = false"
      @created="loadTaskData()"
    />

    <!-- Delete Confirmation Modal (Teleported to body to escape overflow-hidden) -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="absolute inset-0 bg-black/60"
          @click="!isDeleting && (showDeleteConfirm = false)"
        ></div>
        <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-sm border border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3 p-5 pb-4 border-b border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 rounded-t-xl">
            <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center flex-shrink-0">
              <i class="fa-solid fa-triangle-exclamation text-red-600 dark:text-red-400 text-lg"></i>
            </div>
            <h3 class="text-lg font-semibold text-red-900 dark:text-red-200 m-0">{{ __('Delete Task') }}</h3>
            <button
              @click="showDeleteConfirm = false"
              :disabled="isDeleting"
              class="ml-auto text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
            >
              <i class="fa-solid fa-xmark text-lg"></i>
            </button>
          </div>
          <div class="p-5">
            <p class="text-sm text-gray-700 dark:text-gray-300 m-0">
              {{ __('This will permanently delete') }} "<strong>{{ task.subject }}</strong>". {{ __('This action') }} <strong class="text-red-600 dark:text-red-400">{{ __('cannot be undone') }}</strong>.
            </p>
          </div>
          <div class="flex justify-end gap-3 p-5 pt-0">
            <button
              @click="showDeleteConfirm = false"
              :disabled="isDeleting"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {{ __('Cancel') }}
            </button>
            <button
              @click="confirmAndDelete"
              :disabled="isDeleting"
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 disabled:opacity-75 disabled:cursor-not-allowed"
            >
              <i v-if="isDeleting" class="fa-solid fa-spinner fa-spin"></i>
              <i v-else class="fa-solid fa-trash"></i>
              {{ isDeleting ? __('Deleting...') : __('Delete') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
