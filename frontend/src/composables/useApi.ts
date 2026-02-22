// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * Orga API Composables
 *
 * Provides Vue composables for interacting with the Orga backend API.
 * Uses frappe-ui's frappeRequest for API calls.
 */

import { ref, type Ref } from 'vue'
import { frappeRequest } from 'frappe-ui'
import type {
  OrgaProject,
  OrgaTask,
  OrgaContact,
  OrgaAssignment,
  OrgaEvent,
  OrgaTimeLog,
  TrackingContext,
  TodayTimeSummary,
  OrgaMilestone,
  OrgaSettings,
  OrgaTaskChecklist,
  OrgaTaskComment,
  OrgaTaskDependency,
  TaskDependency,
  DependencyType,
  OrgaContactSkill,
  OrgaNotification,
  NotificationFilters,
  DashboardStats,
  ProjectHealth,
  HealthOverview,
  ActivityItem,
  ActivityNote,
  ActivityDetails,
  ActivityComment,
  ActivityCommentsResponse,
  MentionUser,
  ReactionResponse,
  RSVPUpdateResponse,
  EventRSVPInfo,
  CalendarEvent,
  ProjectSummaryReport,
  ContactUtilizationReport,
  TaskCompletionReport,
  BudgetTrackingReport,
  MilestoneReport,
  ProjectFilters,
  TaskFilters,
  ContactFilters,
  EventFilters,
  TimeLogFilters,
  ProficiencyLevel,
  RsvpStatus,
  NoteType,
  NoteVisibility,
  DueDiligenceNote,
  DueDiligenceNotesResponse,
  ComplianceStatus,
  RelatedDocument,
  OrgaFileAttachment,
  OrgaDefect,
  DefectFilters,
  ContactStats,
  OrgaProjectTemplate,
  TemplateFilters,
  TemplateData,
} from '@/types/orga'

// ============================================
// Base API Composable
// ============================================

interface UseApiReturn {
  call: <T>(method: string, args?: Record<string, unknown>) => Promise<T>
  loading: Ref<boolean>
  error: Ref<string | null>
}

/**
 * Base API wrapper composable
 * Provides loading state, error handling, and the call method
 */
export function useApi(): UseApiReturn {
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  /**
   * Call a Frappe whitelisted method
   */
  async function call<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
    loading.value = true
    error.value = null

    try {
      const response = await frappeRequest({
        url: '/api/method/' + method,
        params: args
      })
      return response as T
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'An error occurred'
      error.value = errorMessage
      console.error(`API Error [${method}]:`, e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return { call, loading, error }
}

// ============================================
// Project API
// ============================================

interface ProjectTeamMember {
  user: string
  full_name: string
  user_image?: string
  is_manager?: boolean
}

interface ProjectDocument {
  name: string
  file_name: string
  file_url: string
  file_size: number
  file_type?: string
  attached_to_name?: string
  is_private?: number
  creation?: string
  owner?: string
}

interface ProjectDetailResponse {
  project: OrgaProject
  tasks: OrgaTask[]
  milestones: OrgaMilestone[]
  team_members?: ProjectTeamMember[]
  documents?: ProjectDocument[]
  task_attachments?: ProjectDocument[]
}

interface UseProjectApiReturn extends UseApiReturn {
  getProjects: (filters?: ProjectFilters) => Promise<{ projects: OrgaProject[]; total: number }>
  getProject: (name: string) => Promise<ProjectDetailResponse>
  createProject: (data: Partial<OrgaProject>) => Promise<{ name: string }>
  updateProject: (name: string, data: Partial<OrgaProject>) => Promise<{ name: string; modified: string }>
  deleteProject: (name: string) => Promise<{ success: boolean }>
  getProjectStats: (name?: string | null) => Promise<DashboardStats>
  getCriticalPath: (projectName: string) => Promise<{ critical_tasks: string[]; task_floats: Record<string, number> }>
}

/**
 * Project API composable
 */
export function useProjectApi(): UseProjectApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getProjects: (filters: ProjectFilters = {}) =>
      call<{ projects: OrgaProject[]; total: number }>('orga.orga.api.project.get_projects', filters),

    getProject: (name: string) =>
      call<ProjectDetailResponse>('orga.orga.api.project.get_project', { name }),

    createProject: (data: Partial<OrgaProject>) =>
      call<{ name: string }>('orga.orga.api.project.create_project', { data: JSON.stringify(data) }),

    updateProject: (name: string, data: Partial<OrgaProject>) =>
      call<{ name: string; modified: string }>('orga.orga.api.project.update_project', { name, data: JSON.stringify(data) }),

    deleteProject: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.project.delete_project', { name }),

    getProjectStats: (name: string | null = null) =>
      call<DashboardStats>('orga.orga.api.project.get_project_stats', { name }),

    getCriticalPath: (projectName: string) =>
      call<{ critical_tasks: string[]; task_floats: Record<string, number> }>('orga.orga.api.project.get_critical_path', { project_name: projectName })
  }
}

// ============================================
// Task API
// ============================================

interface UseTaskApiReturn extends UseApiReturn {
  getTasks: (filters?: TaskFilters) => Promise<OrgaTask[]>
  getTask: (name: string) => Promise<OrgaTask>
  createTask: (data: Partial<OrgaTask>) => Promise<{ name: string }>
  updateTask: (name: string, data: Partial<OrgaTask>) => Promise<{ name: string; modified: string }>
  deleteTask: (name: string) => Promise<{ success: boolean }>
  updateStatus: (name: string, status: string) => Promise<{ success: boolean }>
  getTasksByStatus: (project: string) => Promise<Record<string, OrgaTask[]>>
  getTaskGroups: (project: string) => Promise<string[]>
  getGroupDependencyStatus: (project: string, groupName: string) => Promise<{ total: number; completed: number; incomplete: number; is_complete: boolean; tasks: Array<{ name: string; subject: string; status: string }> }>
  getMyTasks: (filters?: { status?: string | null; priority?: string | null; project?: string | null; search?: string | null; limit?: number; offset?: number; include_completed?: boolean; scope?: 'assigned' | 'my_projects' | 'all' }) => Promise<{ tasks: OrgaTask[]; total: number }>
  promoteChecklistToTask: (taskName: string, itemName: string) => Promise<{ name: string; subject: string }>
  bulkUpdateStatus: (tasks: string[], status: string) => Promise<{ success: boolean; updated: number }>
  reorderTasks: (project: string, taskId: string, newIndex: number) => Promise<{ success: boolean; updated_tasks: string[]; new_order: string[] }>
  // Checklist operations
  getChecklist: (taskName: string) => Promise<OrgaTaskChecklist[]>
  addChecklistItem: (taskName: string, title: string) => Promise<OrgaTaskChecklist>
  toggleChecklistItem: (taskName: string, itemName: string) => Promise<{ success: boolean }>
  deleteChecklistItem: (taskName: string, itemName: string) => Promise<{ success: boolean }>
  // Comment operations
  getComments: (taskName: string) => Promise<OrgaTaskComment[]>
  addComment: (taskName: string, content: string) => Promise<OrgaTaskComment>
  deleteComment: (taskName: string, commentName: string) => Promise<{ success: boolean }>
  // Dependency operations
  getDependencies: (taskName: string) => Promise<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>
  addDependency: (taskName: string, dependsOn: string, dependencyType?: DependencyType, lagDays?: number) => Promise<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>
  updateDependency: (dependencyName: string, dependencyType?: DependencyType, lagDays?: number) => Promise<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>
  removeDependency: (dependencyName: string) => Promise<{ success: boolean }>
  // Cascade / auto-schedule operations
  previewCascade: (taskName: string, newStartDate?: string, newEndDate?: string) => Promise<{ affected_tasks: Array<{ task_id: string; task_name: string; status: string; field: string; old_value: string | null; new_value: string | null; old_end_date: string | null; new_end_date: string | null; days_shift: number; dependency_type: string; lag_days: number }>; total_affected: number }>
  applyCascade: (taskName: string, newStartDate?: string, newEndDate?: string, changes?: string) => Promise<{ success: boolean; updated_tasks: string[]; total_updated: number }>
  rescheduleDependents: (taskName: string, oldStartDate?: string, oldEndDate?: string) => Promise<{ success: boolean; mode: string; updated_tasks: string[]; total_updated?: number; cascade_preview?: Array<{ task_id: string; task_name: string; days_shift: number }>; total_affected?: number }>
  // Attachment operations
  getAttachments: (taskName: string) => Promise<OrgaFileAttachment[]>
  deleteAttachment: (taskName: string, fileName: string) => Promise<{ success: boolean }>
}

