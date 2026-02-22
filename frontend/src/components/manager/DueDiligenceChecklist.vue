<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  DueDiligenceChecklist.vue - Due diligence checklist component for Manager panel

  Features:
  - Standard checklist items per activity type
  - Track completion per item
  - Show completion percentage
  - Persists to backend via notes
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'
import type { ComplianceStatus, NoteType } from '@/types/orga'

interface ChecklistItem {
  id: string
  label: string
  description: string
  noteType: NoteType
  completed: boolean
}

interface Props {
  doctype: string
  docname: string
  activityType?: string
}

const props = withDefaults(defineProps<Props>(), {
  activityType: 'external'
})

const emit = defineEmits<{
  'item-completed': [item: ChecklistItem]
  'progress-changed': [progress: number]
}>()

const { getComplianceStatus, addDueDiligenceNote } = useActivityApi()

// State
const isLoading = ref(false)
const complianceStatus = ref<ComplianceStatus | null>(null)

// Standard checklist items - can be customized per activity type
const standardItems: ChecklistItem[] = [
  {
    id: 'initial_review',
    label: __('Initial Review'),
    description: __('Perform initial assessment and background check'),
    noteType: 'Due Diligence',
    completed: false
  },
  {
    id: 'documentation',
    label: __('Documentation Review'),
    description: __('Review all relevant documents and contracts'),
    noteType: 'Due Diligence',
    completed: false
  },
  {
    id: 'risk_assessment',
    label: __('Risk Assessment'),
    description: __('Evaluate potential risks and concerns'),
    noteType: 'Due Diligence',
    completed: false
  },
  {
    id: 'offer_preparation',
    label: __('Offer Prepared'),
    description: __('Prepare and document offer terms'),
    noteType: 'Offer',
    completed: false
  },
  {
    id: 'final_decision',
    label: __('Final Decision'),
    description: __('Document final decision and rationale'),
    noteType: 'Decision',
    completed: false
  }
]

const checklistItems = ref<ChecklistItem[]>([...standardItems])

// Computed
const completedCount = computed(() => checklistItems.value.filter(item => item.completed).length)
const totalCount = computed(() => checklistItems.value.length)
const progressPercent = computed(() => totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0)

const progressColor = computed(() => {
  if (progressPercent.value >= 80) return 'bg-green-500'
  if (progressPercent.value >= 50) return 'bg-amber-500'
  return 'bg-orga-500'
})

async function loadStatus() {
  isLoading.value = true
  try {
    const status = await getComplianceStatus(props.doctype, props.docname)
    complianceStatus.value = status

    // Update checklist based on type counts
    checklistItems.value = standardItems.map(item => ({
      ...item,
      completed: (status.type_counts[item.noteType] || 0) > 0
    }))

    emit('progress-changed', progressPercent.value)
  } catch (e) {
    console.error('Failed to load compliance status:', e)
  } finally {
    isLoading.value = false
  }
}

async function toggleItem(item: ChecklistItem) {
  if (item.completed) {
    // Can't uncheck - notes already exist
    return
  }

  // Add a note of the appropriate type to mark as complete
  try {
    await addDueDiligenceNote(
      props.doctype,
      props.docname,
      `Completed: ${item.label} - ${item.description}`,
      item.noteType,
      'Internal'
    )

    item.completed = true
    emit('item-completed', item)
    emit('progress-changed', progressPercent.value)
  } catch (e) {
    console.error('Failed to mark item as complete:', e)
  }
}

function getNoteTypeIcon(noteType: NoteType): string {
  const icons: Record<NoteType, string> = {
    'General': 'fa-sticky-note',
    'Due Diligence': 'fa-clipboard-check',
    'Offer': 'fa-hand-holding-dollar',
    'Decision': 'fa-gavel'
  }
  return icons[noteType] || 'fa-sticky-note'
}

function getNoteTypeColor(noteType: NoteType): string {
  const colors: Record<NoteType, string> = {
    'General': 'text-gray-500',
    'Due Diligence': 'text-blue-500',
    'Offer': 'text-green-500',
    'Decision': 'text-purple-500'
  }
  return colors[noteType] || 'text-gray-500'
}

// Watch for doctype/docname changes
watch([() => props.doctype, () => props.docname], () => {
  loadStatus()
}, { immediate: true })
</script>

<template>
  <div class="due-diligence-checklist">
    <!-- Header with progress -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <i class="fa-solid fa-clipboard-list text-orga-500"></i>
        <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ __('Due Diligence Checklist') }}</span>
      </div>
      <span class="text-xs text-gray-500 dark:text-gray-400">
        {{ completedCount }}/{{ totalCount }}
      </span>
    </div>

    <!-- Progress bar -->
    <div class="mb-4">
      <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          :class="['h-full rounded-full transition-all duration-300', progressColor]"
          :style="{ width: `${progressPercent}%` }"
        ></div>
      </div>
      <div class="flex items-center justify-between mt-1">
        <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('Progress') }}</span>
        <span class="text-xs font-medium text-gray-600 dark:text-gray-400">{{ progressPercent }}%</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-4">
      <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
    </div>

    <!-- Checklist Items -->
    <div v-else class="space-y-2">
      <div
        v-for="item in checklistItems"
        :key="item.id"
        :class="[
          'flex items-start gap-3 p-2 rounded-lg transition-colors',
          item.completed
            ? 'bg-green-50 dark:bg-green-900/20'
            : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer'
        ]"
        @click="toggleItem(item)"
      >
        <!-- Checkbox -->
        <div
          :class="[
            'w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors',
            item.completed
              ? 'border-green-500 bg-green-500 text-white'
              : 'border-gray-300 dark:border-gray-600'
          ]"
        >
          <i v-if="item.completed" class="fa-solid fa-check text-[10px]"></i>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span
              :class="[
                'text-sm font-medium',
                item.completed
                  ? 'text-green-700 dark:text-green-400 line-through'
                  : 'text-gray-800 dark:text-gray-200'
              ]"
            >
              {{ item.label }}
            </span>
            <i :class="['fa-solid text-xs', getNoteTypeIcon(item.noteType), getNoteTypeColor(item.noteType)]"></i>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 m-0 mt-0.5">
            {{ item.description }}
          </p>
        </div>

        <!-- Status indicator -->
        <div v-if="item.completed" class="text-green-500 shrink-0">
          <i class="fa-solid fa-circle-check"></i>
        </div>
      </div>
    </div>

    <!-- Flagged indicator -->
    <div
      v-if="complianceStatus?.is_flagged"
      class="mt-4 flex items-center gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 rounded-lg"
    >
      <i class="fa-solid fa-flag text-amber-500"></i>
      <span class="text-sm text-amber-700 dark:text-amber-400">{{ __('This activity has been flagged for attention') }}</span>
    </div>

    <!-- Last updated -->
    <div v-if="complianceStatus?.last_note_date" class="mt-3 text-xs text-gray-400 dark:text-gray-500">
      {{ __('Last updated:') }} {{ new Date(complianceStatus.last_note_date).toLocaleDateString() }}
    </div>
  </div>
</template>
