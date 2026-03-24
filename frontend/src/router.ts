// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { createRouter, createWebHistory, type RouteRecordRaw, type Router, type RouteLocationNormalized, type NavigationGuardNext } from 'vue-router'
import { useAuth } from './composables/useAuth'
import { __ } from './composables/useTranslate'

// Page components - eager loaded for main navigation
import Dashboard from './pages/Dashboard.vue'
import Projects from './pages/Projects.vue'

// Dock shared pages — calendar, people, notifications, bookmarks rendered inside Orga's layout.
// Each route lazily loads its component from Dock's ESM bundle at navigation time.
const dockEsm = '/assets/dock/js/dock-navbar.esm.js'
const dockInstalled = !!(window as any).frappe?.boot?.dock?.installed

const dockSharedRoutes: RouteRecordRaw[] = dockInstalled ? [
  {
    path: '/orga/account',
    name: 'dock-account',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-account').component()),
    meta: { dockShared: true, title: 'My Account', layout: 'default' },
  },
  {
    path: '/orga/calendar',
    name: 'dock-calendar',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-calendar').component()),
    meta: { dockShared: true, title: 'Calendar', layout: 'default' },
  },
  {
    path: '/orga/people',
    name: 'dock-people',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-people').component()),
    meta: { dockShared: true, title: 'People', layout: 'default' },
  },
  {
    path: '/orga/people/:name',
    name: 'dock-person',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-person').component()),
    meta: { dockShared: true, title: 'Contact', layout: 'default' },
  },
  {
    path: '/orga/notifications',
    name: 'dock-notifications',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-notifications').component()),
    meta: { dockShared: true, title: 'Notifications', layout: 'default' },
  },
  {
    path: '/orga/bookmarks',
    name: 'dock-bookmarks',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-bookmarks').component()),
    meta: { dockShared: true, title: 'Bookmarks', layout: 'default' },
  },
  {
    path: '/orga/notes',
    name: 'dock-notes',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-notes').component()),
    meta: { dockShared: true, title: 'Notes', layout: 'default' },
  },
  {
    path: '/orga/activity',
    name: 'dock-activity',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-activity').component()),
    meta: { dockShared: true, title: 'Activity', layout: 'default' },
  },
  {
    path: '/orga/discussions',
    name: 'dock-discussions',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-discussions').component()),
    meta: { dockShared: true, title: 'Discussions', layout: 'default' },
  },
  {
    path: '/orga/discussions/:name',
    name: 'dock-discussion-detail',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-discussion-detail').component()),
    meta: { dockShared: true, title: 'Discussion', layout: 'default' },
  },
  {
    path: '/orga/bin',
    name: 'dock-bin',
    component: () => import(/* @vite-ignore */ dockEsm).then(m => m.dockSharedRoutes('/orga').find((r: any) => r.name === 'dock-bin').component()),
    meta: { dockShared: true, title: 'Bin', layout: 'default' },
  },
] : []

