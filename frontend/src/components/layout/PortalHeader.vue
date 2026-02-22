<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import UserMenu from '@/components/layout/UserMenu.vue'
import { useAuth } from '@/composables/useAuth'
import { __ } from '@/composables/useTranslate'

const route = useRoute()
const { user } = useAuth()

/**
 * Get welcome message based on current page
 */
const pageTitle = computed(() => {
  if (route.name === 'PortalDashboard') {
    return __('Welcome, {0}', [user.value?.full_name || __('Client')])
  }
  return route.meta.title as string || __('Client Portal')
})

/**
 * Show breadcrumb for non-dashboard pages
 */
const showBreadcrumb = computed(() => {
  return route.name !== 'PortalDashboard'
})
</script>

<template>
  <header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sticky top-0 z-50">
    <!-- Left: Logo + Title -->
    <div class="flex items-center gap-4">
      <router-link to="/orga/portal" class="flex items-center gap-2 font-bold text-lg no-underline">
        <svg class="w-6 h-6 text-orga-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 3h7v7H3V3zm11 0h7v7h-7V3zm0 11h7v7h-7v-7zM3 14h7v7H3v-7z"/>
        </svg>
        <span class="text-gray-800"><span class="text-orga-500">ORGA</span></span>
      </router-link>

      <!-- Breadcrumb navigation -->
      <nav v-if="showBreadcrumb" class="hidden sm:flex items-center gap-2 text-sm text-gray-500">
        <span class="text-gray-300">/</span>
        <router-link to="/orga/portal" class="hover:text-orga-500 no-underline text-gray-500">
          {{ __('Portal') }}
        </router-link>
        <span class="text-gray-300">/</span>
        <span class="text-gray-700">{{ pageTitle }}</span>
      </nav>
    </div>

    <!-- Right: Support + User -->
    <div class="flex items-center gap-4">
      <!-- Support Link -->
      <router-link
        to="/orga/portal/support"
        class="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-orga-500 hover:bg-gray-50 rounded transition-colors no-underline"
        :class="{ 'text-orga-500 bg-orga-50': route.name === 'PortalSupport' }"
      >
        <i class="fa-solid fa-headset"></i>
        <span class="hidden sm:inline">{{ __('Support') }}</span>
      </router-link>

      <!-- User Menu -->
      <UserMenu />
    </div>
  </header>
</template>
