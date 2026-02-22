<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, type Ref } from 'vue'
import { useRoute } from 'vue-router'
import { useActivityUnread } from '@/composables/useActivityUnread'
import { useUpdateChecker } from '@/composables/useUpdateChecker'
import { __ } from '@/composables/useTranslate'
import { version as appVersion } from '../../../package.json'

interface NavItem {
  path: string
  name: string
  icon: string
  badge?: Ref<number>
}

interface Props {
  collapsed: boolean
  mobileOpen: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const route = useRoute()
const { unreadCount } = useActivityUnread()
const { updateAvailable, updateInfo } = useUpdateChecker()

const navItems: NavItem[] = [
  { path: '/orga', name: __('Dashboard'), icon: 'fa-solid fa-gauge-high' },
  { path: '/orga/my-tasks', name: __('My Tasks'), icon: 'fa-solid fa-circle-check' },
  { path: '/orga/activity', name: __('Activity'), icon: 'fa-solid fa-comments', badge: unreadCount },
  { path: '/orga/projects', name: __('Projects'), icon: 'fa-solid fa-folder-open' },
  { path: '/orga/contacts', name: __('Contacts'), icon: 'fa-solid fa-users' },
  { path: '/orga/schedule', name: __('Schedule'), icon: 'fa-solid fa-calendar-days' },
  { path: '/orga/timesheets', name: __('Timesheets'), icon: 'fa-solid fa-stopwatch' },
  { path: '/orga/reports', name: __('Reports'), icon: 'fa-solid fa-chart-bar' },
  { path: '/orga/templates', name: __('Templates'), icon: 'fa-solid fa-copy' },
  { path: '/orga/settings', name: __('Settings'), icon: 'fa-solid fa-gear' },
]

const isActive = (item: NavItem): boolean => {
  if (item.path === '/orga') {
    return route.path === '/orga'
  }
  return route.path.startsWith(item.path)
}

const sidebarClasses = computed<string[]>(() => [
  'orga-sidebar bg-orga-500 flex-shrink-0 transition-all duration-200',
  props.collapsed ? 'w-16' : 'w-52',
  // Mobile styles
  'max-sm:fixed max-sm:left-0 max-sm:top-14 max-sm:h-[calc(100vh-3.5rem)] max-sm:z-40',
  props.mobileOpen ? 'max-sm:translate-x-0' : 'max-sm:-translate-x-full'
])

const navItemClasses = (item: NavItem): string[] => [
  'sidebar-item flex items-center no-underline transition-all duration-200 rounded-r-lg relative',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/50 focus-visible:ring-offset-2 focus-visible:ring-offset-orga-500',
  // Ensure minimum 44px touch target height
  'min-h-[44px]',
  props.collapsed
    ? 'justify-center px-2 py-3 mx-1'
    : 'gap-3 px-4 py-3 mr-2',
  isActive(item)
    ? 'bg-white/20 text-white font-semibold border-r-4 border-white'
    : 'text-white/90 hover:bg-white/10 hover:text-white'
]

const iconClasses = (item: NavItem): string[] => [
  item.icon,
  'transition-transform duration-200',
  props.collapsed ? 'text-xl' : 'w-5 text-center',
  isActive(item) ? 'scale-110' : 'group-hover:scale-105'
]
</script>

<template>
  <aside :class="sidebarClasses" class="flex flex-col">
    <nav class="py-3 flex-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="['group', ...navItemClasses(item)]"
        :title="props.collapsed ? item.name : ''"
        @click="emit('close')"
      >
        <i :class="iconClasses(item)"></i>
        <span v-if="!props.collapsed" class="flex-1">{{ item.name }}</span>
        <!-- Unread badge -->
        <span
          v-if="item.badge && item.badge.value > 0"
          :class="[
            'rounded-full bg-white text-orga-600 font-bold leading-none flex items-center justify-center',
            props.collapsed ? 'absolute top-1 right-1 w-4 h-4 text-[9px]' : 'ml-auto px-1.5 py-0.5 text-[10px] min-w-[18px] text-center'
          ]"
        >
          {{ item.badge.value > 99 ? '99+' : item.badge.value }}
        </span>
      </router-link>
    </nav>

    <!-- Footer: Edition, version, and links (AGPL v3 source code requirement) -->
    <div class="py-3 border-t border-orga-400">
      <!-- Edition & version -->
      <div v-if="!props.collapsed" class="px-4 pb-2">
        <div class="text-sm font-semibold text-white/80">Community Edition</div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-orga-200">v{{ appVersion }}</span>
          <router-link
            v-if="updateAvailable"
            to="/orga/settings"
            class="flex items-center gap-1 text-xs text-amber-300 hover:text-amber-200 transition-colors no-underline"
            :title="__('Update available: v{0}', [updateInfo?.latest_version || ''])"
            @click="emit('close')"
          >
            <i class="fa-solid fa-arrow-up text-[10px]"></i>
            <span>{{ __('Update') }}</span>
          </router-link>
        </div>
      </div>
      <!-- Collapsed: update dot -->
      <div v-if="props.collapsed && updateAvailable" class="flex justify-center pb-2">
        <router-link
          to="/orga/settings"
          class="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse block"
          :title="__('Update available')"
          @click="emit('close')"
        ></router-link>
      </div>
      <!-- Links -->
      <div :class="['flex items-center', props.collapsed ? 'justify-center gap-4 px-2' : 'gap-4 px-4']">
        <a
          href="https://github.com/tonic-6101/orga"
          target="_blank"
          rel="noopener noreferrer"
          class="text-orga-200 hover:text-white transition-colors"
          :title="__('Source Code')"
        >
          <i class="fa-brands fa-github" :class="props.collapsed ? 'text-xl' : 'text-base'"></i>
        </a>
        <a
          href="https://www.linkedin.com/in/tonic-frappe-solution-1642a0273/"
          target="_blank"
          rel="noopener noreferrer"
          class="text-orga-200 hover:text-white transition-colors"
          title="LinkedIn"
        >
          <i class="fa-brands fa-linkedin" :class="props.collapsed ? 'text-xl' : 'text-base'"></i>
        </a>
      </div>
    </div>
  </aside>

  <!-- Mobile overlay -->
  <div
    v-if="mobileOpen"
    class="fixed inset-0 bg-black/50 z-30 sm:hidden"
    @click="emit('close')"
  ></div>
</template>
