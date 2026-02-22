<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  LinkInput.vue - Autocomplete input for selecting linked documents.
  Searches via unified_search API filtered to a single category.
-->
<script setup lang="ts">
import { ref, watch, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { frappeRequest } from 'frappe-ui'
import type { SearchCategory, SearchResultItem, SearchResponse } from '@/types/orga'
import { __ } from '@/composables/useTranslate'

interface Props {
  modelValue: string
  category: SearchCategory
  placeholder?: string
  required?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: __('Start typing to search...'),
  required: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'select', item: SearchResultItem): void
  (e: 'clear'): void
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const dropdownRef = ref<HTMLDivElement | null>(null)
const query = ref('')
const results = ref<SearchResultItem[]>([])
const isOpen = ref(false)
const loading = ref(false)
const activeIndex = ref(-1)
const selectedLabel = ref('')

let debounceTimer: ReturnType<typeof setTimeout> | null = null

// Display text: show label if selected, otherwise the query
const displayText = computed(() => {
  if (props.modelValue && selectedLabel.value) {
    return selectedLabel.value
  }
  return query.value
})

// If modelValue is set on mount (default prop), resolve its label
onMounted(() => {
  if (props.modelValue) {
    resolveLabel(props.modelValue)
  }
})

async function resolveLabel(name: string): Promise<void> {
  if (!name || !props.category) return
  try {
    const response = await frappeRequest({
      url: '/api/method/orga.orga.api.search.unified_search',
      params: { query: name, category: props.category, limit: 1 }
    }) as SearchResponse

    const categoryKey = getCategoryKey(props.category)
    const items = response?.results?.[categoryKey] || []
    const match = items.find((item: SearchResultItem) => item.name === name)
    if (match) {
      selectedLabel.value = `${match.label} (${match.name})`
    } else {
      selectedLabel.value = name
    }
  } catch {
    selectedLabel.value = name
  }
}

function getCategoryKey(cat: SearchCategory): keyof import('@/types/orga').SearchResults {
  const map: Record<string, keyof import('@/types/orga').SearchResults> = {
    project: 'projects',
    task: 'tasks',
    resource: 'contacts',
    milestone: 'milestones',
    event: 'events',
  }
  return map[cat] || 'projects'
}

async function performSearch(): Promise<void> {
  const q = query.value.trim()
  if (q.length < 1) {
    results.value = []
    isOpen.value = false
    return
  }

  loading.value = true

  try {
    const response = await frappeRequest({
      url: '/api/method/orga.orga.api.search.unified_search',
      params: {
        query: q,
        category: props.category,
        limit: 8
      }
    }) as SearchResponse

    const categoryKey = getCategoryKey(props.category)
    results.value = response?.results?.[categoryKey] || []
    isOpen.value = results.value.length > 0
    activeIndex.value = -1
  } catch {
    results.value = []
    isOpen.value = false
  } finally {
    loading.value = false
  }
}

function handleInput(e: Event): void {
  const target = e.target as HTMLInputElement
  query.value = target.value

  // Clear selection when user edits
  if (props.modelValue) {
    emit('update:modelValue', '')
    selectedLabel.value = ''
  }

  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(performSearch, 250)
}

function handleFocus(): void {
  if (props.modelValue && selectedLabel.value) {
    // User clicked back into a selected field — show the search query
    query.value = ''
    selectedLabel.value = ''
    emit('update:modelValue', '')
  }
  if (query.value.trim().length >= 1) {
    performSearch()
  }
}

function selectItem(item: SearchResultItem): void {
  emit('update:modelValue', item.name)
  selectedLabel.value = `${item.label} (${item.name})`
  query.value = ''
  results.value = []
  isOpen.value = false
  activeIndex.value = -1
  emit('select', item)
}

function clearSelection(): void {
  emit('update:modelValue', '')
  selectedLabel.value = ''
  query.value = ''
  results.value = []
  isOpen.value = false
  emit('clear')
  nextTick(() => inputRef.value?.focus())
}

function handleKeydown(e: KeyboardEvent): void {
  if (!isOpen.value) return

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      activeIndex.value = activeIndex.value < results.value.length - 1
        ? activeIndex.value + 1
        : 0
      break
    case 'ArrowUp':
      e.preventDefault()
      activeIndex.value = activeIndex.value > 0
        ? activeIndex.value - 1
        : results.value.length - 1
      break
    case 'Enter':
      e.preventDefault()
      if (activeIndex.value >= 0 && activeIndex.value < results.value.length) {
        selectItem(results.value[activeIndex.value])
      }
      break
    case 'Escape':
      isOpen.value = false
      activeIndex.value = -1
      break
  }
}

