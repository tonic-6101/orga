<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityChangesTab.vue - Enhanced changes/history tab for Activity Manager

  Features:
  - Group changes by date/session
  - Full diff view with expandable details
  - Show who made each change
  - Filter by field
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { ActivityChange } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  changes: ActivityChange[]
  isLoading: boolean
}

const props = defineProps<Props>()

// State
const expandedChanges = ref<Set<number>>(new Set())
const showFullDiff = ref(false)
const selectedField = ref<string | null>(null)

// Group changes by date
interface ChangeGroup {
  date: string
  dateLabel: string
  changes: (ActivityChange & { index: number })[]
}

const groupedChanges = computed<ChangeGroup[]>(() => {
  if (!props.changes.length) return []

  const groups: Record<string, ChangeGroup> = {}

  props.changes.forEach((change, index) => {
    const dateKey = change.modified ? new Date(change.modified).toDateString() : 'Unknown'
    const date = change.modified ? new Date(change.modified) : new Date()

    if (!groups[dateKey]) {
      groups[dateKey] = {
        date: dateKey,
        dateLabel: formatDateLabel(date),
        changes: []
      }
    }

    // Filter by field if selected
    if (!selectedField.value || change.field === selectedField.value) {
      groups[dateKey].changes.push({ ...change, index })
    }
  })

  // Sort groups by date (newest first)
  return Object.values(groups)
    .filter(g => g.changes.length > 0)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
})

// Get unique fields for filter
const uniqueFields = computed(() => {
  const fields = new Set(props.changes.map(c => c.field))
  return Array.from(fields).sort()
})

// Total filtered changes count
const filteredCount = computed(() => {
  return groupedChanges.value.reduce((sum, g) => sum + g.changes.length, 0)
})

function formatDateLabel(date: Date): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86400000)
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())

  if (dateOnly.getTime() === today.getTime()) return __('Today')
  if (dateOnly.getTime() === yesterday.getTime()) return __('Yesterday')

  const diffDays = Math.floor((today.getTime() - dateOnly.getTime()) / 86400000)
  if (diffDays < 7) return __('{0} days ago', [diffDays])

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTime(timestamp?: string): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

function formatRelativeTime(timestamp?: string): string {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0}m ago', [diffMins])
  if (diffHours < 24) return __('{0}h ago', [diffHours])
  if (diffDays < 7) return __('{0}d ago', [diffDays])

  return date.toLocaleDateString()
}

function formatChangeValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? __('Yes') : __('No')
  if (typeof value === 'number') return String(value)
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function isLongValue(value: unknown): boolean {
  const formatted = formatChangeValue(value)
  return formatted.length > 50 || formatted.includes('\n')
}

function toggleExpanded(index: number) {
  if (expandedChanges.value.has(index)) {
    expandedChanges.value.delete(index)
  } else {
    expandedChanges.value.add(index)
  }
}

function clearFilter() {
  selectedField.value = null
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header with filter -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {{ __('Change History') }} ({{ filteredCount }})
      </span>

      <!-- Field Filter -->
      <div v-if="uniqueFields.length > 1" class="relative">
        <select
          v-model="selectedField"
          class="text-xs px-2 py-1 border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"
        >
          <option :value="null">{{ __('All fields') }}</option>
          <option v-for="field in uniqueFields" :key="field" :value="field">
            {{ field }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading changes...') }}</p>
    </div>

    <!-- Grouped Changes -->
    <div v-else-if="groupedChanges.length" class="flex-1 overflow-auto space-y-4">
      <div v-for="group in groupedChanges" :key="group.date">
        <!-- Date Header -->
        <div class="flex items-center gap-2 mb-2">
          <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
          <span class="text-xs font-medium text-gray-400 dark:text-gray-500 px-2">
            {{ group.dateLabel }}
          </span>
          <div class="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
        </div>

        <!-- Changes in group -->
        <div class="space-y-2">
          <div
            v-for="change in group.changes"
            :key="change.index"
            class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
          >
            <!-- Change Header -->
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {{ change.field_label }}
                </span>
                <span class="text-[10px] px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">
                  {{ change.field }}
                </span>
              </div>
              <span class="text-[10px] text-gray-400 dark:text-gray-500">
                {{ formatTime(change.modified) }}
              </span>
            </div>

            <!-- Compact Diff View -->
            <div
              v-if="!isLongValue(change.old_value) && !isLongValue(change.new_value) && !expandedChanges.has(change.index)"
              class="flex items-center gap-3 text-sm"
            >
              <span class="text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 rounded line-through max-w-[45%] truncate">
                {{ formatChangeValue(change.old_value) || __('(empty)') }}
              </span>
              <i class="fa-solid fa-arrow-right text-gray-300 dark:text-gray-600 shrink-0"></i>
              <span class="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-0.5 rounded max-w-[45%] truncate">
                {{ formatChangeValue(change.new_value) || __('(empty)') }}
              </span>
            </div>

            <!-- Expanded Diff View -->
            <div
              v-else
              class="space-y-2"
            >
              <!-- Old Value -->
              <div class="bg-red-50 dark:bg-red-900/20 rounded p-2">
                <div class="text-[10px] text-red-500 dark:text-red-400 uppercase tracking-wider mb-1">{{ __('Previous') }}</div>
                <pre class="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap break-words m-0 font-mono">{{ formatChangeValue(change.old_value) || __('(empty)') }}</pre>
              </div>

              <!-- New Value -->
              <div class="bg-green-50 dark:bg-green-900/20 rounded p-2">
                <div class="text-[10px] text-green-500 dark:text-green-400 uppercase tracking-wider mb-1">{{ __('Current') }}</div>
                <pre class="text-sm text-green-700 dark:text-green-300 whitespace-pre-wrap break-words m-0 font-mono">{{ formatChangeValue(change.new_value) || __('(empty)') }}</pre>
              </div>
            </div>

            <!-- Expand/Collapse Button for long values -->
            <button
              v-if="isLongValue(change.old_value) || isLongValue(change.new_value)"
              @click="toggleExpanded(change.index)"
              class="text-xs text-orga-500 hover:text-orga-600 mt-2"
            >
              <i :class="['fa-solid mr-1', expandedChanges.has(change.index) ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              {{ expandedChanges.has(change.index) ? __('Show less') : __('Show full diff') }}
            </button>

            <!-- Author -->
            <div v-if="change.modified_by" class="flex items-center gap-2 mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
              <UserAvatar
                :name="change.modified_by"
                :image="change.modified_by_image"
                size="xs"
                color="gray"
              />
              <span class="text-[10px] text-gray-400 dark:text-gray-500">
                {{ change.modified_by }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8">
      <i class="fa-solid fa-code-compare fa-2x text-gray-300 dark:text-gray-600 mb-3 block"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500">
        {{ selectedField ? __('No changes for this field.') : __('No changes recorded for this activity.') }}
      </p>
      <p v-if="!selectedField" class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Changes appear when fields are modified.') }}</p>
      <button
        v-if="selectedField"
        @click="clearFilter"
        class="text-xs text-orga-500 hover:text-orga-600 mt-2"
      >
        {{ __('Show all changes') }}
      </button>
    </div>
  </div>
</template>
