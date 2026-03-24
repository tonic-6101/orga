<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskChecklistTab.vue - Checklist tab content for Task Manager
-->
<template>
  <div class="flex flex-col h-full">
    <!-- Progress Header -->
    <div v-if="checklist.length" class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ __('Progress') }}</span>
        <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ progress }}%</span>
      </div>
      <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full bg-accent-500 transition-all duration-300"
          :style="{ width: progress + '%' }"
        ></div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <Loader2 class="w-5 h-5 animate-spin text-gray-400 dark:text-gray-500 mx-auto" aria-hidden="true" />
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading checklist...') }}</p>
    </div>

    <!-- Checklist Items -->
    <div v-else class="flex-1 overflow-auto space-y-2 mb-3">
      <div
        v-for="item in checklist"
        :key="item.name"
        class="flex items-center gap-2 group"
      >
        <button
          @click="emit('toggle', item)"
          :class="[
            'w-5 h-5 rounded border flex items-center justify-center transition-colors shrink-0',
            item.is_completed
              ? 'bg-accent-500 border-accent-500 text-white'
              : 'border-gray-300 dark:border-gray-600 hover:border-accent-500'
          ]"
        >
          <Check v-if="item.is_completed" class="w-3 h-3" aria-hidden="true" />
        </button>
        <span :class="[
          'text-sm flex-1',
          item.is_completed
            ? 'text-gray-400 dark:text-gray-500 line-through'
            : 'text-gray-700 dark:text-gray-300'
        ]">
          {{ item.title }}
        </span>
        <button
          v-if="!item.is_completed"
          @click="emit('promote', item)"
          class="text-gray-300 dark:text-gray-600 hover:text-accent-500 opacity-0 group-hover:opacity-100 transition-opacity"
          :title="__('Promote to task')"
        >
          <ExternalLink class="w-3 h-3" aria-hidden="true" />
        </button>
        <button
          @click="emit('delete', item)"
          class="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
          :title="__('Delete item')"
        >
          <Trash2 class="w-3 h-3" aria-hidden="true" />
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="!checklist.length && !isLoading" class="text-center py-8">
        <ListChecks class="w-6 h-6 text-gray-300 dark:text-gray-600 mb-3 mx-auto" aria-hidden="true" />
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No checklist items yet.') }}</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Add items below to track progress.') }}</p>
      </div>
    </div>

    <!-- Add Item Input -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-2 border-t border-gray-100 dark:border-gray-800">
      <div class="flex gap-2">
        <input
          v-model="newItem"
          @keyup.enter="handleAddItem"
          type="text"
          :placeholder="__('Add checklist item...')"
          :disabled="isAdding"
          class="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500/20 disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500"
        />
        <button
          @click="handleAddItem"
          :disabled="isAdding || !newItem.trim()"
          class="px-3 py-2 bg-accent-500 text-white rounded-lg hover:bg-accent-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          :title="__('Add item')"
        >
          <Loader2 v-if="isAdding" class="w-4 h-4 animate-spin" aria-hidden="true" />
          <Plus v-else class="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { TaskChecklistItem } from '@/types/orga'
import { Loader2, Check, ExternalLink, Trash2, ListChecks, Plus } from 'lucide-vue-next'

interface Props {
  checklist: TaskChecklistItem[]
  isLoading: boolean
  isAdding: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  add: [title: string]
  toggle: [item: TaskChecklistItem]
  delete: [item: TaskChecklistItem]
  promote: [item: TaskChecklistItem]
}>()

const newItem = ref('')

const progress = computed(() => {
  if (!props.checklist.length) return 0
  const completed = props.checklist.filter(item => item.is_completed).length
  return Math.round((completed / props.checklist.length) * 100)
})

function handleAddItem() {
  if (newItem.value.trim() && !props.isAdding) {
    emit('add', newItem.value.trim())
    newItem.value = ''
  }
}
</script>
