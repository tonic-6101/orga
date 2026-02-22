# Changelog

All notable changes to Orga will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.14.0] - 2026-02-22

### Fixed

- Remove debug console.log from cascade preview handler
- Add missing translation wrappers to 404 page (NotFound.vue)

### Changed

- Bump version to 0.14.0 for initial public GitHub release

---

## [0.13.0] - 2026-02-22

### Added

#### Version Management & Update Checker

- **Sidebar version display**: The sidebar footer now shows "Community Edition" with the current version number, plus GitHub and LinkedIn icons
- **Automated update checking**: A daily scheduled job checks the GitHub releases API for newer versions and caches results in Redis for 24 hours
- **Sidebar update indicator**: When a newer version is available, an amber "Update" link appears next to the version number (or a pulsing amber dot when the sidebar is collapsed)
- **Settings Updates tab**: View installed vs. latest version, read release notes preview, open the GitHub release page, dismiss notifications, or manually check for updates
- **Dismiss per version**: Dismiss an update notification and it stays hidden until a newer version is released
- **Version sync tooling**: `bump_version.py` script keeps version numbers consistent across VERSION, `__init__.py`, setup.py, package.json, and README badge

#### Auto-Trail Start

- **Per-task Auto-Trail Start checkbox**: Enable on any task to keep its start date trailing forward to today while the task is Open with 0% progress. Due date shifts by the same offset to preserve task duration
- **Project-level default**: Enable Auto-Trail Start as a project default from the settings gear menu. New tasks inherit the setting automatically; individual tasks can override it
- **Create Task integration**: The Auto-Trail Start option appears in the task creation form, pre-checked when the project default is active
- **Daily scheduled job**: Overnight catch-up job updates all trailing tasks whose start dates fell behind, even if they weren't opened during the day

### Notes

Trailing stops automatically when the task moves out of Open status or any progress is recorded. This keeps Gantt charts and schedules forward-looking without manual date maintenance.

---

## [0.12.0] - 2026-02-17

### Added

#### Dependency Scheduling

- **Dependency modes**: Choose how date changes cascade through your project — Flexible (preview before applying), Strict (automatic cascade), or Off (informational only)
- **Successor advancement on completion**: When you complete a task, its Finish-to-Start successors automatically move to the earliest valid start date, preserving task duration
- **Blocked task indicators**: Tasks with incomplete predecessors show an amber lock badge and are dimmed on Kanban and List views. Hover to see which tasks are blocking
- **Unblock notifications**: Assignees receive an in-app notification when all predecessors complete and their task becomes unblocked
- **Critical path highlighting**: Toggle on the Gantt chart to see the longest chain of dependent tasks. Critical tasks get a red ring; non-critical tasks dim. Any delay on a critical task pushes back the project end date
- **Hammock tasks**: A scheduling type that auto-spans the gap between its predecessor's end and successor's start. Duration is calculated, not set manually
- **Buffer tasks**: Explicit schedule padding with consumption tracking. Visual traffic-light indicator (green/yellow/red) shows how much buffer has been consumed by upstream delays
- **Drag-to-create dependencies**: Hover a task bar on the Gantt chart, drag from the connection handle to another task to create a Finish-to-Start dependency visually
- **Group dependencies**: Set "Depends on Group" to block a task until all tasks in that group are complete

#### Developer APIs

- `reschedule_dependents` — trigger cascade based on project dependency mode
- `preview_cascade` / `apply_cascade` — preview and apply date cascade changes
- `get_critical_path` — calculate critical path and float values using CPM algorithm

### Notes

This release adds comprehensive dependency scheduling to Orga. Projects can now control how date changes propagate through task chains, with three modes to suit different team workflows. Completing a task automatically advances its successors. Visual indicators on Kanban and List views make blocked tasks immediately obvious. The Gantt chart gains critical path highlighting, advanced scheduling types (hammock and buffer), and drag-to-create dependencies.

---

## [0.11.0] - 2026-02-08

### Added

#### Dark Mode

