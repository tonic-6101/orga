<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Orga Settings — rendered inside Dock's unified settings host.
  Dock provides the page title ("Orga Settings") and layout chrome.
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsApi } from '@/composables/useApi'
import { useUpdateChecker } from '@/composables/useUpdateChecker'
import { __ } from '@/composables/useTranslate'
import { version as appVersion } from '../../package.json'
import { Loader2, TriangleAlert, CircleCheck, AlertCircle, ArrowUpCircle, RotateCcw } from 'lucide-vue-next'
import type { OrgaSettings } from '@/types/orga'

const { getSettings, updateSettings } = useSettingsApi()
const { updateInfo, updateAvailable, isChecking, checkError, forceCheck, dismissUpdate } = useUpdateChecker()

// Tabs
const tabs = [
  { label: __('Defaults') },
  { label: __('Features') },
  { label: __('Notifications') },
  { label: __('Updates') },
]

const activeTab = ref(0)

// State
const settings = ref<OrgaSettings>({
  default_task_status: 'Open',
  default_project_status: 'Planning',
  project_code_prefix: 'ORG',
  default_priority: 'Medium',
  auto_calculate_progress: 1,
  auto_set_missed_milestones: 1,
  enable_time_tracking: 0,
  default_capacity_hours: 40,
  notify_on_task_assignment: 1,
  notify_on_status_change: 0,
  notify_on_due_date: 1,
  due_date_reminder_days: 1
})

const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref<string | null>(null)
const saveMessage = ref<{ type: 'success' | 'error'; text: string } | null>(null)

async function loadSettings(): Promise<void> {
  isLoading.value = true
  loadError.value = null
  try {
    const data = await getSettings()
    settings.value = {
      default_task_status: data.default_task_status || 'Open',
      default_project_status: data.default_project_status || 'Planning',
      project_code_prefix: data.project_code_prefix || 'ORG',
      default_priority: data.default_priority || 'Medium',
      auto_calculate_progress: data.auto_calculate_progress ? 1 : 0,
      auto_set_missed_milestones: data.auto_set_missed_milestones ? 1 : 0,
      enable_time_tracking: data.enable_time_tracking ? 1 : 0,
      default_capacity_hours: data.default_capacity_hours || 40,
      notify_on_task_assignment: data.notify_on_task_assignment ? 1 : 0,
      notify_on_status_change: data.notify_on_status_change ? 1 : 0,
      notify_on_due_date: data.notify_on_due_date ? 1 : 0,
      due_date_reminder_days: data.due_date_reminder_days || 1
    }
  } catch (e) {
    loadError.value = (e as Error).message || __('Failed to load settings')
  } finally {
    isLoading.value = false
  }
}

async function saveSettings(): Promise<void> {
  isSaving.value = true
  saveMessage.value = null
  try {
    await updateSettings(settings.value)
    saveMessage.value = { type: 'success', text: __('Saved') }
    setTimeout(() => { saveMessage.value = null }, 2500)
  } catch (e) {
    saveMessage.value = { type: 'error', text: (e as Error).message || __('Failed to save') }
  } finally {
    isSaving.value = false
  }
}

function resetDefaults(): void {
  settings.value = {
    default_task_status: 'Open',
    default_project_status: 'Planning',
    project_code_prefix: 'ORG',
    default_priority: 'Medium',
    auto_calculate_progress: 1,
    auto_set_missed_milestones: 1,
    enable_time_tracking: 0,
    default_capacity_hours: 40,
    notify_on_task_assignment: 1,
    notify_on_status_change: 0,
    notify_on_due_date: 1,
    due_date_reminder_days: 1
  }
}

onMounted(loadSettings)
</script>

