<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskAttachmentsTab.vue - File attachments tab content for Task Manager
-->
<template>
  <div class="flex flex-col h-full">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <Loader2 class="w-5 h-5 animate-spin text-gray-400 dark:text-gray-500 mx-auto" aria-hidden="true" />
      <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">{{ __('Loading files...') }}</p>
    </div>

    <!-- File List -->
    <div v-else class="flex-1 overflow-auto space-y-1.5 mb-3">
      <div
        v-for="file in attachments"
        :key="file.name"
        class="flex items-center gap-2 group px-1 py-1.5 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <OrgaIcon :name="getFileIconName(file)" :class="['w-3.5 h-3.5', getFileIconColor(file)]" />
        <a
          :href="file.file_url"
          target="_blank"
          class="text-sm text-gray-700 dark:text-gray-300 hover:text-accent-600 dark:hover:text-accent-400 truncate flex-1 hover:underline"
        >
          {{ file.file_name }}
        </a>
        <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
          {{ formatFileSize(file.file_size) }}
        </span>
        <button
          @click="emit('delete', file)"
          class="text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          :title="__('Delete file')"
        >
          <Trash2 class="w-3 h-3" aria-hidden="true" />
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="!attachments.length && !isLoading" class="text-center py-8">
        <Paperclip class="w-6 h-6 text-gray-300 dark:text-gray-600 mb-3 mx-auto" aria-hidden="true" />
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No files attached yet.') }}</p>
        <p class="text-xs text-gray-300 dark:text-gray-600 mt-1">{{ __('Upload files below to attach them to this task.') }}</p>
      </div>
    </div>

    <!-- Upload Area -->
    <div class="sticky bottom-0 bg-white dark:bg-gray-900 pt-2 border-t border-gray-100 dark:border-gray-800">
      <!-- Upload Progress -->
      <div v-if="isUploading" class="mb-2">
        <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-1">
          <Loader2 class="w-3 h-3 animate-spin" aria-hidden="true" />
          <span>{{ __('Uploading...') }}</span>
          <span v-if="uploadProgress > 0">{{ uploadProgress }}%</span>
        </div>
        <div class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-accent-500 transition-all duration-300"
            :style="{ width: (uploadProgress || 0) + '%' }"
          ></div>
        </div>
      </div>

      <!-- Upload Button -->
      <label
        :class="[
          'flex items-center justify-center gap-2 px-3 py-2.5 border-2 border-dashed rounded-lg cursor-pointer transition-colors text-sm',
          isUploading
            ? 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 cursor-not-allowed'
            : 'border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-accent-500 hover:text-accent-500'
        ]"
      >
        <CloudUpload class="w-4 h-4" aria-hidden="true" />
        <span>{{ __('Choose file to upload') }}</span>
        <input
          type="file"
          class="hidden"
          :disabled="isUploading"
          @change="handleFileSelect"
        />
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OrgaFileAttachment } from '@/types/orga'
import { __ } from '@/composables/useTranslate'
import { Loader2, Trash2, Paperclip, CloudUpload } from 'lucide-vue-next'
import OrgaIcon from '@/components/common/OrgaIcon.vue'

interface Props {
  attachments: OrgaFileAttachment[]
  isLoading: boolean
  isUploading: boolean
  uploadProgress: number
}

defineProps<Props>()

const emit = defineEmits<{
  upload: [file: File]
  delete: [attachment: OrgaFileAttachment]
}>()

function handleFileSelect(event: Event): void {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    emit('upload', input.files[0])
    // Reset input so same file can be selected again
    input.value = ''
  }
}

function getFileIconName(file: OrgaFileAttachment): string {
  const name = file.file_name || ''
  const type = file.file_type || ''
  if (type.includes('pdf') || name.endsWith('.pdf')) return 'file-pdf'
  if (type.includes('image') || /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(name)) return 'file-image'
  if (type.includes('word') || /\.(doc|docx)$/i.test(name)) return 'file-word'
  if (type.includes('excel') || /\.(xls|xlsx|csv)$/i.test(name)) return 'file-excel'
  if (/\.(dwg|dxf)$/i.test(name)) return 'compass-drafting'
  if (/\.(zip|rar|7z|tar|gz)$/i.test(name)) return 'file-zipper'
  if (type.includes('text') || /\.(txt|md)$/i.test(name)) return 'file-lines'
  return 'file'
}

function getFileIconColor(file: OrgaFileAttachment): string {
  const name = file.file_name || ''
  const type = file.file_type || ''
  if (type.includes('pdf') || name.endsWith('.pdf')) return 'text-red-500'
  if (type.includes('image') || /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(name)) return 'text-blue-500'
  if (type.includes('word') || /\.(doc|docx)$/i.test(name)) return 'text-blue-600'
  if (type.includes('excel') || /\.(xls|xlsx|csv)$/i.test(name)) return 'text-green-600'
  if (/\.(dwg|dxf)$/i.test(name)) return 'text-orange-500'
  if (/\.(zip|rar|7z|tar|gz)$/i.test(name)) return 'text-yellow-600'
  if (type.includes('text') || /\.(txt|md)$/i.test(name)) return 'text-gray-500'
  return 'text-gray-400'
}

function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let size = bytes
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(size < 10 ? 1 : 0)} ${units[unitIndex]}`
}
</script>