/**
 * Task API composable
 */
export function useTaskApi(): UseTaskApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getTasks: (filters: TaskFilters = {}) =>
      call<OrgaTask[]>('orga.orga.api.task.get_tasks', filters),

    getTask: (name: string) =>
      call<OrgaTask>('orga.orga.api.task.get_task', { name }),

    createTask: (data: Partial<OrgaTask>) =>
      call<{ name: string }>('orga.orga.api.task.create_task', { data: JSON.stringify(data) }),

    updateTask: (name: string, data: Partial<OrgaTask>) =>
      call<{ name: string; modified: string }>('orga.orga.api.task.update_task', { name, data: JSON.stringify(data) }),

    deleteTask: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.task.delete_task', { name }),

    updateStatus: (name: string, status: string) =>
      call<{ success: boolean }>('orga.orga.api.task.update_task_status', { name, status }),

    getTasksByStatus: (project: string) =>
      call<Record<string, OrgaTask[]>>('orga.orga.api.task.get_tasks_by_status', { project }),

    getTaskGroups: (project: string) =>
      call<string[]>('orga.orga.api.task.get_task_groups', { project }),

    getGroupDependencyStatus: (project: string, groupName: string) =>
      call<{ total: number; completed: number; incomplete: number; is_complete: boolean; tasks: Array<{ name: string; subject: string; status: string }> }>('orga.orga.api.task.get_group_dependency_status', { project, group_name: groupName }),

    getMyTasks: (filters: { status?: string | null; priority?: string | null; project?: string | null; search?: string | null; limit?: number; offset?: number; include_completed?: boolean; scope?: 'assigned' | 'my_projects' | 'all' } = {}) =>
      call<{ tasks: OrgaTask[]; total: number }>('orga.orga.api.task.get_my_tasks', {
        status: filters.status || null,
        priority: filters.priority || null,
        project: filters.project || null,
        search: filters.search || null,
        limit: filters.limit || 20,
        offset: filters.offset || 0,
        include_completed: filters.include_completed || false,
        scope: filters.scope || 'assigned'
      }),

    promoteChecklistToTask: (taskName: string, itemName: string) =>
      call<{ name: string; subject: string }>('orga.orga.api.task.promote_checklist_to_task', { task_name: taskName, item_name: itemName }),

    bulkUpdateStatus: (tasks: string[], status: string) =>
      call<{ success: boolean; updated: number }>('orga.orga.api.task.bulk_update_status', { tasks: JSON.stringify(tasks), status }),

    reorderTasks: (project: string, taskId: string, newIndex: number) =>
      call<{ success: boolean; updated_tasks: string[]; new_order: string[] }>('orga.orga.api.task.reorder_tasks', { project, task_id: taskId, new_index: newIndex }),

    // Checklist operations
    getChecklist: (taskName: string) =>
      call<OrgaTaskChecklist[]>('orga.orga.api.task.get_task_checklist', { task_name: taskName }),

    addChecklistItem: (taskName: string, title: string) =>
      call<OrgaTaskChecklist>('orga.orga.api.task.add_checklist_item', { task_name: taskName, title }),

    toggleChecklistItem: (taskName: string, itemName: string) =>
      call<{ success: boolean }>('orga.orga.api.task.toggle_checklist_item', { task_name: taskName, item_name: itemName }),

    deleteChecklistItem: (taskName: string, itemName: string) =>
      call<{ success: boolean }>('orga.orga.api.task.delete_checklist_item', { task_name: taskName, item_name: itemName }),

    // Comment operations
    getComments: (taskName: string) =>
      call<OrgaTaskComment[]>('orga.orga.api.task.get_task_comments', { task_name: taskName }),

    addComment: (taskName: string, content: string) =>
      call<OrgaTaskComment>('orga.orga.api.task.add_task_comment', { task_name: taskName, content }),

    deleteComment: (taskName: string, commentName: string) =>
      call<{ success: boolean }>('orga.orga.api.task.delete_task_comment', { task_name: taskName, comment_name: commentName }),

    // Dependency operations
    getDependencies: (taskName: string) =>
      call<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>('orga.orga.api.task.get_task_dependencies', { task_name: taskName }),

    addDependency: (taskName: string, dependsOn: string, dependencyType: DependencyType = 'FS', lagDays: number = 0) => {
      // Convert short form to full form for backend
      const typeMap: Record<DependencyType, string> = {
        'FS': 'Finish to Start',
        'SS': 'Start to Start',
        'FF': 'Finish to Finish',
        'SF': 'Start to Finish'
      }
      return call<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>('orga.orga.api.task.add_task_dependency', {
        task_name: taskName,
        depends_on: dependsOn,
        dependency_type: typeMap[dependencyType] || 'Finish to Start',
        lag_days: lagDays
      })
    },

    updateDependency: (dependencyName: string, dependencyType?: DependencyType, lagDays?: number) => {
      const typeMap: Record<DependencyType, string> = {
        'FS': 'Finish to Start',
        'SS': 'Start to Start',
        'FF': 'Finish to Finish',
        'SF': 'Start to Finish'
      }
      const args: Record<string, unknown> = { dependency_name: dependencyName }
      if (dependencyType !== undefined) {
        args.dependency_type = typeMap[dependencyType] || 'Finish to Start'
      }
      if (lagDays !== undefined) {
        args.lag_days = lagDays
      }
      return call<{ predecessors: TaskDependency[]; successors: TaskDependency[] }>('orga.orga.api.task.update_task_dependency', args)
    },

    removeDependency: (dependencyName: string) =>
      call<{ success: boolean }>('orga.orga.api.task.remove_task_dependency', { dependency_name: dependencyName }),

    // Cascade / auto-schedule operations
    previewCascade: (taskName: string, newStartDate?: string, newEndDate?: string) =>
      call<{ affected_tasks: Array<{ task_id: string; task_name: string; status: string; field: string; old_value: string | null; new_value: string | null; old_end_date: string | null; new_end_date: string | null; days_shift: number; dependency_type: string; lag_days: number }>; total_affected: number }>('orga.orga.api.task.preview_cascade', { task_name: taskName, new_start_date: newStartDate, new_end_date: newEndDate }),

    applyCascade: (taskName: string, newStartDate?: string, newEndDate?: string, changes?: string) =>
      call<{ success: boolean; updated_tasks: string[]; total_updated: number }>('orga.orga.api.task.apply_cascade', { task_name: taskName, new_start_date: newStartDate, new_end_date: newEndDate, changes }),

    rescheduleDependents: (taskName: string, oldStartDate?: string, oldEndDate?: string) =>
      call<{ success: boolean; mode: string; updated_tasks: string[]; total_updated?: number; cascade_preview?: Array<{ task_id: string; task_name: string; days_shift: number }>; total_affected?: number }>('orga.orga.api.task.reschedule_dependents', { task_name: taskName, old_start_date: oldStartDate, old_end_date: oldEndDate }),

    // Attachment operations
    getAttachments: (taskName: string) =>
      call<OrgaFileAttachment[]>('orga.orga.api.task.get_task_attachments', { task_name: taskName }),

    deleteAttachment: (taskName: string, fileName: string) =>
      call<{ success: boolean }>('orga.orga.api.task.delete_task_attachment', { task_name: taskName, file_name: fileName })
  }
}

