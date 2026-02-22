<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ToastContainer.vue - Global toast notification display

  Position: Fixed bottom-right corner
  Features:
  - Stacked toast display with animations
  - Auto-dismiss with progress indicator
  - Manual dismiss button
  - Accessible with ARIA live region
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useToast, type Toast, type ToastType } from '@/composables/useToast'

const { toasts, dismiss } = useToast()

// Icon configuration by toast type
const iconConfig: Record<ToastType, { icon: string; color: string }> = {
  success: { icon: 'fa-check-circle', color: 'text-green-500' },
  error: { icon: 'fa-exclamation-circle', color: 'text-red-500' },
  warning: { icon: 'fa-exclamation-triangle', color: 'text-amber-500' },
  info: { icon: 'fa-info-circle', color: 'text-blue-500' }
}

// Background colors by toast type
const bgConfig: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800',
  error: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800',
  warning: 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800',
  info: 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800'
}

// Progress bar colors
const progressConfig: Record<ToastType, string> = {
  success: 'bg-green-500',
  error: 'bg-red-500',
  warning: 'bg-amber-500',
  info: 'bg-blue-500'
}

/**
 * Get the icon class for a toast type
 */
function getIcon(type: ToastType): string {
  return iconConfig[type].icon
}

/**
 * Get the icon color for a toast type
 */
function getIconColor(type: ToastType): string {
  return iconConfig[type].color
}

/**
 * Get the background class for a toast type
 */
function getBgClass(type: ToastType): string {
  return bgConfig[type]
}

/**
 * Get the progress bar class for a toast type
 */
function getProgressClass(type: ToastType): string {
  return progressConfig[type]
}

/**
 * Handle keyboard dismiss
 */
function handleKeydown(event: KeyboardEvent, toast: Toast): void {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    dismiss(toast.id)
  }
}
</script>

<template>
  <!-- Toast container - fixed position bottom right -->
  <div
    class="fixed bottom-4 right-4 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none"
    aria-live="polite"
    :aria-label="__('Notifications')"
  >
    <!-- Transition group for smooth enter/leave animations -->
    <TransitionGroup
      name="toast"
      tag="div"
      class="flex flex-col gap-3"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="[
          'pointer-events-auto rounded-lg border shadow-lg overflow-hidden',
          'transform transition-all duration-300',
          getBgClass(toast.type)
        ]"
        role="alert"
        :aria-label="`${toast.type}: ${toast.title}`"
      >
        <!-- Toast content -->
        <div class="flex items-start gap-3 p-4">
          <!-- Icon -->
          <div class="flex-shrink-0 mt-0.5">
            <i
              :class="[
                'fa-solid text-lg',
                getIcon(toast.type),
                getIconColor(toast.type)
              ]"
              aria-hidden="true"
            ></i>
          </div>

          <!-- Text content -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
              {{ toast.title }}
            </p>
            <p
              v-if="toast.message"
              class="mt-1 text-sm text-gray-600 dark:text-gray-400"
            >
              {{ toast.message }}
            </p>
          </div>

          <!-- Dismiss button -->
          <button
            v-if="toast.dismissible"
            type="button"
            class="flex-shrink-0 p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200/50 dark:hover:bg-gray-700/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orga-500"
            @click="dismiss(toast.id)"
            @keydown="handleKeydown($event, toast)"
            :aria-label="__('Dismiss {0} notification', [toast.title])"
          >
            <i class="fa-solid fa-xmark text-sm" aria-hidden="true"></i>
          </button>
        </div>

        <!-- Progress bar for auto-dismiss -->
        <div
          v-if="toast.duration > 0"
          class="h-1 w-full bg-gray-200/50 dark:bg-gray-700/50"
        >
          <div
            :class="[
              'h-full transition-all ease-linear',
              getProgressClass(toast.type)
            ]"
            :style="{
              animation: `toast-progress ${toast.duration}ms linear forwards`
            }"
          ></div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Toast enter/leave transitions */
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.2s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}

/* Progress bar animation */
@keyframes toast-progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}
</style>
