// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'
import { frappeRequest } from 'frappe-ui'
import type { SearchCategory, SearchResultItem, SearchResults, SearchResponse } from '@/types/orga'

interface UseSearchReturn {
  query: Ref<string>
  category: Ref<SearchCategory>
  results: Ref<SearchResults>
  loading: Ref<boolean>
  isOpen: Ref<boolean>
  activeIndex: Ref<number>
  flatResults: ComputedRef<SearchResultItem[]>
  clear: () => void
  close: () => void
  navigateUp: () => void
  navigateDown: () => void
  selectActive: () => SearchResultItem | null
}

const EMPTY_RESULTS: SearchResults = {
  projects: [],
  tasks: [],
  contacts: [],
  milestones: [],
  events: [],
}

export function useSearch(): UseSearchReturn {
  const query = ref<string>('')
  const category = ref<SearchCategory>('')
  const results = ref<SearchResults>({ ...EMPTY_RESULTS })
  const loading = ref(false)
  const isOpen = ref(false)
  const activeIndex = ref(-1)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  const flatResults = computed<SearchResultItem[]>(() => {
    const flat: SearchResultItem[] = []
    const r = results.value
    if (r.projects.length) flat.push(...r.projects)
    if (r.tasks.length) flat.push(...r.tasks)
    if (r.contacts.length) flat.push(...r.contacts)
    if (r.milestones.length) flat.push(...r.milestones)
    if (r.events.length) flat.push(...r.events)
    return flat
  })

  async function performSearch(): Promise<void> {
    const q = query.value.trim()
    if (q.length < 2) {
      results.value = { ...EMPTY_RESULTS }
      isOpen.value = false
      return
    }

    loading.value = true
    isOpen.value = true
    activeIndex.value = -1

    try {
      const response = await frappeRequest({
        url: '/api/method/orga.orga.api.search.unified_search',
        params: {
          query: q,
          category: category.value,
          limit: 5,
        },
      }) as SearchResponse

      if (response && response.results) {
        // Ensure all expected keys exist to prevent runtime errors
        results.value = { ...EMPTY_RESULTS, ...response.results }
      } else {
        results.value = { ...EMPTY_RESULTS }
      }
    } catch {
      results.value = { ...EMPTY_RESULTS }
    } finally {
      loading.value = false
    }
  }

  // Debounced watch on query
  watch(query, () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(performSearch, 300)
  })

  // Category change triggers immediate search
  watch(category, () => {
    if (query.value.trim().length >= 2) {
      performSearch()
    }
  })

  function clear(): void {
    query.value = ''
    results.value = { ...EMPTY_RESULTS }
    isOpen.value = false
    activeIndex.value = -1
  }

  function close(): void {
    isOpen.value = false
    activeIndex.value = -1
  }

  function navigateDown(): void {
    const max = flatResults.value.length - 1
    if (max < 0) return
    activeIndex.value = activeIndex.value < max ? activeIndex.value + 1 : 0
  }

  function navigateUp(): void {
    const max = flatResults.value.length - 1
    if (max < 0) return
    activeIndex.value = activeIndex.value > 0 ? activeIndex.value - 1 : max
  }

  function selectActive(): SearchResultItem | null {
    if (activeIndex.value >= 0 && activeIndex.value < flatResults.value.length) {
      return flatResults.value[activeIndex.value]
    }
    return null
  }

  return {
    query,
    category,
    results,
    loading,
    isOpen,
    activeIndex,
    flatResults,
    clear,
    close,
    navigateUp,
    navigateDown,
    selectActive,
  }
}
