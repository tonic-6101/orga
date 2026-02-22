<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  CommentInput.vue - Rich text comment input with @mention autocomplete (Tiptap)
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { TextEditor } from 'frappe-ui'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'

interface Props {
  placeholder?: string
  isSubmitting?: boolean
  showCancelReply?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: __('Add a comment...'),
  isSubmitting: false,
  showCancelReply: false
})

const emit = defineEmits<{
  submit: [content: string]
  'cancel-reply': []
}>()

const { getUsersForMention } = useActivityApi()

const content = ref('')
const editorRef = ref<InstanceType<typeof TextEditor> | null>(null)

const canSubmit = computed(() => {
  // Strip HTML tags to check if there's actual text content
  const text = content.value.replace(/<[^>]*>/g, '').trim()
  return text.length > 0 && !props.isSubmitting
})

// Load mention suggestions from the API
const mentionUsers = ref<{ id: string; label: string; value: string }[]>([])

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

// Load users on mount
loadMentionUsers()

function handleSubmit() {
  if (!canSubmit.value) return
  emit('submit', content.value.trim())
  content.value = ''
  // Clear the editor
  if (editorRef.value?.editor) {
    editorRef.value.editor.commands.clearContent()
  }
}

function focus() {
  if (editorRef.value?.editor) {
    editorRef.value.editor.commands.focus()
  }
}

// Watch for editable changes when submitting
watch(() => props.isSubmitting, (submitting) => {
  if (editorRef.value?.editor) {
    editorRef.value.editor.setEditable(!submitting)
  }
})

defineExpose({ focus })
</script>

<template>
  <div class="relative">
    <!-- Cancel Reply Button -->
    <div
      v-if="showCancelReply"
      class="flex items-center justify-between mb-2 px-2 py-1 bg-gray-50 rounded text-xs"
    >
      <span class="text-gray-500">{{ __('Replying to comment') }}</span>
      <button @click="emit('cancel-reply')" class="text-gray-400 hover:text-gray-600">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>

    <!-- Input Area -->
    <div class="flex gap-2 items-end">
      <div class="flex-1 comment-editor border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden
                  focus-within:border-orga-500 transition-colors"
           :class="{ 'opacity-50': isSubmitting }"
      >
        <TextEditor
          ref="editorRef"
          :content="content"
          :placeholder="placeholder"
          :editable="!isSubmitting"
          :bubble-menu="true"
          :fixed-menu="false"
          :mentions="mentionUsers"
          editor-class="prose prose-sm min-h-[40px] max-h-[200px] overflow-y-auto px-3 py-2 text-sm text-gray-800 dark:text-gray-200"
          @change="content = $event"
        />
      </div>
      <button
        @click="handleSubmit"
        :disabled="!canSubmit"
        class="px-3 py-2 bg-orga-500 text-white rounded-lg hover:bg-orga-600
               disabled:opacity-50 disabled:cursor-not-allowed shrink-0 transition-colors"
      >
        <i :class="['fa-solid', isSubmitting ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Keep the editor compact for inline comments */
.comment-editor :deep(.ProseMirror) {
  min-height: 40px;
  max-height: 200px;
  overflow-y: auto;
  outline: none;
}

.comment-editor :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: #9ca3af;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Style mentions in the editor */
.comment-editor :deep(.mention) {
  background-color: rgba(var(--orga-500-rgb, 59 130 246) / 0.1);
  color: rgb(var(--orga-600-rgb, 37 99 235));
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  font-weight: 500;
}
</style>
