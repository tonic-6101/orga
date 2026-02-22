<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  FloatingTimer.vue - Global timer widget for the Header bar.
  Shows clock icon when idle; pulsing timer when running.
-->
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTimer } from '@/composables/useTimer'
import { useTimeLogApi } from '@/composables/useApi'
import type { TrackingContext } from '@/types/orga'

const {
  timerState,
  formattedTime,
  startTimer,
  stopTimer,
  discardTimer,
  loading
} = useTimer()
const api = useTimeLogApi()

const showDropdown = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

// Start form state
const newDescription = ref('')
const newContext = ref<TrackingContext>('standalone')

// Running timer description
const timerDescription = ref('')

function toggleDropdown(): void {
  showDropdown.value = !showDropdown.value
}

async function handleStart(): Promise<void> {
  try {
    await startTimer({
      trackingContext: newContext.value,
      description: newDescription.value || undefined
    })
    newDescription.value = ''
    newContext.value = 'standalone'
    showDropdown.value = false
  } catch (e) {
    console.error('Failed to start timer:', e)
  }
}

async function handleStop(): Promise<void> {
  try {
    const result = await stopTimer()
    if (timerDescription.value.trim() && result?.name) {
      await api.updateTimeLog(result.name, { description: timerDescription.value.trim() })
    }
    timerDescription.value = ''
    showDropdown.value = false
  } catch (e) {
    console.error('Failed to stop timer:', e)
  }
}

async function handleDiscard(): Promise<void> {
  try {
    await discardTimer()
    showDropdown.value = false
  } catch (e) {
    console.error('Failed to discard timer:', e)
  }
}

function handleClickOutside(e: MouseEvent): void {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    showDropdown.value = false
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
  <div ref="dropdownRef" class="relative">
    <!-- Timer Button -->
    <button
      v-if="!timerState.isRunning"
      @click="toggleDropdown"
      class="w-9 h-9 flex items-center justify-center rounded-lg border border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:text-orga-500 dark:hover:text-orga-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      :title="__('Start Timer')"
    >
      <i class="fa-regular fa-clock text-sm"></i>
    </button>

    <!-- Running Timer Display -->
    <button
      v-else
      @click="toggleDropdown"
      class="flex items-center gap-2 h-9 px-3 rounded-lg border border-orga-200 dark:border-orga-700 bg-orga-50 dark:bg-orga-900/30 text-orga-700 dark:text-orga-300 hover:bg-orga-100 dark:hover:bg-orga-900/50 transition-colors"
      :title="__('Timer running')"
    >
      <!-- Pulsing dot -->
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-orga-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-orga-500"></span>
      </span>
      <!-- Elapsed time -->
      <span class="text-sm font-mono font-medium tabular-nums">{{ formattedTime }}</span>
      <!-- Context label (truncated) -->
      <span v-if="timerState.contextLabel" class="text-xs text-orga-500 dark:text-orga-400 max-w-[80px] truncate hidden sm:inline">
        {{ timerState.contextLabel }}
      </span>
    </button>

    <!-- Dropdown -->
    <div
      v-if="showDropdown"
      class="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-gray-950/50 z-50"
    >
      <!-- Idle: Start form -->
      <div v-if="!timerState.isRunning" class="p-4 space-y-3">
        <h4 class="text-sm font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Start Timer') }}</h4>

        <input
          v-model="newDescription"
          type="text"
          :placeholder="__('What are you working on?')"
          class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:border-orga-500 dark:focus:border-orga-400"
          @keydown.enter="handleStart"
        />

        <select
          v-model="newContext"
          class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 outline-none focus:border-orga-500"
        >
          <option value="standalone">{{ __('Standalone') }}</option>
          <option value="project">{{ __('Project') }}</option>
        </select>

        <button
          @click="handleStart"
          :disabled="loading"
          class="w-full px-4 py-2 bg-orga-500 text-white text-sm font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
        >
          <i class="fa-solid fa-play text-xs"></i>
          {{ __('Start') }}
        </button>
      </div>

      <!-- Running: Timer details -->
      <div v-else class="p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Timer Running') }}</h4>
          <span class="text-lg font-mono font-bold text-orga-600 dark:text-orga-400 tabular-nums">{{ formattedTime }}</span>
        </div>

        <!-- Context info -->
        <div class="p-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 uppercase">
            <i :class="[
              'fa-solid',
              timerState.context === 'task' ? 'fa-check-square' :
              timerState.context === 'event' ? 'fa-calendar' :
              timerState.context === 'project' ? 'fa-folder' : 'fa-clock'
            ]"></i>
            {{ timerState.context }}
          </div>
          <p v-if="timerState.contextLabel" class="text-sm text-gray-800 dark:text-gray-200 mt-1 m-0">
            {{ timerState.contextLabel }}
          </p>
        </div>

        <input
          v-model="timerDescription"
          type="text"
          :placeholder="timerState.activeTimeLog?.description || __('What are you working on?')"
          class="w-full px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:border-orga-500 dark:focus:border-orga-400"
        />

        <!-- Actions -->
        <div class="flex gap-2">
          <button
            @click="handleStop"
            :disabled="loading"
            class="flex-1 px-4 py-2 bg-orga-500 text-white text-sm font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            <i class="fa-solid fa-stop text-xs"></i>
            {{ __('Stop & Save') }}
          </button>
          <button
            @click="handleDiscard"
            :disabled="loading"
            class="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
            :title="__('Discard timer')"
          >
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
