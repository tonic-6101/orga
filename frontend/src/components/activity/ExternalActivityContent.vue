<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ExternalActivityContent.vue - Content for external company activities

  Features:
  - Company info display
  - Due diligence note button
  - Make offer button (when applicable)
  - Flag/escalate button
  - Inline due diligence notes display
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import { useCurrency } from '@/composables/useCurrency'
import type { ActivityItem, DueDiligenceNote, ComplianceStatus, NoteType } from '@/types/orga'
import DueDiligenceNoteModal from './DueDiligenceNoteModal.vue'
import { __ } from '@/composables/useTranslate'

interface Props {
  activity: ActivityItem & {
    company_name?: string
    contact_name?: string
    contact_email?: string
    value?: number
    can_make_offer?: boolean
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'note-added': [note: DueDiligenceNote]
  'flagged': []
}>()

const { getDueDiligenceNotes, getComplianceStatus, toggleReaction } = useActivityApi()
const { formatCurrency } = useCurrency()

const dueDiligenceNotes = ref<DueDiligenceNote[]>([])
const complianceStatus = ref<ComplianceStatus | null>(null)
const showAllNotes = ref(false)
const showNoteModal = ref(false)
const initialNoteType = ref<NoteType>('Due Diligence')
const isLoadingNotes = ref(false)
const isFlagging = ref(false)

const doctype = computed(() => props.activity.reference_doctype || props.activity.doctype || 'Activity Log')
const docname = computed(() => props.activity.reference_name || props.activity.name)

const visibleNotes = computed(() => {
  if (showAllNotes.value) return dueDiligenceNotes.value
  return dueDiligenceNotes.value.slice(0, 2)
})

const isFlagged = computed(() => complianceStatus.value?.is_flagged || false)

const checklistProgress = computed(() => {
  return complianceStatus.value?.checklist_progress || 0
})

function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return ''
  const now = new Date()
  const date = new Date(timestamp)
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return __('Just now')
  if (diffMins < 60) return __("{0}m ago", [diffMins])
  if (diffHours < 24) return __("{0}h ago", [diffHours])
  if (diffDays === 1) return __('Yesterday')
  if (diffDays < 7) return __("{0}d ago", [diffDays])
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getNoteTypeIcon(type: NoteType): string {
  const icons: Record<NoteType, string> = {
    'General': 'fa-sticky-note',
    'Due Diligence': 'fa-clipboard-check',
    'Offer': 'fa-hand-holding-dollar',
    'Decision': 'fa-gavel'
  }
  return icons[type] || 'fa-sticky-note'
}

function getNoteTypeColor(type: NoteType): string {
  const colors: Record<NoteType, string> = {
    'General': 'gray',
    'Due Diligence': 'blue',
    'Offer': 'green',
    'Decision': 'purple'
  }
  return colors[type] || 'gray'
}

async function loadNotes() {
  isLoadingNotes.value = true
  try {
    const [notesResult, statusResult] = await Promise.all([
      getDueDiligenceNotes(doctype.value, docname.value, undefined, 10, 0),
      getComplianceStatus(doctype.value, docname.value)
    ])
    dueDiligenceNotes.value = notesResult.notes
    complianceStatus.value = statusResult
  } catch (e) {
    console.error('Failed to load due diligence notes:', e)
  } finally {
    isLoadingNotes.value = false
  }
}

function openNoteModal(type: NoteType = 'Due Diligence') {
  initialNoteType.value = type
  showNoteModal.value = true
}

function handleNoteAdded(note: DueDiligenceNote) {
  dueDiligenceNotes.value.unshift(note)
  showNoteModal.value = false
  // Refresh compliance status
  getComplianceStatus(doctype.value, docname.value).then(status => {
    complianceStatus.value = status
  })
  emit('note-added', note)
}

async function handleFlag() {
  if (isFlagging.value) return

  isFlagging.value = true
  try {
    await toggleReaction(doctype.value, docname.value, 'flag')
    // Refresh compliance status
    const status = await getComplianceStatus(doctype.value, docname.value)
    complianceStatus.value = status
    emit('flagged')
  } catch (e) {
    console.error('Failed to toggle flag:', e)
  } finally {
    isFlagging.value = false
  }
}

onMounted(() => {
  loadNotes()
})
</script>

<template>
  <div class="external-activity-content">
    <!-- Company Header -->
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center shrink-0">
        <i class="fa-solid fa-building text-gray-500 dark:text-gray-400"></i>
      </div>