// Close dropdown when clicking outside
function handleClickOutside(e: MouseEvent): void {
  const target = e.target as Node
  if (
    dropdownRef.value && !dropdownRef.value.contains(target) &&
    inputRef.value && !inputRef.value.contains(target)
  ) {
    isOpen.value = false
    activeIndex.value = -1
    // Restore display if value is set
    if (props.modelValue && !selectedLabel.value) {
      resolveLabel(props.modelValue)
    }
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleClickOutside)
  if (debounceTimer) clearTimeout(debounceTimer)
})

// Re-resolve label when modelValue changes externally
watch(() => props.modelValue, (newVal) => {
  if (newVal && !selectedLabel.value) {
    resolveLabel(newVal)
  } else if (!newVal) {
    selectedLabel.value = ''
  }
})
</script>

<template>
  <div class="relative">
    <!-- Input -->
    <div class="relative">
      <input
        ref="inputRef"
        type="text"
        :value="modelValue ? selectedLabel || modelValue : query"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="[
          'w-full px-3 py-2 text-sm rounded-lg transition-colors outline-none',
          'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100',
          'border border-gray-200 dark:border-gray-600 focus:border-orga-500',
          'placeholder-gray-400',
          modelValue ? 'pr-8' : 'pr-3',
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        ]"
        @input="handleInput"
        @focus="handleFocus"
        @keydown="handleKeydown"
      />
      <!-- Loading indicator -->
      <div v-if="loading" class="absolute right-2.5 top-1/2 -translate-y-1/2">
        <i class="fa-solid fa-spinner fa-spin text-xs text-gray-400"></i>
      </div>
      <!-- Clear button -->
      <button
        v-else-if="modelValue && !disabled"
        @mousedown.prevent="clearSelection"
        class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
      >
        <i class="fa-solid fa-xmark text-xs"></i>
      </button>
    </div>

    <!-- Dropdown -->
    <div
      v-if="isOpen && results.length > 0"
      ref="dropdownRef"
      class="absolute z-50 mt-1 w-full bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto"
    >
      <button
        v-for="(item, idx) in results"
        :key="item.name"
        type="button"
        @mousedown.prevent="selectItem(item)"
        :class="[
          'w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors',
          'flex flex-col gap-0.5',
          idx === activeIndex ? 'bg-orga-50 dark:bg-orga-900/30' : ''
        ]"
      >
        <div class="flex items-center justify-between">
          <span class="font-medium text-gray-800 dark:text-gray-100 truncate">{{ item.label }}</span>
          <span
            v-if="item.status"
            :class="[
              'text-xs px-1.5 py-0.5 rounded-full ml-2 shrink-0',
              item.status === 'Completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
              item.status === 'In Progress' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
              item.status === 'Open' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
              'bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
            ]"
          >{{ item.status }}</span>
        </div>
        <span class="text-xs text-gray-500 dark:text-gray-400 truncate">
          {{ item.name }}
          <template v-if="item.description"> &middot; {{ item.description }}</template>
        </span>
      </button>
    </div>

    <!-- No results -->
    <div
      v-if="isOpen && results.length === 0 && !loading && query.trim().length >= 1"
      ref="dropdownRef"
      class="absolute z-50 mt-1 w-full bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg"
    >
      <div class="px-3 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
        {{ __('No results found') }}
      </div>
    </div>
  </div>
</template>
