<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityDiscussionTab.vue - Unified Discussion tab for any document type

  Features:
  - Single stream with filter dropdown (All / Comments / Notes / Resolved)
  - Threaded comments with @mention support (rich text via Tiptap)
  - Notes displayed with distinct visual treatment (tinted background, Note badge)
  - Resolve/reopen threads
  - Pin one comment to top of stream
  - Ctrl+Enter to submit
  - Works standalone (TaskManager) or with external notes (ActivityPanel)
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { TextEditor } from 'frappe-ui'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import { sanitizeHtml } from '@/utils/sanitize'
import type { ActivityComment, ActivityNote } from '@/types/orga'
import UserAvatar from '@/components/common/UserAvatar.vue'

interface Props {
  doctype: string
  docname: string
  notes?: ActivityNote[]
  isLoadingNotes?: boolean
  isAddingNote?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  notes: () => [],
  isLoadingNotes: false,
  isAddingNote: false
})

const emit = defineEmits<{
  'comment-added': [comment: ActivityComment]
  'comment-deleted': [commentName: string]
  'note-add': [content: string]
  'note-delete': [noteName: string]
}>()

const {
  getActivityComments,
  getCommentReplies,
  addActivityComment,
  deleteActivityComment,
  resolveComment,
  unresolveComment,
  pinComment,
  unpinComment,
  getUsersForMention
} = useActivityApi()

// Filter state
type FilterMode = 'all' | 'comments' | 'notes' | 'resolved'
const filterMode = ref<FilterMode>('all')

// Whether external notes are available (ActivityPanel passes them)
const hasExternalNotes = computed(() => props.notes.length > 0 || props.isLoadingNotes)

// Comment state
const comments = ref<ActivityComment[]>([])
const isLoadingComments = ref(false)
const isSubmitting = ref(false)
const hasMore = ref(false)
const commentTotal = ref(0)
const newContent = ref('')
const noteContent = ref('')
const replyTo = ref<ActivityComment | null>(null)
const expandedReplies = ref<Set<string>>(new Set())
const inputMode = ref<'comment' | 'note'>('comment')

// TextEditor ref and mention users
const editorRef = ref<InstanceType<typeof TextEditor> | null>(null)
const mentionUsers = ref<{ id: string; label: string; value: string }[]>([])

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

// ============================================
// Load mention users for TextEditor
// ============================================

async function loadMentionUsers() {
  try {
    const users = await getUsersForMention('', 20)
    mentionUsers.value = users.map(u => ({
      id: u.name,
      label: u.full_name,
      value: u.name
    }))
  } catch {
    mentionUsers.value = []
  }
}

loadMentionUsers()

// ============================================
// Unified stream items
// ============================================

interface StreamItem {
  id: string
  type: 'comment' | 'note'
  content: string
  user: string
  user_fullname: string
  user_image?: string
  creation: string
  // Comment-specific
  comment?: ActivityComment
  reply_count?: number
  is_resolved?: boolean
  is_pinned?: boolean
  // Note-specific
  note?: ActivityNote
}

const streamItems = computed<StreamItem[]>(() => {
  const items: StreamItem[] = []

  // Add comments based on filter
  const showResolved = filterMode.value === 'resolved'
  if (filterMode.value !== 'notes') {
    for (const c of comments.value) {
      const resolved = !!(c as Record<string, unknown>).is_resolved
      // In 'resolved' filter mode: only show resolved. In other modes: show unresolved
      if (showResolved && !resolved) continue
      if (!showResolved && resolved && filterMode.value !== 'all') continue

      items.push({
        id: `comment_${c.name}`,
        type: 'comment',
        content: c.content,
        user: c.user,
        user_fullname: c.user_fullname,
        user_image: c.user_image,
        creation: c.creation || '',
        comment: c,
        reply_count: c.reply_count,
        is_resolved: resolved,
        is_pinned: !!(c as Record<string, unknown>).is_pinned
      })
    }
  }

  // Add notes (not in resolved filter)
  if (filterMode.value !== 'comments' && filterMode.value !== 'resolved') {
    for (const n of props.notes) {
      items.push({
        id: `note_${n.name}`,
        type: 'note',
        content: n.content,
        user: n.created_by,
        user_fullname: n.created_by_name,
        user_image: n.created_by_image ?? undefined,
        creation: n.creation || '',
        note: n
      })
    }
  }

  // Sort: pinned first, then by creation time (newest first)
  items.sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1
    if (!a.is_pinned && b.is_pinned) return 1
    return new Date(b.creation).getTime() - new Date(a.creation).getTime()
  })

  return items
})

