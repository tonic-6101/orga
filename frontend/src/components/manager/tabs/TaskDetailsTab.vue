<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskDetailsTab.vue - Task details tab content for Task Manager
-->
<template>
  <div class="space-y-4">
    <!-- Priority, Status & Task Type Badges -->
    <div class="flex items-center gap-2 flex-wrap">
      <span :class="['px-2 py-1 text-xs rounded-full border', priorityColors[task.priority]]">
        <i class="fa-solid fa-flag mr-1"></i>
        {{ task.priority }}
      </span>
      <span :class="['px-2 py-1 text-xs rounded-full', statusColors[task.status]]">
        {{ task.status }}
      </span>
      <span
        v-if="task.task_type"
        :class="['px-2 py-1 text-xs rounded-full border', taskTypeColors[task.task_type] || taskTypeColors.default]"
      >
        <i :class="['mr-1', taskTypeIcons[task.task_type] || 'fa-solid fa-circle']"></i>
        {{ task.task_type }}
      </span>
    </div>

    <!-- Task Type (Editable Select) -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Task Type') }}</label>
      <select
        :value="task.task_type || ''"
        @change="handleTaskTypeChange(($event.target as HTMLSelectElement).value)"
        class="w-full mt-1 px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 cursor-pointer"
      >
        <option value="">{{ __('None') }}</option>
        <option value="Task">{{ __('Task') }}</option>
        <option value="Bug">{{ __('Bug') }}</option>
        <option value="Feature">{{ __('Feature') }}</option>
        <option value="Research">{{ __('Research') }}</option>
        <option value="Meeting">{{ __('Meeting') }}</option>
      </select>
    </div>

    <!-- Subject (Inline Editable) -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Subject') }}</label>
      <div v-if="isEditingSubject" class="mt-1">
        <input
          ref="subjectInputRef"
          v-model="editSubjectText"
          type="text"
          class="w-full px-2 py-1.5 text-sm font-medium border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400"
          @keydown.enter="saveSubject"
          @keydown.escape="cancelEditSubject"
          @blur="saveSubject"
        />
      </div>
      <p
        v-else
        @click="startEditSubject"
        class="text-sm text-gray-800 dark:text-gray-200 mt-1 font-medium cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
        :title="__('Click to edit')"
      >{{ task.subject }}</p>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ task.name }}</p>
    </div>

    <!-- Description (Inline Editable) -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Description') }}</label>
      <!-- Editing mode -->
      <div v-if="isEditingDescription" class="mt-1">
        <textarea
          v-model="editDescriptionText"
          rows="3"
          class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400 resize-y"
          :placeholder="__('Add a task description...')"
          @keydown.escape="cancelEditDescription"
        ></textarea>
        <div class="flex justify-end gap-2 mt-1.5">
          <button
            @click="cancelEditDescription"
            class="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="saveDescription"
            :disabled="isSavingDescription"
            class="px-2 py-1 text-xs font-medium text-white bg-orga-500 rounded hover:bg-orga-600 transition-colors disabled:opacity-50 flex items-center gap-1"
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
        class="mt-1 cursor-pointer group"
        :title="__('Click to edit description')"
      >
        <p
          v-if="task.description"
          class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap m-0 group-hover:text-orga-600 dark:group-hover:text-orga-400 transition-colors"
        >{{ task.description }}</p>
        <p v-else class="text-sm text-gray-400 dark:text-gray-500 m-0 italic group-hover:text-orga-500 dark:group-hover:text-orga-400 transition-colors">
          {{ __('Click to add description...') }}
        </p>
      </div>
    </div>

    <!-- Task Group (Inline Editable with Autocomplete) -->
    <div class="relative">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Task Group') }}</label>
      <div v-if="isEditingGroup" class="mt-1 relative">
        <input
          ref="groupInputRef"
          v-model="editGroupText"
          type="text"
          list="task-group-suggestions"
          placeholder="e.g. Pre-work, Finishing..."
          class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400"
          @keydown.enter="saveGroup"
          @keydown.escape="cancelEditGroup"
          @blur="saveGroup"
        />
        <datalist id="task-group-suggestions">
          <option v-for="g in availableGroups" :key="g" :value="g" />
        </datalist>
      </div>
      <div v-else @click="startEditGroup" class="mt-1 cursor-pointer group flex items-center gap-1.5">
        <span
          v-if="task.task_group"
          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 group-hover:bg-indigo-200 dark:group-hover:bg-indigo-900/50 transition-colors"
        >
          <i class="fa-solid fa-layer-group text-[9px]"></i>
          {{ task.task_group }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500 italic group-hover:text-orga-500 dark:group-hover:text-orga-400 transition-colors">
          {{ __('Click to set group...') }}
        </span>
        <button
          v-if="task.task_group"
          @click.stop="clearGroup"
          class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
          :title="__('Remove from group')"
        >
          <i class="fa-solid fa-xmark text-[10px]"></i>
        </button>
      </div>
    </div>

    <!-- Depends on Group (Inline Editable with Autocomplete) -->
    <div class="relative">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Depends on Group') }}</label>
      <div v-if="isEditingDependsOnGroup" class="mt-1 relative">
        <input
          ref="dependsOnGroupInputRef"
          v-model="editDependsOnGroupText"
          type="text"
          list="depends-on-group-suggestions"
          placeholder="e.g. Pre-work — blocks until all complete"
          class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400 focus:ring-1 focus:ring-orga-500 dark:focus:ring-orga-400"
          @keydown.enter="saveDependsOnGroup"
          @keydown.escape="cancelEditDependsOnGroup"
          @blur="saveDependsOnGroup"
        />
        <datalist id="depends-on-group-suggestions">
          <option v-for="g in availableGroups" :key="g" :value="g" />
        </datalist>
      </div>
      <div v-else @click="startEditDependsOnGroup" class="mt-1 cursor-pointer group flex items-center gap-1.5">
        <span
          v-if="task.depends_on_group"
          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 group-hover:bg-amber-200 dark:group-hover:bg-amber-900/50 transition-colors"
        >
          <i class="fa-solid fa-lock text-[9px]"></i>
          {{ __('Waits for:') }} {{ task.depends_on_group }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500 italic group-hover:text-orga-500 dark:group-hover:text-orga-400 transition-colors">
          {{ __('Click to set group dependency...') }}
        </span>
        <button
          v-if="task.depends_on_group"
          @click.stop="clearDependsOnGroup"
          class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
          :title="__('Remove group dependency')"
        >
          <i class="fa-solid fa-xmark text-[10px]"></i>
        </button>
      </div>
    </div>

    <!-- Contact Assignment (Clickable Picker) -->
    <div class="relative">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Assigned Contact') }}</label>
      <button
        @click="isAssigneeOpen = !isAssigneeOpen"
        class="w-full flex items-center gap-2 mt-1 px-2 py-1.5 rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
        :title="__('Click to assign contact')"
      >
        <template v-if="assignedContact">
          <UserAvatar :name="assignedContact.resource_name" size="xs" color="orga" />
          <span class="text-sm text-gray-800 dark:text-gray-200 flex-1">{{ assignedContact.resource_name }}</span>
        </template>
        <template v-else-if="task.assigned_to_name">
          <UserAvatar :name="task.assigned_to_name" :image="task.assigned_to_image" size="xs" color="orga" />
          <span class="text-sm text-gray-800 dark:text-gray-200 flex-1">{{ task.assigned_to_name }}</span>
        </template>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500 flex-1">{{ __('Unassigned') }}</span>
        <i class="fa-solid fa-chevron-down text-[10px] text-gray-400"></i>
      </button>
      <!-- Dropdown -->
      <div
        v-if="isAssigneeOpen"
        class="absolute left-0 right-0 mt-1 z-30 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto"
      >
        <!-- Unassign option -->
        <button
          v-if="assignedContact || task.assigned_to"
          @click="selectContact(null)"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-b border-gray-100 dark:border-gray-700"
        >
          <i class="fa-solid fa-user-slash text-xs text-gray-400 w-5 text-center"></i>
          <span>{{ __('Unassign') }}</span>
        </button>
        <!-- Contacts -->
        <button
          v-for="contact in contacts"
          :key="contact.name"
          @click="selectContact(contact.name)"
          :class="[
            'w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors',
            assignedContact?.name === contact.name
              ? 'bg-orga-50 dark:bg-orga-900/20 text-orga-700 dark:text-orga-400'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
          ]"
        >
          <UserAvatar :name="contact.resource_name" size="xs" color="orga" />
          <div class="flex-1 text-left min-w-0">
            <span class="block truncate">{{ contact.resource_name }}</span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ contact.department || contact.status }}</span>
          </div>
          <i v-if="assignedContact?.name === contact.name" class="fa-solid fa-check text-xs text-orga-500"></i>
        </button>
        <!-- Empty state -->
        <p v-if="!contacts.length" class="text-xs text-gray-400 dark:text-gray-500 text-center py-3">
          {{ __('No contacts available') }}
        </p>
      </div>
    </div>

    <!-- Dates (Editable) -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Start Date') }}</label>
        <div class="mt-1 relative">
          <input
            type="date"
            :value="task.start_date || ''"
            @change="handleDateChange('start_date', ($event.target as HTMLInputElement).value)"
            class="w-full px-2 py-1.5 text-sm text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-orga-500 focus:border-orga-500 transition-colors"
          />
          <button
            v-if="task.start_date"
            @click="handleDateChange('start_date', '')"
            class="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            :title="__('Clear date')"
          >
            <i class="fa-solid fa-xmark text-xs"></i>
          </button>
        </div>
      </div>
      <div>
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Due Date') }}</label>
        <div class="mt-1 relative">
          <input
            type="date"
            :value="task.due_date || ''"
            @change="handleDateChange('due_date', ($event.target as HTMLInputElement).value)"
            class="w-full px-2 py-1.5 text-sm text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-orga-500 focus:border-orga-500 transition-colors"
          />
          <button
            v-if="task.due_date"
            @click="handleDateChange('due_date', '')"
            class="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            :title="__('Clear date')"
          >
            <i class="fa-solid fa-xmark text-xs"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Auto-Trail Start -->
    <label
      v-if="task.start_date"
      class="flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition-colors"
      :class="task.auto_trail_start
        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
        : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700'"
    >
      <input
        type="checkbox"
        :checked="!!task.auto_trail_start"
        @change="handleAutoTrailToggle(($event.target as HTMLInputElement).checked)"
        class="w-3.5 h-3.5 rounded accent-blue-500 cursor-pointer flex-shrink-0"
      />
      <span class="text-xs text-gray-600 dark:text-gray-400 leading-tight">
        {{ __('Auto-Trail Start') }}
        <span class="text-gray-400 dark:text-gray-500"> — {{ __('trails to today while Open at 0%') }}</span>
      </span>
    </label>

    <!-- Time Tracking -->
    <div class="grid grid-cols-2 gap-4">
      <div v-if="task.estimated_hours">
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Estimated') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ task.estimated_hours }}h</p>
      </div>
      <div v-if="task.actual_hours">
        <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Actual') }}</label>
        <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ task.actual_hours }}h</p>
      </div>
    </div>

    <!-- Progress (Interactive Editor) -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Progress') }}</label>

      <!-- Progress Bar Visual -->
      <div class="flex items-center gap-3 mt-1">
        <div class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full transition-all duration-150"
            :class="progressBarClass"
            :style="{ width: localProgress + '%' }"
          ></div>
        </div>
        <span class="text-sm font-medium text-gray-800 dark:text-gray-200 w-10 text-right">{{ localProgress }}%</span>
      </div>

      <!-- Interactive Controls -->
      <div class="mt-3 space-y-3">
        <!-- Range Slider + Number Input -->
        <div class="flex items-center gap-3">
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            :value="localProgress"
            @input="handleProgressInput(($event.target as HTMLInputElement).valueAsNumber)"
            @change="handleProgressCommit"
            :disabled="isProgressDisabled"
            class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orga-500 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <input
            type="number"
            min="0"
            max="100"
            step="1"
            :value="localProgress"
            @input="handleProgressNumberInput(($event.target as HTMLInputElement).value)"
            @blur="handleProgressCommit"
            @keydown.enter="handleProgressCommit"
            :disabled="isProgressDisabled"
            class="w-16 px-2 py-1 text-sm text-center text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-orga-500 focus:border-orga-500 disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        <!-- Quick Action Buttons -->
        <div class="flex items-center gap-2">
          <button
            v-for="preset in progressPresets"
            :key="preset"
            @click="handleProgressPreset(preset)"
            :disabled="isProgressDisabled"
            :class="[
              'px-2 py-1 text-xs font-medium rounded-md transition-colors',
              localProgress === preset
                ? 'bg-orga-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            ]"
          >
            {{ preset }}%
          </button>
          <span v-if="isSavingProgress" class="ml-2 text-xs text-gray-400">
            <i class="fa-solid fa-spinner fa-spin mr-1"></i>{{ __('Saving...') }}
          </span>
        </div>

        <!-- Status Hint -->
        <p v-if="isProgressDisabled" class="text-xs text-gray-400 dark:text-gray-500">
          <i class="fa-solid fa-info-circle mr-1"></i>
          {{ progressDisabledReason }}
        </p>
      </div>
    </div>

    <!-- Project Reference -->
    <div v-if="task.project">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{{ __('Project') }}</label>
      <p class="text-sm text-gray-800 dark:text-gray-200 mt-1">{{ task.project_name || task.project }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaTask, OrgaContact, TaskPriority, TaskType } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  task: OrgaTask
  contacts?: OrgaContact[]
  availableGroups?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  contacts: () => [],
  availableGroups: () => []
})