- Choose between System, Light, and Dark themes using the new three-button selector in the user menu
- All pages respect your system preference by default, or pick a theme manually
- Dark mode applies consistently across every view: dashboard, projects, Gantt, schedule, resources, and settings
- No flash of light theme on page load — your preference is applied instantly

#### Team & Documents in Project View

- See your project team at a glance with avatar circles in the project detail page
- Project managers are highlighted with a star badge
- View attached documents with file type icons and formatted file sizes
- New bottom bar layout: Project Info, Team, Milestones, Documents

#### Gantt Chart Improvements

- Drag task bars to reschedule directly on the timeline
- See task dependency arrows connecting related tasks
- Today marker (red line) keeps you oriented on the timeline
- Milestones display at their correct positions on the Gantt
- Sticky header and footer stay visible when scrolling large projects
- Calendar and Gantt views stay synchronized when switching between them

### Fixed

- Task creation form now includes start date for proper Gantt display
- Notification clicks navigate to the correct page
- Manager panel tabs display correctly
- Improved data consistency between frontend and backend for task dependencies

### Changed

- Internal API calls upgraded to use FrappeUI composables for better reliability and type safety

### Notes

This release adds dark mode support, enriches the project detail view with team and document sections, and significantly improves the Gantt chart with drag-to-reschedule, dependency arrows, and a today marker. Several stability fixes improve the overall experience.

---

## [0.10.0] - 2026-02-05

### Added

#### Improved Visual Design

- Refreshed color palette with better contrast for easier reading
- New status indicators combine colors with icons, so you can identify task status at a glance
- Cards and buttons have smoother hover effects that give visual feedback as you interact
- Focus indicators are more visible when navigating with keyboard

#### Better Mobile Experience

- Dashboard and project views now adapt smoothly to phones and tablets
- On mobile, stats cards stack vertically for easier scrolling
- Kanban boards show one column at a time on small screens with easy navigation
- Task panels open as full-screen modals on mobile for easier editing
- All buttons and touch targets are sized for comfortable tapping

#### Loading States That Match Your Layout

- When pages load, you'll see placeholder shapes that match where content will appear
- Dashboard shows skeleton cards for stats, tasks, and activity while loading
- No more jarring layout shifts when content appears
- Smooth transitions from loading to content

#### Toast Notifications

- Get instant feedback when actions complete: "Task updated", "Saved successfully"
- Success, error, and warning messages appear briefly in the corner
- Messages dismiss automatically after a few seconds
- Click to dismiss immediately if you prefer

#### Form Validation Feedback

- Form fields show validation in real-time as you type
- Green checkmarks indicate valid entries
- Error messages appear only after you've interacted with a field
- Character counters help you stay within limits
- Clear visual distinction between valid, invalid, and neutral states

#### Interactive Dashboard

- Click on stat cards to navigate directly to related pages
- Click "Active Projects" to see your projects, "Overdue Tasks" to see what needs attention
- Health bars show tooltips explaining what each color means
- Progress bars are color-coded: green for complete, other colors indicate progress level
- Legend items are clickable for quick filtering

#### Consistent Typography

- Text sizes follow a clear hierarchy across all pages
- Section headers, page titles, and body text are consistently styled
- Better readability with optimized line spacing and font weights

### Changed

#### Task Status Badges

- Status badges now include both color and icon for accessibility
- Open tasks: blue with circle
- In Progress: amber with play icon
- Review: purple with eye icon
- Completed: green with checkmark
- Works better for colorblind users and in bright light conditions

#### Project Detail Layout

- Stats bar adapts to screen size: 3 columns on desktop, stacked on mobile
- Manager panel becomes a full-screen overlay on mobile devices
- View toggle buttons show icons only on mobile to save space

### Notes

This release focuses on making Orga more accessible, more responsive, and more polished. Whether you're working from a phone, tablet, or desktop, the interface adapts to give you the best experience. The new visual feedback—hover effects, loading states, and notifications—helps you understand what's happening as you work. Status badges with icons ensure everyone can quickly identify task status regardless of color perception.

---

## [0.9.1] - 2026-02-04

### Added

