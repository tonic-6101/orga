<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Breadcrumb.vue - Navigation breadcrumb trail

  Provides hierarchical navigation context.
  Can auto-generate from route or accept custom items.
-->
<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRoute } from 'vue-router'
import { Home, ChevronRight } from 'lucide-vue-next'
import OrgaIcon from './OrgaIcon.vue'
import { __ } from '@/composables/useTranslate'

export interface BreadcrumbItem {
  /** Display label */
  label: string
  /** Route path or name */
  to?: string
  /** Lucide icon name (resolved by OrgaIcon) */
  icon?: string
  /** Mark as current page (not clickable) */
  current?: boolean
}

interface Props {
  /** Custom breadcrumb items (overrides auto-generation) */
  items?: BreadcrumbItem[]
  /** Show home icon link */
  showHome?: boolean
  /** Home route path */
  homePath?: string
}

const props = withDefaults(defineProps<Props>(), {
  showHome: true,
  homePath: '/orga',
})

const route = useRoute()

// Route name to label mapping
const routeLabels: Record<string, string> = {
  'orga': __('Dashboard'),
  'activity': __('Activity'),
  'projects': __('Projects'),
  'contacts': __('People'),
  'people': __('People'),
  'schedule': __('Schedule'),
  'settings': __('Settings')
}

// Auto-generate breadcrumbs from route if items not provided
const breadcrumbs = computed((): BreadcrumbItem[] => {
  if (props.items) {
    return props.items
  }

  // Generate from route path
  const pathSegments = route.path.split('/').filter(Boolean)

  return pathSegments.map((segment, index) => {
    const isLast = index === pathSegments.length - 1
    const path = '/' + pathSegments.slice(0, index + 1).join('/')

    // Get label from mapping or format the segment
    let label = routeLabels[segment]
    if (!label) {
      // Format segment: capitalize, replace dashes with spaces
      label = segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }

    return {
      label,
      to: isLast ? undefined : path,
      current: isLast
    }
  })
})
</script>

<template>
  <nav
    :aria-label="__('Breadcrumb')"
    class="flex items-center gap-2 text-sm flex-wrap"
  >
    <!-- Home link -->
    <router-link
      v-if="showHome"
      :to="homePath"
      class="text-gray-500 dark:text-gray-400 hover:text-accent-600 dark:hover:text-accent-400 transition-colors"
      :aria-label="__('Home')"
    >
      <Home class="w-4 h-4" />
    </router-link>

    <!-- Breadcrumb items -->
    <template v-for="(item, index) in breadcrumbs" :key="index">
      <!-- Separator -->
      <ChevronRight
        class="w-3 h-3 text-gray-400 dark:text-gray-500"
        aria-hidden="true"
      />

      <!-- Breadcrumb link or text -->
      <router-link
        v-if="item.to && !item.current"
        :to="item.to"
        class="text-gray-500 dark:text-gray-400 hover:text-accent-600 dark:hover:text-accent-400 transition-colors inline-flex items-center gap-1.5"
      >
        <OrgaIcon
          v-if="item.icon"
          :name="item.icon"
          class="w-3 h-3"
        />
        {{ item.label }}
      </router-link>

      <span
        v-else
        class="text-gray-800 dark:text-gray-100 font-medium inline-flex items-center gap-1.5"
        :aria-current="item.current ? 'page' : undefined"
      >
        <OrgaIcon
          v-if="item.icon"
          :name="item.icon"
          class="w-3 h-3"
        />
        {{ item.label }}
      </span>
    </template>
  </nav>
</template>
