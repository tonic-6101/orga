<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskActionsTab.vue - Actions tab content for Task Manager
  Includes status changes, priority, and quick actions
-->
<template>
  <div class="space-y-6">
    <!-- Quick Status Change -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-toggle-on text-orga-500"></i>
        {{ __('Change Status') }}
      </h5>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="col in columns"
          :key="col.id"
          @click="emit('status-change', col.id)"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
            task.status === col.id
              ? 'bg-orga-500 text-white border-orga-500'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-orga-500 hover:text-orga-500'
          ]"
        >
          {{ col.title }}
        </button>
      </div>
    </div>

    <!-- Priority Change -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-flag text-orga-500"></i>
        {{ __('Change Priority') }}
      </h5>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="priority in priorities"
          :key="priority"
          @click="emit('priority-change', priority)"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
            task.priority === priority
              ? priorityActiveColors[priority]
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-400'
          ]"
        >
          {{ __(priority) }}
        </button>
      </div>
    </div>

    <!-- Quick Actions -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-bolt text-orga-500"></i>
        {{ __('Quick Actions') }}
      </h5>
      <div class="space-y-2">
        <!-- Navigate to Task -->
        <button
          @click="emit('navigate')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-external-link text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Open Task Log') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Audit trail, assignments, version history') }}</p>
          </div>
        </button>

        <!-- Assign to Me -->
        <button
          @click="emit('assign-to-me')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-user-plus text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Assign to Me') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Take ownership of this task') }}</p>
          </div>
        </button>

        <!-- Duplicate Task -->
        <button
          @click="emit('duplicate')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-copy text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Duplicate Task') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Create a copy of this task') }}</p>
          </div>
        </button>

        <!-- Delete Task (Danger) -->
        <button
          v-if="canDelete"
          @click="emit('delete')"
          class="w-full flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors text-left"
        >
          <i class="fa-solid fa-trash text-red-500"></i>
          <div>
            <p class="text-sm font-medium text-red-700 dark:text-red-400">{{ __('Delete Task') }}</p>
            <p class="text-xs text-red-500 dark:text-red-400">{{ __('Permanently remove this task') }}</p>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from '@/composables/useTranslate'
import type { OrgaTask, TaskStatus, TaskPriority } from '@/types/orga'

interface KanbanColumn {
  id: TaskStatus
  title: string
  color?: string
}

interface Props {
  task: OrgaTask
  columns: KanbanColumn[]
  canDelete?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canDelete: true
})

const emit = defineEmits<{
  'status-change': [status: TaskStatus]
  'priority-change': [priority: TaskPriority]
  'navigate': []
  'assign-to-me': []
  'duplicate': []
  'delete': []
}>()

const priorities: TaskPriority[] = ['Low', 'Medium', 'High', 'Urgent']

const priorityActiveColors: Record<TaskPriority, string> = {
  'Low': 'bg-gray-500 text-white border-gray-500',
  'Medium': 'bg-yellow-500 text-white border-yellow-500',
  'High': 'bg-orange-500 text-white border-orange-500',
  'Urgent': 'bg-red-500 text-white border-red-500'
}

</script>
