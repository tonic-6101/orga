<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
defineProps<{
  label: string
}>()
</script>

<template>
  <div class="sticky top-0 z-10 flex items-center gap-3 py-2 px-1 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm">
    <div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap">
      {{ label }}
    </span>
    <div class="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
  </div>
</template>
