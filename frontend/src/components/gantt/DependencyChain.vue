<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * DependencyChain - Visual dependency flowchart for Gantt focus panel
 *
 * Displays dependencies as a vertical flowchart:
 * - Predecessors (tasks this depends on) above
 * - Current task highlighted in the middle
 * - Successors (tasks that depend on this) below
 */

import { ref, computed } from 'vue'
import type { TaskDependencyInfo, DependencyType, OrgaTask, GanttTask } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

interface Props {
  taskId: string
  taskName: string
  dependencies: TaskDependencyInfo[]   // Tasks this depends on
  dependents: TaskDependencyInfo[]     // Tasks that depend on this
  isBlocked?: boolean
  availableTasks?: (OrgaTask | GanttTask)[]  // Tasks available for linking
}

const props = withDefaults(defineProps<Props>(), {
  isBlocked: false,
  availableTasks: () => []
})

const emit = defineEmits<{
  (e: 'navigate', taskId: string): void
  (e: 'add', taskName: string, dependsOn: string, type: DependencyType): void
  (e: 'remove', dependsOn: string): void
  (e: 'edit', payload: { dependsOn: string; type: DependencyType; lag: number }): void
}>()

// Add dependency form state
const isAddingDep = ref(false)
const newDepType = ref<DependencyType>('FS')
const newDepSearch = ref('')
const selectedDepTask = ref('')

const filteredAvailableTasks = computed(() => {
  const search = newDepSearch.value.toLowerCase()
  const existingDeps = new Set(props.dependencies.map(d => d.task_id))
  return props.availableTasks.filter(t =>
    t.name !== props.taskId &&
    !existingDeps.has(t.name) &&
    (!search || t.subject.toLowerCase().includes(search))
  )
})

function handleAdd(): void {
  if (!selectedDepTask.value) return
  emit('add', props.taskId, selectedDepTask.value, newDepType.value)
  selectedDepTask.value = ''
  newDepSearch.value = ''
  isAddingDep.value = false
}

function cancelAdd(): void {
  isAddingDep.value = false
  selectedDepTask.value = ''
  newDepSearch.value = ''
}

// Dependency type labels
const typeLabels: Record<string, string> = {
  FS: __('Finish-to-Start'),
  SS: __('Start-to-Start'),
  FF: __('Finish-to-Finish'),
  SF: __('Start-to-Finish'),
  'Finish to Start': 'FS',
  'Start to Start': 'SS',
  'Finish to Finish': 'FF',
  'Start to Finish': 'SF'
}

// Get short label for dependency type
function getTypeShort(type: string): string {
  return typeLabels[type] || type.split(' ').map(w => w[0]).join('')
}

// Get full label for dependency type
function getTypeFull(type: string): string {
  const shortToFull: Record<string, string> = {
    FS: __('Finish-to-Start'),
    SS: __('Start-to-Start'),
    FF: __('Finish-to-Finish'),
    SF: __('Start-to-Finish')
  }
  return shortToFull[type] || type
}

// Status colors
function getStatusColor(status?: string): string {
  switch (status) {
    case 'Completed': return 'text-green-600'
    case 'In Progress': return 'text-blue-600'
    case 'Cancelled': return 'text-gray-400'
    default: return 'text-gray-600'
  }
}

// Check if dependency is completed
function isCompleted(status?: string): boolean {
  return status === 'Completed'
}

// Has dependencies
const hasDependencies = computed(() => props.dependencies.length > 0)
const hasDependents = computed(() => props.dependents.length > 0)
</script>

