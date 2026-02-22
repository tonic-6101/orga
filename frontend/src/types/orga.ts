// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// src/types/orga.ts
// Type definitions for Orga DocTypes

// ============================================
// Base Types
// ============================================

export interface OrgaDocument {
  name: string
  owner: string
  creation: string
  modified: string
  modified_by: string
  docstatus: 0 | 1 | 2
}

// ============================================
// Orga Project
// ============================================

export type ProjectStatus = 'Planning' | 'Active' | 'On Hold' | 'Completed' | 'Cancelled'
export type ProjectType = 'Internal' | 'Client' | 'Mixed'
export type HealthStatus = 'Green' | 'Yellow' | 'Red' | 'Unknown'

export interface OrgaProject extends OrgaDocument {
  project_name: string
  project_code?: string
  project_type?: string
  description?: string
  status: ProjectStatus
  health_status?: HealthStatus
  start_date?: string
  end_date?: string
  progress: number
  project_manager?: string
  department?: string
  budget?: number
  estimated_cost?: number
  spent?: number
  client?: string
  // Scheduling
  dependency_mode?: 'Flexible' | 'Strict' | 'Off'
  auto_schedule_on_completion?: boolean | number
  auto_trail_start_default?: boolean | number
  // Computed fields
  task_count?: number
  completed_tasks?: number
}

// ============================================
// Orga Task
// ============================================

export type TaskStatus = 'Open' | 'Working' | 'In Progress' | 'Pending Review' | 'Review' | 'Completed' | 'Cancelled'
export type TaskPriority = 'Low' | 'Medium' | 'High' | 'Urgent'
export type TaskType = '' | 'Task' | 'Bug' | 'Feature' | 'Research' | 'Meeting'

export interface OrgaTask extends OrgaDocument {
  subject: string
  project: string
  project_name?: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  task_type?: TaskType
  assigned_to?: string
  assigned_to_name?: string
  assigned_to_image?: string
  assigned_resource?: string
  assigned_resource_name?: string
  start_date?: string
  due_date?: string
  completed_date?: string
  progress?: number
  estimated_hours?: number
  actual_hours?: number
  milestone?: string
  parent_task?: string
  task_group?: string
  depends_on_group?: string
  sort_order?: number
  auto_trail_start?: boolean | number
  is_blocked?: boolean | number
  // Scheduling type
  task_scheduling_type?: 'Fixed Duration' | 'Hammock' | 'Buffer'
  buffer_size?: number
  buffer_consumed?: number
  // Financial fields
  estimated_cost?: number
  actual_cost?: number
  is_billable?: boolean
  billing_rate?: number
  // Child tables
  checklist?: OrgaTaskChecklist[]
  comments?: OrgaTaskComment[]
  dependencies?: OrgaTaskDependency[]
}

export interface OrgaTaskChecklist {
  name?: string
  title: string
  completed: 0 | 1
  completed_by?: string
  completed_on?: string
}

export interface OrgaTaskComment {
  name?: string
  content: string
  comment_by: string
  comment_by_name?: string
  posted_on: string
}

// Aliases for backwards compatibility with TaskManager
export type TaskChecklistItem = OrgaTaskChecklist
export type TaskComment = OrgaTaskComment

export interface OrgaTaskDependency {
  name?: string
  depends_on: string
  depends_on_subject?: string
  dependency_type: 'Finish to Start' | 'Start to Start' | 'Finish to Finish' | 'Start to Finish'
  lag_days?: number
}

// Extended dependency interface for Manager panel
export interface TaskDependency {
  name: string
  task?: string
  task_subject?: string
  task_status?: string
  depends_on: string
  depends_on_subject?: string
  depends_on_status?: string
  dependency_type: DependencyType
  lag_days?: number
}

// ============================================
// Orga Milestone
// ============================================

export type MilestoneStatus = 'Upcoming' | 'In Progress' | 'Completed' | 'Missed'

