<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EventActionsTab.vue - Actions tab content for Event Manager
  Includes status change, quick actions, and delete with confirmation
-->
<template>
  <div class="space-y-6">
    <!-- Change Status -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-toggle-on text-orga-500"></i>
        {{ __('Change Status') }}
      </h5>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="status in statuses"
          :key="status"
          @click="emit('status-change', status)"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
            event.status === status
              ? 'bg-orga-500 text-white border-orga-500'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-orga-500 hover:text-orga-500'
          ]"
        >
          {{ __(status) }}
        </button>
      </div>
    </div>

    <!-- Quick Actions -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-bolt text-orga-500"></i>
        {{ __('Quick Actions') }}
      </h5>
      <div class="space-y-2">
        <!-- Edit Event -->
        <button
          @click="emit('edit')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-pen text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Edit Event') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Modify details, time, or attendees') }}</p>
          </div>
        </button>

        <!-- Send Invitations -->
        <button
          @click="emit('send-invitations')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-envelope text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Send Invitations') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Email invitations to all attendees') }}</p>
          </div>
        </button>

        <!-- Open in Desk -->
        <button
          @click="emit('open-desk')"
          class="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
        >
          <i class="fa-solid fa-external-link text-gray-400 dark:text-gray-500"></i>
          <div>
            <p class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Open in Desk') }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ __('Full form view with audit trail') }}</p>
          </div>
        </button>

        <!-- Delete Event (Danger) -->
        <button
          @click="confirmDelete"
          class="w-full flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors text-left"
        >
          <i class="fa-solid fa-trash text-red-500"></i>
          <div>
            <p class="text-sm font-medium text-red-700 dark:text-red-400">{{ __('Delete Event') }}</p>
            <p class="text-xs text-red-500 dark:text-red-400">{{ __('Permanently remove this event') }}</p>
          </div>
        </button>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteConfirm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showDeleteConfirm = false"
    >
      <div class="bg-white dark:bg-gray-900 rounded-lg p-6 max-w-sm mx-4 shadow-xl">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">{{ __('Delete Event?') }}</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {{ __('This will permanently delete "{0}". This action cannot be undone.', [event.title || event.subject]) }}
        </p>
        <div class="flex gap-2 justify-end">
          <button
            @click="showDeleteConfirm = false"
            :disabled="isDeleting"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleDelete"
            :disabled="isDeleting"
            class="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 flex items-center gap-1"
          >
            <i v-if="isDeleting" class="fa-solid fa-spinner fa-spin"></i>
            {{ isDeleting ? __('Deleting...') : __('Delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { OrgaEvent, EventStatus } from '@/types/orga'

interface Props {
  event: OrgaEvent
  isDeleting: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  edit: []
  'send-invitations': []
  'status-change': [status: EventStatus]
  'open-desk': []
  delete: []
}>()

const statuses: EventStatus[] = ['Scheduled', 'Completed', 'Cancelled']
const showDeleteConfirm = ref(false)

function confirmDelete(): void {
  showDeleteConfirm.value = true
}

function handleDelete(): void {
  emit('delete')
}
</script>
