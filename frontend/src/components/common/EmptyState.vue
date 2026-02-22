<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  EmptyState.vue - Informative empty state with optional CTA

  Use this component when a section has no data to display.
  It provides helpful messaging and optionally a call-to-action button.
-->
<script setup lang="ts">
interface Props {
  /** Font Awesome icon class (without fa-solid prefix) */
  icon?: string
  /** Main heading text */
  title: string
  /** Optional description text */
  description?: string
  /** Optional action button label */
  actionLabel?: string
  /** Optional secondary action label */
  secondaryActionLabel?: string
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  icon: 'fa-inbox',
  size: 'md'
})

const emit = defineEmits<{
  action: []
  secondaryAction: []
}>()

const sizeClasses = {
  sm: {
    wrapper: 'py-6 px-4',
    iconWrapper: 'w-10 h-10 mb-3',
    icon: 'text-lg',
    title: 'text-sm font-medium',
    description: 'text-xs',
    button: 'px-3 py-1.5 text-sm'
  },
  md: {
    wrapper: 'py-12 px-6',
    iconWrapper: 'w-16 h-16 mb-4',
    icon: 'text-2xl',
    title: 'text-lg font-medium',
    description: 'text-sm',
    button: 'px-4 py-2 text-sm'
  },
  lg: {
    wrapper: 'py-16 px-8',
    iconWrapper: 'w-20 h-20 mb-5',
    icon: 'text-3xl',
    title: 'text-xl font-semibold',
    description: 'text-base',
    button: 'px-5 py-2.5 text-base'
  }
}

const classes = sizeClasses[props.size]
</script>

<template>
  <div :class="['flex flex-col items-center justify-center text-center', classes.wrapper]">
    <!-- Icon -->
    <div
      :class="[
        'rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center',
        classes.iconWrapper
      ]"
    >
      <i
        :class="[
          'fa-solid',
          icon,
          classes.icon,
          'text-gray-400 dark:text-gray-500'
        ]"
        aria-hidden="true"
      ></i>
    </div>

    <!-- Title -->
    <h3 :class="['text-gray-800 dark:text-gray-100 mb-2', classes.title]">
      {{ title }}
    </h3>

    <!-- Description -->
    <p
      v-if="description"
      :class="['text-gray-600 dark:text-gray-400 max-w-md mb-6', classes.description]"
    >
      {{ description }}
    </p>

    <!-- Actions -->
    <div v-if="actionLabel || secondaryActionLabel" class="flex items-center gap-3">
      <button
        v-if="actionLabel"
        @click="emit('action')"
        :class="[
          'bg-orga-500 text-white rounded-lg font-medium',
          'hover:bg-orga-600 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-orga-500 focus:ring-offset-2',
          'dark:focus:ring-offset-gray-900',
          classes.button
        ]"
      >
        {{ actionLabel }}
      </button>

      <button
        v-if="secondaryActionLabel"
        @click="emit('secondaryAction')"
        :class="[
          'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300',
          'border border-gray-300 dark:border-gray-600 rounded-lg font-medium',
          'hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
          'dark:focus:ring-offset-gray-900',
          classes.button
        ]"
      >
        {{ secondaryActionLabel }}
      </button>
    </div>

    <!-- Slot for custom content -->
    <slot></slot>
  </div>
</template>
