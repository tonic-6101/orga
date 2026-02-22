<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
/**
 * BudgetBurnRate - Budget utilization visualization for Gantt focus panel
 *
 * Displays budget vs spent with color-coded burn rate:
 * - Green (0-80%): On track
 * - Yellow (80-95%): Watch closely
 * - Red (>95%): Over budget risk
 */

import { computed } from 'vue'
import { useCurrency } from '@/composables/useCurrency'

interface Props {
  budget: number
  spent: number
  showLabels?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  showLabels: true,
  size: 'md'
})

const { formatCurrency } = useCurrency()

// Calculate burn rate percentage
const burnRate = computed<number>(() => {
  if (!props.budget || props.budget <= 0) return 0
  return Math.min(100, Math.round((props.spent / props.budget) * 100))
})

// Remaining budget
const remaining = computed<number>(() => {
  return Math.max(0, props.budget - props.spent)
})

// Determine color based on burn rate
const barColor = computed<string>(() => {
  if (burnRate.value <= 80) return 'bg-green-500'
  if (burnRate.value <= 95) return 'bg-yellow-500'
  return 'bg-red-500'
})

const textColor = computed<string>(() => {
  if (burnRate.value <= 80) return 'text-green-600'
  if (burnRate.value <= 95) return 'text-yellow-600'
  return 'text-red-600'
})

// Size variants
const barHeight = computed<string>(() => {
  switch (props.size) {
    case 'sm': return 'h-1.5'
    case 'lg': return 'h-3'
    default: return 'h-2'
  }
})

</script>

<template>
  <div class="budget-burn-rate">
    <!-- Labels -->
    <div v-if="showLabels" class="space-y-1.5 mb-2">
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">{{ __('Budget') }}</span>
        <span class="font-medium text-gray-800">{{ formatCurrency(budget) }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">{{ __('Spent') }}</span>
        <span class="font-medium text-gray-800">{{ formatCurrency(spent) }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-500">{{ __('Remaining') }}</span>
        <span :class="['font-medium', remaining > 0 ? 'text-green-600' : 'text-red-600']">
          {{ formatCurrency(remaining) }}
        </span>
      </div>
    </div>

    <!-- Burn rate bar -->
    <div class="mt-2">
      <div class="flex items-center justify-between mb-1">
        <span class="text-xs text-gray-500">{{ __('Burn Rate') }}</span>
        <span :class="['text-xs font-medium', textColor]">{{ burnRate }}%</span>
      </div>
      <div :class="['w-full bg-gray-200 rounded-full overflow-hidden', barHeight]">
        <div
          :class="['h-full rounded-full transition-all duration-300', barColor]"
          :style="{ width: burnRate + '%' }"
        ></div>
      </div>
    </div>

    <!-- Warning indicator -->
    <div v-if="burnRate > 95" class="mt-2 flex items-center gap-1 text-xs text-red-600">
      <i class="fa-solid fa-exclamation-triangle"></i>
      <span>{{ __('Budget at risk') }}</span>
    </div>
    <div v-else-if="burnRate > 80" class="mt-2 flex items-center gap-1 text-xs text-yellow-600">
      <i class="fa-solid fa-exclamation-circle"></i>
      <span>{{ __('Watch budget closely') }}</span>
    </div>
  </div>
</template>