const emit = defineEmits<{
  'date-change': [field: 'start_date' | 'due_date', value: string]
  'progress-change': [value: number]
  'description-change': [value: string]
  'subject-change': [value: string]
  'assign-contact': [contactName: string | null]
  'task-group-change': [value: string]
  'depends-on-group-change': [value: string]
  'task-type-change': [value: string]
  'auto-trail-change': [value: boolean]
}>()

// ============================================
// Task Type Handling
// ============================================

function handleTaskTypeChange(value: string): void {
  if (value === (props.task.task_type || '')) return
  emit('task-type-change', value)
}

// ============================================
// Subject Inline Editing
// ============================================

const isEditingSubject = ref(false)
const editSubjectText = ref('')
const subjectInputRef = ref<HTMLInputElement | null>(null)
const isSavingSubject = ref(false)

function startEditSubject(): void {
  editSubjectText.value = props.task.subject || ''
  isEditingSubject.value = true
  nextTick(() => subjectInputRef.value?.focus())
}

function cancelEditSubject(): void {
  isEditingSubject.value = false
}

function saveSubject(): void {
  if (isSavingSubject.value) return
  const trimmed = editSubjectText.value.trim()
  if (!trimmed || trimmed === props.task.subject) {
    isEditingSubject.value = false
    return
  }
  isSavingSubject.value = true
  isEditingSubject.value = false
  emit('subject-change', trimmed)
  nextTick(() => { isSavingSubject.value = false })
}

