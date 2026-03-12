<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/layout/Sidebar.vue'
import PortalLayout from './components/layout/PortalLayout.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import { useSidebar } from './composables/useSidebar'
import { useTimer } from './composables/useTimer'
import { useCurrency } from './composables/useCurrency'

// Use DockNavbar when Dock is installed; fall back to own Header otherwise
const dockInstalled = !!(window as any).frappe?.boot?.dock?.installed
const NavbarComponent = dockInstalled
  ? defineAsyncComponent(() =>
      import('/assets/dock/js/dock-navbar.esm.js').then((m: any) => m.DockNavbar)
    )
  : defineAsyncComponent(() => import('./components/layout/Header.vue'))

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
    <!-- Navbar: DockNavbar when Dock installed, own Header as fallback -->
    <NavbarComponent @toggle-sidebar="toggle" />

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
