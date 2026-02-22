<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityCommentsTab.vue - Full threaded comments tab for Activity Manager

  Features:
  - Full comment history with threading
  - Reply functionality
  - @mention support
  - Delete capability (author/admin)
  - Ctrl+Enter to submit
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'
import type { ActivityComment, MentionUser } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  doctype: string
  docname: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'comment-added': [comment: ActivityComment]
  'comment-deleted': [commentName: string]
}>()

const {
  getActivityComments,
  getCommentReplies,
  addActivityComment,
  deleteActivityComment,
  getUsersForMention
} = useActivityApi()

// State
const comments = ref<ActivityComment[]>([])
const isLoading = ref(false)
const isSubmitting = ref(false)
const hasMore = ref(false)
const total = ref(0)
const newComment = ref('')
const replyTo = ref<ActivityComment | null>(null)
const expandedReplies = ref<Set<string>>(new Set())

// @mention autocomplete
const showMentionDropdown = ref(false)
const mentionSearch = ref('')
const mentionUsers = ref<MentionUser[]>([])
const mentionPosition = ref({ top: 0, left: 0 })

// Current user for delete permissions
const currentUser = computed(() => {
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    return ((window as Record<string, unknown>).frappe as Record<string, Record<string, string>>)?.session?.user || ''
  }
  return ''
})

const isAdmin = computed(() => {
  if (typeof window !== 'undefined' && (window as Record<string, unknown>).frappe) {
    const frappe = (window as Record<string, unknown>).frappe as Record<string, Record<string, Record<string, string[]>>>
    const roles = frappe?.boot?.user?.roles || []
    return roles.includes('System Manager')
  }
  return false
})

async function loadComments(offset = 0) {
  isLoading.value = true
  try {
    const result = await getActivityComments(props.doctype, props.docname, 20, offset)
    if (offset === 0) {
      comments.value = result.comments
    } else {
      comments.value = [...comments.value, ...result.comments]
    }
    hasMore.value = result.has_more
    total.value = result.total
  } catch (e) {
    console.error('Failed to load comments:', e)
  } finally {
    isLoading.value = false
  }
}

async function loadReplies(comment: ActivityComment) {
  if (comment.replies.length > 0) {
    // Already loaded, just toggle visibility
    if (expandedReplies.value.has(comment.name)) {
      expandedReplies.value.delete(comment.name)
    } else {
      expandedReplies.value.add(comment.name)
    }
    return
  }

  try {
    const replies = await getCommentReplies(comment.name, 50)
    comment.replies = replies
    expandedReplies.value.add(comment.name)
  } catch (e) {
    console.error('Failed to load replies:', e)
  }
}

