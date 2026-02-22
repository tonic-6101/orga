<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * MigrationPanel - UI for migrating from Frappe Projects to Orga
 *
 * Features:
 * - Preview migration (dry run)
 * - Execute migration with progress
 * - View migration history
 * - Rollback capability
 */

import { ref, computed, onMounted } from 'vue'
import { frappeRequest } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'

interface MigrationPreview {
  success: boolean
  projects: Array<{
    name: string
    project_name: string
    task_count: number
    already_migrated: boolean
  }>
  total_projects: number
  total_tasks: number
  already_migrated: number
  warnings: Array<{
    type: string
    message: string
  }>
}

interface MigrationResult {
  success: boolean
  migration_id: string
  dry_run: boolean
  projects_created: number
  projects_updated: number
  projects_skipped: number
  tasks_created: number
  tasks_updated: number
  errors: Array<{
    type: string
    name: string
    error: string
  }>
}

interface MigrationHistory {
  migration_id: string
  timestamp: string
  user: string
  projects_created: number
  tasks_created: number
  rolled_back: boolean
}

// State
const isLoading = ref(false)
const preview = ref<MigrationPreview | null>(null)
const migrationResult = ref<MigrationResult | null>(null)
const history = ref<MigrationHistory[]>([])
const activeTab = ref<'migrate' | 'history'>('migrate')
const skipExisting = ref(true)
const isRollingBack = ref(false)

// Computed
const canMigrate = computed(() => {
  return preview.value?.success &&
    preview.value.total_projects > 0 &&
    !isLoading.value
})

const hasErrors = computed(() => {
  return migrationResult.value?.errors && migrationResult.value.errors.length > 0
})

// Load preview on mount
onMounted(async () => {
  await loadPreview()
  await loadHistory()
})

// Load migration preview
async function loadPreview() {
  isLoading.value = true
  try {
    const result = await frappeRequest<MigrationPreview>({
      method: 'orga.orga.integrations.migration.preview_migration'
    })
    preview.value = result
  } catch (e) {
    console.error('Failed to load preview:', e)
    preview.value = null
  } finally {
    isLoading.value = false
  }
}

// Load migration history
async function loadHistory() {
  try {
    const result = await frappeRequest<MigrationHistory[]>({
      method: 'orga.orga.integrations.migration.get_migration_history'
    })
    history.value = result || []
  } catch (e) {
    console.error('Failed to load history:', e)
    history.value = []
  }
}

// Execute dry run
async function executeDryRun() {
  isLoading.value = true
  migrationResult.value = null
  try {
    const result = await frappeRequest<MigrationResult>({
      method: 'orga.orga.integrations.migration.migrate_from_frappe_projects',
      args: {
        skip_existing: skipExisting.value,
        dry_run: true
      }
    })
    migrationResult.value = result
  } catch (e) {
    console.error('Dry run failed:', e)
  } finally {
    isLoading.value = false
  }
}

// Execute real migration
async function executeMigration() {
  if (!confirm(__('This will import all Frappe Projects into Orga. Continue?'))) {
    return
  }

  isLoading.value = true
  migrationResult.value = null
  try {
    const result = await frappeRequest<MigrationResult>({
      method: 'orga.orga.integrations.migration.migrate_from_frappe_projects',
      args: {
        skip_existing: skipExisting.value,
        dry_run: false
      }
    })
    migrationResult.value = result
    await loadHistory()
    await loadPreview()
  } catch (e) {
    console.error('Migration failed:', e)
  } finally {
    isLoading.value = false
  }
}

// Rollback migration
async function rollbackMigration(migrationId: string) {
  if (!confirm(__('This will delete all records created by migration {0}. Continue?', [migrationId]))) {
    return
  }

  isRollingBack.value = true
  try {
    await frappeRequest({
      method: 'orga.orga.integrations.migration.rollback_migration',
      args: { migration_id: migrationId }
    })
    await loadHistory()
    await loadPreview()
  } catch (e) {
    console.error('Rollback failed:', e)
  } finally {
    isRollingBack.value = false
  }
}