// ============================================
// Task Group Inline Editing
// ============================================

const isEditingGroup = ref(false)
const editGroupText = ref('')
const groupInputRef = ref<HTMLInputElement | null>(null)

function startEditGroup(): void {
  editGroupText.value = props.task.task_group || ''
  isEditingGroup.value = true
  nextTick(() => groupInputRef.value?.focus())
}

function cancelEditGroup(): void {
  isEditingGroup.value = false
}

function saveGroup(): void {
  const trimmed = editGroupText.value.trim()
  isEditingGroup.value = false
  if (trimmed === (props.task.task_group || '')) return
  emit('task-group-change', trimmed)
}

function clearGroup(): void {
  emit('task-group-change', '')
}

// ============================================
// Depends on Group Inline Editing
// ============================================

const isEditingDependsOnGroup = ref(false)
const editDependsOnGroupText = ref('')
const dependsOnGroupInputRef = ref<HTMLInputElement | null>(null)

function startEditDependsOnGroup(): void {
  editDependsOnGroupText.value = props.task.depends_on_group || ''
  isEditingDependsOnGroup.value = true
  nextTick(() => dependsOnGroupInputRef.value?.focus())
}

function cancelEditDependsOnGroup(): void {
  isEditingDependsOnGroup.value = false
}

function saveDependsOnGroup(): void {
  const trimmed = editDependsOnGroupText.value.trim()
  isEditingDependsOnGroup.value = false
  if (trimmed === (props.task.depends_on_group || '')) return
  emit('depends-on-group-change', trimmed)
}

