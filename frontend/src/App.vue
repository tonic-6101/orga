<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/layout/Sidebar.vue'
import Header from './components/layout/Header.vue'
import PortalLayout from './components/layout/PortalLayout.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import { useSidebar } from './composables/useSidebar'
import { useTimer } from './composables/useTimer'
import { useCurrency } from './composables/useCurrency'

const route = useRoute()
const { collapsed, mobileOpen, toggle, closeMobile } = useSidebar()
const { loadActiveTimer } = useTimer()
const { loadCurrency } = useCurrency()

/**
 * Check if current route should use the portal layout
 */
const isPortalLayout = computed(() => {
  return route.meta.layout === 'portal'
})

// Close mobile sidebar when clicking outside
const handleClickOutside = (e: MouseEvent): void => {
  if (mobileOpen.value) {
    const sidebar = document.querySelector('.orga-sidebar')
    const toggleBtn = document.querySelector('.sidebar-toggle')
    if (sidebar && !sidebar.contains(e.target as Node) && toggleBtn && !toggleBtn.contains(e.target as Node)) {
      closeMobile()
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadActiveTimer()
  loadCurrency()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <!-- Global Toast Notifications -->
  <ToastContainer />

  <!-- Portal Layout (for Orga Client users) -->
  <PortalLayout v-if="isPortalLayout">
    <router-view />
  </PortalLayout>

  <!-- Default Layout (for internal users) -->
  <div v-else class="h-screen flex flex-col bg-gray-100 dark:bg-gray-950 transition-colors">
    <!-- Header -->
    <Header @toggle-sidebar="toggle" />

    <!-- Main Layout -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <Sidebar
        :collapsed="collapsed"
        :mobile-open="mobileOpen"
        @close="closeMobile"
      />

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-950 transition-colors">
        <router-view />
      </main>
    </div>
  </div>
</template>