/**
 * Extended route meta for Orga
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    layout?: 'default' | 'portal' | 'guest'
    requiresRole?: string
    requiresAuth?: boolean
    dockShared?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  // Root redirect - will be handled by navigation guard based on role
  { path: '/', redirect: '/orga' },

  // ============================================
  // Internal App Routes (Orga User/Manager)
  // ============================================
  {
    path: '/orga',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard', layout: 'default' }
  },
  {
    path: '/orga/my-tasks',
    name: 'MyTasks',
    component: () => import('./pages/MyTasks.vue'),
    meta: { title: 'My Tasks', layout: 'default' }
  },
  {
    path: '/orga/projects',
    name: 'Projects',
    component: Projects,
    meta: { title: 'Projects', layout: 'default' }
  },
  {
    path: '/orga/projects/:id',
    name: 'ProjectDetail',
    component: () => import('./pages/ProjectDetail.vue'),
    props: true,
    meta: { title: 'Project Details', layout: 'default' }
  },
  // Legacy redirects — contacts now live in Dock People
  {
    path: '/orga/contacts',
    redirect: '/orga/people'
  },
  {
    path: '/orga/contacts/:id',
    redirect: '/orga/people'
  },
  {
    path: '/orga/resources',
    redirect: '/orga/people'
  },
  // Legacy redirect — old /orga/schedule URLs now go to Dock's shared calendar
  {
    path: '/orga/schedule',
    redirect: '/orga/calendar',
  },
  {
    path: '/orga/reports',
    name: 'Reports',
    component: () => import('./pages/Reports.vue'),
    meta: { title: 'Reports', layout: 'default' }
  },
  {
    path: '/orga/templates',
    name: 'Templates',
    component: () => import('./pages/Templates.vue'),
    meta: { title: 'Templates', layout: 'default' }
  },
  // Settings live in Dock unified settings hub (/dock/settings/app/orga)
  {
    path: '/orga/preferences',
    name: 'Preferences',
    component: () => import('./pages/Preferences.vue'),
    meta: { title: 'Preferences', layout: 'default' }
  },

  // ============================================
  // Guest Portal Routes (loaded inside Dock Guest Portal iframe, no auth)
  // ============================================
  {
    path: '/orga/guest/project/:name',
    name: 'GuestProjectStatus',
    component: () => import('./pages/guest/GuestProjectStatus.vue'),
    props: true,
    meta: {
      title: 'Project Status',
      layout: 'guest',
      requiresAuth: false
    }
  },

  // ============================================
  // Client Portal Routes (Orga Client)
  // ============================================
  {
    path: '/orga/portal',
    name: 'PortalDashboard',
    component: () => import('./pages/portal/PortalDashboard.vue'),
    meta: {
      title: 'Client Portal',
      layout: 'portal',
      requiresRole: 'Orga Client'
    }
  },
  {
    path: '/orga/portal/project/:id',
    name: 'PortalProjectDetail',
    component: () => import('./pages/portal/PortalProjectDetail.vue'),
    props: true,
    meta: {
      title: 'Project Details',
      layout: 'portal',
      requiresRole: 'Orga Client'
    }
  },
  {
    path: '/orga/portal/support',
    name: 'PortalSupport',
    component: () => import('./pages/portal/PortalSupport.vue'),
    meta: {
      title: 'Support',
      layout: 'portal',
      requiresRole: 'Orga Client'
    }
  },

  // ============================================
  // Legacy Portal Redirects
  // ============================================
  {
    path: '/orga_portal',
    redirect: '/orga/portal'
  },
  {
    path: '/orga_portal/project/:id',
    redirect: to => `/orga/portal/project/${to.params.id}`
  },
  {
    path: '/orga_portal/support',
    redirect: '/orga/portal/support'
  },

  // ============================================
  // Dock Shared Pages (Calendar, People, Notifications, Bookmarks)
  // ============================================
  ...dockSharedRoutes,

  // ============================================
  // 404 Catch-All (must be last)
  // ============================================
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('./pages/NotFound.vue'),
    meta: { title: 'Page Not Found', layout: 'default' }
  },
]

const router: Router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * Navigation guard for role-based access control
 */
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const { isLoggedIn, isGuest, hasRole, isOrgaClient, isInternalUser } = useAuth()

  // Allow public routes (none currently, but future-proofed)
  if (to.meta.requiresAuth === false) {
    return next()
  }

  // Redirect guests to login
  if (isGuest.value) {
    return next('/login')
  }

  // Check required role for portal routes
  if (to.meta.requiresRole) {
    if (!hasRole(to.meta.requiresRole)) {
      // User doesn't have required role
      if (isInternalUser.value) {
        // Internal user trying to access portal - redirect to main app
        return next('/orga')
      }
      // Client trying to access something they shouldn't - redirect to portal
      return next('/orga/portal')
    }
  }

  // Redirect clients away from internal routes
  // (Clients with ONLY Orga Client role should use portal)
  if (to.meta.layout !== 'portal' && to.path.startsWith('/orga')) {
    if (isOrgaClient.value && !isInternalUser.value) {
      return next('/orga/portal')
    }
  }

  // Root redirect based on role
  if (to.path === '/' || to.path === '/orga') {
    if (isOrgaClient.value && !isInternalUser.value) {
      return next('/orga/portal')
    }
  }

  next()
})

/**
 * Update document title on navigation
 */
router.afterEach((to: RouteLocationNormalized) => {
  const title = to.meta.title
  document.title = title ? `${__(title)} | Orga` : 'Orga'
})

export default router
