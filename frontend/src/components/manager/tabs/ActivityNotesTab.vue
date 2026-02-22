<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityNotesTab.vue - Notes/annotations tab content for Activity Manager
-->
<template>
  <div class="flex flex-col h-full">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading notes...') }}</p>
    </div>

    <!-- Notes List -->
    <div v-else class="flex-1 overflow-auto space-y-3 mb-3">
      <div
        v-for="note in notes"
        :key="note.name"
        class="flex gap-2 group"
      >
        <UserAvatar
          :name="note.created_by_name"
          :image="note.created_by_image"
          size="sm"
          color="orga"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="text-xs font-medium text-gray-800 dark:text-gray-200">{{ note.created_by_name }}</span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formatRelativeTime(note.creation) }}</span>
            <button
              v-if="canDeleteNote(note)"
              @click="emit('delete', note.name)"
              class="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
              :title="__('Delete note')"
            >
              <i class="fa-solid fa-trash-can text-[10px]"></i>
            </button>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 m-0 break-words whitespace-pre-wrap">{{ note.content }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!notes.length && !isLoading" class="text-center py-8">
        <i class="fa-solid fa-sticky-note fa-2x text-gray-300 dark:text-gray-600 mb-3 block"></i>
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No notes yet.') }}</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Add a note below to annotate this activity.') }}</p>
      </div>
    </div>

    <!-- Add Note Input (sticky at bottom) -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-2 border-t border-gray-100 dark:border-gray-800">
      <div class="flex gap-2">
        <input
          v-model="newNote"
          @keyup.enter="handleAddNote"
          type="text"
          :placeholder="__('Add a note...')"
          :disabled="isAdding"
          class="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:border-orga-500 focus:outline-none focus:ring-1 focus:ring-orga-500/20 disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500"
        />
        <button
          @click="handleAddNote"
          :disabled="isAdding || !newNote.trim()"
          class="px-3 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          :title="__('Add note')"
        >
          <i :class="['fa-solid', isAdding ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { ActivityNote } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  notes: ActivityNote[]
  isLoading: boolean
  isAdding: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  add: [content: string]
  delete: [noteName: string]
}>()

const newNote = ref('')

// Get current user from frappe
const currentUser = computed(() => {
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    return ((window as Record<string, unknown>).frappe as Record<string, Record<string, string>>)?.session?.user || ''
  }
  return ''
})

// Check if user is admin
const isAdmin = computed(() => {
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    const frappe = (window as Record<string, unknown>).frappe as Record<string, Record<string, Record<string, string[]>>>
    const roles = frappe?.boot?.user?.roles || []
    return roles.includes('System Manager')
  }
  return false
})

/**
 * Check if current user can delete a note
 */
function canDeleteNote(note: ActivityNote): boolean {
  return note.created_by === currentUser.value || isAdmin.value
}

/**
 * Handle adding a new note
 */
function handleAddNote() {
  if (newNote.value.trim() && !props.isAdding) {
    emit('add', newNote.value.trim())
    newNote.value = ''
  }
}

/**
 * Format timestamp as relative time
 */
function formatRelativeTime(timestamp?: string): string {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0}m ago', [diffMins])
  if (diffHours < 24) return __('{0}h ago', [diffHours])
  if (diffDays < 7) return __('{0}d ago', [diffDays])

  return date.toLocaleDateString()
}
</script>
