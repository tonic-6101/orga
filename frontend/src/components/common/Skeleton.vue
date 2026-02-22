<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Skeleton.vue - Loading placeholder with shimmer animation

  Usage:
  - <Skeleton /> - Default line
  - <Skeleton type="text" /> - Text line
  - <Skeleton type="circle" /> - Avatar placeholder
  - <Skeleton type="rect" /> - Rectangle/card
  - <Skeleton type="stat" /> - Stat card placeholder
-->
<script setup lang="ts">
interface Props {
  type?: 'text' | 'circle' | 'rect' | 'stat' | 'card'
  width?: string
  height?: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  count: 1
})

// Compute classes based on type
const skeletonClass = {
  text: 'h-4 rounded',
  circle: 'rounded-full',
  rect: 'rounded-lg',
  stat: 'rounded-lg',
  card: 'rounded-lg'
}
</script>

<template>
  <!-- Stat Card Skeleton -->
  <div v-if="type === 'stat'" class="bg-white dark:bg-gray-800 rounded-lg p-5 border border-gray-200 dark:border-gray-700">
    <div class="flex justify-between items-start">
      <div class="flex-1">
        <div class="skeleton-shimmer h-3 w-24 rounded mb-3"></div>
        <div class="skeleton-shimmer h-8 w-16 rounded"></div>
      </div>
      <div class="skeleton-shimmer w-8 h-8 rounded opacity-30"></div>
    </div>
  </div>

  <!-- Card Skeleton -->
  <div v-else-if="type === 'card'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <div class="skeleton-shimmer h-4 w-32 rounded"></div>
    </div>
    <div class="p-4 space-y-3">
      <template v-for="i in count" :key="i">
        <div class="flex items-center gap-3">
          <div class="skeleton-shimmer w-8 h-8 rounded-full flex-shrink-0"></div>
          <div class="flex-1 space-y-2">
            <div class="skeleton-shimmer h-4 rounded" :style="{ width: `${70 + Math.random() * 30}%` }"></div>
            <div class="skeleton-shimmer h-3 w-24 rounded"></div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- Circle Skeleton -->
  <div
    v-else-if="type === 'circle'"
    class="skeleton-shimmer rounded-full"
    :style="{ width: width || '40px', height: height || '40px' }"
  ></div>

  <!-- Rectangle Skeleton -->
  <div
    v-else-if="type === 'rect'"
    class="skeleton-shimmer rounded-lg"
    :style="{ width: width || '100%', height: height || '100px' }"
  ></div>

  <!-- Text/Line Skeleton (default) -->
  <template v-else>
    <div
      v-for="i in count"
      :key="i"
      class="skeleton-shimmer rounded"
      :class="[i < count ? 'mb-2' : '']"
      :style="{
        width: width || (i === count ? '70%' : '100%'),
        height: height || '16px'
      }"
    ></div>
  </template>
</template>

<style scoped>
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgb(229 231 235) 0%,
    rgb(243 244 246) 50%,
    rgb(229 231 235) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.dark .skeleton-shimmer {
  background: linear-gradient(
    90deg,
    rgb(55 65 81) 0%,
    rgb(75 85 99) 50%,
    rgb(55 65 81) 100%
  );
  background-size: 200% 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
