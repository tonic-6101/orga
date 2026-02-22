<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import { __ } from '@/composables/useTranslate'

const router = useRouter()
const { mode: themeMode, isDark, setMode: setThemeMode } = useTheme()

const isOpen = ref<boolean>(false)
const menuRef = ref<HTMLElement | null>(null)

interface UserInfo {
  name: string
  email: string
  initial: string
  avatar: string | null
}

interface MenuItem {
  label?: string
  icon?: string
  to?: string
  action?: string
  divider?: boolean
  danger?: boolean
  isThemeToggle?: boolean
}

const user = computed<UserInfo>(() => {
  const session = (window as Window & { frappe?: { boot?: { user?: Record<string, string> } } }).frappe?.boot?.user || {}
  const name = session.full_name || session.name || 'User'
  return {
    name,
    email: session.email || '',
    initial: name[0]?.toUpperCase() || 'U',
    avatar: session.user_image || null
  }
})

const menuItems: MenuItem[] = [
  { label: __('My Assignments'), icon: 'fa-clipboard-list', to: '/orga/projects' },
  { label: __('My Schedule'), icon: 'fa-calendar', to: '/orga/schedule' },
  { label: __('Preferences'), icon: 'fa-sliders', to: '/orga/preferences' },
  { isThemeToggle: true },
  { divider: true },
  { label: __('Logout'), icon: 'fa-right-from-bracket', action: 'logout', danger: true }
]

function toggleMenu(): void {
  isOpen.value = !isOpen.value
}

function handleSelect(item: MenuItem): void {
  isOpen.value = false
  if (item.to) {
    router.push(item.to)
  } else if (item.action === 'logout') {
    logout()
  }
}

async function logout(): Promise<void> {
  try {
    await fetch('/api/method/logout', { method: 'POST' })
    window.location.href = '/login'
  } catch (e) {
    console.error('Logout failed:', e)
    // Force redirect even on error
    window.location.href = '/login'
  }
}

function handleClickOutside(e: MouseEvent): void {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

function handleKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="menuRef" class="relative user-menu">
    <!-- Avatar Trigger -->
    <button
      @click="toggleMenu"
      class="w-9 h-9 rounded-full overflow-hidden cursor-pointer focus:outline-none focus:ring-2 focus:ring-orga-500 focus:ring-offset-2"
      :title="user.name"
      aria-haspopup="true"
      :aria-expanded="isOpen"
    >
      <img
        v-if="user.avatar"
        :src="user.avatar"
        :alt="user.name"
        class="w-full h-full object-cover"
      />
      <div
        v-else
        class="w-full h-full bg-orga-500 text-white flex items-center justify-center font-semibold text-sm"
      >
        {{ user.initial }}
      </div>
    </button>

    <!-- Dropdown Menu -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50"
        role="menu"
      >
        <!-- User Info Header -->
        <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
          <p class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{{ user.name }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ user.email }}</p>
        </div>

        <!-- Menu Items -->
        <div class="py-1">
          <template v-for="(item, index) in menuItems" :key="index">
            <!-- Divider -->
            <div v-if="item.divider" class="border-t border-gray-100 dark:border-gray-700 my-1"></div>

            <!-- Theme Selector -->
            <div
              v-else-if="item.isThemeToggle"
              class="px-4 py-3"
              @click.stop
            >
              <div class="flex items-center gap-2 mb-3">
                <i :class="['fa-solid w-4 text-center', isDark ? 'fa-moon' : 'fa-sun']" class="text-gray-500 dark:text-gray-400"></i>
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{{ __('Theme') }}</span>
              </div>
              <div class="flex gap-1 bg-gray-100 dark:bg-gray-900 rounded-lg p-1" role="radiogroup" :aria-label="__('Theme preference')">
                <button
                  @click="setThemeMode('auto')"
                  :class="[
                    'flex-1 px-3 py-2 text-xs font-medium rounded transition-colors',
                    themeMode === 'auto'
                      ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  ]"
                  role="radio"
                  :aria-checked="themeMode === 'auto'"
                >
                  {{ __('System') }}
                </button>
                <button
                  @click="setThemeMode('light')"
                  :class="[
                    'flex-1 px-3 py-2 text-xs font-medium rounded transition-colors',
                    themeMode === 'light'
                      ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  ]"
                  role="radio"
                  :aria-checked="themeMode === 'light'"
                >
                  {{ __('Light') }}
                </button>
                <button
                  @click="setThemeMode('dark')"
                  :class="[
                    'flex-1 px-3 py-2 text-xs font-medium rounded transition-colors',
                    themeMode === 'dark'
                      ? 'bg-orga-500 text-white'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  ]"
                  role="radio"
                  :aria-checked="themeMode === 'dark'"
                >
                  {{ __('Dark') }}
                </button>
              </div>
            </div>

            <!-- Regular Menu Item -->
            <button
              v-else
              @click="handleSelect(item)"
              :class="[
                'w-full px-4 py-2 text-sm text-left flex items-center gap-3 transition-colors',
                item.danger
                  ? 'text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20'
                  : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700'
              ]"
              role="menuitem"
            >
              <i :class="['fa-solid w-4 text-center', item.icon]"></i>
              <span>{{ item.label }}</span>
            </button>
          </template>
        </div>
      </div>
    </Transition>
  </div>
</template>
