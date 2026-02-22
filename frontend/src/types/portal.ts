// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Portal TypeScript Type Definitions
 *
 * Types for the Client Portal Vue components and API responses.
 */

/**
 * Client record from Orga Client DocType
 */
export interface PortalClient {
  name: string
  client_name: string
  company?: string
  email: string
  phone?: string
}

/**
 * Project as seen in the portal dashboard
 */
export interface PortalProject {
  name: string
  project_name: string
  description?: string
  status: ProjectStatus
  progress: number
  health_status?: HealthStatus
  start_date?: string
  end_date?: string
  // Computed fields
  task_count: number
  completed_tasks: number
  upcoming_milestone?: PortalUpcomingMilestone
  status_color: string
  health_color: string
}

/**
 * Detailed project view for portal project detail page
 */
export interface PortalProjectDetail extends PortalProject {
  budget?: number
  spent?: number
  project_manager?: string
  manager_name?: string
  days_remaining?: number | null
  days_overdue?: number | null
  budget_utilization: number
}

/**
 * Upcoming milestone preview shown on project cards
 */
export interface PortalUpcomingMilestone {
  milestone_name: string
  due_date?: string
}

/**
 * Full milestone record for project detail view
 */
export interface PortalMilestone {
  name: string
  milestone_name: string
  description?: string
  status: MilestoneStatus
  due_date?: string
  completion_date?: string
  is_overdue: boolean
  status_color: string
}

/**
 * Task counts by status
 */
export interface PortalTaskSummary {
  Open: number
  Working: number
  'Pending Review': number
  Completed: number
  Cancelled: number
  total: number
}

/**
 * Activity item for recent activity feed
 */
export interface PortalActivityItem {
  type: 'milestone' | 'task'
  title: string
  action: 'completed' | 'updated'
  timestamp: string
}

/**
 * Dashboard statistics
 */
export interface PortalStats {
  total_projects: number
  active_projects: number
  completed_projects: number
  on_hold_projects: number
  total_tasks: number
  completed_tasks: number
  overall_progress: number
}

/**
 * Response from get_portal_dashboard API
 */
export interface PortalDashboardResponse {
  client: PortalClient
  projects: PortalProject[]
  stats: PortalStats
}

/**
 * Response from get_portal_project API
 */
export interface PortalProjectResponse {
  project: PortalProjectDetail
  milestones: PortalMilestone[]
  task_summary: PortalTaskSummary
  recent_activity: PortalActivityItem[]
}

/**
 * Response from submit_support_request API
 */
export interface SupportRequestResponse {
  success: boolean
  message: string
  reference: string
}

/**
 * Project status values
 */
export type ProjectStatus = 'Planning' | 'Active' | 'On Hold' | 'Completed' | 'Cancelled'

/**
 * Health status values
 */
export type HealthStatus = 'Green' | 'Yellow' | 'Red' | 'Unknown'

/**
 * Milestone status values
 */
export type MilestoneStatus = 'Upcoming' | 'Completed' | 'Missed'

/**
 * Color mapping for project status
 */
export const PROJECT_STATUS_COLORS: Record<ProjectStatus, string> = {
  'Planning': 'bg-blue-100 text-blue-600',
  'Active': 'bg-green-100 text-green-600',
  'On Hold': 'bg-orange-100 text-orange-600',
  'Completed': 'bg-gray-100 text-gray-600',
  'Cancelled': 'bg-red-100 text-red-600'
}

/**
 * Color mapping for health status
 */
export const HEALTH_STATUS_COLORS: Record<HealthStatus, string> = {
  'Green': 'bg-green-100 text-green-600',
  'Yellow': 'bg-yellow-100 text-yellow-600',
  'Red': 'bg-red-100 text-red-600',
  'Unknown': 'bg-gray-100 text-gray-500'
}

/**
 * Color mapping for milestone status
 */
export const MILESTONE_STATUS_COLORS: Record<MilestoneStatus, string> = {
  'Upcoming': 'bg-blue-100 text-blue-600',
  'Completed': 'bg-green-100 text-green-600',
  'Missed': 'bg-red-100 text-red-600'
}
