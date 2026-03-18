<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { DockLayout } from '/assets/dock/js/dock-navbar.esm.js'
import Sidebar from './components/layout/Sidebar.vue'
import PortalLayout from './components/layout/PortalLayout.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import { useSidebar } from './composables/useSidebar'
import { useTimer } from './composables/useTimer'
import { useCurrency } from './composables/useCurrency'

const route = useRoute()
const { collapsed, mobileOpen, toggle, closeMobile } = useSidebar()
const { loadActiveTimer } = useTimer()
const { loadCurrency } = useCurrency()

const isPortalLayout = computed(() => {
  return route.meta.layout === 'portal'
})

// Bridge: DockNavbar dispatches this event when sidebar toggle is clicked
function onDockToggle() { toggle() }

// Close mobile sidebar when clicking outside
function handleClickOutside(e: MouseEvent): void {
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
  window.addEventListener('dock:toggleSidebar', onDockToggle)
  loadActiveTimer()
  loadCurrency()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('dock:toggleSidebar', onDockToggle)
})
</script>

<template>
  <ToastContainer />

  <!-- Portal Layout (for Orga Client users) -->
  <PortalLayout v-if="isPortalLayout">
    <router-view />
  </PortalLayout>

  <!-- Default Layout (for internal users) -->
  <DockLayout v-else>
    <Sidebar
      :collapsed="collapsed"
      :mobile-open="mobileOpen"
      @close="closeMobile"
    />
    <main class="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-950 transition-colors">
      <router-view />
    </main>
  </DockLayout>
</template>
