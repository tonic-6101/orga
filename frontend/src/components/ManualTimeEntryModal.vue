<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ManualTimeEntryModal.vue - Modal for manually logging time.
  Supports all tracking contexts: task, event, project, standalone.
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTimeLogApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import LinkInput from '@/components/common/LinkInput.vue'
import type { TrackingContext } from '@/types/orga'

interface Props {
  show: boolean
  defaultContext?: TrackingContext
  defaultTask?: string
  defaultEvent?: string
  defaultProject?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultContext: 'standalone',
  defaultTask: '',
  defaultEvent: '',
  defaultProject: ''
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created'): void
}>()

const api = useTimeLogApi()

// Form state
const trackingContext = ref<TrackingContext>(props.defaultContext)
const task = ref(props.defaultTask)
const event = ref(props.defaultEvent)
const project = ref(props.defaultProject)
const hours = ref<number | null>(null)
const description = ref('')
const logDate = ref(new Date().toISOString().split('T')[0])
const billable = ref(true)
const isSaving = ref(false)
const errorMsg = ref('')

const canSubmit = computed(() => {
  if (!hours.value || hours.value <= 0) return false
  if (trackingContext.value === 'task' && !task.value) return false
  if (trackingContext.value === 'event' && !event.value) return false
  if (trackingContext.value === 'project' && !project.value) return false
  return true
})

async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || isSaving.value) return
  isSaving.value = true
  errorMsg.value = ''

  try {
    await api.createTimeLog({
      hours: hours.value!,
      tracking_context: trackingContext.value,
      task: trackingContext.value === 'task' ? task.value : null,
      event: trackingContext.value === 'event' ? event.value : null,
      project: ['project', 'task', 'event'].includes(trackingContext.value) ? project.value || null : null,
      description: description.value || null,
      log_date: logDate.value,
      billable: billable.value ? 1 : 0
    })
    emit('created')
    emit('close')
    resetForm()
  } catch (e) {
    errorMsg.value = (e as Error).message || __('Failed to create time log')
  } finally {
    isSaving.value = false
  }
}

function resetForm(): void {
  hours.value = null
  description.value = ''
  logDate.value = new Date().toISOString().split('T')[0]
  billable.value = true
  errorMsg.value = ''
}

// Reset defaults when modal opens
watch(() => props.show, (shown) => {
  if (shown) {
    trackingContext.value = props.defaultContext
    task.value = props.defaultTask
    event.value = props.defaultEvent
    project.value = props.defaultProject
    resetForm()
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-[60] flex items-center justify-center"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/30 dark:bg-black/60" @click="emit('close')"></div>

      <!-- Modal -->
      <div class="relative w-full max-w-md mx-4 bg-white dark:bg-gray-800 rounded-xl shadow-xl dark:shadow-gray-950/50">
        <!-- Header -->
        <div class="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 m-0">{{ __('Log Time') }}</h3>
          <button
            @click="emit('close')"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="p-5 space-y-4">
          <!-- Error -->
          <div v-if="errorMsg" class="p-3 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 text-sm rounded-lg">
            {{ errorMsg }}
          </div>

          <!-- Context -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Context') }}</label>
            <select
              v-model="trackingContext"
              class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 outline-none focus:border-orga-500"
            >
              <option value="task">{{ __('Task') }}</option>
              <option value="event">{{ __('Event') }}</option>
              <option value="project">{{ __('Project') }}</option>
              <option value="standalone">{{ __('Standalone') }}</option>
            </select>
          </div>

          <!-- Task input (shown when context=task) -->
          <div v-if="trackingContext === 'task'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Task') }} <span class="text-red-500">*</span></label>
            <LinkInput
              v-model="task"
              category="task"
              :placeholder="__('Search for a task...')"
            />
          </div>

          <!-- Event input (shown when context=event) -->
          <div v-if="trackingContext === 'event'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Event') }} <span class="text-red-500">*</span></label>
            <LinkInput
              v-model="event"
              category="event"
              :placeholder="__('Search for an event...')"
            />
          </div>

          <!-- Project input (shown when context=project or can be set for task/event) -->
          <div v-if="trackingContext === 'project'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Project') }} <span class="text-red-500">*</span></label>
            <LinkInput
              v-model="project"
              category="project"
              :placeholder="__('Search for a project...')"
            />
          </div>

          <!-- Hours + Date row -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Hours') }} <span class="text-red-500">*</span></label>
              <input
                v-model.number="hours"
                type="number"
                min="0.01"
                step="0.25"
                placeholder="0.00"
                class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 outline-none focus:border-orga-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Date') }}</label>
              <input
                v-model="logDate"
                type="date"
                class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 outline-none focus:border-orga-500"
              />
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ __('Description') }}</label>
            <textarea
              v-model="description"
              rows="2"
              :placeholder="__('What did you work on?')"
              class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-800 dark:text-gray-100 placeholder-gray-400 outline-none focus:border-orga-500 resize-none"
            ></textarea>
          </div>

          <!-- Billable toggle -->
          <div class="flex items-center gap-2">
            <button
              @click="billable = !billable"
              :class="[
                'w-5 h-5 rounded flex items-center justify-center transition-colors',
                billable
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-400 dark:text-gray-500'
              ]"
            >
              <i v-if="billable" class="fa-solid fa-check text-xs"></i>
            </button>
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Billable') }}</span>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 p-5 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleSubmit"
            :disabled="!canSubmit || isSaving"
            class="px-4 py-2 bg-orga-500 text-white text-sm font-medium rounded-lg hover:bg-orga-600 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <i v-if="isSaving" class="fa-solid fa-spinner fa-spin text-xs"></i>
            {{ __('Log Time') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
