<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskPanel.vue - Task Manager Panel with tabbed interface

  Reorganized tab structure for reduced cognitive load:
  - Details: Task metadata and assignment info
  - Checklist: Subtasks and progress tracking
  - Comments: Discussion and collaboration
  - Actions: Status changes and quick actions
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useTaskApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'
import UserAvatar from '@/components/common/UserAvatar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { OrgaTask, TaskChecklistItem, TaskComment, TaskStatus, TaskPriority } from '@/types/orga'

// Tab definition
type TabId = 'details' | 'checklist' | 'comments' | 'actions'

interface Tab {
  id: TabId
  label: string
  icon: string
  badge?: number | string
}

// Kanban column interface
interface KanbanColumn {
  id: TaskStatus
  title: string
  color?: string
}

interface Props {
  task: OrgaTask
  columns?: KanbanColumn[]
}

const props = withDefaults(defineProps<Props>(), {
  columns: () => []
})

const emit = defineEmits<{
  (e: 'update'): void
  (e: 'close'): void
  (e: 'status-change', task: OrgaTask, newStatus: TaskStatus): void
}>()

// Active tab state
const activeTab = ref<TabId>('details')

const {
  getChecklist,
  addChecklistItem,
  toggleChecklistItem,
  deleteChecklistItem,
  getComments,
  addComment,
  deleteComment
} = useTaskApi()

const { success: showSuccess, error: showError } = useToast()

// Local state
const checklist = ref<TaskChecklistItem[]>([])
const comments = ref<TaskComment[]>([])
const newChecklistItem = ref<string>('')
const newComment = ref<string>('')
const isLoadingChecklist = ref<boolean>(false)
const isLoadingComments = ref<boolean>(false)
const isAddingItem = ref<boolean>(false)
const isAddingComment = ref<boolean>(false)

// Tab definitions with dynamic badges
const tabs = computed<Tab[]>(() => [
  { id: 'details', label: __('Details'), icon: 'fa-circle-info' },
  {
    id: 'checklist',
    label: __('Checklist'),
    icon: 'fa-list-check',
    badge: checklist.value.length > 0 ? `${getChecklistProgress()}%` : undefined
  },
  {
    id: 'comments',
    label: __('Comments'),
    icon: 'fa-comments',
    badge: comments.value.length > 0 ? comments.value.length : undefined
  },
  { id: 'actions', label: __('Actions'), icon: 'fa-bolt' }
])

// Load checklist
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

// Load comments
async function loadComments(): Promise<void> {
  if (!props.task?.name) return
  isLoadingComments.value = true
  try {
    const data = await getComments(props.task.name)
    comments.value = data || []
  } catch (e) {
    console.error('Failed to load comments:', e)
    comments.value = []
  } finally {
    isLoadingComments.value = false
  }
}

// Add checklist item
async function handleAddChecklistItem(): Promise<void> {
  if (!newChecklistItem.value.trim() || isAddingItem.value) return

  const itemTitle = newChecklistItem.value.trim()
  isAddingItem.value = true
  try {
    await addChecklistItem(props.task.name, itemTitle)
    newChecklistItem.value = ''
    await loadChecklist()
    emit('update')
    showSuccess(__('Item added'), __('"{0}" added to checklist', [itemTitle]))
  } catch (e) {
    console.error('Failed to add checklist item:', e)
    showError(__('Failed to add item'), __('Please try again'))
  } finally {
    isAddingItem.value = false
  }
}

// Toggle checklist item
async function handleToggleChecklistItem(item: TaskChecklistItem): Promise<void> {
  try {
    await toggleChecklistItem(props.task.name, item.name)
    await loadChecklist()
    emit('update')
    const status = item.is_completed ? __('reopened') : __('completed')
    showSuccess(__('Item {0}', [status]), __('"{0}" marked as {1}', [item.title, status]))
  } catch (e) {
    console.error('Failed to toggle checklist item:', e)
    showError(__('Failed to update item'), __('Please try again'))
  }
}

// Delete checklist item
async function handleDeleteChecklistItem(item: TaskChecklistItem): Promise<void> {
  try {
    await deleteChecklistItem(props.task.name, item.name)
    await loadChecklist()
    emit('update')
    showSuccess(__('Item removed'), __('"{0}" removed from checklist', [item.title]))
  } catch (e) {
    console.error('Failed to delete checklist item:', e)
    showError(__('Failed to remove item'), __('Please try again'))
  }
}

// Add comment
async function handleAddComment(): Promise<void> {
  if (!newComment.value.trim() || isAddingComment.value) return

  isAddingComment.value = true
  try {
    await addComment(props.task.name, newComment.value.trim())
    newComment.value = ''
    await loadComments()
    showSuccess(__('Comment added'), __('Your comment has been posted'))
  } catch (e) {
    console.error('Failed to add comment:', e)
    showError(__('Failed to post comment'), __('Please try again'))
  } finally {
    isAddingComment.value = false
  }
}

