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
import { computed } from 'vue'

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
  icon: string
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
    icon: 'fa-lock-open',
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900/30',
    darkText: 'dark:text-blue-300',
    darkBorder: 'dark:border-blue-700'
  },
  'In Progress': {
    icon: 'fa-hourglass-half',
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-300',
    darkBg: 'dark:bg-amber-900/30',
    darkText: 'dark:text-amber-300',
    darkBorder: 'dark:border-amber-700'
  },
  'Review': {
    icon: 'fa-eye',
    bg: 'bg-purple-100',
    text: 'text-purple-700',
    border: 'border-purple-300',
    darkBg: 'dark:bg-purple-900/30',
    darkText: 'dark:text-purple-300',
    darkBorder: 'dark:border-purple-700'
  },
  'Completed': {
    icon: 'fa-check',
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Cancelled': {
    icon: 'fa-xmark',
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
    icon: 'fa-calendar',
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900/30',
    darkText: 'dark:text-blue-300',
    darkBorder: 'dark:border-blue-700'
  },
  'In Progress': {
    icon: 'fa-flag',
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-300',
    darkBg: 'dark:bg-amber-900/30',
    darkText: 'dark:text-amber-300',
    darkBorder: 'dark:border-amber-700'
  },
  'Completed': {
    icon: 'fa-flag-checkered',
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Missed': {
    icon: 'fa-triangle-exclamation',
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
    icon: 'fa-compass-drafting',
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    border: 'border-slate-300',
    darkBg: 'dark:bg-slate-800',
    darkText: 'dark:text-slate-300',
    darkBorder: 'dark:border-slate-600'
  },
  'Active': {
    icon: 'fa-play',
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'On Hold': {
    icon: 'fa-pause',
    bg: 'bg-yellow-100',
    text: 'text-yellow-700',
    border: 'border-yellow-300',
    darkBg: 'dark:bg-yellow-900/30',
    darkText: 'dark:text-yellow-300',
    darkBorder: 'dark:border-yellow-700'
  },
  'Completed': {
    icon: 'fa-circle-check',
    bg: 'bg-green-100',
    text: 'text-green-700',
    border: 'border-green-300',
    darkBg: 'dark:bg-green-900/30',
    darkText: 'dark:text-green-300',
    darkBorder: 'dark:border-green-700'
  },
  'Cancelled': {
    icon: 'fa-ban',
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
    icon: 'fa-arrow-down',
    bg: 'bg-gray-100',
    text: 'text-gray-600',
    border: 'border-gray-300',
    darkBg: 'dark:bg-gray-800',
    darkText: 'dark:text-gray-400',
    darkBorder: 'dark:border-gray-600'
  },
  'Medium': {
    icon: 'fa-minus',
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-300',
    darkBg: 'dark:bg-blue-900',
    darkText: 'dark:text-blue-100',
    darkBorder: 'dark:border-blue-800'
  },
  'High': {
    icon: 'fa-arrow-up',
    bg: 'bg-orange-100',
    text: 'text-orange-700',
    border: 'border-orange-300',
    darkBg: 'dark:bg-orange-900',
    darkText: 'dark:text-orange-100',
    darkBorder: 'dark:border-orange-800'
  },
  'Urgent': {
    icon: 'fa-fire',
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
    icon: 'fa-lock',
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
  icon: 'fa-circle',
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
      return 'text-[10px]'
    case 'lg':
      return 'text-sm'
    default:
      return 'text-xs'
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
    <i
      v-if="showIcon"
      :class="['fa-solid', config.icon, iconSizeClass]"
      aria-hidden="true"
    ></i>
    <span>{{ status }}</span>
  </span>
</template>
