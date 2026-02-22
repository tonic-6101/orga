<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  NewActivityBanner.vue - Sticky banner showing count of new activities available to load
-->
<script setup lang="ts">
defineProps<{
  count: number
}>()

const emit = defineEmits<{
  load: []
}>()
</script>

<template>
  <Transition name="slide">
    <div
      v-if="count > 0"
      class="sticky top-0 z-10 flex items-center justify-center gap-2 px-4 py-2.5 bg-orga-500 text-white cursor-pointer hover:bg-orga-600 transition-colors shadow-md"
      @click="emit('load')"
    >
      <i class="fa-solid fa-arrow-up text-xs"></i>
      <span class="text-sm font-medium">
        {{ count === 1 ? __("{0} new activity", [count]) : __("{0} new activities", [count]) }} — {{ __('Click to load') }}
      </span>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>