function clearDependsOnGroup(): void {
  emit('depends-on-group-change', '')
}

// ============================================
// Contact Assignment Picker
// ============================================

const isAssigneeOpen = ref(false)

// Find the currently assigned contact
const assignedContact = computed(() => {
  const task = props.task as Record<string, unknown>
  // First check if there's a direct contact assignment (from API or optimistic update)
  if (task.assigned_resource) {
    const byName = props.contacts.find(r => r.name === task.assigned_resource)
    if (byName) return byName
  }
  // Fallback: match by user field
  if (props.task.assigned_to) {
    return props.contacts.find(r => r.user === props.task.assigned_to) || null
  }
  return null
})

function selectContact(contactName: string | null): void {
  isAssigneeOpen.value = false
  // Find current contact to compare
  const currentContactName = assignedContact.value?.name || null
  if (contactName === currentContactName) return
  emit('assign-contact', contactName)
}

// ============================================
// Date Handling
// ============================================

function handleDateChange(field: 'start_date' | 'due_date', value: string): void {
  emit('date-change', field, value)
}

function handleAutoTrailToggle(checked: boolean): void {
  emit('auto-trail-change', checked)
}

// ============================================
// Description Inline Editing
// ============================================

const isEditingDescription = ref(false)
const editDescriptionText = ref('')
const isSavingDescription = ref(false)

