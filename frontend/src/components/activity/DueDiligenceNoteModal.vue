<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  DueDiligenceNoteModal.vue - Modal for adding due diligence/typed notes

  Features:
  - Note type selection (General, Due Diligence, Offer, Decision)
  - Visibility selection (Internal, Team, Public)
  - Optional company linking
  - @mention support in content
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { NoteType, NoteVisibility, DueDiligenceNote } from '@/types/orga'

interface Props {
  doctype: string
  docname: string
  initialNoteType?: NoteType
  relatedCompany?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialNoteType: 'Due Diligence'
})

const emit = defineEmits<{
  close: []
  added: [note: DueDiligenceNote]
}>()

const { addDueDiligenceNote } = useActivityApi()

const content = ref('')
const noteType = ref<NoteType>(props.initialNoteType)
const visibility = ref<NoteVisibility>('Internal')
const relatedCompany = ref(props.relatedCompany || '')
const isSubmitting = ref(false)
const error = ref<string | null>(null)

const noteTypes: { value: NoteType; label: string; icon: string; color: string }[] = [
  { value: 'General', label: __('General Note'), icon: 'fa-sticky-note', color: 'gray' },
  { value: 'Due Diligence', label: __('Due Diligence'), icon: 'fa-clipboard-check', color: 'blue' },
  { value: 'Offer', label: __('Offer'), icon: 'fa-hand-holding-dollar', color: 'green' },
  { value: 'Decision', label: __('Decision'), icon: 'fa-gavel', color: 'purple' }
]

const visibilityOptions: { value: NoteVisibility; label: string; description: string }[] = [
  { value: 'Internal', label: __('Internal'), description: __('Only you and admins') },
  { value: 'Team', label: __('Team'), description: __('All team members') },
  { value: 'Public', label: __('Public'), description: __('Anyone with access') }
]

const canSubmit = computed(() => {
  return content.value.trim().length > 0 && !isSubmitting.value
})

const selectedNoteType = computed(() => {
  return noteTypes.find(t => t.value === noteType.value) || noteTypes[0]
})

async function handleSubmit() {
  if (!canSubmit.value) return

  error.value = null
  isSubmitting.value = true

  try {
    const note = await addDueDiligenceNote(
      props.doctype,
      props.docname,
      content.value.trim(),
      noteType.value,
      visibility.value,
      relatedCompany.value || undefined
    )

    emit('added', note)
  } catch (e) {
    error.value = (e as Error).message || __('Failed to add note')
    console.error('Failed to add due diligence note:', e)
  } finally {
    isSubmitting.value = false
  }
}

function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="handleBackdropClick"
    >
      <div
        class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 m-0 flex items-center gap-2">
            <i :class="['fa-solid', selectedNoteType.icon, `text-${selectedNoteType.color}-500`]"></i>
            {{ __('Add {0}', [selectedNoteType.label]) }}
          </h3>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <i class="fa-solid fa-xmark text-lg"></i>
          </button>
        </div>

        <!-- Content -->
        <div class="p-4 space-y-4">
          <!-- Note Type Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ __('Note Type') }}
            </label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="type in noteTypes"
                :key="type.value"
                @click="noteType = type.value"
                :class="[
                  'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all text-sm',
                  noteType === type.value
                    ? `border-${type.color}-500 bg-${type.color}-50 dark:bg-${type.color}-900/20 text-${type.color}-700 dark:text-${type.color}-400`
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                <i :class="['fa-solid', type.icon]"></i>
                {{ type.label }}
              </button>
            </div>
          </div>

          <!-- Content -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Note Content') }}
            </label>
            <textarea
              v-model="content"
              rows="4"
              :placeholder="__('Enter your note... Use @name to mention someone')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                     focus:border-orga-500 focus:outline-none resize-none
                     placeholder-gray-400 dark:placeholder-gray-500"
            ></textarea>
          </div>

          <!-- Visibility -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ __('Visibility') }}
            </label>
            <div class="flex gap-2">
              <button
                v-for="option in visibilityOptions"
                :key="option.value"
                @click="visibility = option.value"
                :title="option.description"
                :class="[
                  'px-3 py-1.5 rounded-lg border text-sm transition-all',
                  visibility === option.value
                    ? 'border-orga-500 bg-orga-50 dark:bg-orga-900/20 text-orga-700 dark:text-orga-400'
                    : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
                ]"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <!-- Related Company (Optional) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {{ __('Related Company (optional)') }}
            </label>
            <input
              v-model="relatedCompany"
              type="text"
              :placeholder="__('Company name...')"
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                     focus:border-orga-500 focus:outline-none
                     placeholder-gray-400 dark:placeholder-gray-500"
            />
          </div>

          <!-- Error -->
          <div v-if="error" class="text-sm text-red-500 dark:text-red-400">
            {{ error }}
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          >
            {{ __('Cancel') }}
          </button>
          <button
            @click="handleSubmit"
            :disabled="!canSubmit"
            class="px-4 py-2 text-sm bg-orga-500 text-white rounded-lg hover:bg-orga-600
                   disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <i v-if="isSubmitting" class="fa-solid fa-spinner fa-spin mr-1"></i>
            <i v-else class="fa-solid fa-plus mr-1"></i>
            {{ __('Add Note') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