#### Create Tasks Directly from Project View

- Click "Add Task" in the project toolbar to create tasks without leaving the page
- Fill in the subject, description, assignee, priority, status, and due date
- Select team members from a dropdown to assign tasks instantly
- Tasks appear immediately in your Kanban board after creation
- Character counter ensures task titles stay concise (255 characters max)

#### Create Milestones from Project View

- Click "Add Milestone" to add project milestones right where you need them
- Set milestone name, description, target date, and status
- Choose from status options: Upcoming, In Progress, Completed, or Missed
- New milestones appear instantly in your project's milestone section

#### Quick-Add Tasks in Kanban

- Each Kanban column now has an "+ Add Task" button at the bottom
- Click to create a task that's automatically assigned to that column's status
- Add "In Progress" tasks directly to the In Progress column
- Add "Review" tasks directly to the Review column
- Speeds up your workflow when organizing work across status columns

#### Keyboard Shortcuts

- Press **Shift+T** to quickly open the task creation dialog
- Press **Shift+M** to quickly open the milestone creation dialog
- Shortcuts are disabled when typing in form fields to avoid conflicts
- Power users can create tasks and milestones without touching the mouse

#### Milestone Management API

- Create, read, update, and delete milestones programmatically
- Get milestone completion percentage based on linked tasks
- List milestones by project with optional status filtering
- Full API documentation available for integrations

### Fixed

- Resolved an issue where project details could fail to load when tasks had certain date formats

### Notes

This release focuses on streamlining task and milestone creation. Instead of navigating to separate forms, you can now create work items directly from your project view. The Kanban quick-add buttons make it even faster to add tasks to specific workflow stages. Keyboard shortcuts help power users stay productive without interrupting their flow.

---

## [0.9.0] - 2026-02-04

### Added

#### Inline Comments on Activities

- Add comments directly on any activity card in your feed
- Start discussions without opening a separate panel
- Reply to comments to create threaded conversations
- Expand or collapse comment threads to focus on what matters
- View the last few comments at a glance, expand to see full history
- Delete your own comments; managers can moderate all comments

#### @Mention in Activity Comments

- Mention team members using @name or @email format
- Type @ and see suggested users as you type
- Mentioned users receive instant notifications
- Keep conversations focused by tagging the right people

#### Quick Reactions

- React to activities with one click: Acknowledge, Celebrate, Seen, or Flag
- See reaction counts showing how your team is engaging
- Hover to see who reacted with each type
- Flag important activities to bring them to your team's attention
- Your reactions are highlighted so you know how you've responded
- Instant visual feedback when you react

#### Event RSVP from Activity Feed

- Respond to appointment invitations directly from the activity feed
- Accept, Decline, or Propose an alternative time with quick buttons
- See event details at a glance: date, time, location, and attendees
- View who has accepted with attendee avatars
- Track attendance: "3/5 accepted" shows response rates
- Propose alternative meeting times when the original doesn't work

#### Due Diligence Workflows

- Categorize activity notes by type: General, Due Diligence, Offer, or Decision
- Control note visibility: Internal, Team, or Public
- Track compliance status across your activities
- Link notes to external companies for relationship management
- Flag activities for escalation or follow-up
- Progress indicators show completion status

#### Enhanced Activity Manager

- **Comments Tab**: Full threaded comment history with @mention support
- **Due Diligence Checklist**: Standard checklist with progress tracking
  - Initial Review, Documentation Review, Risk Assessment
  - Offer Prepared, Final Decision checkpoints
  - Visual progress bar shows completion percentage
- **Related Documents**: See linked projects, tasks, and appointments
  - Quick navigation to related items
  - Relationship indicators (parent, child, linked)
- **Enhanced Change History**: Grouped by date with full diff view
  - Changes organized as Today, Yesterday, or specific dates
  - Filter by field to find specific changes
  - See who made each change with user avatars
  - Expand long values for complete comparison

#### Activity Manager (Foundation)