export interface OrgaMilestone extends OrgaDocument {
  milestone_name: string
  project: string
  description?: string
  status: MilestoneStatus
  due_date: string
  completed_date?: string
  sort_order?: number
  completion_percentage?: number
  task_count?: number
}

// ============================================
// Orga Contact
// ============================================

export type ContactStatus = 'Active' | 'Inactive' | 'On Leave'
export type ProficiencyLevel = 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert'

export type ContactType = 'Employee' | 'Contractor' | 'External'

export interface OrgaContact extends OrgaDocument {
  resource_name: string
  email?: string
  phone?: string
  mobile_no?: string
  user?: string
  department?: string
  designation?: string
  company?: string
  job_title?: string
  resource_type?: ContactType
  status: ContactStatus
  reports_to?: string
  reports_to_name?: string
  date_of_joining?: string
  address?: string
  availability_hours?: number
  weekly_capacity: number
  hourly_cost?: number
  billable_rate?: number
  notes?: string
  // Child tables
  skills?: OrgaContactSkill[]
  // Computed (from API enrichment)
  current_allocation?: number
  available_hours?: number
  active_assignments?: number
  allocated_hours?: number
  utilization_percent?: number
  workload_status?: string
  initials?: string
}

export interface OrgaContactSkill {
  name?: string
  skill_name: string
  proficiency: ProficiencyLevel
  years_experience?: number
  notes?: string
}

// ============================================
// Orga Assignment
// ============================================

export type AssignmentStatus = 'Assigned' | 'In Progress' | 'Completed' | 'Cancelled'

export interface OrgaAssignment extends OrgaDocument {
  task: string
  task_subject?: string
  resource: string
  resource_name?: string
  project?: string
  status: AssignmentStatus
  allocated_hours: number
  actual_hours?: number
  start_date?: string
  end_date?: string
  notes?: string
}

// ============================================
// Orga Defect
// ============================================

export type DefectType = 'Workmanship' | 'Material' | 'Safety' | 'Compliance' | 'Other'
export type DefectSeverity = 'Low' | 'Medium' | 'High' | 'Critical'
export type DefectStatus = 'Open' | 'In Progress' | 'Resolved' | 'Closed'

export interface OrgaDefect extends OrgaDocument {
  title: string
  contact: string
  contact_name?: string
  project?: string
  project_name?: string
  task?: string
  task_subject?: string
  defect_type: DefectType
  severity: DefectSeverity
  status: DefectStatus
  reported_date: string
  resolved_date?: string
  reported_by?: string
  reported_by_name?: string
  cost_estimate?: number
  actual_cost?: number
  description?: string
  resolution_notes?: string
}

// ============================================
// Contact Stats (for Contact Detail page)
// ============================================

export interface ContactStats {
  assignments: {
    total: number
    active: number
    completed: number
    cancelled: number
  }
  time_logs: {
    total_hours: number
    billable_hours: number
    log_count: number
  }
  defects: {
    total: number
    open: number
    resolved: number
    total_cost: number
    total_estimate: number
  }
  projects: {
    total: number
    active_count: number
    project_list: Array<{
      name: string
      project_name: string
      status: string
    }>
  }
  financial: {
    hourly_cost: number
    billable_rate: number
    total_billed_hours: number
    total_cost_to_org: number
    defect_cost: number
  }
}

// ============================================
// Orga Event
// ============================================

export type EventType = 'Meeting' | 'Deadline' | 'Reminder' | 'Event' | 'Review'
export type EventStatus = 'Scheduled' | 'Completed' | 'Cancelled'
export type RsvpStatus = 'Pending' | 'Accepted' | 'Declined' | 'Tentative'

export interface OrgaEvent extends OrgaDocument {
  subject: string
  appointment_type: EventType
  description?: string
  start_datetime: string
  end_datetime?: string
  all_day: 0 | 1
  location?: string
  project?: string
  organizer?: string
  organizer_name?: string
  // Child tables
  attendees?: OrgaEventAttendee[]
  // Reminder settings
  reminder_sent: 0 | 1
  reminder_minutes?: number
}

