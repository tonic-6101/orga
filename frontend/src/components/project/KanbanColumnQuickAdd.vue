<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  KanbanColumnQuickAdd.vue - Quick-add button for Kanban columns
-->
<script setup lang="ts">
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
    class="w-full py-2 px-3 mt-2 text-sm text-gray-500 dark:text-gray-400 hover:text-orga-500 hover:bg-orga-50 dark:hover:bg-orga-900/20 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 hover:border-orga-500 transition-colors flex items-center justify-center gap-2"
  >
    <i class="fa-solid fa-plus text-xs"></i>
    {{ __('Add Task') }}
  </button>
</template>
