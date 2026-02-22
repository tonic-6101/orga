<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityCardComments.vue - Inline comments section for activity cards
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import type { ActivityComment } from '@/types/orga'
import CommentThread from './CommentThread.vue'
import CommentInput from './CommentInput.vue'

interface Props {
  doctype: string
  docname: string
  initialCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialCount: 0
})

const emit = defineEmits<{
  'comment-added': [comment: ActivityComment]
  'comment-deleted': [commentName: string]
  'count-changed': [count: number]
}>()

const { getActivityComments, addActivityComment, deleteActivityComment } = useActivityApi()

const comments = ref<ActivityComment[]>([])
const totalComments = ref(props.initialCount)
const expanded = ref(false)
const hasMore = ref(false)
const isLoading = ref(false)
const isSubmitting = ref(false)
const replyingTo = ref<ActivityComment | null>(null)
const commentInputRef = ref<InstanceType<typeof CommentInput> | null>(null)

const visibleComments = computed(() => {
  if (expanded.value) return comments.value
  return comments.value.slice(-3) // Show last 3 when collapsed
})

const hasComments = computed(() => totalComments.value > 0)

async function loadComments(offset = 0) {
  isLoading.value = true
  try {
    const result = await getActivityComments(props.doctype, props.docname, 10, offset)
    if (offset === 0) {
      comments.value = result.comments
    } else {
      comments.value = [...comments.value, ...result.comments]
    }
    hasMore.value = result.has_more
    totalComments.value = result.total
    emit('count-changed', result.total)
  } catch (e) {
    console.error('Failed to load comments:', e)
  } finally {
    isLoading.value = false
  }
}

function toggleExpanded() {
  expanded.value = !expanded.value
  if (expanded.value && comments.value.length === 0 && totalComments.value > 0) {
    loadComments()
  }
}

function loadMore() {
  if (!isLoading.value && hasMore.value) {
    loadComments(comments.value.length)
  }
}

async function handleSubmit(content: string) {
  if (!content.trim() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const comment = await addActivityComment(
      props.doctype,
      props.docname,
      content,
      replyingTo.value?.name
    )

    if (replyingTo.value) {
      // Add to parent's replies
      const parent = comments.value.find(c => c.name === replyingTo.value?.name)
      if (parent) {
        parent.replies = [...(parent.replies || []), comment]
        parent.reply_count = (parent.reply_count || 0) + 1
      }
    } else {
      comments.value.unshift(comment)
    }

    totalComments.value++
    replyingTo.value = null
    emit('comment-added', comment)
    emit('count-changed', totalComments.value)

    // Auto-expand if first comment
    if (!expanded.value && totalComments.value === 1) {
      expanded.value = true
    }
  } catch (e) {
    console.error('Failed to add comment:', e)
  } finally {
    isSubmitting.value = false
  }
}

function handleReply(comment: ActivityComment) {
  replyingTo.value = comment
  commentInputRef.value?.focus()
}

async function handleDelete(commentName: string) {
  try {
    await deleteActivityComment(commentName)
    comments.value = comments.value.filter(c => c.name !== commentName)
    totalComments.value = Math.max(0, totalComments.value - 1)
    emit('comment-deleted', commentName)
    emit('count-changed', totalComments.value)
  } catch (e) {
    console.error('Failed to delete comment:', e)
  }
}

// Load initial comments if count > 0
watch(() => props.initialCount, (count) => {
  if (count > 0 && comments.value.length === 0) {
    // Don't auto-load, wait for user to expand
    totalComments.value = count
  }
}, { immediate: true })

// Reload when doctype/docname changes
watch([() => props.doctype, () => props.docname], () => {
  comments.value = []
  expanded.value = false
  replyingTo.value = null
  totalComments.value = props.initialCount
})
</script>

<template>
  <div class="activity-comments mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
    <!-- Expand/Collapse Toggle -->
    <button
      v-if="hasComments"
      @click="toggleExpanded"
      class="text-xs text-gray-500 hover:text-orga-500 dark:text-gray-400 dark:hover:text-orga-400 mb-2 transition-colors"
    >
      <i :class="['fa-solid mr-1', expanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
      {{ expanded ? __('Hide') : __('View') }} {{ totalComments }} {{ totalComments !== 1 ? __('comments') : __('comment') }}
    </button>

    <!-- Comments List -->
    <TransitionGroup
      v-if="expanded || !hasComments"
      name="comment-list"
      tag="div"
      class="space-y-3"
    >
      <!-- Loading -->
      <div v-if="isLoading && comments.length === 0" key="loading" class="text-center py-4">
        <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
      </div>

      <!-- Comments -->
      <CommentThread
        v-for="comment in visibleComments"
        :key="comment.name"
        :comment="comment"
        @reply="handleReply"
        @delete="handleDelete"
      />

      <!-- Load More -->
      <button
        v-if="expanded && hasMore"
        key="load-more"
        @click="loadMore"
        :disabled="isLoading"
        class="text-xs text-orga-500 hover:text-orga-600 dark:text-orga-400 dark:hover:text-orga-300 disabled:opacity-50 transition-colors"
      >
        {{ isLoading ? __('Loading...') : __('Load more comments') }}
      </button>
    </TransitionGroup>

    <!-- Add Comment Input -->
    <div class="mt-3">
      <CommentInput
        ref="commentInputRef"
        :placeholder="replyingTo ? __('Reply to {0}...', [replyingTo.user_fullname]) : __('Add a comment...')"
        :is-submitting="isSubmitting"
        :show-cancel-reply="!!replyingTo"
        @submit="handleSubmit"
        @cancel-reply="replyingTo = null"
      />
    </div>
  </div>
</template>

<style scoped>
.comment-list-enter-active,
.comment-list-leave-active {
  transition: all 0.2s ease;
}

.comment-list-enter-from,
.comment-list-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