// Format date
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div class="migration-panel bg-white rounded-lg shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="p-4 border-b border-gray-200">
      <h3 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
        <i class="fa-solid fa-file-import text-orga-500"></i>
        {{ __('Frappe Projects Migration') }}
      </h3>
      <p class="text-sm text-gray-500 mt-1">
        {{ __('Import existing projects and tasks from Frappe Projects module') }}
      </p>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200">
      <div class="flex">
        <button
          @click="activeTab = 'migrate'"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            activeTab === 'migrate'
              ? 'border-orga-500 text-orga-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ __('Migrate') }}
        </button>
        <button
          @click="activeTab = 'history'"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 -mb-px',
            activeTab === 'history'
              ? 'border-orga-500 text-orga-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
        >
          {{ __('History') }}
          <span v-if="history.length" class="ml-1 text-xs bg-gray-100 px-1.5 py-0.5 rounded">
            {{ history.length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Migrate Tab -->
    <div v-if="activeTab === 'migrate'" class="p-4">
      <!-- Loading -->
      <div v-if="isLoading && !migrationResult" class="text-center py-8">
        <i class="fa-solid fa-spinner fa-spin text-2xl text-gray-400"></i>
        <p class="text-sm text-gray-500 mt-2">{{ __('Loading...') }}</p>
      </div>

      <!-- No Frappe Projects -->
      <div v-else-if="preview && !preview.success" class="text-center py-8">
        <i class="fa-solid fa-exclamation-circle text-3xl text-yellow-500"></i>
        <p class="text-sm text-gray-600 mt-2">{{ preview.message || __('Frappe Projects module not available') }}</p>
      </div>

      <!-- Preview -->
      <div v-else-if="preview && preview.success">
        <!-- Stats -->
        <div class="grid grid-cols-3 gap-4 mb-4">
          <div class="bg-blue-50 rounded-lg p-3 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ preview.total_projects }}</div>
            <div class="text-xs text-blue-500">{{ __('Projects') }}</div>
          </div>
          <div class="bg-green-50 rounded-lg p-3 text-center">
            <div class="text-2xl font-bold text-green-600">{{ preview.total_tasks }}</div>
            <div class="text-xs text-green-500">{{ __('Tasks') }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-3 text-center">
            <div class="text-2xl font-bold text-gray-600">{{ preview.already_migrated }}</div>
            <div class="text-xs text-gray-500">{{ __('Already Migrated') }}</div>
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="preview.warnings.length" class="mb-4 space-y-2">
          <div
            v-for="(warning, idx) in preview.warnings"
            :key="idx"
            :class="[
              'px-3 py-2 rounded-lg text-sm flex items-center gap-2',
              warning.type === 'warning' ? 'bg-yellow-50 text-yellow-700' : 'bg-blue-50 text-blue-700'
            ]"
          >
            <i :class="['fa-solid', warning.type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle']"></i>
            {{ warning.message }}
          </div>
        </div>

        <!-- Options -->
        <div class="mb-4 p-3 bg-gray-50 rounded-lg">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              v-model="skipExisting"
              class="rounded border-gray-300 text-orga-500 focus:ring-orga-500"
            />
            <span class="text-sm text-gray-700">{{ __('Skip already migrated projects') }}</span>
          </label>
        </div>

        <!-- Actions -->
        <div class="flex gap-2">
          <button
            @click="executeDryRun"
            :disabled="!canMigrate"
            class="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 flex items-center gap-2"
          >
            <i class="fa-solid fa-flask"></i>
            {{ __('Dry Run') }}
          </button>
          <button
            @click="executeMigration"
            :disabled="!canMigrate"
            class="px-4 py-2 text-sm bg-orga-500 text-white rounded hover:bg-orga-600 disabled:opacity-50 flex items-center gap-2"
          >
            <i v-if="isLoading" class="fa-solid fa-spinner fa-spin"></i>
            <i v-else class="fa-solid fa-play"></i>
            {{ __('Start Migration') }}
          </button>
        </div>

        <!-- Migration Result -->
        <div v-if="migrationResult" class="mt-4 p-4 rounded-lg" :class="migrationResult.success ? 'bg-green-50' : 'bg-red-50'">
          <h4 class="font-medium mb-2 flex items-center gap-2" :class="migrationResult.success ? 'text-green-700' : 'text-red-700'">
            <i :class="['fa-solid', migrationResult.success ? 'fa-check-circle' : 'fa-exclamation-circle']"></i>
            {{ migrationResult.dry_run ? __('Dry Run Complete') : __('Migration Complete') }}
          </h4>

          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>{{ __('Projects created:') }} <strong>{{ migrationResult.projects_created }}</strong></div>
            <div>{{ __('Projects updated:') }} <strong>{{ migrationResult.projects_updated }}</strong></div>
            <div>{{ __('Projects skipped:') }} <strong>{{ migrationResult.projects_skipped }}</strong></div>
            <div>{{ __('Tasks created:') }} <strong>{{ migrationResult.tasks_created }}</strong></div>
            <div>{{ __('Tasks updated:') }} <strong>{{ migrationResult.tasks_updated }}</strong></div>
          </div>

          <div v-if="!migrationResult.dry_run" class="mt-2 text-xs text-gray-500">
            {{ __('Migration ID:') }} {{ migrationResult.migration_id }}
          </div>

          <!-- Errors -->
          <div v-if="hasErrors" class="mt-3 p-2 bg-red-100 rounded text-sm text-red-700">
            <strong>{{ __("{0} errors:", [migrationResult.errors.length]) }}</strong>
            <ul class="mt-1 list-disc list-inside">
              <li v-for="(err, idx) in migrationResult.errors.slice(0, 5)" :key="idx">
                {{ err.type }}: {{ err.name }} - {{ err.error }}
              </li>
              <li v-if="migrationResult.errors.length > 5">
                {{ __('... and {0} more', [migrationResult.errors.length - 5]) }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="p-4">
      <div v-if="history.length === 0" class="text-center py-8 text-gray-400">
        <i class="fa-solid fa-clock-rotate-left text-3xl mb-2"></i>
        <p class="text-sm">{{ __('No migration history') }}</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="mig in history"
          :key="mig.migration_id"
          class="p-3 border border-gray-200 rounded-lg"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-800">{{ mig.migration_id }}</div>
              <div class="text-xs text-gray-500">
                {{ formatDate(mig.timestamp) }} by {{ mig.user }}
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm">
                <span class="text-blue-600">{{ mig.projects_created }}</span> {{ __('projects') }},
                <span class="text-green-600">{{ mig.tasks_created }}</span> {{ __('tasks') }}
              </div>
              <div v-if="mig.rolled_back" class="text-xs text-red-500">
                <i class="fa-solid fa-undo"></i> {{ __('Rolled back') }}
              </div>
            </div>
          </div>

          <div v-if="!mig.rolled_back" class="mt-2 pt-2 border-t border-gray-100">
            <button
              @click="rollbackMigration(mig.migration_id)"
              :disabled="isRollingBack"
              class="text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
            >
              <i :class="['fa-solid', isRollingBack ? 'fa-spinner fa-spin' : 'fa-undo']"></i>
              {{ __('Rollback') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
