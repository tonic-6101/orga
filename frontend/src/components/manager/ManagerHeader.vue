<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ManagerHeader.vue - Reusable header component for all Manager panels

  Usage:
    <ManagerHeader
      title="Manager"
      subtitle="Task Details"
      icon="sliders"
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
      <OrgaIcon :name="icon" class="w-4 h-4 text-accent-500" />
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
        <Pin class="w-4 h-4" aria-hidden="true" />
      </button>

      <!-- Custom Actions Slot -->
      <slot name="actions" />

      <!-- Close Button -->
      <button
        @click="emit('close')"
        class="p-1.5 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100 transition-colors"
        :title="__('Close')"
      >
        <X class="w-4 h-4" aria-hidden="true" />
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
 * Used by: ActivityPanel, TaskPanel, EventPanel
 */
import { __ } from '@/composables/useTranslate'
import { Pin, X } from 'lucide-vue-next'
import OrgaIcon from '@/components/common/OrgaIcon.vue'

interface Props {
  /** Main title displayed in the header */
  title?: string
  /** Optional subtitle (smaller, gray text) */
  subtitle?: string
  /** Lucide icon name for OrgaIcon */
  icon?: string
  /** Whether to show the pin toggle button */
  showPin?: boolean
  /** Current pin state */
  isPinned?: boolean
}

withDefaults(defineProps<Props>(), {
  title: __('Manager'),
  subtitle: '',
  icon: 'sliders',
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
