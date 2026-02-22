// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { createRouter, createWebHistory, type RouteRecordRaw, type Router, type RouteLocationNormalized, type NavigationGuardNext } from 'vue-router'
import { useAuth } from './composables/useAuth'
import { __ } from './composables/useTranslate'

// Page components - eager loaded for main navigation
import Dashboard from './pages/Dashboard.vue'
import Activity from './pages/Activity.vue'
import Projects from './pages/Projects.vue'
import Contacts from './pages/Contacts.vue'
import Schedule from './pages/Schedule.vue'
import Settings from './pages/Settings.vue'

/**
 * Extended route meta for Orga
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    layout?: 'default' | 'portal'
    requiresRole?: string
    requiresAuth?: boolean
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
    path: '/orga/activity',
    name: 'Activity',
    component: Activity,
    meta: { title: 'Activity', layout: 'default' }
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
  {
    path: '/orga/contacts',
    name: 'Contacts',
    component: Contacts,
    meta: { title: 'Contacts', layout: 'default' }
  },
  {
    path: '/orga/contacts/:id',
    name: 'ContactDetail',
    component: () => import('./pages/ContactDetail.vue'),
    props: true,
    meta: { title: 'Contact Details', layout: 'default' }
  },
  {
    path: '/orga/resources',
    redirect: '/orga/contacts'
  },
  {
    path: '/orga/schedule',
    name: 'Schedule',
    component: Schedule,
    meta: { title: 'Schedule', layout: 'default' }
  },
  {
    path: '/orga/calendar',
    redirect: '/orga/schedule'
  },
  {
    path: '/orga/timesheets',
    name: 'Timesheets',
    component: () => import('./pages/Timesheets.vue'),
    meta: { title: 'Timesheets', layout: 'default' }
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
  {
    path: '/orga/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: 'Settings', layout: 'default' }
  },
  {
    path: '/orga/preferences',
    name: 'Preferences',
    component: () => import('./pages/Preferences.vue'),
    meta: { title: 'Preferences', layout: 'default' }
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
