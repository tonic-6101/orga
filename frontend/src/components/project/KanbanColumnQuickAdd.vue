<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  KanbanColumnQuickAdd.vue - Quick-add button for Kanban columns
-->
<script setup lang="ts">
import { Plus } from 'lucide-vue-next'

interface Props {
  status: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'add-task': [status: string]
}>()

function handleClick() {
  emit('add-task', props.status)
}
</script>

<template>
  <button
    @click="handleClick"
    class="w-full py-2 px-3 mt-2 text-sm text-gray-500 dark:text-gray-400 hover:text-accent-500 hover:bg-accent-50 dark:hover:bg-accent-900/20 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 hover:border-accent-500 transition-colors flex items-center justify-center gap-2"
  >
    <Plus class="w-3 h-3" aria-hidden="true" />
    {{ __('Add Task') }}
  </button>
</template>
