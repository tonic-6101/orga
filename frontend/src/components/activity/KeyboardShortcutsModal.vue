<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  KeyboardShortcutsModal.vue - Help modal showing activity feed keyboard shortcuts
-->
<script setup lang="ts">
import { ACTIVITY_SHORTCUTS } from '@/composables/useActivityKeyboard'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/40"
          @click="emit('close')"
        />

        <!-- Modal -->
        <div class="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-700">
            <h3 class="text-base font-semibold text-gray-800 dark:text-gray-100 m-0">
              <i class="fa-regular fa-keyboard mr-2 text-orga-500"></i>{{ __('Keyboard Shortcuts') }}
            </h3>
            <button
              @click="emit('close')"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <!-- Shortcuts list -->
          <div class="px-5 py-4 space-y-2">
            <div
              v-for="shortcut in ACTIVITY_SHORTCUTS"
              :key="shortcut.key"
              class="flex items-center justify-between py-1.5"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400">{{ shortcut.description }}</span>
              <kbd class="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-md
                         bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600
                         text-xs font-mono font-semibold text-gray-600 dark:text-gray-300">
                {{ shortcut.label }}
              </kbd>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-5 py-3 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <p class="text-xs text-gray-400 dark:text-gray-500 m-0 text-center">
              {{ __('Press') }} <kbd class="px-1 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-[10px] font-mono">?</kbd> {{ __('anytime to show this help') }}
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