async function handleSubmit() {
  if (!newComment.value.trim() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const comment = await addActivityComment(
      props.doctype,
      props.docname,
      newComment.value.trim(),
      replyTo.value?.name
    )

    if (replyTo.value) {
      // Add to parent's replies
      const parent = comments.value.find(c => c.name === replyTo.value?.name)
      if (parent) {
        parent.replies = [...parent.replies, comment]
        parent.reply_count++
        expandedReplies.value.add(parent.name)
      }
    } else {
      comments.value.unshift(comment)
    }

    total.value++
    newComment.value = ''
    replyTo.value = null
    emit('comment-added', comment)
  } catch (e) {
    console.error('Failed to add comment:', e)
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(commentName: string, isReply = false, parentName?: string) {
  try {
    await deleteActivityComment(commentName)

    if (isReply && parentName) {
      const parent = comments.value.find(c => c.name === parentName)
      if (parent) {
        parent.replies = parent.replies.filter(r => r.name !== commentName)
        parent.reply_count--
      }
    } else {
      comments.value = comments.value.filter(c => c.name !== commentName)
    }

    total.value--
    emit('comment-deleted', commentName)
  } catch (e) {
    console.error('Failed to delete comment:', e)
  }
}

function canDelete(comment: ActivityComment): boolean {
  return comment.user === currentUser.value || isAdmin.value
}

function startReply(comment: ActivityComment) {
  replyTo.value = comment
  // Focus the textarea
  const textarea = document.querySelector('.comment-input') as HTMLTextAreaElement
  if (textarea) textarea.focus()
}

function cancelReply() {
  replyTo.value = null
}

function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __('{0}m ago', [diffMins])
  if (diffHours < 24) return __('{0}h ago', [diffHours])
  if (diffDays === 1) return __('Yesterday')
  if (diffDays < 7) return __('{0}d ago', [diffDays])
  return date.toLocaleDateString()
}

function getInitials(name: string): string {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

// Format content with @mentions highlighted and sanitized
function formatContent(content: string): string {
  const sanitized = sanitizeHtml(content)
  // Highlight @mentions (applied after sanitization so the span is safe)
  return sanitized.replace(/@(\w+(?:\.\w+)*(?:@[\w.-]+)?)/g, '<span class="text-orga-500 font-medium">@$1</span>')
}

// Handle @mention autocomplete
async function handleInput(event: Event) {
  const textarea = event.target as HTMLTextAreaElement
  const value = textarea.value
  const cursorPos = textarea.selectionStart

  // Check if we're typing an @mention
  const textBeforeCursor = value.substring(0, cursorPos)
  const mentionMatch = textBeforeCursor.match(/@(\w*)$/)

  if (mentionMatch) {
    mentionSearch.value = mentionMatch[1]
    try {
      mentionUsers.value = await getUsersForMention(mentionSearch.value, 5)
      showMentionDropdown.value = mentionUsers.value.length > 0
    } catch (e) {
      showMentionDropdown.value = false
    }
  } else {
    showMentionDropdown.value = false
  }
}

function selectMention(user: MentionUser) {
  const cursorPos = newComment.value.lastIndexOf('@')
  if (cursorPos >= 0) {
    newComment.value = newComment.value.substring(0, cursorPos) + '@' + user.name + ' '
  }
  showMentionDropdown.value = false
}

// Watch for doctype/docname changes
watch([() => props.doctype, () => props.docname], () => {
  comments.value = []
  loadComments()
}, { immediate: true })
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header with count -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {{ __('Comments') }} ({{ total }})
      </span>
      <button
        v-if="comments.length > 0"
        @click="loadComments(0)"
        class="text-xs text-orga-500 hover:text-orga-600"
        :title="__('Refresh')"
      >
        <i class="fa-solid fa-rotate-right"></i>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && comments.length === 0" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading comments...') }}</p>
    </div>

    <!-- Comments List -->
    <div v-else class="flex-1 overflow-auto space-y-4 mb-3">
      <div
        v-for="comment in comments"
        :key="comment.name"
        class="group"
      >
        <!-- Main Comment -->
        <div class="flex gap-3">
          <UserAvatar
            :name="comment.user_fullname"
            :image="comment.user_image"
            size="sm"
            color="orga"
          />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
                {{ comment.user_fullname }}
              </span>
              <span class="text-[10px] text-gray-400 dark:text-gray-500">
                {{ formatRelativeTime(comment.creation) }}
              </span>
            </div>
            <div
              class="text-sm text-gray-600 dark:text-gray-400 mt-1 break-words whitespace-pre-wrap"
              v-html="formatContent(comment.content)"
            ></div>

            <!-- Actions -->
            <div class="flex items-center gap-3 mt-2">
              <button
                @click="startReply(comment)"
                class="text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 transition-colors"
              >
                <i class="fa-solid fa-reply mr-1"></i>{{ __('Reply') }}
              </button>
              <button
                v-if="comment.reply_count > 0"
                @click="loadReplies(comment)"
                class="text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 transition-colors"
              >
                <i :class="['fa-solid mr-1', expandedReplies.has(comment.name) ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                {{ comment.reply_count === 1 ? __('{0} reply', [comment.reply_count]) : __('{0} replies', [comment.reply_count]) }}
              </button>
              <button
                v-if="canDelete(comment)"
                @click="handleDelete(comment.name)"
                class="text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all ml-auto"
              >
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Replies -->
        <div
          v-if="expandedReplies.has(comment.name) && comment.replies.length > 0"
          class="ml-10 mt-3 space-y-3 border-l-2 border-gray-100 dark:border-gray-700 pl-4"
        >
          <div
            v-for="reply in comment.replies"
            :key="reply.name"
            class="flex gap-2 group"
          >
            <div class="w-6 h-6 rounded-full bg-gray-400 dark:bg-gray-600 flex items-center justify-center text-white text-[10px] shrink-0">
              {{ getInitials(reply.user_fullname) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {{ reply.user_fullname }}
                </span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500">
                  {{ formatRelativeTime(reply.creation) }}
                </span>
                <button
                  v-if="canDelete(reply)"
                  @click="handleDelete(reply.name, true, comment.name)"
                  class="text-[10px] text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all ml-auto"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
              <p
                class="text-sm text-gray-600 dark:text-gray-400 mt-0.5 m-0 break-words"
                v-html="formatContent(reply.content)"
              ></p>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More -->
      <div v-if="hasMore" class="text-center">
        <button
          @click="loadComments(comments.length)"
          :disabled="isLoading"
          class="text-xs text-orga-500 hover:text-orga-600 disabled:opacity-50"
        >
          {{ isLoading ? __('Loading...') : __('Load more comments') }}
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="!comments.length && !isLoading" class="text-center py-8">
        <i class="fa-solid fa-comments fa-2x text-gray-300 dark:text-gray-600 mb-3 block"></i>
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No comments yet.') }}</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Start the conversation below.') }}</p>
      </div>
    </div>

    <!-- Input Area -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-3 border-t border-gray-100 dark:border-gray-800">
      <!-- Reply indicator -->
      <div v-if="replyTo" class="flex items-center justify-between mb-2 px-2 py-1 bg-gray-50 dark:bg-gray-800 rounded text-xs">
        <span class="text-gray-500 dark:text-gray-400">
          {{ __('Replying to') }} <strong class="text-gray-700 dark:text-gray-300">{{ replyTo.user_fullname }}</strong>
        </span>
        <button @click="cancelReply" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <!-- Comment input with @mention dropdown -->
      <div class="relative">
        <div class="flex gap-2">
          <textarea
            v-model="newComment"
            @input="handleInput"
            @keyup.ctrl.enter="handleSubmit"
            @keyup.meta.enter="handleSubmit"
            :placeholder="__('Write a comment... Use @name to mention (Ctrl+Enter to send)')"
            :disabled="isSubmitting"
            rows="2"
            class="comment-input flex-1 px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:border-orga-500 focus:outline-none focus:ring-1 focus:ring-orga-500/20 disabled:opacity-50 placeholder-gray-400 dark:placeholder-gray-500 resize-none"
          ></textarea>
          <button
            @click="handleSubmit"
            :disabled="isSubmitting || !newComment.trim()"
            class="px-3 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
            :title="__('Send comment')"
          >
            <i :class="['fa-solid', isSubmitting ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
          </button>
        </div>

        <!-- @mention dropdown -->
        <div
          v-if="showMentionDropdown"
          class="absolute bottom-full left-0 mb-1 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-10"
        >
          <button
            v-for="user in mentionUsers"
            :key="user.name"
            @click="selectMention(user)"
            class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
          >
            <UserAvatar
              :name="user.full_name"
              :image="user.user_image"
              size="xs"
              color="gray"
            />
            <div class="min-w-0">
              <div class="text-sm text-gray-800 dark:text-gray-200 truncate">{{ user.full_name }}</div>
              <div class="text-xs text-gray-400 dark:text-gray-500 truncate">{{ user.name }}</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
