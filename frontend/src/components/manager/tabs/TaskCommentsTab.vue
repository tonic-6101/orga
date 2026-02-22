<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskCommentsTab.vue - Comments tab content for Task Manager
-->
<template>
  <div class="flex flex-col h-full">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading comments...') }}</p>
    </div>

    <!-- Comments List -->
    <div v-else class="flex-1 overflow-auto space-y-3 mb-3">
      <div
        v-for="comment in comments"
        :key="comment.name"
        class="flex gap-2 group"
      >
        <UserAvatar
          :name="comment.comment_by_name || comment.comment_by"
          size="sm"
          color="teal"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="text-xs font-medium text-gray-800 dark:text-gray-200">
              {{ comment.comment_by_name || comment.comment_by }}
            </span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">
              {{ formatRelativeTime(comment.comment_time) }}
            </span>
            <button
              v-if="canDeleteComment(comment)"
              @click="emit('delete', comment)"
              class="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
              :title="__('Delete comment')"
            >
              <i class="fa-solid fa-trash-can text-[10px]"></i>
            </button>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 m-0 break-words whitespace-pre-wrap">
            {{ comment.content }}
          </p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!comments.length && !isLoading" class="text-center py-8">
        <i class="fa-solid fa-comments fa-2x text-gray-300 dark:text-gray-600 mb-3 block"></i>
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No comments yet.') }}</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Start the conversation below.') }}</p>
      </div>
    </div>

    <!-- Add Comment Input -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-2 border-t border-gray-100 dark:border-gray-800">
      <div class="flex gap-2">
        <textarea
          v-model="newComment"
          @keyup.ctrl.enter="handleAddComment"
          @keyup.meta.enter="handleAddComment"
          :placeholder="__('Add a comment... (Ctrl+Enter to send)')"
          :disabled="isAdding"
          rows="2"
          class="flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:border-orga-500 focus:outline-none focus:ring-1 focus:ring-orga-500/20 disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500 resize-none"
        ></textarea>
        <button
          @click="handleAddComment"
          :disabled="isAdding || !newComment.trim()"
          class="px-3 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          :title="__('Send comment')"
        >
          <i :class="['fa-solid', isAdding ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TaskComment } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  comments: TaskComment[]
  isLoading: boolean
  isAdding: boolean
  currentUser?: string
}

const props = withDefaults(defineProps<Props>(), {
  currentUser: ''
})

const emit = defineEmits<{
  add: [content: string]
  delete: [comment: TaskComment]
}>()

const newComment = ref('')

// Get current user from frappe if not provided
const currentUserEmail = computed(() => {
  if (props.currentUser) return props.currentUser
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    return ((window as Record<string, unknown>).frappe as Record<string, Record<string, string>>)?.session?.user || ''
  }
  return ''
})

function canDeleteComment(comment: TaskComment): boolean {
  // Allow delete if user is the author or is admin
  if (comment.comment_by === currentUserEmail.value) return true
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    const frappe = (window as Record<string, unknown>).frappe as Record<string, Record<string, Record<string, string[]>>>
    const roles = frappe?.boot?.user?.roles || []
    return roles.includes('System Manager')
  }
  return false
}

function handleAddComment() {
  if (newComment.value.trim() && !props.isAdding) {
    emit('add', newComment.value.trim())
    newComment.value = ''
  }
}

function formatRelativeTime(timestamp: string | null | undefined): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString()
}
</script>