- Take action on activities instead of just viewing history
- Open any activity to see full details in a side panel
- Five organized tabs: Details, Changes, Comments, Notes, and Actions
- Pin important activities to keep them at the top of your feed
- Archive old activities to declutter your feed
- Navigate directly to related tasks, projects, or appointments

#### Developer APIs

- Comment endpoints: get comments, add comment, delete comment, get replies
- @mention autocomplete endpoint for user search
- Reaction endpoints: toggle reaction, get reaction counts and users
- RSVP endpoints: update RSVP status, propose alternative times
- Due diligence endpoints: add typed notes, get compliance status
- Related documents endpoint for linked item discovery

### Notes

This release transforms the Activity feed into a fully interactive action center. Users can now comment, react, RSVP, and manage due diligence workflows directly from activity cards. The Manager panel has been enhanced with a full comments tab, due diligence checklists, and improved change history. Teams can collaborate more effectively without leaving the context of their work.

---

## [0.8.0] - 2026-02-04

### Added

#### Client Management
- Register and manage external clients with contact details and company information
- Track client status (Active, Inactive, Pending) to manage relationships
- Link clients to projects for clear ownership and accountability
- Store client addresses for complete contact records

#### Client Portal Access
- Grant clients secure access to view their project information
- Automatic portal user creation when inviting clients
- Role-based permissions ensure clients only see their own linked projects
- Track client portal activity including last login

#### Client API
- Complete REST API for client management (create, read, update, delete)
- Invite clients to the portal with automatic user provisioning
- Link and unlink projects to clients programmatically
- Retrieve client projects and milestones via API

### Changed

- Projects now support linking to Orga Client records for external stakeholder management
- Added "Orga Client" role for portal access permissions

### Notes

This release introduces client management capabilities. Organizations can now register external clients, link them to projects, and grant portal access for project visibility. Clients see only their linked projects, ensuring proper access control.

---

## [0.7.0] - 2026-02-04

### Added

#### Gantt Chart View
- Visualize project timelines with interactive Gantt charts
- View tasks as horizontal bars positioned by date on a timeline
- Color-coded task bars by status (Open, Working, Review, Completed)
- Priority indicators show task importance at a glance
- Today marker helps orient your view on the timeline
- Click any task to open the focus panel for quick editing
- Toggle between Kanban, List, and Gantt views on project pages

#### Gantt Focus Panel
- Edit task details directly from the Gantt view
- See task dependencies in a visual flowchart
- Preview how date changes cascade to dependent tasks before committing
- View budget burn rate for tasks with assigned budgets
- Keyboard shortcuts for fast navigation (E=edit, D=dependency, Esc=close)

#### Webhook Integrations
- Configure webhooks to notify external systems when events occur
- Support for 25+ event types across projects, tasks, resources, and appointments
- HMAC-SHA256 payload signing for secure webhook delivery
- Automatic retry logic for failed deliveries
- Track delivery status and troubleshoot integration issues
- Test webhooks before deploying to production

#### Import/Export Tools
- Export projects, tasks, and resources to CSV or JSON format
- Export time logs and generate timesheet reports
- Import tasks and resources from CSV files
- Validation checks before import to catch errors early
- Download CSV templates to ensure correct format

#### Frappe Projects Integration (Optional)
- Sync projects between Orga and Frappe's built-in Projects module
- Two-way task synchronization with status mapping
- Migration tools for teams transitioning from Frappe Projects
- Preview changes before committing sync operations

#### ERPNext Integration (Optional)
- Link resources to ERPNext Employee records
- Auto-populate resource details from Employee data
- Export Orga time logs to ERPNext Timesheets
- Calculate project billing summaries from time entries
- Sync employee status changes automatically

#### Developer APIs
- Webhook configuration API (create, update, test, delete)
- Import/export API endpoints for bulk operations
- Integration status endpoints for sync monitoring

### Notes

This release adds visualization and integration features. The Gantt chart provides timeline visualization for project planning. Webhooks enable real-time notifications to external systems. Import/export tools support bulk data operations, and optional integrations with Frappe Projects and ERPNext enable unified workflows.

---

## [0.6.0] - 2026-02-03

### Added