export interface OrgaEventAttendee {
  name?: string
  resource: string
  resource_name?: string
  email?: string
  rsvp_status: RsvpStatus
  required?: 0 | 1
}

// ============================================
// Orga Time Log
// ============================================

export type TrackingContext = 'task' | 'event' | 'project' | 'standalone'

export interface OrgaTimeLog extends OrgaDocument {
  tracking_context: TrackingContext
  task?: string
  task_subject?: string
  event?: string
  event_subject?: string
  project?: string
  project_name?: string
  resource?: string
  resource_name?: string
  user: string
  user_name?: string
  hours: number
  log_date: string
  description?: string
  billable: 0 | 1
  from_time?: string
  to_time?: string
  is_running: 0 | 1
  timer_started_at?: string
}

export interface TimerState {
  isRunning: boolean
  activeTimeLog: OrgaTimeLog | null
  elapsedSeconds: number
  context: TrackingContext | null
  contextLabel: string
}

export interface TodayTimeSummary {
  total_hours: number
  log_count: number
  logs: OrgaTimeLog[]
  active_timer: OrgaTimeLog | null
}

// ============================================
// Orga Project Template
// ============================================

export type TemplateCategory = 'General' | 'Marketing' | 'Engineering' | 'Operations' | 'Other'

export interface OrgaProjectTemplate extends OrgaDocument {
  template_name: string
  description?: string
  category: TemplateCategory
  project_type: ProjectType
  source_project?: string
  source_project_name?: string
  task_count: number
  milestone_count: number
  dependency_count: number
  template_data?: TemplateData
}

export interface TemplateData {
  tasks: TemplateTask[]
  milestones: TemplateMilestone[]
}

export interface TemplateTask {
  ref_id: string
  subject: string
  description?: string
  priority: TaskPriority
  estimated_hours?: number
  sort_order?: number
  start_offset_days: number
  duration_days: number
  checklist: string[]
  milestone_ref?: string
  dependencies: TemplateDependency[]
}

export interface TemplateDependency {
  predecessor_ref: string
  type: DependencyType
  lag_days: number
}

export interface TemplateMilestone {
  ref_id: string
  milestone_name: string
  description?: string
  offset_days: number
  sort_order?: number
}

export interface TemplateFilters {
  [key: string]: unknown
  category?: TemplateCategory
  limit?: number
  offset?: number
}

// ============================================
// Orga Settings (Single DocType)
// ============================================

export interface OrgaSettings {
  default_project_status: ProjectStatus
  default_task_priority: TaskPriority
  default_currency: string
  enable_time_tracking: 0 | 1
  time_tracking_mandatory: 0 | 1
  default_weekly_capacity: number
  enable_appointment_reminders: 0 | 1
  default_reminder_minutes: number
  enable_health_calculation: 0 | 1
  health_calculation_interval: number
}

// ============================================
// API Response Types
// ============================================

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page?: number
  page_size?: number
}

export interface ApiResponse<T> {
  message: T
}

export interface DashboardStats {
  project_count: number
  task_count: number
  completed_tasks: number
  overdue_tasks: number
  contact_count: number
  upcoming_events: number
  active_assignments: number
  projects_by_status?: Record<string, number>
  tasks_by_status?: Record<string, number>
}

export interface ProjectHealth {
  score: number
  status: HealthStatus
  factors: {
    schedule: number
    budget: number
    tasks: number
    milestones: number
  }
  recommendations: HealthRecommendation[]
}

export interface HealthRecommendation {
  area: string
  message: string
  severity: 'high' | 'medium' | 'low'
}

export interface HealthOverview {
  summary: Record<string, number>
  total: number
  projects: Array<{
    name: string
    project_name: string
    health_status: HealthStatus
    progress: number
  }>
}

// ============================================
// Activity Types
// ============================================

/**
 * Represents a field-level change from the Version doctype.
 * Used in the Activity Manager Changes tab.
 */
export interface ActivityChange {
  field: string
  field_label: string
  old_value: string | number | boolean | null
  new_value: string | number | boolean | null
  modified?: string
  modified_by?: string
  modified_by_image?: string | null
}

