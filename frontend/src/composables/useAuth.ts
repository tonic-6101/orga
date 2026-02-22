// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Authentication composable for Orga
 *
 * Provides access to user session, role checking, and authentication utilities.
 * Uses Frappe's boot data injected into window.frappe.
 */

import { computed, type ComputedRef } from 'vue'

/**
 * Frappe user session data
 */
export interface FrappeUser {
  name: string
  email: string
  full_name: string
  user_image?: string
}

/**
 * Return type for useAuth composable
 */
export interface UseAuthReturn {
  /** Current user data */
  user: ComputedRef<FrappeUser | null>
  /** User's roles array */
  roles: ComputedRef<string[]>
  /** Whether user is logged in (not Guest) */
  isLoggedIn: ComputedRef<boolean>
  /** Whether user is Guest */
  isGuest: ComputedRef<boolean>
  /** Check if user has a specific role */
  hasRole: (role: string) => boolean
  /** Check if user has any of the specified roles */
  hasAnyRole: (roles: string[]) => boolean
  /** Whether user has Orga Client role */
  isOrgaClient: ComputedRef<boolean>
  /** Whether user has Orga User role */
  isOrgaUser: ComputedRef<boolean>
  /** Whether user has Orga Manager role */
  isOrgaManager: ComputedRef<boolean>
  /** Whether user has System Manager role */
  isSystemManager: ComputedRef<boolean>
  /** Whether user is an internal user (Orga User or Manager) */
  isInternalUser: ComputedRef<boolean>
  /** Logout and redirect to login page */
  logout: () => Promise<void>
}

/**
 * Extended window type with Frappe globals
 */
interface FrappeWindow extends Window {
  frappe?: {
    boot?: {
      user?: Record<string, string>
      user_roles?: string[]
    }
    csrf_token?: string
  }
}

/**
 * Get Frappe globals from window
 */
function getFrappe(): FrappeWindow['frappe'] {
  return (window as FrappeWindow).frappe
}

/**
 * Authentication composable
 *
 * @example
 * ```vue
 * <script setup lang="ts">
 * import { useAuth } from '@/composables/useAuth'
 *
 * const { user, isOrgaClient, hasRole, logout } = useAuth()
 *
 * // Check role
 * if (hasRole('Orga Manager')) {
 *   // Show admin controls
 * }
 *
 * // Use computed for reactive checks
 * const showPortal = computed(() => isOrgaClient.value && !isInternalUser.value)
 * </script>
 * ```
 */
export function useAuth(): UseAuthReturn {
  /**
   * Current user data from Frappe boot
   * Note: getFrappe() is called inside computed to handle late initialization
   */
  const user = computed<FrappeUser | null>(() => {
    const frappe = getFrappe()
    const bootUser = frappe?.boot?.user
    if (!bootUser) return null

    return {
      name: bootUser.name || 'Guest',
      email: bootUser.email || '',
      full_name: bootUser.full_name || bootUser.name || 'Guest',
      user_image: bootUser.user_image || undefined
    }
  })

  /**
   * User's roles from Frappe boot
   */
  const roles = computed<string[]>(() => {
    const frappe = getFrappe()
    return frappe?.boot?.user_roles || []
  })

  /**
   * Whether user is logged in (not Guest)
   */
  const isLoggedIn = computed(() => {
    return user.value !== null && user.value.name !== 'Guest'
  })

  /**
   * Whether user is Guest
   */
  const isGuest = computed(() => {
    return !user.value || user.value.name === 'Guest'
  })

  /**
   * Check if user has a specific role
   */
  function hasRole(role: string): boolean {
    return roles.value.includes(role)
  }

  /**
   * Check if user has any of the specified roles
   */
  function hasAnyRole(checkRoles: string[]): boolean {
    return checkRoles.some(role => hasRole(role))
  }

  /**
   * Whether user has Orga Client role
   */
  const isOrgaClient = computed(() => hasRole('Orga Client'))

  /**
   * Whether user has Orga User role
   */
  const isOrgaUser = computed(() => hasRole('Orga User'))

  /**
   * Whether user has Orga Manager role
   */
  const isOrgaManager = computed(() => hasRole('Orga Manager'))

  /**
   * Whether user has System Manager role
   */
  const isSystemManager = computed(() => hasRole('System Manager'))

  /**
   * Whether user is an internal user (Orga User, Manager, or System Manager)
   * Internal users can access the main Orga app, not just the portal
   */
  const isInternalUser = computed(() => {
    return isOrgaUser.value || isOrgaManager.value || isSystemManager.value
  })

  /**
   * Logout and redirect to login page
   */
  async function logout(): Promise<void> {
    try {
      const frappe = getFrappe()
      await fetch('/api/method/logout', {
        method: 'POST',
        headers: {
          'X-Frappe-CSRF-Token': frappe?.csrf_token || ''
        }
      })
    } catch (e) {
      console.error('Logout error:', e)
    }
    window.location.href = '/login'
  }

  return {
    user,
    roles,
    isLoggedIn,
    isGuest,
    hasRole,
    hasAnyRole,
    isOrgaClient,
    isOrgaUser,
    isOrgaManager,
    isSystemManager,
    isInternalUser,
    logout
  }
}