// Delete comment
async function handleDeleteComment(comment: TaskComment): Promise<void> {
  try {
    await deleteComment(props.task.name, comment.name)
    await loadComments()
    showSuccess(__('Comment removed'), __('The comment has been deleted'))
  } catch (e) {
    console.error('Failed to delete comment:', e)
    showError(__('Failed to delete comment'), __('Please try again'))
  }
}

// Handle status change
function handleStatusChange(newStatus: TaskStatus): void {
  emit('status-change', props.task, newStatus)
}

// Format date
function formatDate(date: string | null | undefined): string {
  if (!date) return 'Not set'
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Format relative time
function formatRelativeTime(timestamp: string | null | undefined): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(timestamp)
}

// Checklist progress
function getChecklistProgress(): number {
  if (!checklist.value.length) return 0
  const completed = checklist.value.filter((item: TaskChecklistItem) => item.is_completed).length
  return Math.round((completed / checklist.value.length) * 100)
}

// Track previous task to detect actual task switches vs. data refreshes
let previousTaskName: string | undefined

// Watch for task changes - only reset tab when switching to a different task
watch(() => props.task?.name, (newVal) => {
  if (newVal) {
    loadChecklist()
    loadComments()
    // Only reset to details tab when switching to a different task,
    // not when the same task is refreshed after a save
    if (newVal !== previousTaskName) {
      activeTab.value = 'details'
    }
    previousTaskName = newVal
  }
}, { immediate: true })
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-900">
    <!-- Header with Task Info -->
    <div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-700">
      <!-- Title Bar -->
      <div class="p-3 flex items-center justify-between">
        <h3 class="font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
          <i class="fa-solid fa-sliders text-orga-500"></i> {{ __('Manager') }}
        </h3>
        <button
          @click="emit('close')"
          class="w-7 h-7 rounded-lg flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800 transition-colors"
        >
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <!-- Task Summary (Always Visible) -->
      <div class="px-3 pb-3">
        <div class="flex items-start gap-2 mb-2">
          <StatusBadge :status="task.priority" type="priority" size="sm" />
          <StatusBadge :status="task.status" type="task" size="sm" />
        </div>
        <h4 class="text-base font-semibold text-gray-800 dark:text-gray-100 m-0 leading-tight">
          {{ task.subject }}
        </h4>
        <p class="text-xs text-gray-500 dark:text-gray-500 m-0 mt-1">{{ task.name }}</p>
      </div>

      <!-- Tab Navigation -->
      <div class="flex border-t border-gray-100 dark:border-gray-800">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex-1 px-2 py-2.5 text-xs font-medium transition-colors relative',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orga-500',
            activeTab === tab.id
              ? 'text-orga-600 dark:text-orga-400 bg-orga-50 dark:bg-orga-900/20'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
          ]"
        >
          <div class="flex items-center justify-center gap-1.5">
            <i :class="['fa-solid', tab.icon, 'text-[10px]']"></i>
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.badge"
              class="ml-0.5 px-1.5 py-0.5 text-[10px] rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
            >
              {{ tab.badge }}
            </span>
          </div>
          <!-- Active indicator -->
          <div
            v-if="activeTab === tab.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-orga-500"
          ></div>
        </button>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="flex-1 overflow-auto">
      <!-- Details Tab -->
      <div v-if="activeTab === 'details'" class="p-4 space-y-4">
        <!-- Assignment -->
        <div class="space-y-3">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Assignment') }}
          </h5>
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Assigned To') }}</span>
            <div v-if="task.assigned_to_name" class="flex items-center gap-2">
              <UserAvatar :name="task.assigned_to_name" :image="task.assigned_to_image" size="xs" color="orga" />
              <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ task.assigned_to_name }}</span>
            </div>
            <span v-else class="text-sm text-gray-400 dark:text-gray-500 italic">{{ __('Unassigned') }}</span>
          </div>
        </div>

        <!-- Dates -->
        <div class="space-y-3">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Dates') }}
          </h5>
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Due Date') }}</span>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ formatDate(task.due_date) }}</span>
          </div>
          <div v-if="task.start_date" class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Start Date') }}</span>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ formatDate(task.start_date) }}</span>
          </div>
        </div>

        <!-- Time Tracking -->
        <div v-if="task.estimated_hours || task.actual_hours" class="space-y-3">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Time Tracking') }}
          </h5>
          <div v-if="task.estimated_hours" class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Estimated') }}</span>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ task.estimated_hours }}h</span>
          </div>
          <div v-if="task.actual_hours" class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Actual') }}</span>
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ task.actual_hours }}h</span>
          </div>
          <div v-if="task.estimated_hours && task.actual_hours" class="flex items-center justify-between py-2">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{ __('Variance') }}</span>
            <span :class="[
              'text-sm font-medium',
              task.actual_hours > task.estimated_hours ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
            ]">
              {{ task.actual_hours > task.estimated_hours ? '+' : '' }}{{ (task.actual_hours - task.estimated_hours).toFixed(1) }}h
            </span>
          </div>
        </div>

        <!-- Description -->
        <div v-if="task.description" class="space-y-3">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Description') }}
          </h5>
          <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{{ task.description }}</p>
        </div>
      </div>

      <!-- Checklist Tab -->
      <div v-if="activeTab === 'checklist'" class="p-4">
        <!-- Progress bar -->
        <div v-if="checklist.length" class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-gray-600 dark:text-gray-400">{{ __('Progress') }}</span>
            <span class="text-xs font-semibold text-orga-600 dark:text-orga-400">{{ getChecklistProgress() }}%</span>
          </div>
          <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-orga-500 rounded-full transition-all duration-300"
              :style="{ width: getChecklistProgress() + '%' }"
            ></div>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoadingChecklist" class="flex items-center justify-center py-8">
          <i class="fa-solid fa-spinner fa-spin text-xl text-gray-400"></i>
        </div>

        <!-- Checklist items -->
        <div v-else class="space-y-2 mb-4">
          <div
            v-for="item in checklist"
            :key="item.name"
            class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 group transition-colors"
          >
            <button
              @click="handleToggleChecklistItem(item)"
              :class="[
                'w-5 h-5 rounded border-2 flex items-center justify-center transition-all shrink-0',
                item.is_completed
                  ? 'bg-orga-500 border-orga-500 text-white'
                  : 'border-gray-300 dark:border-gray-600 hover:border-orga-500'
              ]"
            >
              <i v-if="item.is_completed" class="fa-solid fa-check text-xs"></i>
            </button>
            <span :class="[
              'text-sm flex-1',
              item.is_completed ? 'text-gray-400 dark:text-gray-500 line-through' : 'text-gray-700 dark:text-gray-300'
            ]">
              {{ item.title }}
            </span>
            <button
              @click="handleDeleteChecklistItem(item)"
              class="w-6 h-6 rounded flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all"
            >
              <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
          </div>

          <!-- Empty state -->
          <div v-if="!checklist.length && !isLoadingChecklist" class="text-center py-8">
            <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <i class="fa-solid fa-list-check text-xl text-gray-400"></i>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('No checklist items yet') }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('Add items below to track subtasks') }}</p>
          </div>
        </div>

        <!-- Add checklist item -->
        <div class="flex gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
          <input
            v-model="newChecklistItem"
            @keyup.enter="handleAddChecklistItem"
            type="text"
            :placeholder="__('Add a checklist item...')"
            :disabled="isAddingItem"
            class="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20 disabled:opacity-50"
          />
          <button
            @click="handleAddChecklistItem"
            :disabled="isAddingItem || !newChecklistItem.trim()"
            class="px-4 py-2 bg-orga-500 text-white rounded-lg text-sm font-medium hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i :class="['fa-solid', isAddingItem ? 'fa-spinner fa-spin' : 'fa-plus']"></i>
          </button>
        </div>
      </div>

      <!-- Comments Tab -->
      <div v-if="activeTab === 'comments'" class="p-4">
        <!-- Loading -->
        <div v-if="isLoadingComments" class="flex items-center justify-center py-8">
          <i class="fa-solid fa-spinner fa-spin text-xl text-gray-400"></i>
        </div>

        <!-- Comments list -->
        <div v-else class="space-y-4 mb-4">
          <div
            v-for="comment in comments"
            :key="comment.name"
            class="group"
          >
            <div class="flex gap-3">
              <UserAvatar
                :name="comment.comment_by_name || comment.comment_by"
                size="sm"
                color="teal"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {{ comment.comment_by_name || comment.comment_by }}
                  </span>
                  <span class="text-xs text-gray-400 dark:text-gray-500">
                    {{ formatRelativeTime(comment.comment_time) }}
                  </span>
                  <button
                    @click="handleDeleteComment(comment)"
                    class="ml-auto w-6 h-6 rounded flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <i class="fa-solid fa-trash-can text-xs"></i>
                  </button>
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-400 m-0 leading-relaxed">{{ comment.content }}</p>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="!comments.length && !isLoadingComments" class="text-center py-8">
            <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <i class="fa-solid fa-comments text-xl text-gray-400"></i>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('No comments yet') }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('Start a discussion below') }}</p>
          </div>
        </div>

        <!-- Add comment -->
        <div class="flex gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
          <input
            v-model="newComment"
            @keyup.enter="handleAddComment"
            type="text"
            :placeholder="__('Write a comment...')"
            :disabled="isAddingComment"
            class="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:border-orga-500 focus:outline-none focus:ring-2 focus:ring-orga-500/20 disabled:opacity-50"
          />
          <button
            @click="handleAddComment"
            :disabled="isAddingComment || !newComment.trim()"
            class="px-4 py-2 bg-orga-500 text-white rounded-lg text-sm font-medium hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i :class="['fa-solid', isAddingComment ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
          </button>
        </div>
      </div>

      <!-- Actions Tab -->
      <div v-if="activeTab === 'actions'" class="p-4 space-y-6">
        <!-- Quick Status Change -->
        <div class="space-y-3">
          <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Change Status') }}
          </h5>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="col in columns"
              :key="col.id"
              @click="handleStatusChange(col.id)"
              :class="[
                'px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orga-500',
                task.status === col.id
                  ? 'bg-orga-500 text-white shadow-sm'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              ]"
            >
              {{ col.title }}
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
