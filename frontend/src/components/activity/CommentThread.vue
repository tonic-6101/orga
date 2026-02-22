<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  CommentThread.vue - Single comment with replies and actions
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { ActivityComment } from '@/types/orga'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'

interface Props {
  comment: ActivityComment
  isReply?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isReply: false
})

const emit = defineEmits<{
  reply: [comment: ActivityComment]
  delete: [commentName: string]
  'replies-loaded': [replies: ActivityComment[]]
}>()

const { getCommentReplies } = useActivityApi()

const showReplies = ref(false)
const isLoadingReplies = ref(false)
const localReplies = ref<ActivityComment[]>([])

const hasReplies = computed(() => props.comment.reply_count > 0)
const displayReplies = computed(() => {
  // Use local replies if loaded, otherwise use passed replies
  return localReplies.value.length > 0 ? localReplies.value : (props.comment.replies || [])
})

function formatRelativeTime(dateStr: string): string {
  if (!dateStr) return ''

  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return __('just now')
  if (diffMins < 60) return __("{0}m ago", [diffMins])
  if (diffHours < 24) return __("{0}h ago", [diffHours])
  if (diffDays < 7) return __("{0}d ago", [diffDays])

  return date.toLocaleDateString()
}

async function toggleReplies() {
  if (!hasReplies.value) return

  showReplies.value = !showReplies.value

  if (showReplies.value && localReplies.value.length === 0) {
    await loadReplies()
  }
}

async function loadReplies() {
  if (isLoadingReplies.value) return

  isLoadingReplies.value = true
  try {
    const replies = await getCommentReplies(props.comment.name)
    localReplies.value = replies
    emit('replies-loaded', replies)
  } catch (e) {
    console.error('Failed to load replies:', e)
  } finally {
    isLoadingReplies.value = false
  }
}

function handleReply() {
  emit('reply', props.comment)
}

function handleDelete() {
  if (confirm(__('Are you sure you want to delete this comment?'))) {
    emit('delete', props.comment.name)
  }
}

function handleDeleteReply(replyName: string) {
  emit('delete', replyName)
  localReplies.value = localReplies.value.filter(r => r.name !== replyName)
}
</script>

<template>
  <div class="comment-thread">
    <!-- Main Comment -->
    <div class="flex gap-2 group">
      <!-- Avatar -->
      <UserAvatar
        :name="comment.user_fullname"
        :image="comment.user_image"
        :size="isReply ? 'xs' : 'md'"
        color="orga"
      />

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <span :class="['font-medium text-gray-800 dark:text-gray-200', isReply ? 'text-xs' : 'text-sm']">
            {{ comment.user_fullname }}
          </span>
          <span class="text-[10px] text-gray-400 dark:text-gray-500">
            {{ formatRelativeTime(comment.creation) }}
          </span>
        </div>

        <div
          :class="['text-gray-600 dark:text-gray-400 mt-0.5 break-words', isReply ? 'text-xs' : 'text-sm', 'comment-content prose prose-sm max-w-none']"
          v-html="sanitizeHtml(comment.content)"
        />

        <!-- Actions -->
        <div class="flex items-center gap-3 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            v-if="!isReply"
            @click="handleReply"
            class="text-[11px] text-gray-500 hover:text-orga-500 dark:text-gray-400 dark:hover:text-orga-400 transition-colors"
          >
            <i class="fa-solid fa-reply mr-1"></i>{{ __('Reply') }}
          </button>

          <button
            v-if="comment.can_delete"
            @click="handleDelete"
            class="text-[11px] text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
          >
            <i class="fa-solid fa-trash mr-1"></i>{{ __('Delete') }}
          </button>
        </div>

        <!-- Reply Count / Toggle -->
        <button
          v-if="hasReplies && !isReply"
          @click="toggleReplies"
          class="mt-2 text-xs text-orga-500 hover:text-orga-600 dark:text-orga-400 dark:hover:text-orga-300 transition-colors"
        >
          <i :class="['fa-solid mr-1', showReplies ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
          {{ showReplies ? __('Hide') : __('Show') }} {{ comment.reply_count }} {{ comment.reply_count === 1 ? __('reply') : __('replies') }}
        </button>
      </div>
    </div>

    <!-- Replies -->
    <Transition name="replies">
      <div
        v-if="showReplies && !isReply"
        class="ml-8 mt-3 space-y-3 border-l-2 border-gray-100 dark:border-gray-700 pl-4"
      >
        <div v-if="isLoadingReplies" class="text-xs text-gray-400 py-2">
          <i class="fa-solid fa-spinner fa-spin mr-1"></i>{{ __('Loading replies...') }}
        </div>

        <CommentThread
          v-for="reply in displayReplies"
          :key="reply.name"
          :comment="reply"
          :is-reply="true"
          @delete="handleDeleteReply"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.replies-enter-active,
.replies-leave-active {
  transition: all 0.2s ease;
}

.replies-enter-from,
.replies-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Rich text comment content styles */
.comment-content :deep(p) {
  margin: 0;
}

.comment-content :deep(p + p) {
  margin-top: 0.25em;
}

.comment-content :deep(.mention) {
  background-color: rgba(var(--orga-500-rgb, 59 130 246) / 0.1);
  color: rgb(var(--orga-600-rgb, 37 99 235));
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  font-weight: 500;
}
</style>
