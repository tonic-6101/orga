<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  WatchTimeTab.vue - Time tracking tab for Task Manager (Watch integration)
  Shows Watch entries linked to this task via orga_task custom field.
  Delegates timer to Dock's dock_timer_api (Watch backend).
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { OrgaTask } from '@/types/orga'
import { Timer as TimerIcon, ExternalLink, Loader2, Circle } from 'lucide-vue-next'

interface WatchEntry {
  name: string
  date: string
  user: string
  start_time?: string
  end_time?: string
  duration_hours: number
  description?: string
  entry_type: string
  is_running: 0 | 1
  orga_task?: string
  orga_project?: string
  tags?: Array<{ tag: string }>
}

interface Props {
  task: OrgaTask
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update'): void
}>()

const entries = ref<WatchEntry[]>([])
const totalHours = ref(0)
const loading = ref(false)
const watchInstalled = ref(false)

// Check if Watch is available
const boot = (window as any).frappe?.boot
const dockBoot = boot?.dock || (window as any).dockBoot?.dock
watchInstalled.value = !!(dockBoot?.registered_apps?.some((a: any) => a.app === 'watch' || a.label === 'Watch'))
  || boot?.installed_apps?.includes?.('watch')

async function loadEntries(): Promise<void> {
  if (!watchInstalled.value || !props.task?.name) return

  loading.value = true
  try {
    const result = await frappeRequest({
      url: '/api/method/watch.api.time_entry.get_entries',
      params: {
        filters: JSON.stringify({ orga_task: props.task.name, is_running: 0 }),
        limit: 50,
        order_by: 'date desc',
      },
    })
    entries.value = (result?.entries || result?.message?.entries || result || []) as WatchEntry[]
    totalHours.value = entries.value.reduce((sum, e) => sum + (e.duration_hours || 0), 0)
  } catch {
    entries.value = []
    totalHours.value = 0
  } finally {
    loading.value = false
  }
}

function formatHours(h: number): string {
  if (h >= 1) return `${h.toFixed(1)}h`
  const mins = Math.round(h * 60)
  return mins > 0 ? `${mins}m` : '0m'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

watch(() => props.task?.name, () => loadEntries())
onMounted(() => loadEntries())
</script>

<template>
  <div class="p-4">
    <!-- Watch not installed -->
    <div v-if="!watchInstalled" class="text-center py-8">
      <TimerIcon class="w-8 h-8 text-gray-300 dark:text-gray-600 mb-3 mx-auto" aria-hidden="true" />
      <p class="text-sm text-gray-500 dark:text-gray-400">{{ __('Time tracking requires Watch') }}</p>
      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('Install the Watch app to track time on tasks') }}</p>
    </div>

    <!-- Watch installed -->
    <div v-else>
      <!-- Summary -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <TimerIcon class="w-4 h-4 text-accent-500" aria-hidden="true" />
          <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {{ formatHours(totalHours) }}
          </span>
          <span v-if="props.task.estimated_hours" class="text-xs text-gray-400">
            / {{ formatHours(props.task.estimated_hours) }} {{ __('estimated') }}
          </span>
        </div>
        <a
          href="/watch"
          target="_blank"
          class="text-xs text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 no-underline"
        >
          {{ __('Open Watch') }}
          <ExternalLink class="w-2.5 h-2.5 inline ml-0.5" aria-hidden="true" />
        </a>
      </div>

      <!-- Progress bar -->
      <div v-if="props.task.estimated_hours" class="mb-4">
        <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300"
            :class="totalHours > (props.task.estimated_hours || 0) ? 'bg-red-500' : 'bg-accent-500'"
            :style="{ width: Math.min((totalHours / (props.task.estimated_hours || 1)) * 100, 100) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="py-6 text-center">
        <Loader2 class="w-4 h-4 animate-spin text-gray-400 mx-auto" aria-hidden="true" />
      </div>

      <!-- Empty state -->
      <div v-else-if="entries.length === 0" class="text-center py-6">
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No time logged on this task') }}</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
          {{ __('Start a timer from Watch or the Dock top bar') }}
        </p>
      </div>

      <!-- Entries list -->
      <div v-else class="space-y-1.5">
        <div
          v-for="entry in entries"
          :key="entry.name"
          class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <div class="flex-1 min-w-0">
            <p class="text-sm text-gray-700 dark:text-gray-300 truncate m-0">
              {{ entry.description || __('Time entry') }}
            </p>
            <p class="text-xs text-gray-400 dark:text-gray-500 m-0 mt-0.5">
              {{ formatDate(entry.date) }}
              <span v-if="entry.start_time"> &middot; {{ entry.start_time?.slice(0, 5) }}</span>
              <span v-if="entry.entry_type === 'billable'" class="text-green-500 ml-1">
                <Circle class="w-1.5 h-1.5 inline fill-current" aria-hidden="true" />
              </span>
            </p>
          </div>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300 ml-3 flex-shrink-0">
            {{ formatHours(entry.duration_hours) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