// ============================================
// Dashboard API
// ============================================

interface ActivitySinceResponse {
  items: ActivityItem[]
  count: number
  latest_timestamp: string
}

interface UseDashboardApiReturn extends UseApiReturn {
  getStats: () => Promise<DashboardStats>
  getRecentActivity: (limit?: number) => Promise<ActivityItem[]>
  getActivitySince: (sinceTimestamp: string, limit?: number) => Promise<ActivitySinceResponse>
  getMyTasks: (status?: string | null, limit?: number) => Promise<OrgaTask[]>
  getOverdueTasks: (limit?: number) => Promise<OrgaTask[]>
  getUpcomingMilestones: (days?: number, limit?: number) => Promise<OrgaMilestone[]>
  getProjectSummary: () => Promise<{ projects: OrgaProject[]; by_status: Record<string, number> }>
  getWorkloadByUser: (project?: string | null) => Promise<Array<{ user: string; task_count: number; hours: number }>>
}

/**
 * Dashboard API composable
 */
export function useDashboardApi(): UseDashboardApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getStats: () =>
      call<DashboardStats>('orga.orga.api.dashboard.get_stats'),

    getRecentActivity: (limit: number = 20) =>
      call<ActivityItem[]>('orga.orga.api.dashboard.get_recent_activity', { limit }),

    getActivitySince: (sinceTimestamp: string, limit: number = 20) =>
      call<ActivitySinceResponse>('orga.orga.api.dashboard.get_activity_since', { since_timestamp: sinceTimestamp, limit }),

    getMyTasks: (status: string | null = null, limit: number = 10) =>
      call<OrgaTask[]>('orga.orga.api.dashboard.get_my_tasks', { status, limit }),

    getOverdueTasks: (limit: number = 20) =>
      call<OrgaTask[]>('orga.orga.api.dashboard.get_overdue_tasks', { limit }),

    getUpcomingMilestones: (days: number = 14, limit: number = 10) =>
      call<OrgaMilestone[]>('orga.orga.api.dashboard.get_upcoming_milestones', { days, limit }),

    getProjectSummary: () =>
      call<{ projects: OrgaProject[]; by_status: Record<string, number> }>('orga.orga.api.dashboard.get_project_summary'),

    getWorkloadByUser: (project: string | null = null) =>
      call<Array<{ user: string; task_count: number; hours: number }>>('orga.orga.api.dashboard.get_workload_by_user', { project })
  }
}

// ============================================
// Activity API
// ============================================

interface UseActivityApiReturn extends UseApiReturn {
  getActivityDetails: (doctype: string, docname: string) => Promise<ActivityDetails>
  addActivityNote: (doctype: string, docname: string, content: string) => Promise<ActivityNote>
  deleteActivityNote: (noteName: string) => Promise<{ success: boolean }>
  toggleActivityPin: (doctype: string, docname: string) => Promise<{ is_pinned: boolean }>
  toggleActivityArchive: (doctype: string, docname: string) => Promise<{ is_archived: boolean }>
  getPinnedActivities: () => Promise<Array<{ doctype: string; name: string }>>
  getArchivedActivities: () => Promise<Array<{ doctype: string; name: string }>>
  deleteActivity: (doctype: string, docname: string) => Promise<{ success: boolean; message: string; deleted_notes: number }>
  // Read/Unread state
  markActivityViewed: () => Promise<{ last_viewed: string }>
  getActivityLastViewed: () => Promise<{ last_viewed: string | null }>
  getUnreadActivityCount: () => Promise<number>
  // Inline comments (threaded)
  getActivityComments: (doctype: string, docname: string, limit?: number, offset?: number) => Promise<ActivityCommentsResponse>
  getCommentReplies: (commentName: string, limit?: number) => Promise<ActivityComment[]>
  addActivityComment: (doctype: string, docname: string, content: string, parentComment?: string) => Promise<ActivityComment>
  deleteActivityComment: (commentName: string) => Promise<{ success: boolean }>
  // Comment resolve/pin
  resolveComment: (commentName: string) => Promise<{ success: boolean; is_resolved: boolean; resolved_by: string; resolved_at: string }>
  unresolveComment: (commentName: string) => Promise<{ success: boolean; is_resolved: boolean }>
  pinComment: (commentName: string) => Promise<{ success: boolean; is_pinned: boolean; pinned_by: string; pinned_at: string }>
  unpinComment: (commentName: string) => Promise<{ success: boolean; is_pinned: boolean }>
  getUsersForMention: (search?: string, limit?: number) => Promise<MentionUser[]>
  // Reactions
  toggleReaction: (doctype: string, docname: string, reactionType: string) => Promise<ReactionResponse>
  getReactions: (doctype: string, docname: string) => Promise<ReactionResponse>
  // Due Diligence Notes
  addDueDiligenceNote: (
    doctype: string,
    docname: string,
    content: string,
    noteType?: NoteType,
    visibility?: NoteVisibility,
    relatedCompany?: string
  ) => Promise<DueDiligenceNote>
  getDueDiligenceNotes: (
    doctype: string,
    docname: string,
    noteType?: NoteType,
    limit?: number,
    offset?: number
  ) => Promise<DueDiligenceNotesResponse>
  getComplianceStatus: (doctype: string, docname: string) => Promise<ComplianceStatus>
  // Related Documents
  getRelatedDocuments: (doctype: string, docname: string) => Promise<RelatedDocument[]>
  // Source Document Info (for Overview tab)
  getSourceDocumentInfo: (doctype: string, docname: string) => Promise<Record<string, unknown>>
}

/**
 * Activity API composable
 *
 * Provides functions for activity management including:
 * - Fetching activity details with changes and notes
 * - Adding/deleting notes on activities
 * - Pinning/archiving activities
 * - Admin delete functionality
 */