<template>
  <div class="dependency-chain">
    <!-- Section header -->
    <div class="flex items-center justify-between mb-3">
      <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
        <i class="fa-solid fa-link text-orga-500"></i>
        {{ __('Dependencies') }}
      </h5>
      <button
        v-if="!isAddingDep"
        @click="isAddingDep = true; newDepSearch = ''; selectedDepTask = ''"
        class="text-xs text-orga-500 hover:text-orga-600 flex items-center gap-1"
      >
        <i class="fa-solid fa-plus"></i>
        {{ __('Add') }}
      </button>
      <button
        v-else
        @click="cancelAdd"
        class="text-xs text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 font-medium transition-colors"
      >
        {{ __('Cancel') }}
      </button>
    </div>

    <!-- Add dependency form -->
    <div v-if="isAddingDep" class="mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-2">
      <!-- Current task (read-only context) -->
      <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <i class="fa-solid fa-circle-dot text-orga-500 text-[10px]"></i>
        <span class="truncate font-medium text-gray-700 dark:text-gray-300">{{ taskName }}</span>
        <span class="text-gray-400">{{ __('depends on...') }}</span>
      </div>

      <!-- Dependency type -->
      <select
        v-model="newDepType"
        class="w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300"
      >
        <option value="FS">{{ __('FS - Finish-to-Start (default)') }}</option>
        <option value="SS">{{ __('SS - Start-to-Start') }}</option>
        <option value="FF">{{ __('FF - Finish-to-Finish') }}</option>
        <option value="SF">{{ __('SF - Start-to-Finish') }}</option>
      </select>

      <!-- Task search -->
      <input
        v-model="newDepSearch"
        type="text"
        :placeholder="__('Search for a task...')"
        class="w-full px-2.5 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-orga-500 focus:ring-1 focus:ring-orga-500"
      />

      <!-- Task suggestions (always visible, click to add) -->
      <div class="max-h-36 overflow-y-auto rounded border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div
          v-for="t in filteredAvailableTasks.slice(0, 10)"
          :key="t.name"
          @click="selectedDepTask = t.name; handleAdd()"
          class="flex items-center gap-2 px-2.5 py-2 hover:bg-orga-50 dark:hover:bg-gray-700 cursor-pointer transition-colors border-b border-gray-100 dark:border-gray-700 last:border-b-0"
        >
          <i class="fa-solid fa-plus text-[10px] text-gray-300 dark:text-gray-600"></i>
          <span class="text-sm text-gray-700 dark:text-gray-300 truncate flex-1">{{ t.subject }}</span>
        </div>
        <p
          v-if="filteredAvailableTasks.length === 0"
          class="text-xs text-gray-400 dark:text-gray-500 text-center py-3"
        >
          {{ newDepSearch ? __('No matching tasks found') : __('No tasks available to add') }}
        </p>
      </div>
    </div>

    <!-- Blocked warning -->
    <div v-if="isBlocked" class="mb-3 px-3 py-2 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
      <i class="fa-solid fa-lock"></i>
      <span>{{ __('Task is blocked by incomplete dependencies') }}</span>
    </div>

    <!-- Dependency flow -->
    <div class="bg-gray-50 rounded-lg p-3">
      <!-- Empty state -->
      <div v-if="!hasDependencies && !hasDependents" class="text-center py-4 text-sm text-gray-400">
        <i class="fa-solid fa-link text-2xl mb-2 opacity-50"></i>
        <p>{{ __('No dependencies defined') }}</p>
        <button
          @click="isAddingDep = true; newDepSearch = ''; selectedDepTask = ''"
          class="mt-2 text-orga-500 hover:text-orga-600"
        >
          {{ __('Add first dependency') }}
        </button>
      </div>

      <!-- Has dependencies -->
      <div v-else class="space-y-1">
        <!-- Predecessors (tasks this depends on) -->
        <div v-if="hasDependencies" class="space-y-1">
          <div
            v-for="dep in dependencies"
            :key="dep.task_id"
            class="group"
          >
            <button
              @click="emit('navigate', dep.task_id)"
              class="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 transition-colors text-left"
            >
              <span
                :class="[
                  'w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0',
                  isCompleted(dep.status) ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-500'
                ]"
              >
                <i :class="['fa-solid', isCompleted(dep.status) ? 'fa-check' : 'fa-circle text-[6px]']"></i>
              </span>
              <span :class="['text-sm flex-1 truncate', getStatusColor(dep.status)]">
                {{ dep.task_name }}
              </span>
              <span class="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                {{ getTypeShort(dep.type) }}
              </span>
              <button
                @click.stop="emit('remove', dep.task_id)"
                class="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                :title="__('Remove dependency')"
              >
                <i class="fa-solid fa-times text-xs"></i>
              </button>
            </button>
          </div>
        </div>

        <!-- Connector line from predecessors -->
        <div v-if="hasDependencies" class="flex items-center justify-center py-1">
          <div class="flex flex-col items-center text-gray-400">
            <div class="w-px h-3 bg-gray-300"></div>
            <i class="fa-solid fa-chevron-down text-[10px]"></i>
          </div>
        </div>

        <!-- Current task (highlighted) -->
        <div class="px-2 py-2 bg-orga-50 border border-orga-200 rounded-lg">
          <div class="flex items-center gap-2">
            <span class="w-5 h-5 rounded-full bg-orga-500 flex items-center justify-center text-white text-xs shrink-0">
              <i class="fa-solid fa-circle text-[6px]"></i>
            </span>
            <span class="text-sm font-medium text-orga-700 flex-1 truncate">{{ taskName }}</span>
            <span class="text-[10px] text-orga-500 bg-orga-100 px-1.5 py-0.5 rounded">
              {{ __('Current') }}
            </span>
          </div>
        </div>

        <!-- Connector line to successors -->
        <div v-if="hasDependents" class="flex items-center justify-center py-1">
          <div class="flex flex-col items-center text-gray-400">
            <i class="fa-solid fa-chevron-down text-[10px]"></i>
            <div class="w-px h-3 bg-gray-300"></div>
          </div>
        </div>

        <!-- Successors (tasks that depend on this) -->
        <div v-if="hasDependents" class="space-y-1">
          <div
            v-for="dep in dependents"
            :key="dep.task_id"
            class="group"
          >
            <button
              @click="emit('navigate', dep.task_id)"
              class="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 transition-colors text-left"
            >
              <span
                :class="[
                  'w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0',
                  isCompleted(dep.status) ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-500'
                ]"
              >
                <i :class="['fa-solid', isCompleted(dep.status) ? 'fa-check' : 'fa-circle text-[6px]']"></i>
              </span>
              <span :class="['text-sm flex-1 truncate', getStatusColor(dep.status)]">
                {{ dep.task_name }}
              </span>
              <span class="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                {{ __('depends') }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-3 text-[10px] text-gray-400 flex items-center gap-3">
      <span class="flex items-center gap-1">
        <i class="fa-solid fa-check text-green-500"></i> {{ __('Completed') }}
      </span>
      <span class="flex items-center gap-1">
        <i class="fa-solid fa-circle text-[4px] text-gray-400"></i> {{ __('Pending') }}
      </span>
    </div>
  </div>
</template>