#### Custom Workflows
- Define custom workflows for tasks and projects with multiple states and transitions
- Configure workflow states with custom colors for visual identification
- Set transition rules that control who can move items between states
- Apply role-based permissions so only authorized users can perform specific transitions
- Add Python conditions for advanced transition logic when needed
- Activate one workflow per document type with automatic state assignment

#### Workflow Actions
- See available workflow actions directly on tasks and projects
- One-click transitions between workflow states
- Visual state indicators show current workflow position
- Workflow management page for creating and editing workflows

#### In-App Notifications
- Notification bell icon in the header shows unread count at a glance
- Click to see recent notifications in a dropdown panel
- Mark individual notifications as read or clear all at once
- Click through to jump directly to related documents
- Notification types include assignments, status changes, comments, mentions, deadlines, and workflow updates

#### @Mentions
- Mention team members in comments using @email or @name format
- Mentioned users receive automatic notifications
- Stay informed when colleagues need your attention

#### Deadline Reminders
- Automatic notifications for upcoming task deadlines
- Receive reminders for tasks due today, tomorrow, and in three days
- Never miss an important deadline with proactive alerts

#### Automation Rules
- Create rules that automatically perform actions when events occur
- Trigger on task creation, updates, status changes, or assignments
- Define conditions to control when rules execute
- Automatic actions include setting field values, sending notifications, adding comments, and assigning users
- Test rules before activation to verify behavior

#### Developer APIs
- Complete workflow API for custom integrations (9 endpoints)
- Notification API for building custom notification experiences (5 endpoints)
- Automation API for managing rules programmatically (8 endpoints)

### Notes

This release brings workflow automation to Orga. Teams can now define custom workflows that match their processes, receive in-app notifications to stay informed, and create automation rules to eliminate repetitive manual work. The TypeScript migration from 0.5.1 is included in this release.

---

## [0.5.1] - 2026-02-03

### Changed

#### Frontend TypeScript Migration
- The entire frontend codebase has been migrated to TypeScript for improved code quality and developer experience
- All Vue components now use TypeScript with full type safety
- Comprehensive type definitions for all Orga data types (projects, tasks, resources, appointments)
- Type definitions for Frappe framework integration
- Improved IDE support with autocompletion and error detection

#### Developer Experience
- Better code documentation through TypeScript interfaces
- Reduced runtime errors through compile-time type checking
- Easier onboarding for new contributors with self-documenting types

### Notes

This release focuses on code quality improvements. There are no user-facing changes—the application works exactly as before, but with a more maintainable and robust codebase. Developers extending Orga will benefit from TypeScript's type safety and improved tooling support.

---

## [0.5.0] - 2026-02-03

### Added

*(Portfolios moved to orga_pro)*

#### Project Health Monitoring
- Automatic health status calculation for every project (Green, Yellow, Red)
- Health scores based on schedule adherence, budget utilization, task completion, and milestone achievement
- Visual health indicators on dashboard views
- At-risk projects highlighted for immediate attention
- Actionable recommendations when projects need attention

#### Health Dashboard Widgets
- New "Project Health" widget showing health distribution across all projects
- Quick view of projects needing attention with click-through navigation
- Visual health bars showing Green/Yellow/Red project counts

#### Reports
- **Project Summary Report**: Overview of all projects with status and health breakdown
- **Resource Utilization Report**: Team workload and availability status
- **Task Completion Report**: On-time vs. late completions with efficiency metrics
- **Budget Tracking Report**: Budget variance analysis showing over/under status
- **Milestone Report**: Upcoming and overdue milestone tracking

#### Developer APIs
- Project health endpoints for custom integrations
- Five report endpoints for data export and analysis
- Metrics recalculation endpoints for on-demand updates

### Notes

This release adds project health monitoring and reports. Project managers can now monitor health across their projects and generate reports to track progress and identify issues early.

---

## [0.4.0] - 2026-02-03

### Added

#### Appointment Scheduling
- Create and manage appointments for meetings, deadlines, reviews, and milestones
- Schedule single events or all-day events with flexible date and time options
- Add physical locations or video conference links to appointments
- Link appointments to projects, tasks, or milestones for context