export function useActivityApi(): UseActivityApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    /**
     * Get full activity details including changes, notes, and user preferences
     */
    getActivityDetails: (doctype: string, docname: string) =>
      call<ActivityDetails>('orga.orga.api.activity.get_activity_details', { doctype, docname }),

    /**
     * Add a note/annotation to an activity
     */
    addActivityNote: (doctype: string, docname: string, content: string) =>
      call<ActivityNote>('orga.orga.api.activity.add_activity_note', { doctype, docname, content }),

    /**
     * Delete an activity note (author or admin only)
     */
    deleteActivityNote: (noteName: string) =>
      call<{ success: boolean }>('orga.orga.api.activity.delete_activity_note', { note_name: noteName }),

    /**
     * Toggle pin status for an activity
     */
    toggleActivityPin: (doctype: string, docname: string) =>
      call<{ is_pinned: boolean }>('orga.orga.api.activity.toggle_activity_pin', { doctype, docname }),

    /**
     * Toggle archive status for an activity
     */
    toggleActivityArchive: (doctype: string, docname: string) =>
      call<{ is_archived: boolean }>('orga.orga.api.activity.toggle_activity_archive', { doctype, docname }),

    /**
     * Get list of pinned activities for current user
     */
    getPinnedActivities: () =>
      call<Array<{ doctype: string; name: string }>>('orga.orga.api.activity.get_pinned_activities'),

    /**
     * Get list of archived activities for current user
     */
    getArchivedActivities: () =>
      call<Array<{ doctype: string; name: string }>>('orga.orga.api.activity.get_archived_activities'),

    /**
     * Delete activity data (admin only) - removes notes and user preferences
     */
    deleteActivity: (doctype: string, docname: string) =>
      call<{ success: boolean; message: string; deleted_notes: number }>('orga.orga.api.activity.delete_activity', { doctype, docname }),

    // ============================================
    // Read/Unread State
    // ============================================

    /**
     * Mark current timestamp as last viewed (call when leaving Activity page)
     */
    markActivityViewed: () =>
      call<{ last_viewed: string }>('orga.orga.api.activity.mark_activity_viewed'),

    /**
     * Get the user's last activity view timestamp
     */
    getActivityLastViewed: () =>
      call<{ last_viewed: string | null }>('orga.orga.api.activity.get_activity_last_viewed'),

    /**
     * Get count of activities newer than last viewed (capped at 99)
     */
    getUnreadActivityCount: () =>
      call<number>('orga.orga.api.activity.get_unread_activity_count'),

    // ============================================
    // Inline Comments (Threaded)
    // ============================================

    /**
     * Get inline comments for an activity with pagination
     */
    getActivityComments: (doctype: string, docname: string, limit: number = 10, offset: number = 0) =>
      call<ActivityCommentsResponse>('orga.orga.api.activity.get_activity_comments', { doctype, docname, limit, offset }),

    /**
     * Get replies to a specific comment
     */
    getCommentReplies: (commentName: string, limit: number = 20) =>
      call<ActivityComment[]>('orga.orga.api.activity.get_comment_replies', { comment_name: commentName, limit }),

    /**
     * Add an inline comment to an activity (with optional parent for replies)
     */
    addActivityComment: (doctype: string, docname: string, content: string, parentComment?: string) =>
      call<ActivityComment>('orga.orga.api.activity.add_activity_comment', {
        doctype,
        docname,
        content,
        parent_comment: parentComment || null
      }),

    /**
     * Delete an inline comment (author or admin only)
     */
    deleteActivityComment: (commentName: string) =>
      call<{ success: boolean }>('orga.orga.api.activity.delete_activity_comment', { comment_name: commentName }),

    /**
     * Mark a comment thread as resolved
     */
    resolveComment: (commentName: string) =>
      call<{ success: boolean; is_resolved: boolean; resolved_by: string; resolved_at: string }>('orga.orga.api.activity.resolve_comment', { comment_name: commentName }),

    /**
     * Reopen a resolved comment thread
     */
    unresolveComment: (commentName: string) =>
      call<{ success: boolean; is_resolved: boolean }>('orga.orga.api.activity.unresolve_comment', { comment_name: commentName }),

    /**
     * Pin a comment to the top of the discussion (one per document)
     */
    pinComment: (commentName: string) =>
      call<{ success: boolean; is_pinned: boolean; pinned_by: string; pinned_at: string }>('orga.orga.api.activity.pin_comment', { comment_name: commentName }),

    /**
     * Unpin a comment
     */
    unpinComment: (commentName: string) =>
      call<{ success: boolean; is_pinned: boolean }>('orga.orga.api.activity.unpin_comment', { comment_name: commentName }),

    /**
     * Get users for @mention autocomplete
     */
    getUsersForMention: (search: string = '', limit: number = 10) =>
      call<MentionUser[]>('orga.orga.api.activity.get_users_for_mention', { search, limit }),

    // ============================================
    // Reactions
    // ============================================

    /**
     * Toggle a reaction on an activity (add if not present, remove if present)
     */
    toggleReaction: (doctype: string, docname: string, reactionType: string) =>
      call<ReactionResponse>('orga.orga.api.activity.toggle_reaction', {
        doctype,
        docname,
        reaction_type: reactionType
      }),

    /**
     * Get reactions for an activity
     */
    getReactions: (doctype: string, docname: string) =>
      call<ReactionResponse>('orga.orga.api.activity.get_reactions', { doctype, docname }),

    // ============================================
    // Due Diligence Notes
    // ============================================

    /**
     * Add a due diligence or typed note to an activity
     */
    addDueDiligenceNote: (
      doctype: string,
      docname: string,
      content: string,
      noteType: NoteType = 'Due Diligence',
      visibility: NoteVisibility = 'Internal',
      relatedCompany?: string
    ) =>
      call<DueDiligenceNote>('orga.orga.api.activity.add_due_diligence_note', {
        doctype,
        docname,
        content,
        note_type: noteType,
        visibility,
        related_company: relatedCompany || null
      }),

    /**
     * Get due diligence notes for an activity with optional filtering
     */
    getDueDiligenceNotes: (
      doctype: string,
      docname: string,
      noteType?: NoteType,
      limit: number = 20,
      offset: number = 0
    ) =>
      call<DueDiligenceNotesResponse>('orga.orga.api.activity.get_due_diligence_notes', {
        doctype,
        docname,
        note_type: noteType || null,
        limit,
        offset
      }),

    /**
     * Get compliance/due diligence status for an activity
     */
    getComplianceStatus: (doctype: string, docname: string) =>
      call<ComplianceStatus>('orga.orga.api.activity.get_compliance_status', { doctype, docname }),

    // ============================================
    // Related Documents
    // ============================================

    /**
     * Get related/linked documents for an activity
     */
    getRelatedDocuments: (doctype: string, docname: string) =>
      call<RelatedDocument[]>('orga.orga.api.activity.get_related_documents', { doctype, docname }),

    // ============================================
    // Source Document Info (for Overview tab)
    // ============================================

    /**
     * Get key fields from the source document for the Activity Overview tab
     */
    getSourceDocumentInfo: (doctype: string, docname: string) =>
      call<Record<string, unknown>>('orga.orga.api.activity.get_source_document_info', { doctype, docname })
  }
}

