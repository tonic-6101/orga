<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Spec: ecosystem.localhost/spec/apps/orga/features/community/task-assignment.md

  Flat Assignees picker (Model 1a). Single source: Dock People (Frappe Contact),
  permission-scoped by Dock. Orga Resource enriches rows with role/department
  but does not gate visibility and is never auto-created. No per-task Owner —
  all assignees are equal.
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Check, Search, AlertTriangle } from 'lucide-vue-next'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { __ } from '@/composables/useTranslate'
import { useAssignees, type Assignable } from '@/composables/useAssignees'

const props = defineProps<{
  task: string
  contacts: string[]
  project?: string | null
}>()

const emit = defineEmits<{
  (e: 'update', payload: { contacts: string[] }): void
  (e: 'close'): void
}>()

const SOFT_WARN = 10 // Community tier: soft nudge only, never blocking.

const query = ref('')
const { results, loading, search } = useAssignees()

const selected = ref<Set<string>>(new Set(props.contacts))

const overSoftCap = computed(() => selected.value.size >= SOFT_WARN)

const grouped = computed(() => {
  if (query.value) return { flat: results.value }
  const internal: Assignable[] = []
  const external: Assignable[] = []
  for (const row of results.value) {
    if (row.is_internal) internal.push(row)
    else external.push(row)
  }
  return { internal, external }
})

watch(query, (q: string) => search({ query: q, project: props.project ?? null }), { immediate: false })
onMounted(() => search({ query: '', project: props.project ?? null }))

function toggle(row: Assignable) {
  if (selected.value.has(row.contact)) selected.value.delete(row.contact)
  else selected.value.add(row.contact)
  emit('update', { contacts: Array.from(selected.value) })
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
</script>

<template>
  <div
    class="w-80 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl"
    role="dialog"
    :aria-label="__('Assign people')"
    @keydown="onKeydown"
  >
    <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-100 dark:border-gray-800">
      <Search class="w-4 h-4 text-gray-400" aria-hidden="true" />
      <input
        v-model="query"
        type="text"
        :placeholder="__('Type name or email…')"
        class="flex-1 text-sm bg-transparent outline-none text-gray-800 dark:text-gray-200 placeholder-gray-400"
        autofocus
      />
    </div>

    <div
      v-if="overSoftCap"
      class="flex items-start gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-100 dark:border-amber-900 text-[11px] text-amber-800 dark:text-amber-200"
    >
      <AlertTriangle class="w-3 h-3 mt-0.5 shrink-0" aria-hidden="true" />
      <span>{{ __('Many assignees can diffuse ownership — consider splitting the task.') }}</span>
    </div>

    <div class="max-h-80 overflow-y-auto py-1">
      <p v-if="loading" class="text-xs text-gray-400 text-center py-4">{{ __('Loading…') }}</p>

      <template v-else-if="query">
        <AssigneeRow
          v-for="row in grouped.flat"
          :key="row.contact"
          :row="row"
          :is-selected="selected.has(row.contact)"
          @toggle="toggle(row)"
        />
      </template>

      <template v-else>
        <SectionHeader v-if="grouped.internal?.length" :label="__('Internal')" />
        <AssigneeRow
          v-for="row in grouped.internal ?? []"
          :key="row.contact"
          :row="row"
          :is-selected="selected.has(row.contact)"
          @toggle="toggle(row)"
        />
        <SectionHeader v-if="grouped.external?.length" :label="__('External')" />
        <AssigneeRow
          v-for="row in grouped.external ?? []"
          :key="row.contact"
          :row="row"
          :is-selected="selected.has(row.contact)"
          @toggle="toggle(row)"
        />
      </template>

      <p
        v-if="!loading && !results.length"
        class="text-xs text-gray-400 text-center py-4"
      >
        {{ __('No people match.') }}
      </p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, h } from 'vue'

export const SectionHeader = defineComponent({
  props: { label: { type: String, required: true } },
  setup: (props) =>
    () =>
      h(
        'div',
        {
          class:
            'px-3 pt-2 pb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider',
        },
        props.label,
      ),
})

export const AssigneeRow = defineComponent({
  props: {
    row: { type: Object, required: true },
    isSelected: Boolean,
  },
  emits: ['toggle'],
  setup: (props, { emit }) => {
    return () =>
      h(
        'div',
        {
          class:
            'flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer text-sm',
          onClick: () => emit('toggle'),
        },
        [
          h(UserAvatar, { name: props.row.name, size: 'xs', color: 'orga' }),
          h('div', { class: 'flex-1 min-w-0' }, [
            h('div', { class: 'flex items-center gap-1' }, [
              h('span', { class: 'truncate text-gray-800 dark:text-gray-200' }, props.row.name),
              !props.row.is_internal
                ? h(
                    'span',
                    {
                      class:
                        'text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500',
                      title:
                        'External contact — no login on this site. Will be notified by email.',
                    },
                    'ext',
                  )
                : null,
            ]),
            props.row.role_label
              ? h(
                  'span',
                  { class: 'text-[10px] text-gray-400' },
                  props.row.role_label,
                )
              : null,
          ]),
          props.isSelected ? h(Check, { class: 'w-3 h-3 text-accent-500' }) : null,
        ],
      )
  },
})
</script>
