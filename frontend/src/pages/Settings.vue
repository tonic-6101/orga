<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsApi } from '@/composables/useApi'
import { useCurrency } from '@/composables/useCurrency'
import { useUpdateChecker } from '@/composables/useUpdateChecker'
import { __ } from '@/composables/useTranslate'
import { version as appVersion } from '../../package.json'
import type { OrgaSettings } from '@/types/orga'

const { getSettings, updateSettings } = useSettingsApi()
const { loadCurrency } = useCurrency()
const { updateInfo, updateAvailable, isChecking, checkError, forceCheck, dismissUpdate } = useUpdateChecker()

// Tab definition
interface Tab {
  id: string
  name: string
  icon: string
}

// Save message
interface SaveMessage {
  type: 'success' | 'error'
  text: string
}

const activeTab = ref<string>('defaults')
const tabs: Tab[] = [
  { id: 'defaults', name: __('Defaults'), icon: 'sliders' },
  { id: 'features', name: __('Features'), icon: 'toggle-on' },
  { id: 'notifications', name: __('Notifications'), icon: 'bell' },
  { id: 'updates', name: __('Updates'), icon: 'arrow-up-from-bracket' }
]

// State
const settings = ref<OrgaSettings>({
  default_task_status: 'Open',
  default_project_status: 'Planning',
  project_code_prefix: 'ORG',
  default_priority: 'Medium',
  default_currency: 'USD',
  auto_calculate_progress: 1,
  auto_set_missed_milestones: 1,
  enable_time_tracking: 0,
  default_capacity_hours: 40,
  notify_on_task_assignment: 1,
  notify_on_status_change: 0,
  notify_on_due_date: 1,
  due_date_reminder_days: 1
})

const isLoading = ref<boolean>(true)
const isSaving = ref<boolean>(false)
const loadError = ref<string | null>(null)
const saveMessage = ref<SaveMessage | null>(null)