// ============================================
// Time Log API
// ============================================

interface UseTimeLogApiReturn extends UseApiReturn {
  getTimeLogs: (filters?: TimeLogFilters) => Promise<{ logs: OrgaTimeLog[]; total: number }>
  getTimeLog: (name: string) => Promise<OrgaTimeLog>
  createTimeLog: (data: {
    hours: number
    task?: string | null
    event?: string | null
    project?: string | null
    tracking_context?: TrackingContext
    description?: string | null
    from_time?: string | null
    log_date?: string | null
    billable?: number
  }) => Promise<OrgaTimeLog>
  updateTimeLog: (name: string, data: Partial<OrgaTimeLog>) => Promise<OrgaTimeLog>
  deleteTimeLog: (name: string) => Promise<{ success: boolean }>
  getTimeSummary: (filters?: TimeLogFilters & { group_by?: string }) => Promise<{ total_hours: number; log_count: number; grouped?: Array<{ group_key: string; total_hours: number; log_count: number }> }>
  getMyTimeLogs: (limit?: number) => Promise<{ logs: OrgaTimeLog[]; total: number }>
  // Timer endpoints
  startTimer: (trackingContext: TrackingContext, task?: string, event?: string, project?: string, description?: string) => Promise<OrgaTimeLog>
  stopTimer: (name?: string) => Promise<OrgaTimeLog>
  getActiveTimer: () => Promise<OrgaTimeLog | null>
  discardTimer: (name?: string) => Promise<{ success: boolean }>
  getTodaySummary: () => Promise<TodayTimeSummary>
}

/**
 * Time Log API composable
 */
export function useTimeLogApi(): UseTimeLogApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getTimeLogs: (filters: TimeLogFilters = {}) =>
      call<{ logs: OrgaTimeLog[]; total: number }>('orga.orga.api.timelog.get_time_logs', filters),

    getTimeLog: (name: string) =>
      call<OrgaTimeLog>('orga.orga.api.timelog.get_time_log', { name }),

    createTimeLog: (data) =>
      call<OrgaTimeLog>('orga.orga.api.timelog.create_time_log', data as Record<string, unknown>),

    updateTimeLog: (name: string, data: Partial<OrgaTimeLog>) =>
      call<OrgaTimeLog>('orga.orga.api.timelog.update_time_log', { name, ...data }),

    deleteTimeLog: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.timelog.delete_time_log', { name }),

    getTimeSummary: (filters: TimeLogFilters & { group_by?: string } = {}) =>
      call<{ total_hours: number; log_count: number; grouped?: Array<{ group_key: string; total_hours: number; log_count: number }> }>('orga.orga.api.timelog.get_time_summary', filters),

    getMyTimeLogs: (limit: number = 20) =>
      call<{ logs: OrgaTimeLog[]; total: number }>('orga.orga.api.timelog.get_my_time_logs', { limit }),

    // Timer endpoints
    startTimer: (trackingContext: TrackingContext, task?: string, event?: string, project?: string, description?: string) =>
      call<OrgaTimeLog>('orga.orga.api.timelog.start_timer', {
        tracking_context: trackingContext,
        task: task || null,
        event: event || null,
        project: project || null,
        description: description || null
      }),

    stopTimer: (name?: string) =>
      call<OrgaTimeLog>('orga.orga.api.timelog.stop_timer', { name: name || null }),

    getActiveTimer: () =>
      call<OrgaTimeLog | null>('orga.orga.api.timelog.get_active_timer', {}),

    discardTimer: (name?: string) =>
      call<{ success: boolean }>('orga.orga.api.timelog.discard_timer', { name: name || null }),

    getTodaySummary: () =>
      call<TodayTimeSummary>('orga.orga.api.timelog.get_today_summary', {})
  }
}

// ============================================
// Settings API
// ============================================

interface UseSettingsApiReturn extends UseApiReturn {
  getSettings: () => Promise<OrgaSettings>
  updateSettings: (data: Partial<OrgaSettings>) => Promise<{ success: boolean }>
}

/**
 * Settings API composable
 */
export function useSettingsApi(): UseSettingsApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getSettings: () =>
      call<OrgaSettings>('orga.orga.api.settings.get_settings'),

    updateSettings: (data: Partial<OrgaSettings>) =>
      call<{ success: boolean }>('orga.orga.api.settings.update_settings', { data: JSON.stringify(data) })
  }
}

// ============================================
// Contact API
// ============================================

interface UseContactApiReturn extends UseApiReturn {
  getContacts: (filters?: ContactFilters) => Promise<{ resources: OrgaContact[]; total: number }>
  getContact: (name: string) => Promise<OrgaContact>
  createContact: (data: Partial<OrgaContact>) => Promise<{ name: string }>
  updateContact: (name: string, data: Partial<OrgaContact>) => Promise<{ name: string; modified: string }>
  deleteContact: (name: string) => Promise<{ success: boolean }>
  getWorkload: (name: string, startDate?: string | null, endDate?: string | null) => Promise<{ allocated_hours: number; available_hours: number; utilization: number }>
  searchBySkill: (skill: string, minProficiency?: ProficiencyLevel | null) => Promise<OrgaContact[]>
  addSkill: (contactName: string, skillName: string, proficiency?: ProficiencyLevel) => Promise<OrgaContactSkill>
  removeSkill: (contactName: string, skillName: string) => Promise<{ success: boolean }>
  getContactStats: (name: string) => Promise<ContactStats>
  getContactTimeline: (name: string, limit?: number, offset?: number) => Promise<{ timeline: OrgaAssignment[]; total: number }>
}

/**
 * Contact API composable
 */
export function useContactApi(): UseContactApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getContacts: (filters: ContactFilters = {}) =>
      call<{ resources: OrgaContact[]; total: number }>('orga.orga.api.resource.get_resources', filters),

    getContact: (name: string) =>
      call<OrgaContact>('orga.orga.api.resource.get_resource', { name }),

    createContact: (data: Partial<OrgaContact>) =>
      call<{ name: string }>('orga.orga.api.resource.create_resource', { data: JSON.stringify(data) }),

    updateContact: (name: string, data: Partial<OrgaContact>) =>
      call<{ name: string; modified: string }>('orga.orga.api.resource.update_resource', { name, data: JSON.stringify(data) }),

    deleteContact: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.resource.delete_resource', { name }),

    getWorkload: (name: string, startDate: string | null = null, endDate: string | null = null) =>
      call<{ allocated_hours: number; available_hours: number; utilization: number }>('orga.orga.api.resource.get_resource_workload', {
        name,
        start_date: startDate,
        end_date: endDate
      }),

    searchBySkill: (skill: string, minProficiency: ProficiencyLevel | null = null) =>
      call<OrgaContact[]>('orga.orga.api.resource.search_resources_by_skill', {
        skill,
        min_proficiency: minProficiency
      }),

    addSkill: (contactName: string, skillName: string, proficiency: ProficiencyLevel = 'Intermediate') =>
      call<OrgaContactSkill>('orga.orga.api.resource.add_resource_skill', {
        resource_name: contactName,
        skill_name: skillName,
        proficiency
      }),

    removeSkill: (contactName: string, skillName: string) =>
      call<{ success: boolean }>('orga.orga.api.resource.remove_resource_skill', {
        resource_name: contactName,
        skill_name: skillName
      }),

    getContactStats: (name: string) =>
      call<ContactStats>('orga.orga.api.resource.get_contact_stats', { name }),

    getContactTimeline: (name: string, limit = 20, offset = 0) =>
      call<{ timeline: OrgaAssignment[]; total: number }>('orga.orga.api.resource.get_contact_timeline', {
        name,
        limit,
        offset
      })
  }
}

