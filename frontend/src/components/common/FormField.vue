<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  FormField.vue - Reusable form field wrapper with validation UI

  Features:
  - Required field indicator (red asterisk)
  - Real-time validation feedback
  - Character counter (optional)
  - Success checkmark for valid fields
  - Error message display
  - Accessible with proper ARIA attributes
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  label: string
  required?: boolean
  error?: string
  hint?: string
  maxLength?: number
  currentLength?: number
  showSuccess?: boolean
  touched?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  showSuccess: false,
  touched: false
})

// Generate unique ID for accessibility
const fieldId = ref(`field-${Math.random().toString(36).slice(2, 9)}`)

// Computed states
const hasError = computed(() => !!props.error && props.touched)
const isValid = computed(() => props.showSuccess && props.touched && !props.error)
const showCharCounter = computed(() => props.maxLength !== undefined && props.currentLength !== undefined)
const charCounterClass = computed(() => {
  if (!props.maxLength || !props.currentLength) return 'text-gray-400'
  const ratio = props.currentLength / props.maxLength
  if (ratio >= 1) return 'text-red-500'
  if (ratio >= 0.9) return 'text-amber-500'
  return 'text-gray-400'
})
</script>

<template>
  <div class="form-field">
    <!-- Label Row -->
    <div class="flex items-center justify-between mb-1.5">
      <label
        :for="fieldId"
        class="block text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        {{ label }}
        <span v-if="required" class="text-red-500 ml-0.5" :aria-label="__('required')">*</span>
      </label>

      <!-- Validation indicator -->
      <span v-if="isValid" class="text-green-500 text-sm" :aria-label="__('Valid')">
        <i class="fa-solid fa-check-circle"></i>
      </span>
      <span v-else-if="hasError" class="text-red-500 text-sm" :aria-label="__('Error')">
        <i class="fa-solid fa-exclamation-circle"></i>
      </span>
    </div>

    <!-- Field Content (slot) -->
    <div class="relative">
      <slot :id="fieldId" :has-error="hasError" :is-valid="isValid" />
    </div>

    <!-- Footer Row: Error/Hint + Character Counter -->
    <div class="flex items-start justify-between mt-1 min-h-[1.25rem]">
      <!-- Error or Hint -->
      <div class="flex-1">
        <p
          v-if="hasError"
          class="text-xs text-red-500 flex items-center gap-1"
          role="alert"
        >
          <i class="fa-solid fa-exclamation-triangle text-[10px]"></i>
          {{ error }}
        </p>
        <p
          v-else-if="hint && !isValid"
          class="text-xs text-gray-500 dark:text-gray-400"
        >
          {{ hint }}
        </p>
      </div>

      <!-- Character Counter -->
      <span
        v-if="showCharCounter"
        :class="['text-xs ml-2 tabular-nums', charCounterClass]"
      >
        {{ currentLength }} / {{ maxLength }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.form-field {
  @apply mb-0;
}
</style>
