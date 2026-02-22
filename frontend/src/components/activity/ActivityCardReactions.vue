<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  ActivityCardReactions.vue - Inline reactions for activity cards

  Features:
  - Quick reactions: acknowledge, celebrate, seen, flag
  - Optimistic updates for instant feedback
  - User reaction highlighting
  - Reaction counts with tooltips
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActivityApi } from '@/composables/useApi'
import { __ } from '@/composables/useTranslate'

interface Props {
  doctype: string
  docname: string
  initialCounts?: Record<string, number>
  initialUserReactions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  initialCounts: () => ({}),
  initialUserReactions: () => []
})

const emit = defineEmits<{
  'reaction-changed': [type: string, reacted: boolean, counts: Record<string, number>]
}>()

const { toggleReaction } = useActivityApi()

// Reaction definitions
const reactionTypes = [
  { type: 'acknowledge', emoji: '👍', label: __('Acknowledge') },
  { type: 'celebrate', emoji: '🎉', label: __('Celebrate') },
  { type: 'seen', emoji: '👀', label: __('Seen') },
  { type: 'flag', emoji: '🚩', label: __('Flag for attention') }
]

// Local state
const counts = ref<Record<string, number>>({ ...props.initialCounts })
const userReactions = ref<string[]>([...props.initialUserReactions])
const showDropdown = ref(false)
const isToggling = ref<string | null>(null)

// Has any reactions?
const hasAnyReactions = computed(() => {
  return Object.values(counts.value).some(c => c > 0) || userReactions.value.length > 0
})

// Reactions to show (only those with counts or user has reacted)
const visibleReactions = computed(() => {
  return reactionTypes.filter(r =>
    (counts.value[r.type] || 0) > 0 || userReactions.value.includes(r.type)
  )
})

function hasReacted(type: string): boolean {
  return userReactions.value.includes(type)
}

function getCount(type: string): number {
  return counts.value[type] || 0
}

function getTooltip(type: string): string {
  const count = getCount(type)
  const reaction = reactionTypes.find(r => r.type === type)
  const label = reaction?.label || type

  if (count === 0) return label
  if (count === 1 && hasReacted(type)) return __('You reacted with {0}', [label])
  if (hasReacted(type)) return __('You and {0} others - {1}', [count - 1, label])
  return `${count} ${label}`
}

async function handleToggle(type: string) {
  if (isToggling.value) return

  isToggling.value = type
  const wasReacted = hasReacted(type)
  // Snapshot for revert on error
  const prevReactions = [...userReactions.value]
  const prevCounts = { ...counts.value }

  // Optimistic update — only one reaction per user
  if (wasReacted) {
    // Toggle off current reaction
    userReactions.value = []
    counts.value[type] = Math.max(0, (counts.value[type] || 0) - 1)
  } else {
    // Remove previous reaction (if any) before adding new one
    for (const prev of prevReactions) {
      counts.value[prev] = Math.max(0, (counts.value[prev] || 0) - 1)
    }
    userReactions.value = [type]
    counts.value[type] = (counts.value[type] || 0) + 1
  }

  try {
    const result = await toggleReaction(props.doctype, props.docname, type)
    // Update with server response
    counts.value = result.counts
    userReactions.value = result.user_reactions
    emit('reaction-changed', type, result.reacted ?? !wasReacted, result.counts)
  } catch (e) {
    // Revert to snapshot on error
    userReactions.value = prevReactions
    counts.value = prevCounts
    console.error('Failed to toggle reaction:', e)
  } finally {
    isToggling.value = null
  }
}

function handleDropdownToggle(event: MouseEvent) {
  event.stopPropagation()
  showDropdown.value = !showDropdown.value
}

function handleReactionFromDropdown(type: string, event: MouseEvent) {
  event.stopPropagation()
  handleToggle(type)
  showDropdown.value = false
}

// Close dropdown when clicking outside
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.reaction-dropdown-container')) {
    showDropdown.value = false
  }
}

// Add/remove click outside listener
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex items-center gap-1.5 flex-wrap" @click.stop>
    <!-- Existing Reactions -->
    <button
      v-for="reaction in visibleReactions"
      :key="reaction.type"
      @click.stop="handleToggle(reaction.type)"
      :disabled="isToggling === reaction.type"
      :class="[
        'inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full transition-all',
        'hover:scale-105 active:scale-95 disabled:opacity-50',
        hasReacted(reaction.type)
          ? 'bg-orga-100 dark:bg-orga-900/40 text-orga-700 dark:text-orga-300 border border-orga-300 dark:border-orga-700'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 border border-transparent'
      ]"
      :title="getTooltip(reaction.type)"
    >
      <span class="text-sm">{{ reaction.emoji }}</span>
      <span v-if="getCount(reaction.type) > 0" class="font-medium">{{ getCount(reaction.type) }}</span>
    </button>

    <!-- Add Reaction Button (Dropdown) -->
    <div class="relative reaction-dropdown-container">
      <button
        @click="handleDropdownToggle"
        class="inline-flex items-center justify-center w-6 h-6 rounded-full text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        :title="__('Add reaction')"
      >
        <i class="fa-regular fa-face-smile text-sm"></i>
      </button>

      <!-- Dropdown -->
      <Transition name="dropdown">
        <div
          v-if="showDropdown"
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-1.5 flex gap-0.5 z-50"
        >
          <button
            v-for="reaction in reactionTypes"
            :key="reaction.type"
            @click="handleReactionFromDropdown(reaction.type, $event)"
            :disabled="isToggling === reaction.type"
            :class="[
              'p-1.5 rounded-lg transition-all text-base hover:scale-110 disabled:opacity-50',
              hasReacted(reaction.type)
                ? 'bg-orga-100 dark:bg-orga-900/40'
                : 'hover:bg-gray-100 dark:hover:bg-gray-700'
            ]"
            :title="reaction.label"
          >
            {{ reaction.emoji }}
          </button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
