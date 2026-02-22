<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityActionsTab.vue - Actions tab content for Activity Manager
-->
<template>
  <div class="space-y-4">
    <!-- Quick Actions -->
    <div>
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3 block">
        {{ __('Quick Actions') }}
      </label>

      <div class="space-y-2">
        <!-- View Reference -->
        <button
          v-if="activity.reference_doctype && activity.reference_name"
          @click="emit('navigate')"
          class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-left"
        >
          <i class="fa-solid fa-external-link-alt text-orga-500 w-5"></i>
          <span>{{ __('View {0}', [formatDoctype(activity.reference_doctype)]) }}</span>
          <i class="fa-solid fa-chevron-right ml-auto text-gray-400 dark:text-gray-500"></i>
        </button>

        <!-- Pin Toggle -->
        <button
          @click="emit('toggle-pin')"
          class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-left"
        >
          <i :class="['fa-solid fa-thumbtack w-5', state.is_pinned ? 'text-amber-500' : 'text-gray-500 dark:text-gray-400']"></i>
          <span>{{ state.is_pinned ? __('Unpin Activity') : __('Pin Activity') }}</span>
        </button>

        <!-- Archive Toggle -->
        <button
          @click="emit('toggle-archive')"
          class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-left"
        >
          <i :class="['fa-solid w-5', state.is_archived ? 'fa-box-open text-gray-500 dark:text-gray-400' : 'fa-archive text-gray-500 dark:text-gray-400']"></i>
          <span>{{ state.is_archived ? __('Unarchive Activity') : __('Archive Activity') }}</span>
        </button>
      </div>
    </div>

    <!-- Activity Info -->
    <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
      <label class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2 block">
        {{ __('Activity Info') }}
      </label>
      <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
        <p><span class="font-medium">{{ __('Type') }}:</span> {{ activity.reference_doctype || activity.doctype }}</p>
        <p><span class="font-medium">{{ __('ID') }}:</span> {{ activity.reference_name || activity.name }}</p>
      </div>
    </div>

    <!-- Danger Zone (Admin Only) -->
    <div v-if="state.can_delete" class="pt-4 border-t border-gray-200 dark:border-gray-700">
      <label class="text-[10px] font-semibold text-red-400 uppercase tracking-wider mb-3 block">
        {{ __('Danger Zone') }}
      </label>

      <button
        @click="handleDelete"
        class="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 rounded-lg transition-colors text-left"
      >
        <i class="fa-solid fa-trash w-5"></i>
        <span>{{ __('Delete Activity Data') }}</span>
      </button>

      <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-2">
        {{ __('This will delete all notes and preferences associated with this activity.') }}
        {{ __('The source document will not be affected.') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from '@/composables/useTranslate'
import type { ActivityItem } from '@/types/orga'

interface Props {
  activity: ActivityItem
  state: {
    is_pinned: boolean
    is_archived: boolean
    can_delete: boolean
  }
}

defineProps<Props>()
const emit = defineEmits<{
  'toggle-pin': []
  'toggle-archive': []
  'delete': []
  'navigate': []
}>()

/**
 * Format doctype name for display (remove "Orga " prefix)
 */
function formatDoctype(doctype?: string): string {
  if (!doctype) return __('Document')
  return doctype.replace('Orga ', '')
}

/**
 * Handle delete with confirmation
 */
function handleDelete() {
  if (confirm(__('Are you sure you want to delete this activity data? This cannot be undone.'))) {
    emit('delete')
  }
}
</script>