/**
 * Represents a user note/annotation on an activity.
 * Stored as Comment doctype with comment_type "Info".
 */
export interface ActivityNote {
  name: string
  content: string
  created_by: string
  created_by_name: string
  created_by_image?: string | null
  creation: string
}

/**
 * Represents an inline comment on an activity (threaded).
 * Stored as Orga Activity Comment DocType.
 */
export interface ActivityComment {
  name: string
  user: string
  user_fullname: string
  user_image?: string
  content: string
  creation: string
  parent_comment?: string
  reply_count: number
  replies: ActivityComment[]
  can_delete: boolean
}

/**
 * Response from get_activity_comments API
 */
export interface ActivityCommentsResponse {
  comments: ActivityComment[]
  has_more: boolean
  total: number
}

/**
 * User info for @mention autocomplete
 */
export interface MentionUser {
  name: string
  full_name: string
  user_image?: string
}

// ============================================
// Activity Reactions
// ============================================

/**
 * Valid reaction types for activities
 */
export type ReactionType = 'acknowledge' | 'celebrate' | 'seen' | 'flag'

/**
 * User info for reaction display
 */
export interface ReactionUser {
  user: string
  user_fullname: string
}

/**
 * Response from toggle_reaction or get_reactions API
 */
export interface ReactionResponse {
  reacted?: boolean
  counts: Record<string, number>
  users: Record<string, ReactionUser[]>
  user_reactions: string[]
}

// ============================================
// RSVP Types
// ============================================

/**
 * RSVP status options
 */
export type RSVPStatus = 'Pending' | 'Accepted' | 'Declined' | 'Tentative'

/**
 * Attendee statistics for an event
 */
export interface AttendeeStats {
  total: number
  accepted: number
  declined: number
  tentative: number
  pending: number
}

/**
 * Attendee info for display
 */
export interface EventAttendee {
  resource?: string
  user?: string
  name: string
  user_image?: string
  rsvp_status: RSVPStatus
  required: number
  proposed_start?: string
  proposed_end?: string
}

/**
 * Response from RSVP update APIs
 */
export interface RSVPUpdateResponse {
  status: RSVPStatus
  attendee_stats: AttendeeStats
  attendees?: EventAttendee[]
  proposed_start?: string
  proposed_end?: string
}

/**
 * Response from get_appointment_rsvp_info
 */
export interface EventRSVPInfo {
  is_attendee: boolean
  user_rsvp_status: RSVPStatus | null
  attendee_stats: AttendeeStats
  attendees: EventAttendee[]
}

/**
 * Activity feed item with optional manager action fields.
 * Extended from basic activity to support pin, archive, notes, and changes.
 */
export interface ActivityItem {
  // Core identity
  doctype: string
  name: string
  subject?: string
  action: string
  timestamp: string
  user: string
  user_fullname?: string
  user_name?: string
  user_image?: string
  reference_doctype?: string
  reference_name?: string

  // Extended fields for Activity view
  type?: string
  title?: string
  status?: string
  project?: string
  project_name?: string
  modified?: string
  modified_by?: string
  modified_by_name?: string

  // Manager action fields (populated by get_activity_details)
  is_pinned?: boolean
  is_archived?: boolean
  notes?: ActivityNote[]
  changes?: ActivityChange[]
  can_delete?: boolean

  // Inline comments
  comment_count?: number

  // Reactions
  reaction_counts?: Record<string, number>
  user_reactions?: string[]

  // Event-specific (RSVP)
  event_type?: string
  start_datetime?: string
  end_datetime?: string
  location?: string
  is_attendee?: boolean
  user_rsvp_status?: string
  attendee_stats?: AttendeeStats
  attendees?: EventAttendee[]
}

// ============================================
// Activity Grouping & Aggregation
// ============================================

/**
 * A group of activities under a date label (Today, Yesterday, etc.)
 */
export interface ActivityGroup {
  label: string
  date: string
  items: (ActivityItem | AggregatedActivity)[]
}

