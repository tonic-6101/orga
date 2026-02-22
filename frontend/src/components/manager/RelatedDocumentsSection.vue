<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  RelatedDocumentsSection.vue - Show related documents for an activity

  Features:
  - Display linked projects, tasks, contacts, events
  - Quick navigation to related items
  - Show relationship type (parent, child, reference)
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'

interface RelatedDocument {
  doctype: string
  name: string
  title: string
  status?: string
  relationship: 'parent' | 'child' | 'reference' | 'linked'
}

interface Props {
  doctype: string
  docname: string
  activity?: {
    project?: string
    project_name?: string
    task?: string
    task_subject?: string
    resource?: string
    resource_name?: string
    appointment?: string
    appointment_subject?: string
    reference_doctype?: string
    reference_name?: string
  } | null
}

const props = defineProps<Props>()

const router = useRouter()
const { getRelatedDocuments } = useActivityApi()

// State
const isLoading = ref(false)
const linkedDocuments = ref<RelatedDocument[]>([])

// Build related documents from activity data and API
const relatedDocuments = computed<RelatedDocument[]>(() => {
  const docs: RelatedDocument[] = []

  if (!props.activity) return docs

  // Add project if present
  if (props.activity.project) {
    docs.push({
      doctype: 'Orga Project',
      name: props.activity.project,
      title: props.activity.project_name || props.activity.project,
      relationship: 'parent'
    })
  }

  // Add task if present
  if (props.activity.task) {
    docs.push({
      doctype: 'Orga Task',
      name: props.activity.task,
      title: props.activity.task_subject || props.activity.task,
      relationship: 'parent'
    })
  }

  // Add resource if present
  if (props.activity.resource) {
    docs.push({
      doctype: 'Orga Resource',
      name: props.activity.resource,
      title: props.activity.resource_name || props.activity.resource,
      relationship: 'reference'
    })
  }

  // Add event if present
  if (props.activity.appointment) {
    docs.push({
      doctype: 'Orga Appointment',
      name: props.activity.appointment,
      title: props.activity.appointment_subject || props.activity.appointment,
      relationship: 'reference'
    })
  }

  // Add linked documents from API
  docs.push(...linkedDocuments.value)

  return docs
})

// Doctype icons
function getDoctypeIcon(doctype: string): string {
  const icons: Record<string, string> = {
    'Orga Project': 'fa-folder',
    'Orga Task': 'fa-check-square',
    'Orga Resource': 'fa-user',
    'Orga Appointment': 'fa-calendar',
    'Orga Milestone': 'fa-flag'
  }
  return icons[doctype] || 'fa-file'
}

// Doctype colors
function getDoctypeColor(doctype: string): string {
  const colors: Record<string, string> = {
    'Orga Project': 'text-blue-500 bg-blue-50 dark:bg-blue-900/30',
    'Orga Task': 'text-green-500 bg-green-50 dark:bg-green-900/30',
    'Orga Resource': 'text-purple-500 bg-purple-50 dark:bg-purple-900/30',
    'Orga Appointment': 'text-amber-500 bg-amber-50 dark:bg-amber-900/30',
    'Orga Milestone': 'text-red-500 bg-red-50 dark:bg-red-900/30'
  }
  return colors[doctype] || 'text-gray-500 bg-gray-50 dark:bg-gray-800'
}

// Relationship labels
function getRelationshipLabel(relationship: string): string {
  const labels: Record<string, string> = {
    'parent': __('Parent'),
    'child': __('Child'),
    'reference': __('Related'),
    'linked': __('Linked')
  }
  return labels[relationship] || relationship
}

// Navigate to document
function navigateToDocument(doc: RelatedDocument) {
  const routes: Record<string, string> = {
    'Orga Project': '/orga/projects',
    'Orga Task': '/orga/tasks',
    'Orga Resource': '/orga/contacts',
    'Orga Appointment': '/orga/schedule',
    'Orga Milestone': '/orga/projects'
  }

  const basePath = routes[doc.doctype] || '/orga'

  if (doc.doctype === 'Orga Task' && props.activity?.project) {
    router.push(`/orga/projects/${props.activity.project}`)
  } else if (doc.doctype === 'Orga Milestone' && props.activity?.project) {
    router.push(`/orga/projects/${props.activity.project}`)
  } else {
    router.push(`${basePath}/${doc.name}`)
  }
}

// Short doctype name for display
function getShortDoctype(doctype: string): string {
  return doctype.replace('Orga ', '')
}

// Load linked documents from API
async function loadLinkedDocuments() {
  if (!props.doctype || !props.docname) return

  isLoading.value = true
  try {
    const docs = await getRelatedDocuments(props.doctype, props.docname)
    linkedDocuments.value = docs
  } catch (e) {
    console.error('Failed to load linked documents:', e)
    linkedDocuments.value = []
  } finally {
    isLoading.value = false
  }
}

// Watch for changes
watch([() => props.doctype, () => props.docname], () => {
  loadLinkedDocuments()
}, { immediate: true })
</script>

<template>
  <div class="related-documents-section">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {{ __('Related Documents') }}
      </span>
      <span v-if="relatedDocuments.length" class="text-xs text-gray-400 dark:text-gray-500">
        {{ relatedDocuments.length }}
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-4">
      <i class="fa-solid fa-spinner fa-spin text-gray-400"></i>
    </div>

    <!-- Documents List -->
    <div v-else-if="relatedDocuments.length" class="space-y-2">
      <button
        v-for="doc in relatedDocuments"
        :key="`${doc.doctype}-${doc.name}`"
        @click="navigateToDocument(doc)"
        class="w-full flex items-center gap-3 p-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left group"
      >
        <!-- Icon -->
        <div
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
            getDoctypeColor(doc.doctype)
          ]"
        >
          <i :class="['fa-solid', getDoctypeIcon(doc.doctype)]"></i>
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
            {{ doc.title }}
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
            <span>{{ getShortDoctype(doc.doctype) }}</span>
            <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600"></span>
            <span>{{ getRelationshipLabel(doc.relationship) }}</span>
          </div>
        </div>

        <!-- Arrow -->
        <i class="fa-solid fa-chevron-right text-gray-300 dark:text-gray-600 group-hover:text-gray-400 dark:group-hover:text-gray-500 transition-colors"></i>
      </button>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-6">
      <i class="fa-solid fa-link-slash fa-lg text-gray-300 dark:text-gray-600 mb-2 block"></i>
      <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No related documents') }}</p>
    </div>
  </div>
</template>