// Load settings from backend
async function loadSettings(): Promise<void> {
  isLoading.value = true
  loadError.value = null

  try {
    const data = await getSettings()
    // Map backend fields to local state
    settings.value = {
      default_task_status: data.default_task_status || 'Open',
      default_project_status: data.default_project_status || 'Planning',
      project_code_prefix: data.project_code_prefix || 'ORG',
      default_priority: data.default_priority || 'Medium',
      default_currency: data.default_currency || 'USD',
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
    console.error('Failed to load settings:', e)
    loadError.value = (e as Error).message || __('Failed to load settings')
  } finally {
    isLoading.value = false
  }
}

// Save settings to backend
async function saveSettings(): Promise<void> {
  isSaving.value = true
  saveMessage.value = null

  try {
    await updateSettings(settings.value)
    // Reload the global currency ref so all components update immediately
    await loadCurrency()
    saveMessage.value = { type: 'success', text: __('Settings saved successfully') }
    setTimeout(() => { saveMessage.value = null }, 3000)
  } catch (e) {
    console.error('Failed to save settings:', e)
    saveMessage.value = { type: 'error', text: (e as Error).message || __('Failed to save settings') }
  } finally {
    isSaving.value = false
  }
}

// Reset to defaults
function resetDefaults(): void {
  settings.value = {
    default_task_status: 'Open',
    default_project_status: 'Planning',
    project_code_prefix: 'ORG',
    default_priority: 'Medium',
    default_currency: 'USD',
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
  <div class="p-6 bg-white dark:bg-gray-950 min-h-full">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Settings') }}</h1>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-20">
      <div class="text-center">
        <i class="fa-solid fa-spinner fa-spin text-3xl text-orga-500 mb-3"></i>
        <p class="text-gray-500 dark:text-gray-400">{{ __('Loading settings...') }}</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="flex items-center justify-center py-20">
      <div class="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 max-w-md text-center">
        <i class="fa-solid fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
        <h3 class="text-red-800 dark:text-red-300 font-medium mb-2">{{ __('Error loading settings') }}</h3>
        <p class="text-red-600 dark:text-red-400 text-sm mb-4">{{ loadError }}</p>
        <button @click="loadSettings" class="px-4 py-2 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-900/60">
          {{ __('Try Again') }}
        </button>
      </div>
    </div>

    <!-- Settings Content -->
    <div v-else class="flex gap-6">
      <!-- Sidebar Nav -->
      <nav class="w-60 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg py-3 shrink-0">
        <a
          v-for="tab in tabs"
          :key="tab.id"
          href="#"
          :class="[
            'flex items-center gap-3 px-5 py-3 text-sm transition-all no-underline',
            activeTab === tab.id
              ? 'text-orga-500 dark:text-orga-400 bg-orga-50 dark:bg-orga-950/30 border-l-[3px] border-orga-500 dark:border-orga-400'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
          ]"
          @click.prevent="activeTab = tab.id"
        >
          <i :class="['fa-solid', `fa-${tab.icon}`, 'w-5 text-center']"></i>
          <span>{{ tab.name }}</span>
        </a>
      </nav>

      <!-- Content -->
      <div class="flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <!-- Save Message -->
        <div v-if="saveMessage" :class="[
          'px-4 py-3 text-sm',
          saveMessage.type === 'success' ? 'bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 border-b border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-b border-red-200 dark:border-red-800'
        ]">
          <i :class="['fa-solid mr-2', saveMessage.type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle']"></i>
          {{ saveMessage.text }}
        </div>

        <!-- Defaults Tab -->
        <template v-if="activeTab === 'defaults'">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Default Values') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0">{{ __('Configure default values for new projects and tasks') }}</p>
          </div>
          <div class="p-6">
            <!-- Default Task Status -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Default Task Status') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Status assigned to new tasks') }}</p>
              </div>
              <select v-model="settings.default_task_status" class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400">
                <option value="Open">{{ __('Open') }}</option>
                <option value="In Progress">{{ __('In Progress') }}</option>
              </select>
            </div>

            <!-- Default Project Status -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Default Project Status') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Status assigned to new projects') }}</p>
              </div>
              <select v-model="settings.default_project_status" class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400">
                <option value="Planning">{{ __('Planning') }}</option>
                <option value="Active">{{ __('Active') }}</option>
              </select>
            </div>

            <!-- Project Code Prefix -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Project Code Prefix') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Prefix for auto-generated project codes (e.g., ORG-2026-0001)') }}</p>
              </div>
              <input
                v-model="settings.project_code_prefix"
                type="text"
                class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-32 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                maxlength="10"
              />
            </div>

            <!-- Default Priority -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Default Priority') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Priority assigned to new tasks') }}</p>
              </div>
              <select v-model="settings.default_priority" class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400">
                <option value="Low">{{ __('Low') }}</option>
                <option value="Medium">{{ __('Medium') }}</option>
                <option value="High">{{ __('High') }}</option>
                <option value="Urgent">{{ __('Urgent') }}</option>
              </select>
            </div>

            <!-- Default Currency -->
            <div class="flex justify-between items-center py-3">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Default Currency') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Currency used for budgets, costs, and billing rates') }}</p>
              </div>
              <select v-model="settings.default_currency" class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm min-w-[150px] text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400">
                <option value="USD">USD — US Dollar</option>
                <option value="EUR">EUR — Euro</option>
                <option value="GBP">GBP — British Pound</option>
                <option value="CHF">CHF — Swiss Franc</option>
                <option value="JPY">JPY — Japanese Yen</option>
                <option value="CAD">CAD — Canadian Dollar</option>
                <option value="AUD">AUD — Australian Dollar</option>
                <option value="INR">INR — Indian Rupee</option>
                <option value="CNY">CNY — Chinese Yuan</option>
                <option value="BRL">BRL — Brazilian Real</option>
                <option value="SEK">SEK — Swedish Krona</option>
                <option value="NOK">NOK — Norwegian Krone</option>
                <option value="DKK">DKK — Danish Krone</option>
                <option value="PLN">PLN — Polish Zloty</option>
                <option value="CZK">CZK — Czech Koruna</option>
                <option value="HUF">HUF — Hungarian Forint</option>
                <option value="TRY">TRY — Turkish Lira</option>
                <option value="ZAR">ZAR — South African Rand</option>
                <option value="SGD">SGD — Singapore Dollar</option>
                <option value="HKD">HKD — Hong Kong Dollar</option>
                <option value="NZD">NZD — New Zealand Dollar</option>
                <option value="MXN">MXN — Mexican Peso</option>
                <option value="KRW">KRW — South Korean Won</option>
              </select>
            </div>
          </div>
        </template>

        <!-- Features Tab -->
        <template v-else-if="activeTab === 'features'">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Features') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0">{{ __('Enable or disable optional features') }}</p>
          </div>
          <div class="p-6">
            <!-- Auto Calculate Progress -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Auto Calculate Progress') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Automatically calculate project progress from task completion') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.auto_calculate_progress" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Auto Set Missed Milestones -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Auto Set Missed Milestones') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Automatically mark milestones as missed when overdue') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.auto_set_missed_milestones" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Enable Time Tracking -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Enable Time Tracking') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Allow users to log time against tasks') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.enable_time_tracking" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Default Capacity Hours -->
            <div class="flex justify-between items-center py-3">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Default Weekly Capacity') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Default hours per week for contact capacity planning') }}</p>
              </div>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="settings.default_capacity_hours"
                  type="number"
                  min="1"
                  max="168"
                  class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                />
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ __('hours') }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Notifications Tab -->
        <template v-else-if="activeTab === 'notifications'">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('Notifications') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0">{{ __('Configure email notification settings') }}</p>
          </div>
          <div class="p-6">
            <!-- Notify on Task Assignment -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Task Assignment') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Send notification when a task is assigned to a user') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.notify_on_task_assignment" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Notify on Status Change -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Status Changes') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Send notification when task status changes') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.notify_on_status_change" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Notify on Due Date -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Due Date Reminders') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Send reminder before task due date') }}</p>
              </div>
              <label class="relative inline-block w-11 h-6">
                <input v-model="settings.notify_on_due_date" type="checkbox" :true-value="1" :false-value="0" class="sr-only peer" />
                <span class="absolute inset-0 bg-gray-200 dark:bg-gray-600 rounded-full cursor-pointer peer-checked:bg-orga-500 transition-all"></span>
                <span class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></span>
              </label>
            </div>

            <!-- Due Date Reminder Days -->
            <div class="flex justify-between items-center py-3">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Reminder Lead Time') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Days before due date to send reminder') }}</p>
              </div>
              <div class="flex items-center gap-2">
                <input
                  v-model.number="settings.due_date_reminder_days"
                  type="number"
                  min="1"
                  max="30"
                  class="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-sm w-20 text-right text-gray-900 dark:text-gray-100 focus:outline-none focus:border-orga-500 dark:focus:border-orga-400"
                />
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ __('days') }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Updates Tab -->
        <template v-else-if="activeTab === 'updates'">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 m-0">{{ __('App Updates') }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-0">{{ __('Check for new versions of Orga') }}</p>
          </div>
          <div class="p-6">
            <!-- Current Version -->
            <div class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Installed Version') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">{{ __('Currently running version') }}</p>
              </div>
              <span class="text-sm font-mono text-gray-900 dark:text-gray-100">
                v{{ updateInfo?.current_version || appVersion }}
              </span>
            </div>

            <!-- Latest Version -->
            <div v-if="updateInfo" class="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 m-0">{{ __('Latest Version') }}</h4>
                <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-1">
                  {{ __('Last checked: {0}', [updateInfo.checked_at ? new Date(updateInfo.checked_at).toLocaleString() : __('Never')]) }}
                </p>
              </div>
              <span :class="[
                'text-sm font-mono',
                updateInfo.update_available ? 'text-amber-600 dark:text-amber-400 font-semibold' : 'text-green-600 dark:text-green-400'
              ]">
                v{{ updateInfo.latest_version }}
              </span>
            </div>

            <!-- Update Available Banner -->
            <div v-if="updateInfo?.update_available" class="mt-4 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
              <div class="flex items-start gap-3">
                <i class="fa-solid fa-circle-up text-amber-500 text-xl mt-0.5"></i>
                <div class="flex-1">
                  <h4 class="text-sm font-semibold text-amber-800 dark:text-amber-300 m-0">
                    {{ __('Update Available') }}
                  </h4>
                  <p class="text-sm text-amber-700 dark:text-amber-400 mt-1 mb-0">
                    {{ __('Version {0} is available. You are running {1}.', [updateInfo.latest_version, updateInfo.current_version]) }}
                  </p>
                  <!-- Release notes preview -->
                  <div v-if="updateInfo.release_notes" class="mt-3 text-xs text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 rounded p-3 max-h-40 overflow-y-auto whitespace-pre-wrap">
                    {{ updateInfo.release_notes.substring(0, 500) }}
                    <span v-if="updateInfo.release_notes.length > 500">...</span>
                  </div>
                  <!-- Actions -->
                  <div class="mt-3 flex items-center gap-3">
                    <a
                      :href="updateInfo.release_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded transition-colors no-underline"
                    >
                      <i class="fa-brands fa-github text-xs"></i>
                      {{ __('View Release') }}
                    </a>
                    <button
                      @click="dismissUpdate"
                      class="px-3 py-1.5 text-sm text-amber-700 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40 rounded transition-colors"
                    >
                      {{ __('Dismiss') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Up to Date Banner -->
            <div v-else-if="updateInfo && !updateInfo.update_available" class="mt-4 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg">
              <div class="flex items-center gap-3">
                <i class="fa-solid fa-circle-check text-green-500 text-xl"></i>
                <div>
                  <h4 class="text-sm font-semibold text-green-800 dark:text-green-300 m-0">{{ __('Up to Date') }}</h4>
                  <p class="text-sm text-green-700 dark:text-green-400 mt-1 mb-0">{{ __('You are running the latest version of Orga.') }}</p>
                </div>
              </div>
            </div>

            <!-- No Data Yet -->
            <div v-else class="mt-4 p-4 bg-gray-50 dark:bg-gray-700/30 border border-gray-200 dark:border-gray-600 rounded-lg text-center">
              <p class="text-sm text-gray-500 dark:text-gray-400 m-0">{{ __('No update information available yet.') }}</p>
            </div>

            <!-- Error Message -->
            <div v-if="checkError" class="mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
              <i class="fa-solid fa-exclamation-triangle mr-1"></i>
              {{ __('Update check failed: {0}', [checkError]) }}
            </div>

            <!-- Manual Check Button -->
            <div class="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
              <button
                @click="forceCheck"
                :disabled="isChecking"
                class="px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <i :class="['fa-solid', isChecking ? 'fa-spinner fa-spin' : 'fa-rotate']"></i>
                {{ isChecking ? __('Checking...') : __('Check for Updates') }}
              </button>
            </div>
          </div>
        </template>

        <!-- Actions (hidden on Updates tab) -->
        <div v-if="activeTab !== 'updates'" class="p-4 bg-gray-50 dark:bg-gray-700/50 flex justify-end gap-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="resetDefaults"
            class="px-4 py-2 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-500 rounded hover:bg-gray-200 dark:hover:bg-gray-500 text-sm font-medium transition-colors"
          >
            {{ __('Reset to Defaults') }}
          </button>
          <button
            @click="saveSettings"
            :disabled="isSaving"
            class="px-4 py-2 bg-orga-500 hover:bg-orga-600 dark:bg-orga-600 dark:hover:bg-orga-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            <i v-if="isSaving" class="fa-solid fa-spinner fa-spin"></i>
            {{ isSaving ? __('Saving...') : __('Save Changes') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
