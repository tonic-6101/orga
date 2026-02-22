<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ManagerTabContent.vue - Dynamic tab content wrapper with transitions

  Usage:
    <ManagerTabContent :active-tab="activeTab" :tabs="tabConfig">
      <template #details>
        <DetailsContent />
      </template>
      <template #dependencies>
        <DependenciesContent />
      </template>
    </ManagerTabContent>
-->
<template>
  <div class="manager-tab-content flex-1 overflow-auto bg-white dark:bg-gray-900 transition-colors">
    <div class="p-4">
      <!-- Dynamic slots based on tabs prop -->
      <template v-for="tab in tabs" :key="tab.id">
        <div v-show="activeTab === tab.id">
          <slot :name="tab.id" />
        </div>
      </template>

      <!-- Fallback for unknown tabs (only if tabs not provided) -->
      <div
        v-if="!tabs.length && !['details', 'changes', 'notes', 'actions', 'dependencies', 'finance', 'checklist', 'comments', 'attendees', 'skills', 'assignments'].includes(activeTab)"
        class="text-gray-400 dark:text-gray-500 text-center py-8"
      >
        <i class="fa-solid fa-circle-question fa-2x mb-2 opacity-30 block"></i>
        {{ __('No content for this tab') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ManagerTabContent Component
 *
 * Dynamic wrapper for tab content that provides:
 * - Support for any tab configuration
 * - Smooth fade transitions between tabs
 * - Consistent padding
 * - Scrollable overflow handling
 * - Named slots matching tab ids
 *
 * The component uses Vue's named slots where the slot name
 * matches the tab id from ManagerTabs.
 */

import type { ManagerTab } from '@/types/orga'

interface Props {
  /** Currently active tab id (must match a slot name) */
  activeTab: string
  /** Tab configuration for dynamic slot rendering */
  tabs?: ManagerTab[]
}

withDefaults(defineProps<Props>(), {
  tabs: () => []
})
</script>

<style scoped>
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.15s ease;
}

.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}

.manager-tab-content {
  /* Ensure content area takes remaining space in flex container */
  min-height: 0;
}
</style>
