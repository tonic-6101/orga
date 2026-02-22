<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import type { SearchResults, SearchResultItem } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

const props = defineProps<{
  results: SearchResults
  loading: boolean
  activeIndex: number
  flatResults: SearchResultItem[]
}>()

const emit = defineEmits<{
  (e: 'select', item: SearchResultItem): void
}>()

interface SectionConfig {
  key: keyof SearchResults
  label: string
  icon: string
}

const sections: SectionConfig[] = [
  { key: 'projects', label: __('Projects'), icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' },
  { key: 'tasks', label: __('Tasks'), icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
  { key: 'contacts', label: __('Contacts'), icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { key: 'milestones', label: __('Milestones'), icon: 'M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9' },
  { key: 'events', label: __('Events'), icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
]

function getFlatIndex(sectionKey: keyof SearchResults, itemIndex: number): number {
  let offset = 0
  for (const section of sections) {
    if (section.key === sectionKey) return offset + itemIndex
    offset += props.results[section.key].length
  }
  return -1
}

function statusColor(status: string): string {
  const s = status?.toLowerCase() || ''
  if (['active', 'completed', 'accepted', 'open'].includes(s)) return 'text-green-600 dark:text-green-400'
  if (['planning', 'upcoming', 'pending', 'working', 'in progress'].includes(s)) return 'text-blue-600 dark:text-blue-400'
  if (['on hold', 'tentative', 'missed'].includes(s)) return 'text-yellow-600 dark:text-yellow-400'
  if (['cancelled', 'inactive', 'declined'].includes(s)) return 'text-red-600 dark:text-red-400'
  return 'text-gray-500 dark:text-gray-400'
}
</script>

<template>
  <div class="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-96 overflow-y-auto z-50">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-6 text-sm text-gray-500 dark:text-gray-400">
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      {{ __('Searching...') }}
    </div>

    <!-- No results -->
    <div v-else-if="flatResults.length === 0" class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
      {{ __('No results found') }}
    </div>

    <!-- Grouped results -->
    <template v-else>
      <template v-for="section in sections" :key="section.key">
        <div v-if="results[section.key].length > 0">
          <!-- Section header -->
          <div class="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider bg-gray-50 dark:bg-gray-700/50 sticky top-0">
            <div class="flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="section.icon" />
              </svg>
              {{ section.label }}
            </div>
          </div>

          <!-- Items -->
          <button
            v-for="(item, idx) in results[section.key]"
            :key="item.name"
            class="w-full px-3 py-2 flex items-center gap-3 text-left text-sm transition-colors"
            :class="getFlatIndex(section.key, idx) === activeIndex
              ? 'bg-orga-50 dark:bg-orga-900/30 text-orga-700 dark:text-orga-300'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300'"
            @click="emit('select', item)"
          >
            <div class="flex-1 min-w-0">
              <div class="truncate font-medium">{{ item.label }}</div>
              <div v-if="item.description" class="truncate text-xs text-gray-400 dark:text-gray-500">
                {{ item.description }}
              </div>
            </div>
            <span v-if="item.status" class="text-xs font-medium shrink-0" :class="statusColor(item.status)">
              {{ item.status }}
            </span>
          </button>
        </div>
      </template>
    </template>
  </div>
</template>