<template>
  <!-- Loading -->
  <div v-if="isLoading" class="flex items-center justify-center py-20">
    <div class="h-6 w-6 animate-spin rounded-full border-2 border-accent-600 border-t-transparent" />
  </div>

  <!-- Error -->
  <div v-else-if="loadError" class="max-w-md">
    <div class="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-center">
      <TriangleAlert class="w-8 h-8 text-red-500 mx-auto mb-3" aria-hidden="true" />
      <h3 class="text-sm font-medium text-red-800 dark:text-red-300 mb-2">{{ __('Error loading settings') }}</h3>
      <p class="text-xs text-red-600 dark:text-red-400 mb-4">{{ loadError }}</p>
      <button
        class="rounded-lg border border-red-300 dark:border-red-700 px-4 py-2 text-sm font-medium text-red-700 dark:text-red-300
               hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
        @click="loadSettings"
      >
        {{ __('Try Again') }}
      </button>
    </div>
  </div>

  <!-- Settings -->
  <template v-else>
    <!-- Tab bar -->
    <nav class="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6">
      <button
        v-for="(tab, i) in tabs"
        :key="tab.label"
        class="relative px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === i
          ? 'text-gray-900 dark:text-white'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="activeTab = i"
      >
        {{ tab.label }}
        <span
          v-if="activeTab === i"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-600 dark:bg-accent-400 rounded-full"
        />
      </button>
    </nav>

    <!-- ── Defaults ──────────────────────────────────── -->
    <div v-if="activeTab === 0" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Default Values') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Configure default values for new projects and tasks') }}</p>
        <div class="space-y-5">
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Default Task Status') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Status assigned to new tasks') }}</p>
            </div>
            <select v-model="settings.default_task_status"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400">
              <option value="Open">{{ __('Open') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
            </select>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Default Project Status') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Status assigned to new projects') }}</p>
            </div>
            <select v-model="settings.default_project_status"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400">
              <option value="Planning">{{ __('Planning') }}</option>
              <option value="Active">{{ __('Active') }}</option>
            </select>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Project Code Prefix') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Prefix for auto-generated project codes (e.g., ORG-2026-0001)') }}</p>
            </div>
            <input v-model="settings.project_code_prefix" type="text" maxlength="10"
              class="w-32 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400" />
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Default Priority') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Priority assigned to new tasks') }}</p>
            </div>
            <select v-model="settings.default_priority"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400">
              <option value="Low">{{ __('Low') }}</option>
              <option value="Medium">{{ __('Medium') }}</option>
              <option value="High">{{ __('High') }}</option>
              <option value="Urgent">{{ __('Urgent') }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Features ──────────────────────────────────── -->
    <div v-else-if="activeTab === 1" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Features') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Enable or disable optional features') }}</p>
        <div class="space-y-5">
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Auto Calculate Progress') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Automatically calculate project progress from task completion') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.auto_calculate_progress ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.auto_calculate_progress"
              @click="settings.auto_calculate_progress = settings.auto_calculate_progress ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.auto_calculate_progress ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Auto Set Missed Milestones') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Automatically mark milestones as missed when overdue') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.auto_set_missed_milestones ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.auto_set_missed_milestones"
              @click="settings.auto_set_missed_milestones = settings.auto_set_missed_milestones ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.auto_set_missed_milestones ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Enable Time Tracking') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Allow users to log time against tasks') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.enable_time_tracking ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.enable_time_tracking"
              @click="settings.enable_time_tracking = settings.enable_time_tracking ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.enable_time_tracking ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Default Weekly Capacity') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Default hours per week for contact capacity planning') }}</p>
            </div>
            <div class="flex items-center gap-1.5">
              <input v-model.number="settings.default_capacity_hours" type="number" min="1" max="168"
                class="w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                       px-3 py-2 text-sm text-gray-900 dark:text-white text-right
                       focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400" />
              <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('hours') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Notifications ─────────────────────────────── -->
    <div v-else-if="activeTab === 2" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Email Notifications') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Configure email notification settings') }}</p>
        <div class="space-y-5">
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Task Assignment') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Send notification when a task is assigned to a user') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.notify_on_task_assignment ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.notify_on_task_assignment"
              @click="settings.notify_on_task_assignment = settings.notify_on_task_assignment ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.notify_on_task_assignment ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Status Changes') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Send notification when task status changes') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.notify_on_status_change ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.notify_on_status_change"
              @click="settings.notify_on_status_change = settings.notify_on_status_change ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.notify_on_status_change ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Due Date Reminders') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Send reminder before task due date') }}</p>
            </div>
            <button
              class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400 focus:ring-offset-2"
              :class="settings.notify_on_due_date ? 'bg-accent-600 dark:bg-accent-400' : 'bg-gray-200 dark:bg-gray-600'"
              role="switch" :aria-checked="!!settings.notify_on_due_date"
              @click="settings.notify_on_due_date = settings.notify_on_due_date ? 0 : 1"
            >
              <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-200"
                :class="settings.notify_on_due_date ? 'translate-x-4' : 'translate-x-0'" />
            </button>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Reminder Lead Time') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Days before due date to send reminder') }}</p>
            </div>
            <div class="flex items-center gap-1.5">
              <input v-model.number="settings.due_date_reminder_days" type="number" min="1" max="30"
                class="w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                       px-3 py-2 text-sm text-gray-900 dark:text-white text-right
                       focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400" />
              <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('days') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Updates ────────────────────────────────────── -->
    <div v-else-if="activeTab === 3" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('App Updates') }}
        </h2>
        <div class="space-y-5">
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Installed Version') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('Currently running version') }}</p>
            </div>
            <span class="text-sm font-mono text-gray-900 dark:text-white">
              v{{ updateInfo?.current_version || appVersion }}
            </span>
          </div>

          <div v-if="updateInfo" class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Latest Version') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">
                {{ __('Last checked:') }} {{ updateInfo.checked_at ? new Date(updateInfo.checked_at).toLocaleString() : __('Never') }}
              </p>
            </div>
            <span class="text-sm font-mono" :class="updateInfo.update_available ? 'text-amber-600 dark:text-amber-400 font-semibold' : 'text-green-600 dark:text-green-400'">
              v{{ updateInfo.latest_version }}
            </span>
          </div>
        </div>
      </div>

      <!-- Update available banner -->
      <div v-if="updateInfo?.update_available" class="rounded-lg border border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 p-5">
        <div class="flex items-start gap-3">
          <ArrowUpCircle class="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div class="flex-1">
            <h3 class="text-sm font-semibold text-amber-800 dark:text-amber-300">{{ __('Update Available') }}</h3>
            <p class="text-sm text-amber-700 dark:text-amber-400 mt-1">
              {{ __('Version {0} is available. You are running {1}.', [updateInfo.latest_version, updateInfo.current_version]) }}
            </p>
            <div v-if="updateInfo.release_notes" class="mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded-lg p-3 max-h-40 overflow-y-auto whitespace-pre-wrap">
              {{ updateInfo.release_notes.substring(0, 500) }}<span v-if="updateInfo.release_notes.length > 500">...</span>
            </div>
            <div class="mt-3 flex items-center gap-3">
              <a :href="updateInfo.release_url" target="_blank" rel="noopener noreferrer"
                class="rounded-lg bg-amber-600 hover:bg-amber-700 px-4 py-2 text-sm font-medium text-white transition-colors no-underline">
                {{ __('View Release') }}
              </a>
              <button @click="dismissUpdate"
                class="rounded-lg px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors">
                {{ __('Dismiss') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Up to date -->
      <div v-else-if="updateInfo && !updateInfo.update_available" class="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-5">
        <div class="flex items-center gap-3">
          <CircleCheck class="w-5 h-5 text-green-500" aria-hidden="true" />
          <div>
            <h3 class="text-sm font-semibold text-green-800 dark:text-green-300">{{ __('Up to Date') }}</h3>
            <p class="text-xs text-green-700 dark:text-green-400 mt-1">{{ __('You are running the latest version of Orga.') }}</p>
          </div>
        </div>
      </div>

      <!-- Check error -->
      <p v-if="checkError" class="text-xs text-red-500">
        <TriangleAlert class="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
        {{ __('Update check failed:') }} {{ checkError }}
      </p>

      <!-- Manual check -->
      <button
        @click="forceCheck" :disabled="isChecking"
        class="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
               text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
      >
        <Loader2 v-if="isChecking" class="w-4 h-4 animate-spin" aria-hidden="true" />
        <RotateCcw v-else class="w-4 h-4" aria-hidden="true" />
        {{ isChecking ? __('Checking...') : __('Check for Updates') }}
      </button>
    </div>

    <!-- Save button (not on Updates tab) -->
    <div v-if="activeTab !== 3" class="flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4 mt-6">
      <button
        @click="saveSettings" :disabled="isSaving"
        class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
               hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
      >
        {{ isSaving ? __('Saving…') : __('Save') }}
      </button>
      <button
        @click="resetDefaults"
        class="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
               text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        {{ __('Reset to Defaults') }}
      </button>
      <span v-if="saveMessage" class="text-xs" :class="saveMessage.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-500'">
        {{ saveMessage.text }}
      </span>
    </div>
  </template>
</template>
