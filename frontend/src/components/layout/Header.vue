<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import NotificationBell from '@/components/NotificationBell.vue'
import FloatingTimer from '@/components/FloatingTimer.vue'
import UserMenu from '@/components/layout/UserMenu.vue'
import SearchDropdown from '@/components/SearchDropdown.vue'
import orgaLogo from '@/assets/orga-icon.svg'
import { useSearch } from '@/composables/useSearch'
import type { SearchResultItem } from '@/types/orga'

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const router = useRouter()
const searchContainerRef = ref<HTMLElement | null>(null)

const {
  query: searchQuery,
  category: searchCategory,
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
} = useSearch()

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    navigateDown()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    navigateUp()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = selectActive()
    if (item) navigateToResult(item)
  } else if (e.key === 'Escape') {
    close()
  }
}

function navigateToResult(item: SearchResultItem): void {
  close()
  searchQuery.value = ''

  switch (item.category) {
    case 'project':
      router.push(`/orga/projects/${item.name}`)
      break
    case 'task':
      // Navigate to the task's parent project (description holds the project name)
      if (item.description) {
        router.push(`/orga/projects/${item.description}`)
      }
      break
    case 'event':
      router.push('/orga/schedule')
      break
    case 'resource':
      router.push('/orga/contacts')
      break
    case 'milestone':
      // Navigate to milestone's parent project
      if (item.description) {
        router.push(`/orga/projects/${item.description}`)
      }
      break
  }
}

function handleClickOutside(e: MouseEvent): void {
  if (searchContainerRef.value && !searchContainerRef.value.contains(e.target as Node)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <header class="h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 sticky top-0 z-50 transition-colors">
    <!-- Left: Toggle + Logo -->
    <div class="flex items-center gap-4">
      <button
        class="sidebar-toggle w-9 h-9 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors"
        @click="emit('toggle-sidebar')"
        :title="__('Toggle Sidebar')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <router-link to="/orga" class="flex items-center gap-2 font-bold text-lg no-underline">
        <img :src="orgaLogo" alt="Orga" class="w-6 h-6" />
        <span class="text-gray-800 dark:text-gray-100">ORGA</span>
      </router-link>
    </div>

    <!-- Center: Search -->
    <div ref="searchContainerRef" class="hidden md:flex items-center flex-1 max-w-lg mx-8 relative">
      <div class="flex items-center w-full h-9 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 overflow-hidden focus-within:ring-2 focus-within:ring-orga-500/40 focus-within:border-orga-500 dark:focus-within:border-orga-400 transition-all">
        <select
          v-model="searchCategory"
          class="h-full px-3 text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 border-r border-gray-200 dark:border-gray-600 outline-none cursor-pointer"
        >
          <option value="">{{ __('All') }}</option>
          <option value="project">{{ __('Projects') }}</option>
          <option value="task">{{ __('Tasks') }}</option>
          <option value="resource">{{ __('Contacts') }}</option>
          <option value="milestone">{{ __('Milestones') }}</option>
          <option value="event">{{ __('Events') }}</option>
        </select>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="__('Search...')"
          class="flex-1 h-full px-3 text-sm bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 outline-none min-w-0"
          @keydown="handleKeydown"
          @focus="searchQuery.trim().length >= 2 && (isOpen = true)"
        />
        <button
          class="h-full px-3 text-gray-400 dark:text-gray-500 hover:text-orga-500 dark:hover:text-orga-400 transition-colors"
          @click="searchQuery.trim().length >= 2 ? (isOpen = true) : undefined"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>

      <!-- Search Dropdown -->
      <SearchDropdown
        v-if="isOpen"
        :results="results"
        :loading="loading"
        :active-index="activeIndex"
        :flat-results="flatResults"
        @select="navigateToResult"
      />
    </div>

    <!-- Right: Timer + Notifications + Apps + User -->
    <div class="flex items-center gap-4">
      <!-- Floating Timer -->
      <FloatingTimer />

      <!-- Notification Bell -->
      <NotificationBell />

      <!-- Apps Grid -->
      <button
        class="grid grid-cols-3 gap-1 p-2 border border-gray-200 dark:border-gray-600 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        :title="__('Apps')"
      >
        <span v-for="i in 9" :key="i" class="w-1.5 h-1.5 bg-gray-800 dark:bg-gray-300 rounded-sm"></span>
      </button>

      <!-- User Menu -->
      <UserMenu />
    </div>
  </header>
</template>
