// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Portal API Composable
 *
 * Provides typed API functions for the Client Portal.
 */

import { ref, type Ref } from 'vue'
import { frappeRequest } from 'frappe-ui'
import type {
  PortalDashboardResponse,
  PortalProjectResponse,
  PortalProject,
  SupportRequestResponse
} from '@/types/portal'

/**
 * Return type for usePortalApi composable
 */
export interface UsePortalApiReturn {
  /** Loading state */
  loading: Ref<boolean>
  /** Error message */
  error: Ref<string | null>
  /** Get portal dashboard data */
  getPortalDashboard: () => Promise<PortalDashboardResponse>
  /** Get detailed project info */
  getPortalProject: (projectName: string) => Promise<PortalProjectResponse>
  /** Get list of client's projects */
  getClientProjects: () => Promise<PortalProject[]>
  /** Submit a support request */
  submitSupportRequest: (
    subject: string,
    message: string,
    project?: string
  ) => Promise<SupportRequestResponse>
}

/**
 * Portal API composable
 *
 * @example
 * ```vue
 * <script setup lang="ts">
 * import { usePortalApi } from '@/composables/usePortalApi'
 *
 * const { getPortalDashboard, loading, error } = usePortalApi()
 *
 * onMounted(async () => {
 *   const data = await getPortalDashboard()
 *   console.log(data.projects)
 * })
 * </script>
 * ```
 */
export function usePortalApi(): UsePortalApiReturn {
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Make an API call with loading and error handling
   */
  async function call<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
    loading.value = true
    error.value = null

    try {
      const response = await frappeRequest({
        url: `/api/method/${method}`,
        params: args
      })
      return response as T
    } catch (e) {
      const message = e instanceof Error ? e.message : 'An error occurred'
      error.value = message
      throw e
    } finally {
      loading.value = false
    }
  }

  /**
   * Get portal dashboard data
   *
   * Returns client info, projects list, and summary statistics.
   */
  async function getPortalDashboard(): Promise<PortalDashboardResponse> {
    return call<PortalDashboardResponse>('orga.orga.api.portal.get_portal_dashboard')
  }

  /**
   * Get detailed project info for portal view
   *
   * @param projectName - Project document name (e.g., ORG-2026-0001)
   */
  async function getPortalProject(projectName: string): Promise<PortalProjectResponse> {
    return call<PortalProjectResponse>('orga.orga.api.portal.get_portal_project', {
      project_name: projectName
    })
  }

  /**
   * Get list of client's projects
   *
   * Returns simplified project list for dropdown selection.
   */
  async function getClientProjects(): Promise<PortalProject[]> {
    return call<PortalProject[]>('orga.orga.api.portal.get_client_projects')
  }

  /**
   * Submit a support request
   *
   * Creates a Communication document in Frappe.
   *
   * @param subject - Request subject line
   * @param message - Request message body
   * @param project - Optional project reference
   */
  async function submitSupportRequest(
    subject: string,
    message: string,
    project?: string
  ): Promise<SupportRequestResponse> {
    return call<SupportRequestResponse>('orga.orga.api.portal.submit_support_request', {
      subject,
      message,
      project: project || null
    })
  }

  return {
    loading,
    error,
    getPortalDashboard,
    getPortalProject,
    getClientProjects,
    submitSupportRequest
  }
}