const totalCount = computed(() => {
  if (filterMode.value === 'comments') return commentTotal.value
  if (filterMode.value === 'notes') return props.notes.length
  if (filterMode.value === 'resolved') {
    return comments.value.filter(c => (c as Record<string, unknown>).is_resolved).length
  }
  return commentTotal.value + props.notes.length
})

const resolvedCount = computed(() => {
  return comments.value.filter(c => (c as Record<string, unknown>).is_resolved).length
})

// ============================================
// Load comments
// ============================================

async function loadComments(offset = 0) {
  isLoadingComments.value = true
  try {
    const result = await getActivityComments(props.doctype, props.docname, 20, offset)
    if (offset === 0) {
      comments.value = result.comments
    } else {
      comments.value = [...comments.value, ...result.comments]
    }
    hasMore.value = result.has_more
    commentTotal.value = result.total
  } catch (e) {
    console.error('Failed to load comments:', e)
  } finally {
    isLoadingComments.value = false
  }
}

async function loadReplies(comment: ActivityComment) {
  if (comment.replies.length > 0) {
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

// ============================================
// Resolve / Pin handlers
// ============================================

async function handleResolve(commentName: string) {
  try {
    const result = await resolveComment(commentName)
    const comment = comments.value.find(c => c.name === commentName)
    if (comment) {
      const rec = comment as Record<string, unknown>
      rec.is_resolved = result.is_resolved
      rec.resolved_by = result.resolved_by
      rec.resolved_at = result.resolved_at
    }
  } catch (e) {
    console.error('Failed to resolve comment:', e)
  }
}

async function handleUnresolve(commentName: string) {
  try {
    await unresolveComment(commentName)
    const comment = comments.value.find(c => c.name === commentName)
    if (comment) {
      const rec = comment as Record<string, unknown>
      rec.is_resolved = false
      rec.resolved_by = null
      rec.resolved_at = null
    }
  } catch (e) {
    console.error('Failed to unresolve comment:', e)
  }
}

async function handlePin(commentName: string) {
  try {
    const result = await pinComment(commentName)
    // Unpin any previously pinned in local state
    for (const c of comments.value) {
      const rec = c as Record<string, unknown>
      if (rec.is_pinned && c.name !== commentName) {
        rec.is_pinned = false
        rec.pinned_by = null
        rec.pinned_at = null
      }
    }
    const comment = comments.value.find(c => c.name === commentName)
    if (comment) {
      const rec = comment as Record<string, unknown>
      rec.is_pinned = result.is_pinned
      rec.pinned_by = result.pinned_by
      rec.pinned_at = result.pinned_at
    }
  } catch (e) {
    console.error('Failed to pin comment:', e)
  }
}

async function handleUnpin(commentName: string) {
  try {
    await unpinComment(commentName)
    const comment = comments.value.find(c => c.name === commentName)
    if (comment) {
      const rec = comment as Record<string, unknown>
      rec.is_pinned = false
      rec.pinned_by = null
      rec.pinned_at = null
    }
  } catch (e) {
    console.error('Failed to unpin comment:', e)
  }
}

// ============================================
// Submit handlers
// ============================================

const canSubmitComment = computed(() => {
  const text = newContent.value.replace(/<[^>]*>/g, '').trim()
  return text.length > 0 && !isSubmitting.value
})

const canSubmitNote = computed(() => {
  return noteContent.value.trim().length > 0 && !props.isAddingNote
})

async function handleSubmit() {
  if (inputMode.value === 'note') {
    if (!canSubmitNote.value) return
    emit('note-add', noteContent.value.trim())
    noteContent.value = ''
    return
  }

  // Comment mode
  if (!canSubmitComment.value) return

  isSubmitting.value = true
  try {
    const comment = await addActivityComment(
      props.doctype,
      props.docname,
      newContent.value.trim(),
      replyTo.value?.name
    )

    if (replyTo.value) {
      const parent = comments.value.find(c => c.name === replyTo.value?.name)
      if (parent) {
        parent.replies = [...parent.replies, comment]
        parent.reply_count++
        expandedReplies.value.add(parent.name)
      }
    } else {
      comments.value.unshift(comment)
    }

    commentTotal.value++
    newContent.value = ''
    replyTo.value = null
    emit('comment-added', comment)

    // Clear the editor
    if (editorRef.value?.editor) {
      editorRef.value.editor.commands.clearContent()
    }
  } catch (e) {
    console.error('Failed to add comment:', e)
  } finally {
    isSubmitting.value = false
  }
}

async function handleDeleteComment(commentName: string, isReply = false, parentName?: string) {
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

    commentTotal.value--
    emit('comment-deleted', commentName)
  } catch (e) {
    console.error('Failed to delete comment:', e)
  }
}

function canDelete(item: { user?: string; created_by?: string }): boolean {
  const user = item.user || item.created_by || ''
  return user === currentUser.value || isAdmin.value
}

function startReply(comment: ActivityComment) {
  replyTo.value = comment
  inputMode.value = 'comment'
  // Focus the TextEditor
  if (editorRef.value?.editor) {
    editorRef.value.editor.commands.focus()
  }
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
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
}

// Watch for editable changes when submitting
watch(() => isSubmitting.value, (submitting) => {
  if (editorRef.value?.editor) {
    editorRef.value.editor.setEditable(!submitting)
  }
})

// Watch for doctype/docname changes
watch([() => props.doctype, () => props.docname], () => {
  comments.value = []
  loadComments()
}, { immediate: true })
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header with filter -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {{ __('Discussion') }} ({{ totalCount }})
        <span v-if="resolvedCount > 0" class="text-[10px] font-normal normal-case ml-1 text-gray-400 dark:text-gray-500">
          {{ __('{0} resolved', [resolvedCount]) }}
        </span>
      </span>

      <div class="flex items-center gap-2">
        <!-- Filter dropdown -->
        <select
          v-model="filterMode"
          class="text-xs px-2 py-1 border border-gray-200 dark:border-gray-700 rounded bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"
        >
          <option value="all">{{ __('All') }}</option>
          <option value="comments">{{ __('Comments') }}</option>
          <option v-if="hasExternalNotes" value="notes">{{ __('Notes') }}</option>
          <option value="resolved">{{ __('Resolved') }}</option>
        </select>

        <!-- Refresh -->
        <button
          @click="loadComments(0)"
          class="text-xs text-orga-500 hover:text-orga-600"
          :title="__('Refresh')"
        >
          <i class="fa-solid fa-rotate-right"></i>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoadingComments && comments.length === 0 && props.isLoadingNotes" class="text-center py-8">
      <i class="fa-solid fa-spinner fa-spin text-gray-400 dark:text-gray-500 text-xl"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading discussion...') }}</p>
    </div>

    <!-- Stream -->
    <div v-else class="flex-1 overflow-auto space-y-3 mb-3">
      <div
        v-for="item in streamItems"
        :key="item.id"
        class="group"
      >
        <!-- ========== NOTE ITEM ========== -->
        <div v-if="item.type === 'note'" class="bg-amber-50 dark:bg-amber-900/15 rounded-lg p-3 border border-amber-200/50 dark:border-amber-800/30">
          <div class="flex items-center gap-2 mb-1">
            <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-300 uppercase">
              {{ __('Note') }}
            </span>
            <UserAvatar
              :name="item.user_fullname"
              :image="item.user_image"
              size="xs"
              color="amber"
            />
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ item.user_fullname }}</span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formatRelativeTime(item.creation) }}</span>
            <button
              v-if="item.note && canDelete(item.note)"
              @click="emit('note-delete', item.note!.name)"
              class="text-[10px] text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all ml-auto"
              :title="__('Delete note')"
            >
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
          <p class="text-sm text-gray-700 dark:text-gray-400 m-0 break-words whitespace-pre-wrap">{{ item.content }}</p>
        </div>

        <!-- ========== COMMENT ITEM ========== -->
        <div v-else :class="['rounded-lg transition-colors', item.is_resolved ? 'opacity-60' : '']">
          <!-- Pinned badge -->
          <div v-if="item.is_pinned" class="flex items-center gap-1 mb-1">
            <i class="fa-solid fa-thumbtack text-[10px] text-orga-500"></i>
            <span class="text-[10px] font-medium text-orga-500">{{ __('Pinned') }}</span>
          </div>

          <div class="flex gap-3">
            <UserAvatar
              :name="item.user_fullname"
              :image="item.user_image"
              size="sm"
              color="orga"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ item.user_fullname }}</span>
                <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formatRelativeTime(item.creation) }}</span>
                <!-- Resolved badge -->
                <span v-if="item.is_resolved" class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                  <i class="fa-solid fa-check mr-0.5"></i>{{ __('Resolved') }}
                </span>
              </div>

              <!-- Content (collapsed if resolved, unless in 'resolved' filter) -->
              <div
                v-if="!item.is_resolved || filterMode === 'resolved' || filterMode === 'all'"
                class="text-sm text-gray-600 dark:text-gray-400 mt-1 break-words comment-content prose prose-sm max-w-none"
                v-html="sanitizeHtml(item.content)"
              ></div>

              <!-- Comment Actions -->
              <div class="flex items-center gap-3 mt-2">
                <button
                  v-if="!item.is_resolved"
                  @click="startReply(item.comment!)"
                  class="text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 transition-colors"
                >
                  <i class="fa-solid fa-reply mr-1"></i>{{ __('Reply') }}
                </button>
                <button
                  v-if="item.reply_count && item.reply_count > 0"
                  @click="loadReplies(item.comment!)"
                  class="text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 transition-colors"
                >
                  <i :class="['fa-solid mr-1', expandedReplies.has(item.comment!.name) ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                  {{ item.reply_count === 1 ? __('{0} reply', [item.reply_count]) : __('{0} replies', [item.reply_count]) }}
                </button>

                <!-- Resolve / Unresolve -->
                <button
                  v-if="!item.is_resolved"
                  @click="handleResolve(item.comment!.name)"
                  class="text-xs text-gray-400 dark:text-gray-500 hover:text-green-600 opacity-0 group-hover:opacity-100 transition-all"
                  :title="__('Resolve thread')"
                >
                  <i class="fa-solid fa-check-circle mr-1"></i>{{ __('Resolve') }}
                </button>
                <button
                  v-else
                  @click="handleUnresolve(item.comment!.name)"
                  class="text-xs text-green-600 dark:text-green-400 hover:text-amber-600 transition-colors"
                  :title="__('Reopen thread')"
                >
                  <i class="fa-solid fa-rotate-left mr-1"></i>{{ __('Reopen') }}
                </button>

                <!-- Pin / Unpin -->
                <button
                  v-if="!item.is_pinned"
                  @click="handlePin(item.comment!.name)"
                  class="text-xs text-gray-400 dark:text-gray-500 hover:text-orga-500 opacity-0 group-hover:opacity-100 transition-all"
                  :title="__('Pin to top')"
                >
                  <i class="fa-solid fa-thumbtack"></i>
                </button>
                <button
                  v-else
                  @click="handleUnpin(item.comment!.name)"
                  class="text-xs text-orga-500 hover:text-gray-500 transition-colors"
                  :title="__('Unpin')"
                >
                  <i class="fa-solid fa-thumbtack"></i>
                </button>

                <!-- Delete -->
                <button
                  v-if="item.comment && canDelete(item.comment)"
                  @click="handleDeleteComment(item.comment!.name)"
                  class="text-xs text-gray-400 dark:text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all ml-auto"
                >
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Replies (for comments) -->
          <div
            v-if="item.type === 'comment' && item.comment && expandedReplies.has(item.comment.name) && item.comment.replies.length > 0"
            class="ml-10 mt-3 space-y-3 border-l-2 border-gray-100 dark:border-gray-700 pl-4"
          >
            <div
              v-for="reply in item.comment.replies"
              :key="reply.name"
              class="flex gap-2 group"
            >
              <div class="w-6 h-6 rounded-full bg-gray-400 dark:bg-gray-600 flex items-center justify-center text-white text-[10px] shrink-0">
                {{ getInitials(reply.user_fullname) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-medium text-gray-700 dark:text-gray-300">{{ reply.user_fullname }}</span>
                  <span class="text-[10px] text-gray-400 dark:text-gray-500">{{ formatRelativeTime(reply.creation) }}</span>
                  <button
                    v-if="canDelete(reply)"
                    @click="handleDeleteComment(reply.name, true, item.comment!.name)"
                    class="text-[10px] text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all ml-auto"
                  >
                    <i class="fa-solid fa-trash"></i>
                  </button>
                </div>
                <div
                  class="text-sm text-gray-600 dark:text-gray-400 mt-0.5 m-0 break-words comment-content prose prose-sm max-w-none"
                  v-html="sanitizeHtml(reply.content)"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More Comments -->
      <div v-if="hasMore && filterMode !== 'notes'" class="text-center">
        <button
          @click="loadComments(comments.length)"
          :disabled="isLoadingComments"
          class="text-xs text-orga-500 hover:text-orga-600 disabled:opacity-50"
        >
          {{ isLoadingComments ? __('Loading...') : __('Load more comments') }}
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="streamItems.length === 0 && !isLoadingComments && !props.isLoadingNotes" class="text-center py-8">
        <i class="fa-solid fa-comments fa-2x text-gray-300 dark:text-gray-600 mb-3 block"></i>
        <p class="text-sm text-gray-400 dark:text-gray-500">
          {{ filterMode === 'resolved' ? __('No resolved threads.') : __('No discussion yet.') }}
        </p>
        <p v-if="filterMode !== 'resolved'" class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Start the conversation below.') }}</p>
      </div>
    </div>

    <!-- Input Area -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-3 border-t border-gray-100 dark:border-gray-800">
      <!-- Mode toggle -->
      <div class="flex items-center gap-1 mb-2">
        <button
          @click="inputMode = 'comment'; replyTo = null"
          :class="[
            'px-2.5 py-1 text-xs rounded-full transition-colors',
            inputMode === 'comment'
              ? 'bg-orga-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
          ]"
        >
          <i class="fa-solid fa-comment mr-1"></i>{{ __('Comment') }}
        </button>
        <button
          v-if="hasExternalNotes"
          @click="inputMode = 'note'; replyTo = null"
          :class="[
            'px-2.5 py-1 text-xs rounded-full transition-colors',
            inputMode === 'note'
              ? 'bg-amber-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
          ]"
        >
          <i class="fa-solid fa-sticky-note mr-1"></i>{{ __('Note') }}
        </button>
      </div>

      <!-- Reply indicator -->
      <div v-if="replyTo" class="flex items-center justify-between mb-2 px-2 py-1 bg-gray-50 dark:bg-gray-800 rounded text-xs">
        <span class="text-gray-500 dark:text-gray-400">
          {{ __('Replying to') }} <strong class="text-gray-700 dark:text-gray-300">{{ replyTo.user_fullname }}</strong>
        </span>
        <button @click="cancelReply" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>

      <!-- Comment Input (TextEditor) -->
      <div v-if="inputMode === 'comment'" class="flex gap-2 items-end">
        <div class="flex-1 discussion-editor border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden
                    focus-within:border-orga-500 focus-within:ring-1 focus-within:ring-orga-500/20 transition-colors"
             :class="{ 'opacity-50': isSubmitting }"
        >
          <TextEditor
            ref="editorRef"
            :content="newContent"
            :placeholder="replyTo ? __('Reply to {0}...', [replyTo.user_fullname]) : __('Write a comment...')"
            :editable="!isSubmitting"
            :bubble-menu="true"
            :fixed-menu="false"
            :mentions="mentionUsers"
            editor-class="prose prose-sm min-h-[40px] max-h-[160px] overflow-y-auto px-3 py-2 text-sm"
            @change="newContent = $event"
          />
        </div>
        <button
          @click="handleSubmit"
          :disabled="!canSubmitComment"
          class="px-3 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
          :title="__('Send comment')"
        >
          <i :class="['fa-solid', isSubmitting ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
        </button>
      </div>

      <!-- Note Input (plain textarea) -->
      <div v-else class="flex gap-2">
        <textarea
          v-model="noteContent"
          @keyup.ctrl.enter="handleSubmit"
          @keyup.meta.enter="handleSubmit"
          :placeholder="__('Add a note...')"
          :disabled="props.isAddingNote"
          rows="2"
          class="discussion-input flex-1 px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-1 disabled:opacity-50
                 placeholder-gray-400 dark:placeholder-gray-500 resize-none
                 border-amber-300 dark:border-amber-700 bg-amber-50/50 dark:bg-amber-900/10
                 text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-amber-500/20"
        ></textarea>
        <button
          @click="handleSubmit"
          :disabled="!canSubmitNote"
          class="px-3 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          :title="__('Add note')"
        >
          <i :class="['fa-solid', props.isAddingNote ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Keep the editor compact in the panel */
.discussion-editor :deep(.ProseMirror) {
  min-height: 40px;
  max-height: 160px;
  overflow-y: auto;
  outline: none;
}

.discussion-editor :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: #9ca3af;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Style mentions in the editor */
.discussion-editor :deep(.mention) {
  background-color: rgba(var(--orga-500-rgb, 59 130 246) / 0.1);
  color: rgb(var(--orga-600-rgb, 37 99 235));
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  font-weight: 500;
}

/* Style mentions in rendered comments */
.comment-content :deep(.mention) {
  background-color: rgba(var(--orga-500-rgb, 59 130 246) / 0.1);
  color: rgb(var(--orga-600-rgb, 37 99 235));
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  font-weight: 500;
}

.comment-content :deep(p) {
  margin: 0;
}

.comment-content :deep(p + p) {
  margin-top: 0.25em;
}
</style>