// ============================================
// User API (meta-driven link field queries)
// ============================================

interface UseUserApiReturn extends UseApiReturn {
  getAssignableUsers: (options?: {
    doctype?: string
    fieldname?: string
    search?: string
    limit?: number
  }) => Promise<MentionUser[]>
}

/**
 * User API composable for meta-driven user queries.
 * Reads the Link field definition to determine which DocType to query.
 */
export function useUserApi(): UseUserApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getAssignableUsers: (options = {}) =>
      call<MentionUser[]>('orga.orga.api.user.get_assignable_users', {
        doctype: options.doctype || 'Orga Task',
        fieldname: options.fieldname || 'assigned_to',
        search: options.search || '',
        limit: options.limit || 50,
      }),
  }
}

// ============================================
// Assignment API
// ============================================

interface UseAssignmentApiReturn extends UseApiReturn {
  getAssignments: (filters?: Partial<OrgaAssignment>) => Promise<OrgaAssignment[]>
  getAssignment: (name: string) => Promise<OrgaAssignment>
  createAssignment: (task: string, resource: string, options?: Partial<OrgaAssignment>) => Promise<{ name: string }>
  updateAssignment: (name: string, data: Partial<OrgaAssignment>) => Promise<{ name: string; modified: string }>
  deleteAssignment: (name: string) => Promise<{ success: boolean }>
  getTaskAssignments: (taskName: string) => Promise<OrgaAssignment[]>
  getResourceAssignments: (resourceName: string, options?: { status?: string }) => Promise<OrgaAssignment[]>
}

/**
 * Assignment API composable
 */
export function useAssignmentApi(): UseAssignmentApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getAssignments: (filters: Partial<OrgaAssignment> = {}) =>
      call<OrgaAssignment[]>('orga.orga.api.assignment.get_assignments', filters),

    getAssignment: (name: string) =>
      call<OrgaAssignment>('orga.orga.api.assignment.get_assignment', { name }),

    createAssignment: (task: string, resource: string, options: Partial<OrgaAssignment> = {}) =>
      call<{ name: string }>('orga.orga.api.assignment.create_assignment', {
        task,
        resource,
        ...options
      }),

    updateAssignment: (name: string, data: Partial<OrgaAssignment>) =>
      call<{ name: string; modified: string }>('orga.orga.api.assignment.update_assignment', {
        name,
        data: JSON.stringify(data)
      }),

    deleteAssignment: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.assignment.delete_assignment', { name }),

    getTaskAssignments: (taskName: string) =>
      call<OrgaAssignment[]>('orga.orga.api.assignment.get_task_assignments', { task_name: taskName }),

    getResourceAssignments: (resourceName: string, options: { status?: string } = {}) =>
      call<OrgaAssignment[]>('orga.orga.api.assignment.get_resource_assignments', {
        resource_name: resourceName,
        ...options
      })
  }
}

// ============================================
// Defect API
// ============================================

interface UseDefectApiReturn extends UseApiReturn {
  getDefects: (filters?: DefectFilters) => Promise<{ defects: OrgaDefect[]; total: number }>
  getDefect: (name: string) => Promise<OrgaDefect>
  createDefect: (data: Partial<OrgaDefect>) => Promise<OrgaDefect>
  updateDefect: (name: string, data: Partial<OrgaDefect>) => Promise<OrgaDefect>
  deleteDefect: (name: string) => Promise<{ success: boolean }>
}

/**
 * Defect API composable
 */
export function useDefectApi(): UseDefectApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getDefects: (filters: DefectFilters = {}) =>
      call<{ defects: OrgaDefect[]; total: number }>('orga.orga.api.defect.get_defects', filters),

    getDefect: (name: string) =>
      call<OrgaDefect>('orga.orga.api.defect.get_defect', { name }),

    createDefect: (data: Partial<OrgaDefect>) =>
      call<OrgaDefect>('orga.orga.api.defect.create_defect', { data: JSON.stringify(data) }),

    updateDefect: (name: string, data: Partial<OrgaDefect>) =>
      call<OrgaDefect>('orga.orga.api.defect.update_defect', { name, data: JSON.stringify(data) }),

    deleteDefect: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.defect.delete_defect', { name })
  }
}

// ============================================
// Event API
// ============================================

interface UseEventApiReturn extends UseApiReturn {
  getEvents: (filters?: EventFilters) => Promise<OrgaEvent[]>
  getEvent: (name: string) => Promise<OrgaEvent>
  createEvent: (data: Partial<OrgaEvent>) => Promise<{ name: string }>
  updateEvent: (name: string, data: Partial<OrgaEvent>) => Promise<{ name: string; modified: string }>
  deleteEvent: (name: string) => Promise<{ success: boolean }>
  getCalendarEvents: (startDate: string, endDate: string, filters?: Partial<EventFilters>) => Promise<CalendarEvent[]>
  getMyEvents: (options?: EventFilters) => Promise<OrgaEvent[]>
  updateRsvp: (eventName: string, status: RsvpStatus) => Promise<{ success: boolean }>
  addAttendee: (eventName: string, resource: string, required?: boolean) => Promise<{ success: boolean }>
  removeAttendee: (eventName: string, resource: string) => Promise<{ success: boolean }>
  sendInvitations: (eventName: string) => Promise<{ success: boolean; sent_to: string[] }>
  createEventWithInvitations: (data: Partial<OrgaEvent>, sendInvites?: boolean) => Promise<{ name: string; invites_sent: boolean }>
  // Enhanced RSVP for Activity Feed
  updateRsvpEnhanced: (eventName: string, status: string, note?: string) => Promise<RSVPUpdateResponse>
  proposeNewTime: (eventName: string, proposedStart: string, proposedEnd: string, note?: string) => Promise<RSVPUpdateResponse>
  getEventRsvpInfo: (eventName: string) => Promise<EventRSVPInfo>
}

/**
 * Event API composable
 */
