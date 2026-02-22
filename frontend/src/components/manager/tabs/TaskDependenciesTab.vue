<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskDependenciesTab.vue - Task dependencies tab for Task Manager

  Supports dependency types:
  - FS: Finish-to-Start (default) - Task B starts when Task A finishes
  - SS: Start-to-Start - Task B starts when Task A starts
  - FF: Finish-to-Finish - Task B finishes when Task A finishes
  - SF: Start-to-Finish - Task B finishes when Task A starts
-->
<template>
  <div class="flex flex-col h-full">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading dependencies...') }}</p>
    </div>

    <template v-else>
      <!-- Predecessors (Blocked By) -->
      <div class="mb-6">
        <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <i class="fa-solid fa-arrow-left text-orga-500"></i>
          {{ __('Predecessors (Blocked By)') }}
        </h5>

        <div v-if="predecessors.length" class="space-y-2">
          <div
            v-for="dep in predecessors"
            :key="dep.name"
            class="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden"
          >
            <!-- Delete confirmation (replaces the normal row) -->
            <div
              v-if="confirmingDelete === dep.name"
              class="p-2.5 bg-red-50 dark:bg-red-900/20 flex items-center gap-2 text-xs"
            >
              <i class="fa-solid fa-triangle-exclamation text-red-500"></i>
              <span class="text-red-600 dark:text-red-400 flex-1">{{ __('Remove dependency on') }} <strong>{{ dep.depends_on_subject || dep.depends_on }}</strong>?</span>
              <button
                @click="confirmingDelete = null"
                class="px-2.5 py-1 text-gray-600 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                {{ __('Cancel') }}
              </button>
              <button
                @click="handleConfirmDelete(dep.name)"
                class="px-2.5 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
              >
                {{ __('Remove') }}
              </button>
            </div>

            <!-- Inline edit row -->
            <div v-else-if="editingDep === dep.name" class="p-2.5 space-y-2 border border-orga-300 dark:border-orga-700 rounded-lg">
              <p class="text-xs text-gray-600 dark:text-gray-300 truncate font-medium">
                <i class="fa-solid fa-pen text-orga-500 mr-1"></i>
                {{ dep.depends_on_subject || dep.depends_on }}
              </p>
              <div class="flex items-center gap-2">
                <select
                  v-model="editType"
                  class="px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 flex-1"
                >
                  <option value="FS">{{ __('FS (Finish-Start)') }}</option>
                  <option value="SS">{{ __('SS (Start-Start)') }}</option>
                  <option value="FF">{{ __('FF (Finish-Finish)') }}</option>
                  <option value="SF">{{ __('SF (Start-Finish)') }}</option>
                </select>
                <div class="flex items-center gap-1">
                  <input
                    v-model.number="editLag"
                    type="number"
                    min="0"
                    class="w-14 px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-center"
                    placeholder="0"
                  />
                  <span class="text-[10px] text-gray-400 whitespace-nowrap">{{ __('d lag') }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1.5 justify-end pt-1">
                <button
                  @click="cancelEditing"
                  class="px-2.5 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  {{ __('Cancel') }}
                </button>
                <button
                  @click="saveEditing(dep.name)"
                  :disabled="isSaving"
                  class="px-2.5 py-1 text-xs bg-orga-500 text-white rounded hover:bg-orga-600 disabled:opacity-50 transition-colors"
                >
                  <i v-if="isSaving" class="fa-solid fa-spinner fa-spin mr-1"></i>
                  {{ __('Save') }}
                </button>
              </div>
            </div>

            <!-- Normal display row -->
            <div v-else class="flex items-center gap-2 p-2">
              <span :class="['px-1.5 py-0.5 text-[10px] font-mono rounded shrink-0', getDependencyTypeColor(dep.dependency_type)]">
                {{ dep.dependency_type || 'FS' }}
              </span>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-gray-800 dark:text-gray-200 truncate">{{ dep.depends_on_subject || dep.depends_on }}</p>
                <p class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ getDependencyTypeLabel(dep.dependency_type) }}
                  <span v-if="dep.lag_days" class="ml-1 text-orga-500">+{{ dep.lag_days }}d lag</span>
                </p>
              </div>
              <span :class="['text-[10px] px-1.5 py-0.5 rounded shrink-0', getStatusColor(dep.depends_on_status)]">
                {{ dep.depends_on_status }}
              </span>
              <div v-if="!readonly" class="flex items-center gap-0.5 shrink-0">
                <button
                  @click.stop="startEditing(dep)"
                  class="p-1 text-gray-400 dark:text-gray-500 hover:text-orga-500 dark:hover:text-orga-400 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  :title="__('Edit dependency')"
                >
                  <i class="fa-solid fa-pen text-[10px]"></i>
                </button>
                <button
                  @click.stop="confirmingDelete = dep.name"
                  class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  :title="__('Remove dependency')"
                >
                  <i class="fa-solid fa-trash-can text-[10px]"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <p v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-4">
          {{ __('No predecessors - this task can start independently') }}
        </p>
      </div>

      <!-- Successors (Blocking) -->
      <div class="mb-6">
        <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <i class="fa-solid fa-arrow-right text-orga-500"></i>
          {{ __('Successors (Blocking)') }}
        </h5>

        <div v-if="successors.length" class="space-y-2">
          <div
            v-for="dep in successors"
            :key="dep.name"
            class="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
          >
            <span :class="['px-1.5 py-0.5 text-[10px] font-mono rounded', getDependencyTypeColor(dep.dependency_type)]">
              {{ dep.dependency_type || 'FS' }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-800 dark:text-gray-200 truncate">{{ dep.task_subject || dep.task }}</p>
              <p class="text-[10px] text-gray-400 dark:text-gray-500">
                {{ __('Waiting for this task') }}
                <span v-if="dep.lag_days" class="ml-1 text-orga-500">+{{ dep.lag_days }}d lag</span>
              </p>
            </div>
            <span :class="['text-[10px] px-1.5 py-0.5 rounded', getStatusColor(dep.task_status)]">
              {{ dep.task_status }}
            </span>
          </div>
        </div>

        <p v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-4">
          {{ __('No successors - no tasks are waiting for this one') }}
        </p>
      </div>

      <!-- Add Dependency -->
      <div v-if="!readonly" class="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700">
        <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
          {{ __('Add Dependency') }}
        </h5>
        <div class="flex gap-2">
          <select
            v-model="newDependencyType"
            class="px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          >
            <option value="FS">{{ __('FS (Finish-Start)') }}</option>
            <option value="SS">{{ __('SS (Start-Start)') }}</option>
            <option value="FF">{{ __('FF (Finish-Finish)') }}</option>
            <option value="SF">{{ __('SF (Start-Finish)') }}</option>
          </select>
          <select
            v-model="selectedTask"
            class="flex-1 px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          >
            <option value="">{{ __('Select task...') }}</option>
            <option v-for="t in availableTasks" :key="t.name" :value="t.name">
              {{ t.subject }}
            </option>
          </select>
          <button
            @click="handleAddDependency"
            :disabled="!selectedTask || isAdding"
            class="px-3 py-1.5 bg-orga-500 text-white rounded text-xs hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i :class="['fa-solid', isAdding ? 'fa-spinner fa-spin' : 'fa-plus']"></i>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaTask, TaskDependency, DependencyType } from '@/types/orga'

interface Props {
  task: OrgaTask
  predecessors: TaskDependency[]
  successors: TaskDependency[]
  availableTasks: OrgaTask[]
  isLoading: boolean
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  'add-dependency': [taskName: string, dependsOn: string, type: DependencyType]
  'update-dependency': [dependencyName: string, type: DependencyType, lagDays: number]
  'remove-dependency': [dependencyName: string]
}>()

const newDependencyType = ref<DependencyType>('FS')
const selectedTask = ref('')
const isAdding = ref(false)

// Edit state
const editingDep = ref<string | null>(null)
const editType = ref<DependencyType>('FS')
const editLag = ref(0)
const isSaving = ref(false)

// Delete confirmation state
const confirmingDelete = ref<string | null>(null)

function startEditing(dep: TaskDependency) {
  editingDep.value = dep.name
  editType.value = dep.dependency_type || 'FS'
  editLag.value = dep.lag_days || 0
  confirmingDelete.value = null
}

function cancelEditing() {
  editingDep.value = null
}

function saveEditing(depName: string) {
  isSaving.value = true
  emit('update-dependency', depName, editType.value, editLag.value)
  editingDep.value = null
  isSaving.value = false
}

function handleConfirmDelete(depName: string) {
  confirmingDelete.value = null
  emit('remove-dependency', depName)
}

function handleAddDependency() {
  if (!selectedTask.value) return
  emit('add-dependency', props.task.name, selectedTask.value, newDependencyType.value)
  selectedTask.value = ''
}

function getDependencyTypeLabel(type?: DependencyType): string {
  const labels: Record<DependencyType, string> = {
    'FS': __('Must finish before this starts'),
    'SS': __('Must start before this starts'),
    'FF': __('Must finish before this finishes'),
    'SF': __('Must start before this finishes')
  }
  return labels[type || 'FS']
}

function getDependencyTypeColor(type?: DependencyType): string {
  const colors: Record<DependencyType, string> = {
    'FS': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'SS': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'FF': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    'SF': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  }
  return colors[type || 'FS']
}

function getStatusColor(status?: string): string {
  const colors: Record<string, string> = {
    'Open': 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    'In Progress': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'Review': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'Completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'Cancelled': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
  return colors[status || 'Open'] || colors['Open']
}
</script>
