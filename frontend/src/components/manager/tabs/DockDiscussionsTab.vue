<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  DockDiscussionsTab.vue — Dock Discussion integration for Orga Manager panels.
  Shows Dock Discussions linked to the current record + Dock Comment thread.
  Uses Dock's embeddable components via ESM import.

  Replaced Orga's ActivityDiscussionTab (Phase F, 2026-03-22).
  Uses Dock's shared comment + discussion infrastructure (#41, #42).
-->
<script lang="ts">
export default { name: 'DockDiscussionsTab' }
</script>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { __ } from '@/composables/useTranslate'

defineProps<{
  doctype: string
  docname: string
}>()

// Load Dock's embeddable components via dynamic ESM import.
// Falls back gracefully if Dock is not installed or build is missing.
const DockCommentThread = defineAsyncComponent(() =>
  import('/assets/dock/js/dock-collab.esm.js').then(m => m.DockCommentThread)
)
const DockDiscussionList = defineAsyncComponent(() =>
  import('/assets/dock/js/dock-collab.esm.js').then(m => m.DockDiscussionList)
)
</script>

<template>
  <div class="flex flex-col gap-6 p-4 h-full overflow-auto">
    <!-- Dock Discussions linked to this record -->
    <Suspense>
      <DockDiscussionList
        :reference-doctype="doctype"
        :reference-name="docname"
      />
      <template #fallback>
        <div class="text-sm text-gray-400 py-4 text-center">
          {{ __('Loading discussions...') }}
        </div>
      </template>
    </Suspense>

    <!-- Dock Comment thread on this record -->
    <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
      <Suspense>
        <DockCommentThread
          :reference-doctype="doctype"
          :reference-name="docname"
          show-notes
        />
        <template #fallback>
          <div class="text-sm text-gray-400 py-4 text-center">
            {{ __('Loading comments...') }}
          </div>
        </template>
      </Suspense>
    </div>
  </div>
</template>