#### Team Invitations
- Invite team members to appointments directly from the create form
- Search and select attendees by name or email
- Mark attendees as required or optional for each event
- Send automatic email invitations when creating appointments
- Track RSVP responses (Accepted, Declined, Tentative, Pending)

#### Schedule Calendar
- View all appointments in a clean monthly calendar layout
- Navigate between months to see past or upcoming events
- Jump to today with a single click
- See events color-coded by type at a glance
- Filter by project to focus on specific work streams
- Filter by event type to see only meetings, deadlines, or milestones

#### Appointment Details
- Click any event to see full details in a side panel
- View attendee list with RSVP status for each person
- Access meeting links directly from the appointment view
- See related project, task, or milestone information
- RSVP to appointments you're invited to with one click

#### Email Reminders
- Receive automatic email reminders before appointments
- Configure reminder timing for each appointment
- Reminders include event details, location, and meeting links
- Only attendees who haven't declined receive reminders

#### Developer APIs
- Complete REST API for appointment management
- Endpoints for creating, updating, and deleting appointments
- Attendee management endpoints (add, remove, update RSVP)
- Calendar events endpoint for custom calendar integrations
- Send invitations programmatically

### Changed

- "Focus" panel renamed to "Manager" panel in project task view for clarity

### Notes

This release adds full appointment scheduling to Orga. Teams can now coordinate meetings, track deadlines, and keep everyone informed with automatic invitations and reminders.

---

## [0.3.0] - 2026-02-03

### Added

#### Resource Management
- Create and manage team members as resources with unique identifiers
- Track resource type (Employee, Contractor, External) and status (Active, Inactive, On Leave)
- Link resources to Frappe Users for seamless integration with your existing team
- Set weekly capacity hours to enable capacity planning

#### Skills Tracking
- Define skills for each resource with proficiency levels (Beginner, Intermediate, Advanced, Expert)
- Record years of experience for each skill
- Search for resources by skill name and minimum proficiency level
- Identify the right team members for specific tasks based on expertise

#### Workload Visualization
- See at-a-glance workload status for each resource
- Visual progress bars show current utilization percentage
- Color-coded indicators highlight overallocated, busy, and available team members
- Hover tooltips display detailed capacity information

#### Task Assignments
- Assign resources to tasks with allocated hours
- Track assignment status through its lifecycle (Assigned, In Progress, Completed, Cancelled)
- Define roles for each assignment (Lead, Support, etc.)
- Set start and end dates for time-bounded allocations
- Automatic prevention of duplicate assignments

#### Resource Panel
- View comprehensive resource details in a side panel
- See all skills with proficiency badges
- Review current assignments with task status
- Quick access from the resources grid

#### Developer APIs
- Complete REST API for resources (create, read, update, delete)
- Skill management endpoints (add/remove skills)
- Assignment API for task allocation
- Workload calculation endpoints for custom integrations

### Notes

This release adds full resource management capabilities to Orga. Teams can now track who's available, what skills they have, and how their time is allocated across tasks.

---

## [0.2.0] - 2026-02-03

### Added

#### Task Checklists
- Break down tasks into checklist items for granular tracking
- Toggle items complete/incomplete with a single click
- See completion progress with a visual progress bar
- Track who completed each item and when

#### Task Comments
- Discuss tasks directly within the task context
- See comment history with author and timestamp
- Delete your own comments; managers can moderate all comments

#### Task Dependencies
- Define which tasks must complete before others can start
- Support for multiple dependency types (Finish-to-Start, Start-to-Start, etc.)
- Configure lag time between dependent tasks
- Automatic detection of circular dependencies to prevent errors
- Tasks automatically marked as "blocked" when dependencies are incomplete

#### Time Tracking
- Log time spent on tasks
- Record start/end times or enter hours directly
- View time summaries by project, task, or user
- Automatic calculation of actual hours on tasks

#### Kanban Drag-and-Drop
- Move tasks between status columns by dragging
- Visual feedback during drag operations
- Instant status updates without page reload