export function useEventApi(): UseEventApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getEvents: (filters: EventFilters = {}) =>
      call<OrgaEvent[]>('orga.orga.api.appointment.get_appointments', filters),

    getEvent: (name: string) =>
      call<OrgaEvent>('orga.orga.api.appointment.get_appointment', { name }),

    createEvent: (data: Partial<OrgaEvent>) =>
      call<{ name: string }>('orga.orga.api.appointment.create_appointment', { data: JSON.stringify(data) }),

    updateEvent: (name: string, data: Partial<OrgaEvent>) =>
      call<{ name: string; modified: string }>('orga.orga.api.appointment.update_appointment', { name, data: JSON.stringify(data) }),

    deleteEvent: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.appointment.delete_appointment', { name }),

    getCalendarEvents: (startDate: string, endDate: string, filters: Partial<EventFilters> = {}) =>
      call<CalendarEvent[]>('orga.orga.api.appointment.get_calendar_events', {
        start_date: startDate,
        end_date: endDate,
        ...filters
      }),

    getMyEvents: (options: EventFilters = {}) =>
      call<OrgaEvent[]>('orga.orga.api.appointment.get_my_appointments', options),

    updateRsvp: (eventName: string, status: RsvpStatus) =>
      call<{ success: boolean }>('orga.orga.api.appointment.update_rsvp', {
        appointment_name: eventName,
        rsvp_status: status
      }),

    addAttendee: (eventName: string, resource: string, required: boolean = true) =>
      call<{ success: boolean }>('orga.orga.api.appointment.add_attendee', {
        appointment_name: eventName,
        resource,
        required: required ? 1 : 0
      }),

    removeAttendee: (eventName: string, resource: string) =>
      call<{ success: boolean }>('orga.orga.api.appointment.remove_attendee', {
        appointment_name: eventName,
        resource
      }),

    sendInvitations: (eventName: string) =>
      call<{ success: boolean; sent_to: string[] }>('orga.orga.api.appointment.send_invitations', {
        appointment_name: eventName
      }),

    createEventWithInvitations: (data: Partial<OrgaEvent>, sendInvites: boolean = true) =>
      call<{ name: string; invites_sent: boolean }>('orga.orga.api.appointment.create_appointment_with_invitations', {
        data: JSON.stringify(data),
        send_invites: sendInvites
      }),

    // Enhanced RSVP for Activity Feed
    updateRsvpEnhanced: (eventName: string, status: string, note?: string) =>
      call<RSVPUpdateResponse>('orga.orga.api.appointment.update_rsvp_enhanced', {
        appointment: eventName,
        status,
        note: note || null
      }),

    proposeNewTime: (eventName: string, proposedStart: string, proposedEnd: string, note?: string) =>
      call<RSVPUpdateResponse>('orga.orga.api.appointment.propose_new_time', {
        appointment: eventName,
        proposed_start: proposedStart,
        proposed_end: proposedEnd,
        note: note || null
      }),

    getEventRsvpInfo: (eventName: string) =>
      call<EventRSVPInfo>('orga.orga.api.appointment.get_appointment_rsvp_info', { appointment: eventName })
  }
}

// ============================================
// Health API
// ============================================

interface UseHealthApiReturn extends UseApiReturn {
  getProjectHealth: (projectName: string) => Promise<ProjectHealth>
  getHealthOverview: () => Promise<HealthOverview>
  recalculateHealth: (projectName: string) => Promise<ProjectHealth>
}

/**
 * Health API composable
 */
export function useHealthApi(): UseHealthApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getProjectHealth: (projectName: string) =>
      call<ProjectHealth>('orga.orga.api.dashboard.get_project_health', { project_name: projectName }),

    getHealthOverview: () =>
      call<HealthOverview>('orga.orga.api.dashboard.get_health_overview'),

    recalculateHealth: (projectName: string) =>
      call<ProjectHealth>('orga.orga.api.dashboard.recalculate_project_health', { project_name: projectName })
  }
}

// ============================================
// Reports API
// ============================================

interface UseReportsApiReturn extends UseApiReturn {
  getProjectSummaryReport: (filters?: { date_from?: string; date_to?: string }) => Promise<ProjectSummaryReport>
  getContactUtilizationReport: (filters?: { date_from?: string; date_to?: string; department?: string }) => Promise<ContactUtilizationReport>
  getTaskCompletionReport: (filters?: { project?: string; date_from?: string; date_to?: string }) => Promise<TaskCompletionReport>
  getBudgetTrackingReport: () => Promise<BudgetTrackingReport>
  getMilestoneReport: (filters?: { days_ahead?: number }) => Promise<MilestoneReport>
}

/**
 * Reports API composable
 */
export function useReportsApi(): UseReportsApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getProjectSummaryReport: (filters: { date_from?: string; date_to?: string } = {}) =>
      call<ProjectSummaryReport>('orga.orga.api.reports.get_project_summary_report', filters),

    getContactUtilizationReport: (filters: { date_from?: string; date_to?: string; department?: string } = {}) =>
      call<ContactUtilizationReport>('orga.orga.api.reports.get_resource_utilization_report', filters),

    getTaskCompletionReport: (filters: { project?: string; date_from?: string; date_to?: string } = {}) =>
      call<TaskCompletionReport>('orga.orga.api.reports.get_task_completion_report', filters),

    getBudgetTrackingReport: () =>
      call<BudgetTrackingReport>('orga.orga.api.reports.get_budget_tracking_report', {}),

    getMilestoneReport: (filters: { days_ahead?: number } = {}) =>
      call<MilestoneReport>('orga.orga.api.reports.get_milestone_report', filters)
  }
}

// ============================================
// Notification API
// ============================================

interface UseNotificationApiReturn extends UseApiReturn {
  getMyNotifications: (filters?: NotificationFilters) => Promise<{ notifications: OrgaNotification[]; total: number; unread_count: number }>
  getUnreadCount: () => Promise<number>
  markAsRead: (name: string) => Promise<{ success: boolean }>
  markAsUnread: (name: string) => Promise<{ success: boolean }>
  markAllAsRead: () => Promise<{ success: boolean; count: number }>
  deleteNotification: (name: string) => Promise<{ success: boolean }>
  deleteAllRead: () => Promise<{ success: boolean; count: number }>
}

/**
 * Notification API composable
 */
export function useNotificationApi(): UseNotificationApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getMyNotifications: (filters: NotificationFilters = {}) =>
      call<{ notifications: OrgaNotification[]; total: number; unread_count: number }>('orga.orga.api.notification.get_my_notifications', {
        limit: filters.limit || 50,
        offset: filters.offset || 0,
        unread_only: filters.unread_only || false
      }),

    getUnreadCount: () =>
      call<number>('orga.orga.api.notification.get_unread_count'),

    markAsRead: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.notification.mark_as_read', { name }),

    markAsUnread: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.notification.mark_as_unread', { name }),

    markAllAsRead: () =>
      call<{ success: boolean; count: number }>('orga.orga.api.notification.mark_all_as_read'),

    deleteNotification: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.notification.delete_notification', { name }),

    deleteAllRead: () =>
      call<{ success: boolean; count: number }>('orga.orga.api.notification.delete_all_read')
  }
}

// ============================================
// Milestone API
// ============================================

interface UseMilestoneApiReturn extends UseApiReturn {
  getMilestones: (project: string, status?: string) => Promise<{ milestones: OrgaMilestone[]; total: number }>
  getMilestone: (name: string) => Promise<OrgaMilestone>
  createMilestone: (data: Partial<OrgaMilestone>) => Promise<{ name: string; milestone_name: string }>
  updateMilestone: (name: string, data: Partial<OrgaMilestone>) => Promise<OrgaMilestone>
  deleteMilestone: (name: string) => Promise<{ success: boolean; unlinked_tasks?: number }>
  reorderMilestones: (project: string, milestoneId: string, newIndex: number) => Promise<{ success: boolean; updated_milestones: string[]; new_order: string[] }>
}

