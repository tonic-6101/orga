<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  DeleteProjectModal.vue - GitHub-style type-to-confirm project deletion
-->
<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useProjectApi } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { __ } from '@/composables/useTranslate'

interface Props {
  isOpen: boolean
  projectName: string
  projectLabel: string
  taskCount: number
  milestoneCount: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  deleted: []
}>()

const { deleteProject } = useProjectApi()
const { success: showSuccess, error: showError } = useToast()

const confirmText = ref('')
const isDeleting = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const canDelete = computed(() => confirmText.value === props.projectLabel)

watch(() => props.isOpen, (open) => {
  if (open) {
    confirmText.value = ''
    isDeleting.value = false
    nextTick(() => inputRef.value?.focus())
  }
})

async function handleDelete(): Promise<void> {
  if (!canDelete.value || isDeleting.value) return

  isDeleting.value = true
  try {
    await deleteProject(props.projectName)
    showSuccess(__('Project deleted'), __('"{0}" and all associated data have been permanently deleted.', [props.projectLabel]))
    emit('deleted')
  } catch (e) {
    console.error('Failed to delete project:', e)
    showError(__('Delete failed'), (e as Error).message || __('Could not delete the project. Please try again.'))
    isDeleting.value = false
  }
}

function handleClose(): void {
  if (!isDeleting.value) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/60"
        @click="handleClose"
      ></div>

      <!-- Modal -->
      <div class="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-gray-700">
        <!-- Header -->
        <div class="flex items-center gap-3 p-5 pb-4 border-b border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 rounded-t-xl">
          <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-triangle-exclamation text-red-600 dark:text-red-400 text-lg"></i>
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg font-semibold text-red-900 dark:text-red-200 m-0">{{ __('Delete Project') }}</h2>
          </div>
          <button
            @click="handleClose"
            :disabled="isDeleting"
            class="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="p-5 space-y-4">
          <p class="text-sm text-gray-700 dark:text-gray-300 m-0">
            {{ __('Are you sure you want to delete this project?') }} {{ __('This action') }} <strong class="text-red-600 dark:text-red-400">{{ __('cannot be undone') }}</strong>.
          </p>

          <!-- What will be deleted -->
          <div class="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/50 rounded-lg p-3 space-y-1.5">
            <p class="text-xs font-semibold text-red-800 dark:text-red-300 uppercase tracking-wider m-0">{{ __('This will permanently delete:') }}</p>
            <ul class="list-none p-0 m-0 space-y-1">
              <li class="flex items-center gap-2 text-sm text-red-700 dark:text-red-400">
                <i class="fa-solid fa-folder text-xs w-4 text-center"></i>
                {{ __('The project') }} "<strong>{{ projectLabel }}</strong>"
              </li>
              <li class="flex items-center gap-2 text-sm text-red-700 dark:text-red-400">
                <i class="fa-solid fa-list-check text-xs w-4 text-center"></i>
                {{ taskCount }} {{ taskCount === 1 ? __('task') : __('tasks') }}
              </li>
              <li class="flex items-center gap-2 text-sm text-red-700 dark:text-red-400">
                <i class="fa-solid fa-flag text-xs w-4 text-center"></i>
                {{ milestoneCount }} {{ milestoneCount === 1 ? __('milestone') : __('milestones') }}
              </li>
            </ul>
          </div>

          <!-- Confirmation input -->
          <div>
            <label class="block text-sm text-gray-700 dark:text-gray-300 mb-2">
              {{ __('Please type') }} <strong class="text-gray-900 dark:text-gray-100 select-all">{{ projectLabel }}</strong> {{ __('to confirm:') }}
            </label>
            <input
              ref="inputRef"
              v-model="confirmText"
              type="text"
              :placeholder="projectLabel"
              :disabled="isDeleting"
              class="w-full px-3 py-2 text-sm border rounded-lg transition-colors bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50 focus:outline-none"
              :class="[
                confirmText.length === 0
                  ? 'border-gray-300 dark:border-gray-600 focus:border-red-500 dark:focus:border-red-400 focus:ring-1 focus:ring-red-500 dark:focus:ring-red-400'
                  : canDelete
                    ? 'border-red-500 dark:border-red-400 ring-1 ring-red-500 dark:ring-red-400'
                    : 'border-gray-300 dark:border-gray-600 focus:border-red-500 dark:focus:border-red-400 focus:ring-1 focus:ring-red-500 dark:focus:ring-red-400'
              ]"
              @keydown.enter="handleDelete"
            />
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 p-5 pt-3 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="handleClose"
            :disabled="isDeleting"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleDelete"
            :disabled="!canDelete || isDeleting"
            class="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2 disabled:cursor-not-allowed"
            :class="[
              canDelete && !isDeleting
                ? 'bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700'
                : 'bg-gray-300 dark:bg-gray-600'
            ]"
          >
            <i v-if="isDeleting" class="fa-solid fa-spinner fa-spin"></i>
            <i v-else class="fa-solid fa-trash"></i>
            {{ isDeleting ? __('Deleting...') : __('Delete this project') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