/**
 * Multiple consecutive same-user/type/action activities collapsed into one card
 */
export interface AggregatedActivity {
  isAggregated: true
  user: string
  user_name: string
  user_image?: string
  type: string
  action: string
  count: number
  items: ActivityItem[]
  timestamp: string
  projects: string[]
}

/**
 * Response from get_activity_details API.
 * Contains full activity details including changes and notes.
 */
export interface ActivityDetails {
  doctype: string
  name: string
  title: string
  modified: string
  modified_by: string
  modified_by_name: string
  changes: ActivityChange[]
  notes: ActivityNote[]
  is_pinned: boolean
  is_archived: boolean
  can_delete: boolean
}

// ============================================
// Manager Tab Type
// ============================================

/**
 * Tab definition for Manager panels
 */
export interface ManagerTab {
  /** Unique identifier for the tab */
  id: string
  /** FontAwesome icon class (without fa-solid prefix) */
  icon: string
  /** Display label (shown in tooltip) */
  label: string
}

// ============================================
// Theme Types
// ============================================

/**
 * Theme mode setting (light/dark/auto)
 */
export type ThemeMode = 'light' | 'dark' | 'auto'

/**
 * Resolved theme after applying auto detection
 */
export type ResolvedTheme = 'light' | 'dark'

// ============================================
// Calendar Event Type
// ============================================

export interface CalendarEvent {
  id: string
  title: string
  start: string
  end?: string
  allDay?: boolean
  type: EventType
  event_name: string
  project?: string
  color?: string
}

// ============================================
// Report Types
// ============================================

export interface ProjectSummaryReport {
  summary: {
    total_projects: number
    by_status: Record<string, number>
    by_health: Record<string, number>
    total_budget: number
    total_spent: number
    avg_progress: number
  }
  projects: OrgaProject[]
  generated_at: string
}

export interface ContactUtilizationReport {
  resources: ContactUtilization[]
  date_range: { from: string; to: string }
  summary: {
    total_contacts: number
    overallocated: number
    busy: number
    available: number
  }
  generated_at: string
}

export interface ContactUtilization {
  resource: string
  resource_name: string
  email?: string
  department?: string
  weekly_capacity: number
  allocated_hours: number
  actual_hours: number
  utilization_percent: number
  assignment_count: number
  status: 'overallocated' | 'busy' | 'available'
}

export interface TaskCompletionReport {
  tasks: OrgaTask[]
  date_range: { from: string; to: string }
  summary: {
    total_completed: number
    on_time: number
    late: number
    on_time_rate: number
    total_estimated_hours: number
    total_actual_hours: number
    efficiency: number
  }
  by_priority: Record<string, number>
  by_project: Record<string, number>
  generated_at: string
}

export interface BudgetTrackingReport {
  projects: (OrgaProject & {
    remaining: number
    utilization_percent: number
    budget_status: 'over' | 'on_track' | 'under'
  })[]
  summary: {
    total_budget: number
    total_spent: number
    total_remaining: number
    overall_utilization: number
    projects_over_budget: number
    projects_on_track: number
    projects_under_budget: number
  }
  generated_at: string
}

export interface MilestoneReport {
  milestones: OrgaMilestone[]
  summary: {
    total: number
    upcoming: number
    completed: number
    missed: number
  }
  generated_at: string
}

// ============================================
// Filter Types
// Index signatures allow passing to Record<string, unknown> API calls
// ============================================

export interface ProjectFilters {
  [key: string]: unknown
  status?: ProjectStatus
  project_type?: ProjectType
  project_manager?: string
  department?: string
  limit?: number
  offset?: number
  order_by?: string
}

export interface TaskFilters {
  [key: string]: unknown
  project?: string
  status?: TaskStatus
  priority?: TaskPriority
  assigned_to?: string
  limit?: number
  offset?: number
}

export interface ContactFilters {
  [key: string]: unknown
  status?: ContactStatus
  department?: string
  skill?: string
  limit?: number
  offset?: number
}

