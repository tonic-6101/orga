<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  StatusBadge.vue - Accessible status badge with icon + color + text

  This component displays status information in a WCAG-compliant way:
  - Color alone is not used to convey information
  - Each status has a unique icon for colorblind users
  - Text label is always visible
  - Contrast ratios meet AA requirements
-->
<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  LockOpen, Hourglass, Eye, Check, X, Ban, Lock, Circle,
  CircleCheck, Calendar, Flag, FlagTriangleRight, TriangleAlert,
  Compass, Play, Pause, ArrowDown, Minus, ArrowUp, Flame,
} from 'lucide-vue-next'

type TaskStatus = 'Open' | 'In Progress' | 'Review' | 'Completed' | 'Cancelled'
type MilestoneStatus = 'Upcoming' | 'In Progress' | 'Completed' | 'Missed'
type ProjectStatus = 'Planning' | 'Active' | 'On Hold' | 'Completed' | 'Cancelled'
type PriorityLevel = 'Low' | 'Medium' | 'High' | 'Urgent'

interface Props {
  status: TaskStatus | MilestoneStatus | ProjectStatus | PriorityLevel | 'Blocked' | string
  type?: 'task' | 'milestone' | 'project' | 'priority' | 'blocked'
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'task',
  size: 'md',
  showIcon: true
})

interface StatusConfig {
  icon: Component
  bg: string
  text: string
  border: string
  darkBg: string
  darkText: string
  darkBorder: string
}

// Task status configuration (semantic colors)
const taskStatusConfig: Record<string, StatusConfig> = {
  'Open': {
    icon: LockOpen,
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900/30',
    darkText: 'dark:text-blue-300',
    darkBorder: 'dark:border-blue-700'
  },
  'In Progress': {
    icon: Hourglass,
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-300',
    darkBg: 'dark:bg-amber-900/30',
    darkText: 'dark:text-amber-300',
    darkBorder: 'dark:border-amber-700'
  },
  'Review': {
    icon: Eye,
    bg: 'bg-purple-100',
    text: 'text-purple-700',
    border: 'border-purple-300',
    darkBg: 'dark:bg-purple-900/30',
    darkText: 'dark:text-purple-300',
    darkBorder: 'dark:border-purple-700'
  },
  'Completed': {
    icon: Check,
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Cancelled': {
    icon: X,
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300',
    darkBg: 'dark:bg-gray-800',
    darkText: 'dark:text-gray-400',
    darkBorder: 'dark:border-gray-600'
  }
}

// Milestone status configuration
const milestoneStatusConfig: Record<string, StatusConfig> = {
  'Upcoming': {
    icon: Calendar,
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900/30',
    darkText: 'dark:text-blue-300',
    darkBorder: 'dark:border-blue-700'
  },
  'In Progress': {
    icon: Flag,
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-300',
    darkBg: 'dark:bg-amber-900/30',
    darkText: 'dark:text-amber-300',
    darkBorder: 'dark:border-amber-700'
  },
  'Completed': {
    icon: FlagTriangleRight,
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Missed': {
    icon: TriangleAlert,
    bg: 'bg-red-100',
    text: 'text-red-700',
    border: 'border-red-300',
    darkBg: 'dark:bg-red-900/30',
    darkText: 'dark:text-red-300',
    darkBorder: 'dark:border-red-700'
  }
}

// Project status configuration
const projectStatusConfig: Record<string, StatusConfig> = {
  'Planning': {
    icon: Compass,
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-300',
    darkBg: 'dark:bg-slate-800',
    darkText: 'dark:text-slate-300',
    darkBorder: 'dark:border-slate-600'
  },
  'Active': {
    icon: Play,
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'On Hold': {
    icon: Pause,
    bg: 'bg-yellow-100',
    text: 'text-yellow-700',
    border: 'border-yellow-300',
    darkBg: 'dark:bg-yellow-900/30',
    darkText: 'dark:text-yellow-300',
    darkBorder: 'dark:border-yellow-700'
  },
  'Completed': {
    icon: CircleCheck,
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Cancelled': {
    icon: Ban,
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300',
    darkBg: 'dark:bg-gray-800',
    darkText: 'dark:text-gray-400',
    darkBorder: 'dark:border-gray-600'
  }
}

// Priority configuration
const priorityConfig: Record<string, StatusConfig> = {
  'Low': {
    icon: ArrowDown,
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300',
    darkBg: 'dark:bg-gray-800',
    darkText: 'dark:text-gray-400',
    darkBorder: 'dark:border-gray-600'
  },
  'Medium': {
    icon: Minus,
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900',
    darkText: 'dark:text-blue-100',
    darkBorder: 'dark:border-blue-800'
  },
  'High': {
    icon: ArrowUp,
    bg: 'bg-orange-100',
    text: 'text-orange-700',
    border: 'border-orange-300',
    darkBg: 'dark:bg-orange-900',
    darkText: 'dark:text-orange-100',
    darkBorder: 'dark:border-orange-800'
  },
  'Urgent': {
    icon: Flame,
    bg: 'bg-red-100',
    text: 'text-red-700',
    border: 'border-red-300',
    darkBg: 'dark:bg-red-900',
    darkText: 'dark:text-red-100',
    darkBorder: 'dark:border-red-800'
  }
}

// Blocked status configuration
const blockedConfig: Record<string, StatusConfig> = {
  'Blocked': {
    icon: Lock,
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-300',
    darkBg: 'dark:bg-amber-900/30',
    darkText: 'dark:text-amber-300',
    darkBorder: 'dark:border-amber-700'
  }
}

// Default fallback config
const defaultConfig: StatusConfig = {
  icon: Circle,
  bg: 'bg-gray-100',
  text: 'text-gray-600',
  border: 'border-gray-300',
  darkBg: 'dark:bg-gray-800',
  darkText: 'dark:text-gray-400',
  darkBorder: 'dark:border-gray-600'
}

const config = computed((): StatusConfig => {
  const status = props.status

  switch (props.type) {
    case 'task':
      return taskStatusConfig[status] || defaultConfig
    case 'milestone':
      return milestoneStatusConfig[status] || defaultConfig
    case 'project':
      return projectStatusConfig[status] || defaultConfig
    case 'priority':
      return priorityConfig[status] || defaultConfig
    case 'blocked':
      return blockedConfig[status] || blockedConfig['Blocked']
    default:
      // Try to find in task status first, then others
      return taskStatusConfig[status]
        || milestoneStatusConfig[status]
        || projectStatusConfig[status]
        || priorityConfig[status]
        || blockedConfig[status]
        || defaultConfig
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs px-2 py-0.5'
    case 'lg':
      return 'text-base px-3 py-1'
    default:
      return 'text-sm px-2.5 py-0.5'
  }
})

const iconSizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-2.5 h-2.5'
    case 'lg':
      return 'w-4 h-4'
    default:
      return 'w-3 h-3'
  }
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 rounded-full border font-medium whitespace-nowrap',
      sizeClasses,
      config.bg,
      config.text,
      config.border,
      config.darkBg,
      config.darkText,
      config.darkBorder
    ]"
    role="status"
    :aria-label="__('Status: {0}', [status])"
  >
    <component
      v-if="showIcon"
      :is="config.icon"
      :class="iconSizeClass"
      aria-hidden="true"
    />
    <span>{{ status }}</span>
  </span>
</template>
