<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  @deprecated This component has been replaced by TaskManager.vue with viewType='gantt'.
  The unified TaskManager now provides consistent tabbed interface across all views
  (Kanban, List, Gantt) while preserving Gantt-specific features like:
  - DependencyChain visualization (in Dependencies tab)
  - CascadePreview (in Cascade tab when dependents exist)
  - BudgetBurnRate (in Financial tab)

  This file is kept for reference only. See Issue #015 for migration details.
  TODO: Remove this file after confirming no regressions in Gantt functionality.
-->
<script setup lang="ts">
/**
 * @deprecated Use TaskManager.vue with viewType='gantt' instead.
 *
 * GanttFocusPanel - Legacy side panel for viewing and editing task details from Gantt chart
 *
 * Features (now available in unified TaskManager):
 * - Task header with priority dropdown and status badge
 * - Editable task name and description
 * - Timeline section (assignee, duration, start/end dates)
 * - Budget section with burn rate visualization
 * - Visual dependency chain
 * - Cascade preview for date change impact
 * - Keyboard shortcuts (Escape to close, Enter to save)
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type {
  GanttTask,
  OrgaProject,
  TaskDependencyInfo,
  CascadeChange,
  TaskPriority,
  TaskStatus
} from '@/types/orga'
import DependencyChain from './DependencyChain.vue'
import CascadePreview from './CascadePreview.vue'
import BudgetBurnRate from './BudgetBurnRate.vue'
import { __ } from '@/composables/useTranslate'

interface Props {
  task: GanttTask
  project: OrgaProject
  allTasks: GanttTask[]
  visible: boolean
  editable?: boolean
  showBudget?: boolean
  showDependencies?: boolean
  showComments?: boolean
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  editable: true,
  showBudget: true,
  showDependencies: true,
  showComments: true,
  width: '380px'
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update', payload: { field: string; value: unknown; task_id: string }): void
  (e: 'add-dependency', payload: { task_id: string; depends_on: string; type: string; lag: number }): void
  (e: 'remove-dependency', payload: { task_id: string; depends_on: string }): void
  (e: 'navigate', payload: { task_id: string }): void
  (e: 'preview-cascade', payload: { changes: CascadeChange[] }): void
  (e: 'apply-cascade', payload: { task_id: string; changes: CascadeChange[] }): void
}>()

// Editing state
const isEditing = ref(false)
const editedTask = ref<Partial<GanttTask>>({})
const cascadeChanges = ref<CascadeChange[]>([])
const showCascadePreview = ref(false)
const isSaving = ref(false)

// Priority options
const priorityOptions: TaskPriority[] = ['Low', 'Medium', 'High', 'Urgent']

// Priority and status colors
const priorityColors: Record<TaskPriority, string> = {
  'Urgent': 'bg-red-100 text-red-700 border-red-200',
  'High': 'bg-orange-100 text-orange-700 border-orange-200',
  'Medium': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'Low': 'bg-gray-100 text-gray-600 border-gray-200'
}

const statusColors: Record<string, string> = {
  'Open': 'bg-gray-100 text-gray-600',
  'Working': 'bg-blue-100 text-blue-600',
  'Pending Review': 'bg-purple-100 text-purple-600',
  'Completed': 'bg-green-100 text-green-600',
  'Cancelled': 'bg-red-100 text-red-600'
}

// Computed values
const taskDuration = computed(() => {
  if (!props.task.start_date || !props.task.due_date) return null
  const start = new Date(props.task.start_date)
  const end = new Date(props.task.due_date)
  const diffTime = Math.abs(end.getTime() - start.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
})

const dependencies = computed<TaskDependencyInfo[]>(() => {
  return props.task.dependencies_info || []
})

const dependents = computed<TaskDependencyInfo[]>(() => {
  return props.task.dependents_info || []
})

const isBlocked = computed(() => {
  return props.task.is_blocked || false
})

const hasBudget = computed(() => {
  return props.task.budget !== undefined && props.task.budget > 0
})

// Initialize edited task when entering edit mode
function startEditing() {
  if (!props.editable) return
  isEditing.value = true
  editedTask.value = {
    subject: props.task.subject,
    description: props.task.description,
    start_date: props.task.start_date,
    due_date: props.task.due_date,
    priority: props.task.priority,
    assigned_to: props.task.assigned_to
  }
}

// Cancel editing
function cancelEditing() {
  isEditing.value = false
  editedTask.value = {}
  cascadeChanges.value = []
  showCascadePreview.value = false
}

// Save changes
async function saveChanges() {
  if (!isEditing.value || isSaving.value) return

  isSaving.value = true
  try {
    // Emit updates for each changed field
    for (const [field, value] of Object.entries(editedTask.value)) {
      if (value !== (props.task as Record<string, unknown>)[field]) {
        emit('update', { field, value, task_id: props.task.name })
      }
    }
    isEditing.value = false
    editedTask.value = {}
  } finally {
    isSaving.value = false
  }
}

// Handle date change - check for cascade
function handleDateChange(field: 'start_date' | 'due_date', newValue: string) {
  if (!editedTask.value) return

  const oldValue = props.task[field]
  editedTask.value[field] = newValue

  // Calculate cascade if there are dependents and dates changed
  if (dependents.value.length > 0 && oldValue !== newValue) {
    const oldDate = new Date(oldValue || '')
    const newDate = new Date(newValue)
    const daysDiff = Math.ceil((newDate.getTime() - oldDate.getTime()) / (1000 * 60 * 60 * 24))

    if (daysDiff !== 0) {
      // Calculate cascade changes
      cascadeChanges.value = calculateCascade(daysDiff)
      showCascadePreview.value = cascadeChanges.value.length > 0
    }
  }
}

// Calculate cascade effect on dependent tasks
function calculateCascade(dayShift: number): CascadeChange[] {
  const changes: CascadeChange[] = []
  const visited = new Set<string>()

  function findDependents(taskId: string, shift: number) {
    // Find tasks that depend on this task
    for (const t of props.allTasks) {
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

// Handle cascade preview
function handleCascadePreview() {
  emit('preview-cascade', { changes: cascadeChanges.value })
}

// Handle cascade apply
function handleCascadeApply() {
  emit('apply-cascade', { task_id: props.task.name, changes: cascadeChanges.value })
  cascadeChanges.value = []
  showCascadePreview.value = false
}

// Handle cascade cancel
function handleCascadeCancel() {
  // Revert date changes
  if (props.task.start_date) {
    editedTask.value.start_date = props.task.start_date
  }
  if (props.task.due_date) {
    editedTask.value.due_date = props.task.due_date
  }
  cascadeChanges.value = []
  showCascadePreview.value = false
}

// Navigate to another task
function handleNavigate(taskId: string) {
  emit('navigate', { task_id: taskId })
}

// Add dependency
function handleAddDependency() {
  // This will trigger a modal in the parent
  emit('add-dependency', {
    task_id: props.task.name,
    depends_on: '',
    type: 'FS',
    lag: 0
  })
}

// Remove dependency
function handleRemoveDependency(dependsOn: string) {
  emit('remove-dependency', {
    task_id: props.task.name,
    depends_on: dependsOn
  })
}

// Handle priority change
function handlePriorityChange(newPriority: TaskPriority) {
  if (isEditing.value) {
    editedTask.value.priority = newPriority
  } else {
    emit('update', { field: 'priority', value: newPriority, task_id: props.task.name })
  }
}

// Format date
function formatDate(date: string | null | undefined): string {
  if (!date) return __('Not set')
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

// Keyboard handler
function handleKeydown(e: KeyboardEvent) {
  if (!props.visible) return

  if (e.key === 'Escape') {
    if (isEditing.value) {
      cancelEditing()
    } else {
      emit('close')
    }
  } else if (e.key === 'Enter' && isEditing.value && !e.shiftKey) {
    saveChanges()
  } else if (e.key === 'e' && !isEditing.value && props.editable) {
    e.preventDefault()
    startEditing()
  }
}

// Watch for task changes
watch(() => props.task?.name, () => {
  // Reset editing state when task changes
  cancelEditing()
})

// Setup keyboard listeners
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Transition
    enter-active-class="transition-transform duration-200 ease-out"
    enter-from-class="translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-150 ease-in"
    leave-from-class="translate-x-0"
    leave-to-class="translate-x-full"
  >
    <div
      v-if="visible"
      class="gantt-focus-panel fixed right-0 top-0 h-full bg-white shadow-xl border-l border-gray-200 flex flex-col z-50"
      :style="{ width }"
    >
      <!-- Header -->
      <div class="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-bars-progress text-orga-500"></i>
          <h3 class="font-semibold text-gray-800 m-0">{{ __('Task Details') }}</h3>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="editable && !isEditing"
            @click="startEditing"
            class="text-gray-400 hover:text-orga-500 px-2 py-1 rounded hover:bg-orga-50"
            :title="__('Edit (E)')"
          >
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 px-2 py-1"
            :title="__('Close (Esc)')"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-auto">
        <!-- Cascade Preview -->
        <div class="p-4" v-if="showCascadePreview">
          <CascadePreview
            :changes="cascadeChanges"
            :loading="isSaving"
            @preview="handleCascadePreview"
            @apply="handleCascadeApply"
            @cancel="handleCascadeCancel"
          />
        </div>

        <!-- Task Header -->
        <div class="p-4 border-b border-gray-200">
          <div class="flex items-start justify-between mb-3">
            <!-- Priority dropdown -->
            <div class="relative">
              <select
                :value="isEditing ? editedTask.priority : task.priority"
                @change="handlePriorityChange(($event.target as HTMLSelectElement).value as TaskPriority)"
                :disabled="!editable"
                :class="[
                  'text-xs px-2 py-1 rounded-full border appearance-none cursor-pointer pr-6',
                  priorityColors[isEditing ? (editedTask.priority as TaskPriority) : task.priority]
                ]"
              >
                <option v-for="p in priorityOptions" :key="p" :value="p">{{ __(p) }}</option>
              </select>
              <i class="fa-solid fa-chevron-down absolute right-2 top-1/2 -translate-y-1/2 text-[8px] pointer-events-none"></i>
            </div>

            <!-- Status badge -->
            <span :class="['text-xs px-2 py-1 rounded-full', statusColors[task.status]]">
              {{ task.status }}
            </span>
          </div>

          <!-- Task name -->
          <div v-if="isEditing" class="mb-2">
            <input
              v-model="editedTask.subject"
              type="text"
              class="w-full text-lg font-semibold text-gray-800 border border-gray-200 rounded px-2 py-1 focus:border-orga-500 focus:outline-none"
              :placeholder="__('Task name')"
            />
          </div>
          <h4 v-else class="text-lg font-semibold text-gray-800 m-0 mb-2">{{ task.subject }}</h4>

          <p class="text-xs text-gray-500 m-0">{{ task.name }}</p>
        </div>

        <!-- Description -->
        <div class="p-4 border-b border-gray-200">
          <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-2">
            <i class="fa-solid fa-align-left text-orga-500"></i>
            {{ __('Description') }}
          </h5>
          <div v-if="isEditing">
            <textarea
              v-model="editedTask.description"
              rows="3"
              class="w-full text-sm text-gray-700 border border-gray-200 rounded px-2 py-1.5 focus:border-orga-500 focus:outline-none resize-none"
              :placeholder="__('Add a description...')"
            ></textarea>
          </div>
          <p v-else class="text-sm text-gray-700 m-0">
            {{ task.description || __('No description') }}
          </p>
        </div>

        <!-- Timeline Section -->
        <div class="p-4 border-b border-gray-200">
          <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-2">
            <i class="fa-solid fa-calendar text-orga-500"></i>
            {{ __('Timeline') }}
          </h5>

          <div class="space-y-3">
            <!-- Assigned To -->
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Assigned To') }}</span>
              <div v-if="task.assigned_to_name" class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-full bg-orga-500 flex items-center justify-center text-white text-xs font-medium">
                  {{ getInitials(task.assigned_to_name) }}
                </div>
                <span class="text-sm font-medium text-gray-800">{{ task.assigned_to_name }}</span>
              </div>
              <span v-else class="text-sm text-gray-400">{{ __('Unassigned') }}</span>
            </div>

            <!-- Duration -->
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Duration') }}</span>
              <span class="text-sm font-medium text-gray-800">
                {{ taskDuration ? (taskDuration === 1 ? __('1 day') : __('{0} days', [taskDuration])) : __('Not set') }}
              </span>
            </div>

            <!-- Start Date -->
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Start Date') }}</span>
              <input
                v-if="isEditing"
                type="date"
                :value="editedTask.start_date"
                @change="handleDateChange('start_date', ($event.target as HTMLInputElement).value)"
                class="text-sm font-medium text-gray-800 border border-gray-200 rounded px-2 py-0.5 focus:border-orga-500 focus:outline-none"
              />
              <span v-else class="text-sm font-medium text-gray-800">{{ formatDate(task.start_date) }}</span>
            </div>

            <!-- End/Due Date -->
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Due Date') }}</span>
              <input
                v-if="isEditing"
                type="date"
                :value="editedTask.due_date"
                @change="handleDateChange('due_date', ($event.target as HTMLInputElement).value)"
                class="text-sm font-medium text-gray-800 border border-gray-200 rounded px-2 py-0.5 focus:border-orga-500 focus:outline-none"
              />
              <span v-else class="text-sm font-medium text-gray-800">{{ formatDate(task.due_date) }}</span>
            </div>

            <!-- Hours -->
            <div v-if="task.estimated_hours" class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Estimated') }}</span>
              <span class="text-sm font-medium text-gray-800">{{ task.estimated_hours }}h</span>
            </div>
            <div v-if="task.actual_hours" class="flex items-center justify-between">
              <span class="text-sm text-gray-500">{{ __('Actual') }}</span>
              <span class="text-sm font-medium text-gray-800">{{ task.actual_hours }}h</span>
            </div>
          </div>
        </div>

        <!-- Budget Section -->
        <div v-if="showBudget && hasBudget" class="p-4 border-b border-gray-200">
          <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-2">
            <i class="fa-solid fa-euro-sign text-orga-500"></i>
            {{ __('Budget') }}
          </h5>
          <BudgetBurnRate
            :budget="task.budget || 0"
            :spent="task.spent || 0"
            :show-labels="true"
            size="md"
          />
        </div>

        <!-- Dependencies Section -->
        <div v-if="showDependencies" class="p-4 border-b border-gray-200">
          <DependencyChain
            :task-id="task.name"
            :task-name="task.subject"
            :dependencies="dependencies"
            :dependents="dependents"
            :is-blocked="isBlocked"
            @navigate="handleNavigate"
            @add="handleAddDependency"
            @remove="handleRemoveDependency"
          />
        </div>

        <!-- Edit Actions -->
        <div v-if="isEditing" class="p-4 border-b border-gray-200 bg-gray-50">
          <div class="flex items-center justify-end gap-2">
            <button
              @click="cancelEditing"
              :disabled="isSaving"
              class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
            >
              {{ __('Cancel') }}
            </button>
            <button
              @click="saveChanges"
              :disabled="isSaving"
              class="px-4 py-2 text-sm text-white bg-orga-500 hover:bg-orga-600 rounded disabled:opacity-50 flex items-center gap-2"
            >
              <i v-if="isSaving" class="fa-solid fa-spinner fa-spin"></i>
              <i v-else class="fa-solid fa-check"></i>
              {{ __('Save Changes') }}
            </button>
          </div>
        </div>

        <!-- Keyboard Hints -->
        <div class="p-4 text-center">
          <p class="text-xs text-gray-400">
            <span v-if="editable && !isEditing">{{ __('Press') }} <kbd class="px-1 py-0.5 bg-gray-100 rounded text-gray-500">E</kbd> {{ __('to edit') }}</span>
            <span v-else-if="isEditing">{{ __('Press') }} <kbd class="px-1 py-0.5 bg-gray-100 rounded text-gray-500">Enter</kbd> {{ __('to save,') }} <kbd class="px-1 py-0.5 bg-gray-100 rounded text-gray-500">Esc</kbd> {{ __('to cancel') }}</span>
            <span v-else>{{ __('Press') }} <kbd class="px-1 py-0.5 bg-gray-100 rounded text-gray-500">Esc</kbd> {{ __('to close') }}</span>
          </p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.gantt-focus-panel {
  max-width: 100vw;
}

@media (max-width: 640px) {
  .gantt-focus-panel {
    width: 100% !important;
  }
}

kbd {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
}
</style>
