<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
// @ts-ignore — served by Dock's built assets
import { DockLayout, DockSidebarShell } from '/assets/dock/js/dock-navbar.esm.js'
import {
  LayoutDashboard, CircleCheckBig, FolderOpen, BarChart3, Copy, Linkedin,
} from 'lucide-vue-next'
import PortalLayout from './components/layout/PortalLayout.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import { useUpdateChecker } from '@/composables/useUpdateChecker'
import { __ } from '@/composables/useTranslate'
const appVersion: string = __APP_VERSION__

const route = useRoute()
const { updateAvailable } = useUpdateChecker()

const isPortalLayout = computed(() => route.meta.layout === 'portal')
const isGuestLayout = computed(() => route.meta.layout === 'guest')

const navItems = [
  { key: 'dashboard', label: __('Dashboard'),  icon: LayoutDashboard, path: '/orga',           exact: true },
  { key: 'tasks',     label: __('My Tasks'),    icon: CircleCheckBig,  path: '/orga/my-tasks' },
  { key: 'projects',  label: __('Projects'),    icon: FolderOpen,      path: '/orga/projects' },
  { key: 'reports',   label: __('Reports'),     icon: BarChart3,       path: '/orga/reports' },
  { key: 'templates', label: __('Templates'),   icon: Copy,            path: '/orga/templates' },
]

const footer = computed(() => ({
  edition: __('Community Edition'),
  version: appVersion,
  sourceUrl: 'https://github.com/tonic-6101/orga',
  updateAvailable: updateAvailable.value,
  updateUrl: '/dock/settings/app/orga',
  links: [
    { label: 'LinkedIn', url: 'https://www.linkedin.com/in/tonic-s-solutions-1642a0273/', icon: Linkedin },
  ],
}))
</script>

<template>
  <ToastContainer />

  <!-- Guest Layout (inside Dock Guest Portal iframe — bare, no chrome) -->
  <router-view v-if="isGuestLayout" />

  <!-- Portal Layout (for Orga Client users) -->
  <PortalLayout v-else-if="isPortalLayout">
    <router-view />
  </PortalLayout>

  <!-- Default Layout (for internal users) -->
  <DockLayout v-else>
    <DockSidebarShell
      color="#018137"
      :items="navItems"
      :footer="footer"
      aria-label="Orga navigation"
    />
    <main class="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-950 transition-colors">
      <router-view />
    </main>
  </DockLayout>
</template>