      <div class="flex-1 min-w-0">
        <h4 class="font-medium text-gray-800 dark:text-gray-200 m-0">
          {{ activity.company_name || activity.title }}
        </h4>
        <p v-if="activity.company_name" class="text-sm text-gray-600 dark:text-gray-400 m-0">
          {{ activity.title }}
        </p>
        <p v-if="activity.contact_name" class="text-xs text-gray-400 dark:text-gray-500 mt-1 m-0">
          {{ __('Contact:') }} {{ activity.contact_name }}
          <a
            v-if="activity.contact_email"
            :href="`mailto:${activity.contact_email}`"
            class="text-orga-500 hover:underline ml-1"
            @click.stop
          >
            {{ activity.contact_email }}
          </a>
        </p>
        <p v-if="activity.value" class="text-sm font-medium text-green-600 dark:text-green-400 mt-1 m-0">
          {{ __('Value:') }} {{ formatCurrency(activity.value) }}
        </p>

        <!-- Compliance Progress -->
        <div v-if="complianceStatus" class="mt-2">
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-orga-500 rounded-full transition-all duration-300"
                :style="{ width: `${checklistProgress}%` }"
              ></div>
            </div>
            <span class="text-[10px] text-gray-500 dark:text-gray-400 whitespace-nowrap">
              {{ __("{0}% complete", [Math.round(checklistProgress)]) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="flex flex-wrap gap-2 mt-3">
      <button
        @click.stop="openNoteModal('Due Diligence')"
        class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
      >
        <i class="fa-solid fa-clipboard-check"></i>
        {{ __('Due Diligence') }}
      </button>

      <button
        v-if="activity.can_make_offer"
        @click.stop="openNoteModal('Offer')"
        class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
      >
        <i class="fa-solid fa-hand-holding-dollar"></i>
        {{ __('Make Offer') }}
      </button>

      <button
        @click.stop="openNoteModal('Decision')"
        class="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
      >
        <i class="fa-solid fa-gavel"></i>
        {{ __('Decision') }}
      </button>

      <button
        @click.stop="handleFlag"
        :disabled="isFlagging"
        :class="[
          'inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg transition-colors',
          isFlagged
            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:text-amber-600 dark:hover:text-amber-400'
        ]"
      >
        <i :class="['fa-solid', isFlagging ? 'fa-spinner fa-spin' : 'fa-flag']"></i>
        {{ isFlagged ? __('Flagged') : __('Flag') }}
      </button>
    </div>

    <!-- Due Diligence Notes -->
    <div v-if="dueDiligenceNotes.length > 0 || isLoadingNotes" class="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          {{ __('Notes') }} ({{ dueDiligenceNotes.length }})
        </span>
        <button
          v-if="dueDiligenceNotes.length > 2"
          @click.stop="showAllNotes = !showAllNotes"
          class="text-xs text-orga-500 hover:text-orga-600 dark:hover:text-orga-400"
        >
          {{ showAllNotes ? __('Show less') : __('Show all') }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoadingNotes" class="text-center py-4">
        <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
      </div>

      <!-- Notes List -->
      <div v-else class="space-y-2">
        <div
          v-for="note in visibleNotes"
          :key="note.name"
          class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2"
        >
          <div class="flex items-center gap-2 mb-1">
            <span
              :class="[
                'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium',
                `bg-${getNoteTypeColor(note.note_type)}-100 dark:bg-${getNoteTypeColor(note.note_type)}-900/30`,
                `text-${getNoteTypeColor(note.note_type)}-700 dark:text-${getNoteTypeColor(note.note_type)}-400`
              ]"
            >
              <i :class="['fa-solid', getNoteTypeIcon(note.note_type)]"></i>
              {{ note.note_type }}
            </span>
            <span class="text-xs font-medium text-gray-700 dark:text-gray-300">
              {{ note.user_fullname }}
            </span>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">
              {{ formatRelativeTime(note.creation) }}
            </span>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 m-0 line-clamp-2">
            {{ note.content }}
          </p>
          <p v-if="note.related_company" class="text-[10px] text-gray-400 dark:text-gray-500 mt-1 m-0">
            <i class="fa-solid fa-building mr-1"></i>{{ note.related_company }}
          </p>
        </div>
      </div>
    </div>

    <!-- Empty State (no notes yet) -->
    <div
      v-else-if="!isLoadingNotes"
      class="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700 text-center py-3"
    >
      <p class="text-xs text-gray-400 dark:text-gray-500 m-0">
        {{ __('No notes yet. Add a due diligence note to track progress.') }}
      </p>
    </div>

    <!-- Due Diligence Note Modal -->
    <DueDiligenceNoteModal
      v-if="showNoteModal"
      :doctype="doctype"
      :docname="docname"
      :initial-note-type="initialNoteType"
      :related-company="activity.company_name"
      @close="showNoteModal = false"
      @added="handleNoteAdded"
    />
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