export interface DefectFilters {
  [key: string]: unknown
  contact?: string
  project?: string
  status?: DefectStatus
  severity?: DefectSeverity
  limit?: number
  offset?: number
}

export interface EventFilters {
  [key: string]: unknown
  project?: string
  resource?: string
  event_type?: EventType
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

export interface TimeLogFilters {
  [key: string]: unknown
  task?: string
  project?: string
  user?: string
  event?: string
  tracking_context?: TrackingContext
  limit?: number
  offset?: number
}

// ============================================
// Orga Notification Types (Phase 6)
// ============================================

export type NotificationType =
  | 'Assignment'
  | 'Status Change'
  | 'Comment'
  | 'Mention'
  | 'Deadline'
  | 'System'

export interface OrgaNotification extends OrgaDocument {
  notification_type: NotificationType
  subject: string
  message?: string
  recipient: string
  is_read: 0 | 1
  read_at?: string
  reference_doctype?: string
  reference_name?: string
  from_user?: string
  from_user_name?: string
  email_sent: 0 | 1
}

export interface NotificationFilters {
  [key: string]: unknown
  unread_only?: boolean
  limit?: number
  offset?: number
}

// ============================================
// Gantt Types (Phase 7)
// ============================================

export type DependencyType = 'FS' | 'SS' | 'FF' | 'SF'

// Bulk dependency edge returned by get_project_dependencies
export interface ProjectDependencyEdge {
  task: string
  depends_on: string
  dependency_type: string  // Full form: 'Finish to Start', etc.
  lag_days: number
  task_subject: string
  task_status: string
  depends_on_subject: string
  depends_on_status: string
}

export interface TaskDependencyInfo {
  task_id: string
  task_name: string
  type: DependencyType
  lag: number  // days (negative = lead)
  status?: string
}

export interface GanttTask extends OrgaTask {
  // Extended for Gantt view
  type?: 'task'  // Discriminator for GanttItem union
  duration?: number  // calculated from dates
  dependencies_info?: TaskDependencyInfo[]
  dependents_info?: TaskDependencyInfo[]
  budget?: number
  spent?: number
  is_blocked?: boolean
}

// Milestone representation for Gantt chart (diamond marker)
export interface GanttMilestone {
  name: string
  subject: string  // milestone_name mapped to subject for consistency
  type: 'milestone'
  status: MilestoneStatus
  start_date: string  // Same as due_date (single point)
  due_date: string
  progress: number  // Calculated from linked task completion percentage
  project: string
  description?: string
  completed_date?: string
  sort_order?: number
  task_count?: number
}

// Union type for all Gantt chart items
export type GanttItem = GanttTask | GanttMilestone

// Type guard for checking if item is a milestone
export function isGanttMilestone(item: GanttItem): item is GanttMilestone {
  return item.type === 'milestone'
}

// Type guard for checking if item is a task
export function isGanttTask(item: GanttItem): item is GanttTask {
  return item.type !== 'milestone'
}

export interface CascadeChange {
  task_id: string
  task_name: string
  field: 'start_date' | 'end_date'
  old_value: string
  new_value: string
  days_shift: number
}

export interface CascadePreviewResult {
  affected_tasks: CascadeChange[]
  total_affected: number
}

// ============================================
// Webhook Types (Phase 7)
// ============================================

export interface OrgaWebhook extends OrgaDocument {
  webhook_name: string
  url: string
  secret?: string
  is_active: 0 | 1
  events: WebhookEvent[]
  last_delivery?: string
  last_status?: 'Success' | 'Failed' | 'Pending'
}

export interface WebhookEvent {
  name?: string
  event_name: string
}

export type WebhookEventType =
  | 'project.created'
  | 'project.updated'
  | 'project.completed'
  | 'task.created'
  | 'task.updated'
  | 'task.completed'
  | 'task.assigned'
  | 'resource.created'
  | 'event.created'
  | 'event.rsvp'
  | 'client.created'
  | 'client.updated'
  | 'client.invited'

// ============================================
// Orga Client Types (Phase 8)
// ============================================

export type ClientStatus = 'Active' | 'Inactive' | 'Pending'

export interface OrgaClient extends OrgaDocument {
  client_name: string
  company?: string
  email: string
  phone?: string
  user?: string
  status: ClientStatus
  portal_enabled: 0 | 1
  last_login?: string
  // Address
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  country?: string
  // Notes
  notes?: string
  // Computed
  project_count?: number
}

export interface ClientFilters {
  [key: string]: unknown
  status?: ClientStatus
  company?: string
  portal_enabled?: 0 | 1
  limit?: number
  offset?: number
}

export interface ClientWithProjects extends OrgaClient {
  projects: OrgaProject[]
  milestones: OrgaMilestone[]
}

// ============================================
// Due Diligence / External Company Types (Phase 4)
// ============================================

/**
 * Note types for categorizing activity comments
 */
export type NoteType = 'General' | 'Due Diligence' | 'Offer' | 'Decision'

/**
 * Visibility levels for notes
 */
export type NoteVisibility = 'Internal' | 'Team' | 'Public'

/**
 * Due diligence note with extended fields
 */
export interface DueDiligenceNote {
  name: string
  user: string
  user_fullname: string
  user_image?: string
  content: string
  creation: string
  note_type: NoteType
  visibility: NoteVisibility
  related_company?: string
  can_delete: boolean
}

/**
 * Response from get_due_diligence_notes API
 */
export interface DueDiligenceNotesResponse {
  notes: DueDiligenceNote[]
  has_more: boolean
  total: number
  type_counts: Record<NoteType, number>
}

/**
 * Compliance/due diligence status for an activity
 */
export interface ComplianceStatus {
  has_due_diligence: boolean
  due_diligence_count: number
  has_decision: boolean
  has_offer: boolean
  is_flagged: boolean
  last_note_date: string | null
  checklist_progress: number
  type_counts: Record<NoteType, number>
}

/**
 * External company activity info for display
 */
export interface ExternalCompanyInfo {
  company_name: string
  contact_name?: string
  contact_email?: string
  value?: number
  can_make_offer: boolean
}

/**
 * Extended ActivityItem with external company fields
 */
export interface ExternalActivityItem extends ActivityItem {
  company_name?: string
  contact_name?: string
  contact_email?: string
  value?: number
  can_make_offer?: boolean
  due_diligence_notes?: DueDiligenceNote[]
  compliance_status?: ComplianceStatus
}

// ============================================
// File Attachment Types
// ============================================

/**
 * Represents a file attached to a project or task via Frappe's File DocType.
 */
export interface OrgaFileAttachment {
  name: string
  file_name: string
  file_url: string
  file_size: number
  file_type?: string
  is_private: number
  creation: string
  owner: string
  attached_to_name?: string
}

/**
 * Documents grouped by context (project-level vs task-level).
 */
export interface GroupedDocuments {
  project: OrgaFileAttachment[]
  byTask: Record<string, { taskSubject: string; files: OrgaFileAttachment[] }>
  totalCount: number
}

/**
 * Related document for Manager panel display
 */
export interface RelatedDocument {
  doctype: string
  name: string
  title: string
  status?: string
  relationship: 'parent' | 'child' | 'reference' | 'linked'
}

// ============================================
// Search Types
// ============================================

export type SearchCategory = '' | 'project' | 'task' | 'resource' | 'milestone' | 'event'

export interface SearchResultItem {
  name: string
  label: string
  description?: string
  status?: string
  extra?: string
  category: SearchCategory
}

export interface SearchResults {
  projects: SearchResultItem[]
  tasks: SearchResultItem[]
  contacts: SearchResultItem[]
  milestones: SearchResultItem[]
  events: SearchResultItem[]
}

export interface SearchResponse {
  results: SearchResults
  total: number
}

// ============================================
// Update Checker
// ============================================

export interface UpdateInfo {
  current_version: string
  latest_version: string
  update_available: boolean
  release_url: string
  release_notes: string
  published_at: string
  checked_at: string
}