function startEditDescription(): void {
  editDescriptionText.value = props.task.description || ''
  isEditingDescription.value = true
}

function cancelEditDescription(): void {
  isEditingDescription.value = false
}

function saveDescription(): void {
  if (isSavingDescription.value) return
  isSavingDescription.value = true
  emit('description-change', editDescriptionText.value)
  isEditingDescription.value = false
  setTimeout(() => { isSavingDescription.value = false }, 500)
}

// ============================================
// Progress Editor State & Logic
// ============================================

const progressPresets = [0, 25, 50, 75, 100] as const
const localProgress = ref<number>(props.task.progress ?? 0)
const isSavingProgress = ref(false)
const pendingProgressValue = ref<number | null>(null)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// Sync local progress with prop when task changes
watch(() => props.task.progress, (newVal) => {
  // Only update if we're not in the middle of editing
  if (!debounceTimer) {
    localProgress.value = newVal ?? 0
  }
}, { immediate: true })

// Also reset when task ID changes
watch(() => props.task.name, () => {
  localProgress.value = props.task.progress ?? 0
  pendingProgressValue.value = null
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
})

// Check if progress editing is disabled
const isProgressDisabled = computed(() => {
  return props.task.status === 'Completed' || props.task.status === 'Cancelled'
})

const progressDisabledReason = computed(() => {
  if (props.task.status === 'Completed') return __('Task is completed')
  if (props.task.status === 'Cancelled') return __('Task is cancelled')
  return ''
})

// Progress bar color based on value
const progressBarClass = computed(() => {
  if (localProgress.value === 100) return 'bg-green-500'
  if (localProgress.value >= 75) return 'bg-orga-500'
  if (localProgress.value >= 50) return 'bg-yellow-500'
  if (localProgress.value >= 25) return 'bg-orange-500'
  return 'bg-gray-400'
})

// Handle slider input (immediate visual feedback, debounced save)
function handleProgressInput(value: number): void {
  const clamped = Math.max(0, Math.min(100, Math.round(value)))
  localProgress.value = clamped
  pendingProgressValue.value = clamped

  // Debounce the API call
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    commitProgress()
  }, 400)
}

// Handle number input (validate and update)
function handleProgressNumberInput(value: string): void {
  const parsed = parseInt(value, 10)
  if (isNaN(parsed)) return

  const clamped = Math.max(0, Math.min(100, parsed))
  localProgress.value = clamped
  pendingProgressValue.value = clamped
}

// Handle preset button click (immediate commit)
function handleProgressPreset(value: number): void {
  if (isProgressDisabled.value) return

  localProgress.value = value
  pendingProgressValue.value = value

  // Cancel any pending debounce and commit immediately
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  commitProgress()
}

// Handle blur/enter on inputs (commit immediately)
function handleProgressCommit(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  commitProgress()
}

// Commit progress change to parent
function commitProgress(): void {
  if (pendingProgressValue.value === null) return
  if (pendingProgressValue.value === props.task.progress) {
    pendingProgressValue.value = null
    return
  }

  isSavingProgress.value = true
  emit('progress-change', pendingProgressValue.value)

  // Reset pending value after emit
  // Note: isSavingProgress will be reset when task prop updates
  pendingProgressValue.value = null

  // Simulate save completion (actual save happens in parent)
  setTimeout(() => {
    isSavingProgress.value = false
  }, 500)
}

const priorityColors: Record<TaskPriority, string> = {
  'Urgent': 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
  'High': 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800',
  'Medium': 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800',
  'Low': 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700'
}

const statusColors: Record<string, string> = {
  'Open': 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  'In Progress': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  'Review': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  'Completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  'Cancelled': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
}

const taskTypeColors: Record<string, string> = {
  'Task': 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800',
  'Bug': 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800',
  'Feature': 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800',
  'Research': 'bg-cyan-100 text-cyan-700 border-cyan-200 dark:bg-cyan-900/30 dark:text-cyan-400 dark:border-cyan-800',
  'Meeting': 'bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800',
  'default': 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700'
}

const taskTypeIcons: Record<string, string> = {
  'Task': 'fa-solid fa-check-circle',
  'Bug': 'fa-solid fa-bug',
  'Feature': 'fa-solid fa-star',
  'Research': 'fa-solid fa-flask',
  'Meeting': 'fa-solid fa-users'
}

function formatDate(date: string | null | undefined): string {
  if (!date) return __('Not set')
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>
