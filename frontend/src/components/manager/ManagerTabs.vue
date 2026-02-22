<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ManagerTabs.vue - Reusable icon-based tab navigation for Manager panels

  Usage:
    <ManagerTabs
      :tabs="[
        { id: 'details', icon: 'fa-file-alt', label: 'Details' },
        { id: 'actions', icon: 'fa-bolt', label: 'Actions' }
      ]"
      storage-key="activity-manager"
      section-label="ACTIVITY"
      @change="activeTab = $event"
    />
-->
<template>
  <div class="manager-tabs border-b border-gray-200 dark:border-gray-700">
    <!-- Section Label (optional) -->
    <div v-if="sectionLabel" class="px-4 pt-2 pb-1">
      <span class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
        {{ sectionLabel }}
      </span>
    </div>

    <!-- Tab Bar -->
    <div class="flex px-4">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="selectTab(tab.id)"
        class="flex-1 flex items-center justify-center py-2 relative group transition-colors"
        :class="[
          activeTab === tab.id
            ? 'text-orga-500'
            : 'text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300'
        ]"
        :title="tab.label"
      >
        <i :class="['fa-solid', tab.icon, 'text-base']"></i>

        <!-- Active Indicator -->
        <div
          v-if="activeTab === tab.id"
          class="absolute bottom-0 left-2 right-2 h-0.5 bg-orga-500 rounded-full"
        ></div>

        <!-- Tooltip -->
        <div class="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1
                    bg-gray-800 dark:bg-gray-700 text-white text-xs rounded whitespace-nowrap
                    opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
          {{ tab.label }}
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { ManagerTab } from '@/types/orga'

interface Props {
  /** Array of tab definitions */
  tabs: ManagerTab[]
  /** Optional localStorage key for persisting active tab */
  storageKey?: string
  /** Optional section label displayed above tabs */
  sectionLabel?: string
  /** Default active tab id (defaults to first tab) */
  defaultTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  storageKey: '',
  sectionLabel: '',
  defaultTab: ''
})

const emit = defineEmits<{
  /** Emitted when active tab changes */
  change: [tabId: string]
}>()

// Initialize: prefer localStorage saved tab, then defaultTab prop, then first tab
function getInitialTab(): string {
  if (props.storageKey) {
    const saved = localStorage.getItem(`manager_tab_${props.storageKey}`)
    if (saved && props.tabs.some(t => t.id === saved)) {
      return saved
    }
  }
  return props.defaultTab || props.tabs[0]?.id || ''
}

const activeTab = ref(getInitialTab())

/**
 * Select a tab and persist to localStorage if key provided
 */
function selectTab(tabId: string) {
  activeTab.value = tabId
  emit('change', tabId)

  // Persist to localStorage if key provided
  if (props.storageKey) {
    localStorage.setItem(`manager_tab_${props.storageKey}`, tabId)
  }
}

// On mount, sync the initial tab with the parent
onMounted(() => {
  // Tell parent which tab is actually active (may differ from defaultTab if localStorage had a saved value)
  emit('change', activeTab.value)
})

// Watch for external forced tab changes (e.g. parent explicitly resets to a specific tab)
// Only apply when the value actually changes from its previous prop value
watch(() => props.defaultTab, (newDefault, oldDefault) => {
  if (newDefault && newDefault !== oldDefault && newDefault !== activeTab.value && props.tabs.some(t => t.id === newDefault)) {
    activeTab.value = newDefault
    if (props.storageKey) {
      localStorage.setItem(`manager_tab_${props.storageKey}`, newDefault)
    }
  }
})

// Expose activeTab for parent access
defineExpose({ activeTab })
</script>

<style scoped>
.manager-tabs {
  background: linear-gradient(to bottom, white, #fafafa);
}

:root.dark .manager-tabs {
  background: linear-gradient(to bottom, rgb(17 24 39), rgb(31 41 55));
}
</style>
