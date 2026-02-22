<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  TaskFinanceTab.vue - Finance information tab for Task Manager
  Editable fields: estimated_cost, actual_cost, is_billable, billing_rate
-->
<template>
  <div class="space-y-6">
    <!-- Cost Summary -->
    <div class="bg-gradient-to-br from-orga-50 to-orga-100 dark:from-orga-900/30 dark:to-orga-800/20 rounded-lg p-4">
      <h5 class="text-xs font-semibold text-orga-700 dark:text-orga-400 uppercase tracking-wider mb-3">
        {{ __('Cost Summary') }}
      </h5>
      <div class="grid grid-cols-2 gap-4">
        <!-- Estimated Cost (editable) -->
        <div>
          <p class="text-[10px] text-orga-600 dark:text-orga-500 uppercase">{{ __('Estimated') }}</p>
          <div
            v-if="editingField === 'estimated_cost'"
            class="flex items-center gap-1 mt-1"
          >
            <span class="text-sm text-orga-600">{{ currencySymbol }}</span>
            <input
              ref="editInputRef"
              v-model.number="editValue"
              type="number"
              min="0"
              step="10"
              @keydown.enter="saveField"
              @keydown.escape="cancelEdit"
              @blur="saveField"
              class="w-full text-lg font-bold bg-transparent border-b-2 border-orga-500 outline-none text-orga-800 dark:text-orga-300"
            />
          </div>
          <p
            v-else
            @click="startEdit('estimated_cost', task.estimated_cost || 0)"
            class="text-xl font-bold text-orga-800 dark:text-orga-300 cursor-text hover:text-orga-600 dark:hover:text-orga-200 transition-colors"
            :title="__('Click to edit')"
          >
            {{ formatCurrency(task.estimated_cost || 0) }}
          </p>
        </div>

        <!-- Actual Cost (editable) -->
        <div>
          <p class="text-[10px] text-orga-600 dark:text-orga-500 uppercase">{{ __('Actual') }}</p>
          <div
            v-if="editingField === 'actual_cost'"
            class="flex items-center gap-1 mt-1"
          >
            <span class="text-sm text-orga-600">{{ currencySymbol }}</span>
            <input
              ref="editInputRef"
              v-model.number="editValue"
              type="number"
              min="0"
              step="10"
              @keydown.enter="saveField"
              @keydown.escape="cancelEdit"
              @blur="saveField"
              class="w-full text-lg font-bold bg-transparent border-b-2 border-orga-500 outline-none text-orga-800 dark:text-orga-300"
            />
          </div>
          <p
            v-else
            @click="startEdit('actual_cost', task.actual_cost || 0)"
            class="text-xl font-bold text-orga-800 dark:text-orga-300 cursor-text hover:text-orga-600 dark:hover:text-orga-200 transition-colors"
            :title="__('Click to edit')"
          >
            {{ formatCurrency(task.actual_cost || 0) }}
          </p>
        </div>
      </div>

      <!-- Budget Variance -->
      <div v-if="budgetVariance !== null" class="mt-3 pt-3 border-t border-orga-200 dark:border-orga-700">
        <div class="flex items-center justify-between">
          <span class="text-xs text-orga-600 dark:text-orga-500">{{ __('Variance') }}</span>
          <span :class="[
            'text-sm font-semibold',
            budgetVariance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          ]">
            {{ budgetVariance >= 0 ? '+' : '' }}{{ formatCurrency(budgetVariance) }}
            ({{ budgetVariancePercent }}%)
          </span>
        </div>
      </div>
    </div>

    <!-- Time & Billing -->
    <div>
      <h5 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <i class="fa-solid fa-clock text-orga-500"></i>
        {{ __('Time & Billing') }}
      </h5>

      <div class="space-y-3">
        <!-- Hours (read-only, from time logs) -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase">{{ __('Estimated Hours') }}</p>
            <p class="text-lg font-semibold text-gray-800 dark:text-gray-200">
              {{ task.estimated_hours || 0 }}h
            </p>
          </div>
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <p class="text-[10px] text-gray-500 dark:text-gray-400 uppercase">{{ __('Actual Hours') }}</p>
            <p class="text-lg font-semibold text-gray-800 dark:text-gray-200">
              {{ task.actual_hours || 0 }}h
            </p>
          </div>
        </div>

        <!-- Billable toggle (editable) -->
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div class="flex items-center gap-2">
            <button
              @click="toggleBillable"
              :class="[
                'w-5 h-5 rounded flex items-center justify-center transition-colors',
                task.is_billable
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-400 dark:text-gray-500'
              ]"
              :title="__('Toggle billable')"
            >
              <i v-if="task.is_billable" class="fa-solid fa-check text-xs"></i>
            </button>
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Billable') }}</span>
          </div>

          <!-- Billing rate (editable, only when billable) -->
          <div v-if="task.is_billable">
            <div
              v-if="editingField === 'billing_rate'"
              class="flex items-center gap-1"
            >
              <span class="text-xs text-gray-400">{{ currencySymbol }}</span>
              <input
                ref="editInputRef"
                v-model.number="editValue"
                type="number"
                min="0"
                step="5"
                @keydown.enter="saveField"
                @keydown.escape="cancelEdit"
                @blur="saveField"
                class="w-20 text-sm font-medium bg-transparent border-b-2 border-orga-500 outline-none text-gray-800 dark:text-gray-200 text-right"
              />
              <span class="text-xs text-gray-400">/hr</span>
            </div>
            <span
              v-else
              @click="startEdit('billing_rate', task.billing_rate || 0)"
              class="text-sm font-medium text-gray-800 dark:text-gray-200 cursor-text hover:text-orga-600 dark:hover:text-orga-400 transition-colors"
              :title="__('Click to edit rate')"
            >
              {{ task.billing_rate ? `${formatCurrency(task.billing_rate)}/hr` : __('Set rate') }}
            </span>
          </div>
        </div>

        <!-- Billable Amount (calculated) -->
        <div v-if="task.is_billable && billableAmount > 0" class="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div class="flex items-center justify-between">
            <span class="text-sm text-green-700 dark:text-green-400">{{ __('Billable Amount') }}</span>
            <span class="text-lg font-bold text-green-800 dark:text-green-300">
              {{ formatCurrency(billableAmount) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import type { OrgaTask } from '@/types/orga'
import { useCurrency } from '@/composables/useCurrency'

interface Props {
  task: OrgaTask
}

const props = defineProps<Props>()

const { formatCurrency, currencySymbol } = useCurrency()

const emit = defineEmits<{
  (e: 'update-finance', field: string, value: number | boolean): void
}>()

// Inline editing state
type EditableField = 'estimated_cost' | 'actual_cost' | 'billing_rate'
const editingField = ref<EditableField | null>(null)
const editValue = ref<number>(0)
const editInputRef = ref<HTMLInputElement | null>(null)
const isSaving = ref(false)

function startEdit(field: EditableField, currentValue: number): void {
  if (isSaving.value) return
  editingField.value = field
  editValue.value = currentValue
  nextTick(() => editInputRef.value?.focus())
}

function cancelEdit(): void {
  editingField.value = null
}

function saveField(): void {
  if (!editingField.value || isSaving.value) return
  isSaving.value = true
  const field = editingField.value
  const val = editValue.value && editValue.value > 0 ? editValue.value : 0
  editingField.value = null
  emit('update-finance', field, val)
  // Reset saving guard after DOM settles (prevents blur double-fire)
  nextTick(() => { isSaving.value = false })
}

function toggleBillable(): void {
  if (isSaving.value) return
  isSaving.value = true
  emit('update-finance', 'is_billable', !props.task.is_billable)
  nextTick(() => { isSaving.value = false })
}

// Computed values
const budgetVariance = computed(() => {
  if (!props.task.estimated_cost) return null
  return (props.task.estimated_cost || 0) - (props.task.actual_cost || 0)
})

const budgetVariancePercent = computed(() => {
  if (!props.task.estimated_cost || budgetVariance.value === null) return '0'
  return Math.round((budgetVariance.value / props.task.estimated_cost) * 100)
})

const billableAmount = computed(() => {
  if (!props.task.is_billable || !props.task.billing_rate) return 0
  return (props.task.actual_hours || 0) * props.task.billing_rate
})


</script>