/**
 * Milestone API composable
 */
export function useMilestoneApi(): UseMilestoneApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getMilestones: (project: string, status?: string) => {
      const args: Record<string, unknown> = { project }
      if (status) args.status = status
      return call<{ milestones: OrgaMilestone[]; total: number }>('orga.orga.api.milestone.get_milestones', args)
    },

    getMilestone: (name: string) =>
      call<OrgaMilestone>('orga.orga.api.milestone.get_milestone', { name }),

    createMilestone: (data: Partial<OrgaMilestone>) =>
      call<{ name: string; milestone_name: string }>('orga.orga.api.milestone.create_milestone', { data: JSON.stringify(data) }),

    updateMilestone: (name: string, data: Partial<OrgaMilestone>) =>
      call<OrgaMilestone>('orga.orga.api.milestone.update_milestone', { name, data: JSON.stringify(data) }),

    deleteMilestone: (name: string) =>
      call<{ success: boolean; unlinked_tasks?: number }>('orga.orga.api.milestone.delete_milestone', { name }),

    reorderMilestones: (project: string, milestoneId: string, newIndex: number) =>
      call<{ success: boolean; updated_milestones: string[]; new_order: string[] }>('orga.orga.api.milestone.reorder_milestones', { project, milestone_id: milestoneId, new_index: newIndex })
  }
}

// ============================================
// Gantt API (unified reorder)
// ============================================

interface ReorderItemPayload {
  item_id: string
  item_type: 'task' | 'milestone'
  project: string
  prev_item_id?: string | null
  next_item_id?: string | null
  prev_item_type?: 'task' | 'milestone' | null
  next_item_type?: 'task' | 'milestone' | null
}

interface ReorderItemResponse {
  success: boolean
  sort_order?: number
  item_id?: string
  reason?: string
}

interface UseGanttApiReturn extends UseApiReturn {
  reorderItem: (payload: ReorderItemPayload) => Promise<ReorderItemResponse>
}

/**
 * Gantt API composable — unified reorder using float sort_order
 */
export function useGanttApi(): UseGanttApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    reorderItem: (payload: ReorderItemPayload) =>
      call<ReorderItemResponse>('orga.orga.api.gantt.reorder_item', {
        item_id: payload.item_id,
        item_type: payload.item_type,
        project: payload.project,
        prev_item_id: payload.prev_item_id || null,
        next_item_id: payload.next_item_id || null,
        prev_item_type: payload.prev_item_type || null,
        next_item_type: payload.next_item_type || null
      })
  }
}

// ============================================
// Template API
// ============================================

interface UseTemplateApiReturn extends UseApiReturn {
  getTemplates: (filters?: TemplateFilters) => Promise<{ templates: OrgaProjectTemplate[]; total: number }>
  getTemplate: (name: string) => Promise<OrgaProjectTemplate>
  createFromProject: (projectName: string, templateName: string, description?: string, category?: string) => Promise<{ name: string; template_name: string; task_count: number; milestone_count: number; dependency_count: number }>
  updateTemplate: (name: string, data: Partial<OrgaProjectTemplate>) => Promise<{ name: string; modified: string }>
  deleteTemplate: (name: string) => Promise<{ success: boolean }>
  applyTemplate: (projectName: string, templateName: string) => Promise<{ tasks_created: number; milestones_created: number; dependencies_created: number }>
  exportTemplate: (name: string) => Promise<{ version: string; template_name: string; description: string; category: string; project_type: string; template_data: TemplateData }>
  importTemplate: (data: Record<string, unknown>) => Promise<{ name: string; template_name: string; task_count: number; milestone_count: number; dependency_count: number }>
}

/**
 * Template API composable
 */
export function useTemplateApi(): UseTemplateApiReturn {
  const { call, loading, error } = useApi()

  return {
    loading,
    error,
    call,

    getTemplates: (filters: TemplateFilters = {}) =>
      call<{ templates: OrgaProjectTemplate[]; total: number }>('orga.orga.api.template.get_templates', filters as Record<string, unknown>),

    getTemplate: (name: string) =>
      call<OrgaProjectTemplate>('orga.orga.api.template.get_template', { name }),

    createFromProject: (projectName: string, templateName: string, description?: string, category?: string) =>
      call<{ name: string; template_name: string; task_count: number; milestone_count: number; dependency_count: number }>(
        'orga.orga.api.template.create_template_from_project',
        { project_name: projectName, template_name: templateName, description, category }
      ),

    updateTemplate: (name: string, data: Partial<OrgaProjectTemplate>) =>
      call<{ name: string; modified: string }>('orga.orga.api.template.update_template', { name, data: JSON.stringify(data) }),

    deleteTemplate: (name: string) =>
      call<{ success: boolean }>('orga.orga.api.template.delete_template', { name }),

    applyTemplate: (projectName: string, templateName: string) =>
      call<{ tasks_created: number; milestones_created: number; dependencies_created: number }>(
        'orga.orga.api.template.apply_template',
        { project_name: projectName, template_name: templateName }
      ),

    exportTemplate: (name: string) =>
      call<{ version: string; template_name: string; description: string; category: string; project_type: string; template_data: TemplateData }>(
        'orga.orga.api.template.export_template',
        { name }
      ),

    importTemplate: (data: Record<string, unknown>) =>
      call<{ name: string; template_name: string; task_count: number; milestone_count: number; dependency_count: number }>(
        'orga.orga.api.template.import_template',
        { data: JSON.stringify(data) }
      )
  }
}

// ============================================
// Combined API Composable
// ============================================

interface UseOrgaApiReturn {
  project: ReturnType<typeof useProjectApi>
  task: ReturnType<typeof useTaskApi>
  dashboard: ReturnType<typeof useDashboardApi>
  activity: ReturnType<typeof useActivityApi>
  timeLog: ReturnType<typeof useTimeLogApi>
  settings: ReturnType<typeof useSettingsApi>
  contact: ReturnType<typeof useContactApi>
  assignment: ReturnType<typeof useAssignmentApi>
  defect: ReturnType<typeof useDefectApi>
  event: ReturnType<typeof useEventApi>
  health: ReturnType<typeof useHealthApi>
  reports: ReturnType<typeof useReportsApi>
  notification: ReturnType<typeof useNotificationApi>
  milestone: ReturnType<typeof useMilestoneApi>
  gantt: ReturnType<typeof useGanttApi>
  template: ReturnType<typeof useTemplateApi>
}

/**
 * Combined API composable - provides all APIs in one place
 */
export function useOrgaApi(): UseOrgaApiReturn {
  return {
    project: useProjectApi(),
    task: useTaskApi(),
    dashboard: useDashboardApi(),
    activity: useActivityApi(),
    timeLog: useTimeLogApi(),
    settings: useSettingsApi(),
    contact: useContactApi(),
    assignment: useAssignmentApi(),
    defect: useDefectApi(),
    event: useEventApi(),
    health: useHealthApi(),
    reports: useReportsApi(),
    notification: useNotificationApi(),
    milestone: useMilestoneApi(),
    gantt: useGanttApi(),
    template: useTemplateApi()
  }
}
