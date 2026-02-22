<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * CascadePreview - Shows impact of date changes on dependent tasks
 *
 * Displays a warning banner when date changes will affect dependent tasks.
 * Allows user to preview, apply, or cancel cascade changes.
 */

import { computed } from 'vue'
import type { CascadeChange } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

interface Props {
  changes: CascadeChange[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'preview'): void
  (e: 'apply'): void
  (e: 'cancel'): void
}>()

// Total number of affected tasks
const affectedCount = computed(() => props.changes.length)

// Check if any tasks move backwards
const hasNegativeShift = computed(() =>
  props.changes.some(c => c.days_shift < 0)
)

// Group changes by direction
const positiveChanges = computed(() =>
  props.changes.filter(c => c.days_shift > 0)
)

const negativeChanges = computed(() =>
  props.changes.filter(c => c.days_shift < 0)
)

// Format days shift
function formatShift(days: number): string {
  if (days === 0) return __('no change')
  const direction = days > 0 ? '+' : ''
  const unit = Math.abs(days) === 1 ? __('day') : __('days')
  return `${direction}${days} ${unit}`
}
</script>

<template>
  <div
    v-if="changes.length > 0"
    class="cascade-preview bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-300 rounded-lg p-3 mb-4"
  >
    <!-- Header -->
    <div class="flex items-start gap-2 mb-2">
      <i class="fa-solid fa-exclamation-triangle text-yellow-600 mt-0.5"></i>
      <div class="flex-1">
        <h4 class="text-sm font-medium text-yellow-800">
          {{ affectedCount === 1 ? __('This change will affect {0} dependent task', [affectedCount]) : __('This change will affect {0} dependent tasks', [affectedCount]) }}
        </h4>
      </div>
    </div>

    <!-- Affected tasks list -->
    <div class="ml-6 space-y-1 mb-3 max-h-32 overflow-y-auto">
      <div
        v-for="change in changes"
        :key="change.task_id"
        class="flex items-center justify-between text-sm"
      >
        <span class="text-yellow-900 truncate flex-1">{{ change.task_name }}</span>
        <span
          :class="[
            'text-xs px-1.5 py-0.5 rounded ml-2 shrink-0',
            change.days_shift > 0
              ? 'bg-yellow-200 text-yellow-800'
              : 'bg-green-200 text-green-800'
          ]"
        >
          {{ formatShift(change.days_shift) }}
        </span>
      </div>
    </div>

    <!-- Summary if many changes -->
    <div v-if="changes.length > 5" class="ml-6 mb-3 text-xs text-yellow-700">
      <span v-if="positiveChanges.length > 0">
        <i class="fa-solid fa-arrow-right"></i>
        {{ positiveChanges.length === 1 ? __('{0} task will be delayed', [positiveChanges.length]) : __('{0} tasks will be delayed', [positiveChanges.length]) }}
      </span>
      <span v-if="negativeChanges.length > 0" class="ml-3">
        <i class="fa-solid fa-arrow-left"></i>
        {{ negativeChanges.length === 1 ? __('{0} task will move earlier', [negativeChanges.length]) : __('{0} tasks will move earlier', [negativeChanges.length]) }}
      </span>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-2 mt-2">
      <button
        @click="emit('cancel')"
        :disabled="loading"
        class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
      >
        {{ __('Cancel') }}
      </button>
      <button
        @click="emit('preview')"
        :disabled="loading"
        class="px-3 py-1.5 text-sm text-yellow-700 bg-yellow-100 hover:bg-yellow-200 rounded disabled:opacity-50"
      >
        <i class="fa-solid fa-eye mr-1"></i>
        {{ __('Preview') }}
      </button>
      <button
        @click="emit('apply')"
        :disabled="loading"
        class="px-3 py-1.5 text-sm text-white bg-yellow-600 hover:bg-yellow-700 rounded disabled:opacity-50 flex items-center gap-1"
      >
        <i v-if="loading" class="fa-solid fa-spinner fa-spin"></i>
        <i v-else class="fa-solid fa-check"></i>
        {{ __('Apply Changes') }}
      </button>
    </div>
  </div>
</template>
