<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ManagerHeader.vue - Reusable header component for all Manager panels

  Usage:
    <ManagerHeader
      title="Manager"
      subtitle="Task Details"
      icon="fa-sliders"
      :show-pin="true"
      :is-pinned="isPinned"
      @pin="handlePin"
      @close="handleClose"
    >
      <template #actions>
        <button>Custom Action</button>
      </template>
    </ManagerHeader>
-->
<template>
  <div class="p-4 border-b border-gray-200 flex items-center justify-between shrink-0">
    <h3 class="font-semibold text-gray-800 m-0 flex items-center gap-2">
      <i :class="['fa-solid', icon, 'text-orga-500']"></i>
      <span>{{ title }}</span>
      <span v-if="subtitle" class="text-xs font-normal text-gray-400">{{ subtitle }}</span>
    </h3>

    <div class="flex items-center gap-2">
      <!-- Pin Toggle (optional) -->
      <button
        v-if="showPin"
        @click="emit('pin')"
        :class="[
          'p-1.5 rounded transition-colors',
          isPinned
            ? 'text-amber-500 bg-amber-50'
            : 'text-gray-400 hover:text-amber-500 hover:bg-amber-50'
        ]"
        :title="isPinned ? __('Unpin') : __('Pin')"
      >
        <i class="fa-solid fa-thumbtack"></i>
      </button>

      <!-- Custom Actions Slot -->
      <slot name="actions" />

      <!-- Close Button -->
      <button
        @click="emit('close')"
        class="p-1.5 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100 transition-colors"
        :title="__('Close')"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ManagerHeader Component
 *
 * A reusable header for Manager panels providing:
 * - Title with icon
 * - Optional subtitle
 * - Optional pin toggle button
 * - Custom actions slot
 * - Close button
 *
 * Used by: ActivityPanel, TaskPanel, ContactPanel, EventPanel
 */
import { __ } from '@/composables/useTranslate'

interface Props {
  /** Main title displayed in the header */
  title?: string
  /** Optional subtitle (smaller, gray text) */
  subtitle?: string
  /** FontAwesome icon class (without fa-solid prefix) */
  icon?: string
  /** Whether to show the pin toggle button */
  showPin?: boolean
  /** Current pin state */
  isPinned?: boolean
}

withDefaults(defineProps<Props>(), {
  title: __('Manager'),
  subtitle: '',
  icon: 'fa-sliders',
  showPin: false,
  isPinned: false
})

const emit = defineEmits<{
  /** Emitted when pin button is clicked */
  pin: []
  /** Emitted when close button is clicked */
  close: []
}>()
</script>