#### Task Focus Panel
- View full task details in a side panel
- Manage checklists and comments without leaving the board
- Quick status change buttons for fast workflow updates

#### Settings Management
- Configure default task and project status
- Enable/disable time tracking
- Set notification preferences

### Notes

This release introduces comprehensive task management features including checklists, comments, dependencies, and time tracking. The Kanban board now supports drag-and-drop for efficient workflow management.

---

## [0.1.0] - 2026-02-03

### Added

#### Project Management
- Create and manage projects with automatic code generation
- Track project status through lifecycle stages (Planning, Active, On Hold, Completed, Cancelled)
- Set project dates, budgets, and assign project managers
- Monitor project progress automatically calculated from task completion

#### Task Management
- Create tasks linked to projects with priorities (Low, Medium, High, Urgent)
- Track task status through workflow stages (Open, In Progress, Review, Completed, Cancelled)
- Assign tasks to team members
- Set start dates, due dates, and estimated hours
- Organize tasks with parent-child relationships (subtasks)
- Link tasks to milestones for delivery tracking

#### Milestones
- Define key project milestones with due dates
- Track milestone status (Upcoming, In Progress, Completed, Missed)
- Automatic status update when milestones become overdue

#### Dashboard & Reporting
- View project and task statistics at a glance
- See task distribution by status and priority
- Track overdue tasks and upcoming milestones
- Monitor team workload distribution

#### Role-Based Access
- Orga Manager role with full access to all features
- Orga User role for team members with appropriate permissions
- System Manager integration for administrators

#### Developer APIs
- Complete REST API for projects, tasks, and milestones
- Dashboard statistics endpoint for custom integrations
- Kanban-ready task grouping by status

### Notes

This is the initial release of Orga, a project management module for Frappe. It provides the foundation for organizing projects, tracking tasks, and managing team workloads.

---

## [Unreleased]

### Added

#### Activity Feed UX

- **Date grouping**: Activities are organized under date headers — Today, Yesterday, This Week, Last Week, or a specific date — so you can quickly scan what happened when
- **Activity aggregation**: When the same person makes several similar changes in a row (e.g., completing 4 tasks), the feed collapses them into a single card. Click to expand and see each individual activity
- **Read/unread indicators**: New activities since your last visit show a green left border and dot. The sidebar badge shows the unread count. Clicking an activity marks it as read; leaving the page marks everything as read
- **Mark all as read**: A dedicated button in the header clears all unread indicators at once
- **Rich text comments**: Comment inputs now support formatting (bold, italic, links) via a bubble menu that appears when you select text. @mention autocomplete is built in
- **Keyboard shortcuts**: Navigate the feed with J/K, open the Manager panel with Enter, close with Escape, pin with P, archive with A, reply with R, mark all read with M, and press ? for a help modal
- **Live polling**: The page checks for new activities every 15 seconds. A green banner appears at the top when something new arrives — click to load it. Polling pauses when you switch to another browser tab

#### My Tasks Page
- See all tasks assigned to you across every project in one place
- Filter by status, priority, or project
- Search tasks by name
- Change task status inline without opening the task
- Paginated list for large workloads
- Accessible from the sidebar and Dashboard "View All" link

#### Promote Checklist Item to Task
- Hover over any incomplete checklist item to reveal the promote button
- One click converts the item into a full Orga Task
- New task inherits the parent's project, priority, and milestone
- Original checklist item is removed automatically

#### Task Manager Documentation
- New user guide documenting all 9 Task Manager tabs

---

[0.14.0]: https://github.com/tonic-6101/orga/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/tonic-6101/orga/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/tonic-6101/orga/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/tonic-6101/orga/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/tonic-6101/orga/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/tonic-6101/orga/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/tonic-6101/orga/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/tonic-6101/orga/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/tonic-6101/orga/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/tonic-6101/orga/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/tonic-6101/orga/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/tonic-6101/orga/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/tonic-6101/orga/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/tonic-6101/orga/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/tonic-6101/orga/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/tonic-6101/orga/releases/tag/v0.1.0
