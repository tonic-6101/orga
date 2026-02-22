<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  LoadingButton.vue - Button with loading state and spinner

  Use this component for buttons that trigger async operations.
  It provides visual feedback during loading and prevents double-clicks.
-->
<script setup lang="ts">
import { computed } from 'vue'
import { __ } from '@/composables/useTranslate'

interface Props {
  /** Show loading spinner */
  loading?: boolean
  /** Disable the button */
  disabled?: boolean
  /** Button style variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  /** Button size */
  size?: 'sm' | 'md' | 'lg'
  /** Text to show while loading */
  loadingText?: string
  /** Button type */
  type?: 'button' | 'submit' | 'reset'
  /** Full width button */
  fullWidth?: boolean
  /** Icon class (Font Awesome) to show before text */
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false,
  variant: 'primary',
  size: 'md',
  loadingText: __('Loading...'),
  type: 'button',
  fullWidth: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const handleClick = (event: MouseEvent) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}

const variantClasses = computed(() => {
  const variants = {
    primary: [
      'bg-orga-500 text-white',
      'hover:bg-orga-600',
      'focus:ring-orga-500',
      'disabled:bg-orga-300'
    ],
    secondary: [
      'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300',
      'border border-gray-300 dark:border-gray-600',
      'hover:bg-gray-50 dark:hover:bg-gray-700',
      'focus:ring-gray-500',
      'disabled:bg-gray-100 dark:disabled:bg-gray-900'
    ],
    danger: [
      'bg-red-500 text-white',
      'hover:bg-red-600',
      'focus:ring-red-500',
      'disabled:bg-red-300'
    ],
    ghost: [
      'bg-transparent text-gray-700 dark:text-gray-300',
      'hover:bg-gray-100 dark:hover:bg-gray-800',
      'focus:ring-gray-500'
    ]
  }
  return variants[props.variant] || variants.primary
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2'
  }
  return sizes[props.size] || sizes.md
})

const isDisabled = computed(() => props.loading || props.disabled)
</script>

<template>
  <button
    :type="type"
    :disabled="isDisabled"
    :class="[
      'inline-flex items-center justify-center rounded-lg font-medium',
      'transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      'dark:focus:ring-offset-gray-900',
      variantClasses,
      sizeClasses,
      {
        'w-full': fullWidth,
        'opacity-50 cursor-not-allowed': isDisabled,
        'hover:-translate-y-0.5 hover:shadow-md': !isDisabled && variant === 'primary'
      }
    ]"
    @click="handleClick"
  >
    <!-- Loading spinner -->
    <i
      v-if="loading"
      class="fa-solid fa-spinner fa-spin"
      aria-hidden="true"
    ></i>

    <!-- Icon (when not loading) -->
    <i
      v-else-if="icon"
      :class="['fa-solid', icon]"
      aria-hidden="true"
    ></i>

    <!-- Button text -->
    <span>
      <slot v-if="!loading" />
      <template v-else>{{ loadingText }}</template>
    </span>
  </button>
</template>
