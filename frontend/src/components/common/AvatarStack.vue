<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Overlapping avatar stack with +N overflow. Used on task cards and the task
  header to render collaborator avatars compactly.

  Spec: ecosystem.localhost/spec/apps/orga/features/community/task-assignment.md
-->
<script setup lang="ts">
import { computed } from 'vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { __ } from '@/composables/useTranslate'

interface StackItem {
  name: string
  image?: string | null
}

const props = withDefaults(
  defineProps<{
    items: StackItem[]
    max?: number
    size?: 'xs' | 'sm' | 'md'
  }>(),
  { max: 3, size: 'sm' },
)

const visible = computed(() => props.items.slice(0, props.max))
const overflow = computed(() => Math.max(0, props.items.length - props.max))
const tooltip = computed(() => props.items.map((i: StackItem) => i.name).join(', '))
</script>

<template>
  <div
    v-if="items.length"
    class="flex items-center"
    :title="tooltip"
    :aria-label="__('Collaborators') + ': ' + tooltip"
  >
    <div
      v-for="(item, idx) in visible"
      :key="idx"
      class="-ml-1 first:ml-0 ring-2 ring-white dark:ring-gray-900 rounded-full"
    >
      <UserAvatar :name="item.name" :image="item.image ?? undefined" :size="size" color="orga" />
    </div>
    <span
      v-if="overflow"
      class="-ml-1 ring-2 ring-white dark:ring-gray-900 rounded-full bg-gray-200 dark:bg-gray-700 text-[10px] text-gray-600 dark:text-gray-300 font-medium flex items-center justify-center w-5 h-5"
    >
      +{{ overflow }}
    </span>
  </div>
</template>
