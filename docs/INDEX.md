# Orga Documentation

**Orga** is a project management module for Frappe that helps teams organize projects, track tasks, and manage workloads effectively.

## Quick Links

- [Getting Started](user-guide/getting-started.md) - Installation and first steps
- [API Reference](developer-guide/API.md) - Developer integration guide
- [Changelog](CHANGELOG.md) - Release history

## Features

### Project Management
Organize your work into projects with automatic code generation, status tracking, and progress monitoring.

### Task Tracking
Break down projects into actionable tasks. Assign team members, set priorities, and track progress through customizable workflows.

### Task Manager
View and edit every aspect of a task in one place. The Task Manager panel opens when you click any task and organizes nine tabs — Details, Dependencies, Time, Finance, Checklist, Discussion, Files, Actions, and Cascade (Gantt only) — behind an icon-based tab bar. See the [Task Manager guide](user-guide/task-manager.md) for a walkthrough of each tab.

### My Tasks
See all tasks assigned to you across every project on a single page. Filter by status, priority, project, or assignee, search by name, and change task status inline without opening the task. Sort by due date, task name, project, priority, or status — your preference is remembered across sessions. See the [My Tasks Sorting guide](user-guide/my-tasks-sorting.md) for details. Accessible from the sidebar and the Dashboard's "View All" link.

### Task Checklists
Add checklist items to tasks for granular tracking. See progress at a glance with visual indicators. Hover over any incomplete item and click the promote button to convert it into a full Orga Task that inherits the parent's project, priority, and milestone.

### Discussion
Collaborate on any document with threaded comments, rich text formatting, and @mentions. Resolve threads when questions are answered and pin important messages to the top. See the [Discussion guide](user-guide/discussion.md) for details.

### Task Dependencies
Define task relationships to ensure work happens in the right order. Automatic blocking prevents starting tasks before dependencies complete.

### Dependency Scheduling
Control how completing or rescheduling tasks affects their successors. Choose between Flexible (preview before applying), Strict (automatic cascade), or Off modes per project. Completing a predecessor automatically advances successor start dates. Visual indicators show blocked tasks across Kanban, List, and Gantt views. See the [Dependency Scheduling guide](user-guide/dependency-scheduling.md) for details.

### Critical Path
Highlight the longest chain of dependent tasks on the Gantt chart. Any delay on a critical task pushes back the project end date. Toggle the critical path view to focus on what matters most.

### Auto-Trail Start
Keep task start dates from falling into the past while tasks are still unworked. When enabled, the start date trails forward to today automatically, preserving the planned duration. Set it per task or as a project-wide default for new tasks. See the [Auto-Trail Start guide](user-guide/auto-trail-start.md) for details.

### Advanced Scheduling Types
Hammock tasks auto-span gaps between predecessors and successors. Buffer tasks provide explicit schedule padding with consumption tracking.

### Time Tracking
Track time across tasks, events, projects, or standalone work. Use the global timer (start/stop from any page) or log hours manually. A floating timer in the header keeps the active session visible while you navigate. View today's time summary on the Schedule page and compare estimated vs. actual hours per task.

### Kanban Board
Drag tasks between columns to update status instantly. Visual workflow management at its best.

### Milestones
Define key deliverables and checkpoints. Stay on track with automatic overdue detection.

### Resource Management
Build a registry of your team members. Track employee types, availability, and link to Frappe users.

### Skills Tracking
Define skills for each resource with proficiency levels. Find the right person for the job based on expertise.

### Workload Visualization
See utilization at a glance with visual progress bars. Identify overallocated team members before problems arise.

### Task Assignments
Allocate resources to tasks with hours and dates. Track who's working on what across all projects.

### Appointment Scheduling
Create meetings, deadlines, reviews, and milestones. Link appointments to projects and track them on a visual calendar.

### Team Invitations
Invite team members to appointments with automatic email invitations. Track RSVP responses to know who's attending.

### Schedule Calendar
View appointments in a monthly calendar. Filter by project or event type, and navigate through time with ease.

### Email Reminders
Never miss an appointment with automatic email reminders. Configure timing per event and receive all relevant details.

### Project Health Monitoring
Automatic health status calculation (Green, Yellow, Red) based on schedule, budget, tasks, and milestones. Identify at-risk projects before they become problems.

### Reports
Generate reports on project status, resource utilization, task completion, budget tracking, and milestones. Export data for stakeholder updates and planning.

### Custom Workflows
Define workflows that match your team's processes. Set up states and transitions with role-based permissions. Documents automatically follow the workflow when actions are performed.

### In-App Notifications
Stay informed with a notification bell that shows unread counts. Receive alerts for assignments, mentions, status changes, and deadlines directly in the application.

### @Mentions
Mention team members in comments to get their attention. Type @ followed by a name or email to notify someone about a task or update.

### Automation Rules
Create rules that automatically perform actions when conditions are met. Set field values, send notifications, or assign tasks without manual intervention.

### Gantt Chart View
Visualize project timelines with interactive Gantt charts. View tasks as horizontal bars, see dependencies, and quickly adjust schedules with the focus panel. Group tasks by status, priority, milestone, or assignee with collapsible headers. See the [Gantt Grouping guide](user-guide/gantt-grouping.md) for details.

### Activity Feed
See what's happening across your projects in a structured, scannable feed. Activities are grouped by date and aggregated when the same person makes multiple similar changes. Unread indicators and a sidebar badge show what's new since your last visit. Navigate with keyboard shortcuts (J/K/Enter/Escape) and get live updates via a banner that appears when new activities arrive. See the [Activity Feed guide](user-guide/activity-feed.md) for details.

### Activity Manager
Take action on activities instead of just viewing history. Pin important items, add notes for annotations, archive old activities, and view detailed change history—all from an organized tabbed panel.

### Client Management
Register external clients and link them to projects. Grant clients portal access to view project progress, milestones, and status updates.

### Webhook Integrations
Configure webhooks to notify external systems when events occur. Secure HMAC-SHA256 signing ensures payload integrity.

### Import/Export
Export projects, tasks, and resources to CSV or JSON. Import bulk data from spreadsheets with validation and templates.

### Frappe Projects Integration
Optionally sync with Frappe's built-in Projects module. Migrate existing projects or maintain two-way synchronization.

### ERPNext Integration
Link resources to ERPNext Employees and export time logs to Timesheets. Unified workflows for organizations using ERPNext.

### Role-Based Access
Control who can view, edit, and manage different aspects of your projects.

### Responsive Design
Work from any device—desktop, tablet, or phone. Layouts adapt automatically to give you the best experience on any screen size.

### Accessibility
Navigate entirely with keyboard if you prefer. Clear focus indicators, sufficient color contrast, and status icons that don't rely on color alone make Orga usable for everyone.

### Dark Mode
Switch between System, Light, and Dark themes using the selector in the user menu. All views adapt to your chosen theme with no flash on page load. See the [Dark Mode guide](user-guide/dark-mode.md) for details.

### Hammock & Buffer Tasks
Use advanced scheduling types for flexible project planning. Hammock tasks auto-span gaps between dependencies. Buffer tasks provide explicit schedule padding with consumption tracking. See the [Hammock & Buffer Tasks guide](user-guide/hammock-buffer-tasks.md) for details.

### Rich Text Comments
Format comments with bold, italic, and links using a bubble menu. Mention team members with @autocomplete to notify them. See the [Rich Text Comments guide](user-guide/rich-text-comments.md) for details.

### Keyboard Shortcuts
Navigate the Activity Feed with J/K, create tasks with Shift+T, edit Gantt tasks with E, and more. Press ? on the Activity page for the full list. See the [Keyboard Shortcuts guide](user-guide/keyboard-shortcuts.md) for details.

### Version Updates
Orga checks for new versions daily and shows an indicator in the sidebar when an update is available. View details, release notes, and dismiss notifications from the Settings page. See the [Version Updates guide](user-guide/version-updates.md) for details.

### Real-Time Feedback
See instant feedback for your actions with toast notifications. Loading states show you exactly what's happening, and form validation helps you get things right the first time.

## Documentation Sections

### For Users
- [Getting Started](user-guide/getting-started.md) - Set up your first project
- [Task Manager](user-guide/task-manager.md) - Guide to the task editing panel
- [Dependency Scheduling](user-guide/dependency-scheduling.md) - Cascade modes, blocked tasks, critical path
- [Auto-Trail Start](user-guide/auto-trail-start.md) - Keep task dates current while unworked
- [My Tasks Sorting](user-guide/my-tasks-sorting.md) - Sort your task list by any column
- [Discussion](user-guide/discussion.md) - Threaded comments, resolve threads, pin messages
- [Activity Feed](user-guide/activity-feed.md) - Date grouping, unread tracking, keyboard shortcuts, live updates
- [Dark Mode](user-guide/dark-mode.md) - Theme selection (System, Light, Dark)
- [Gantt Grouping](user-guide/gantt-grouping.md) - Group tasks by status, priority, milestone, or assignee
- [Hammock & Buffer Tasks](user-guide/hammock-buffer-tasks.md) - Advanced scheduling types
- [Rich Text Comments](user-guide/rich-text-comments.md) - Formatting and @mentions
- [Keyboard Shortcuts](user-guide/keyboard-shortcuts.md) - Activity, Project, and Gantt shortcuts
- [Version Updates](user-guide/version-updates.md) - Update notifications and checking
- [FAQ](user-guide/faq.md) - Common questions answered
- [Troubleshooting](user-guide/troubleshooting.md) - Solutions to common issues

### For Developers
- [API Reference](developer-guide/API.md) - Integrate Orga with your systems
- [Architecture](developer-guide/ARCHITECTURE.md) - Technical overview (Vue 3 + TypeScript frontend)

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/tonic-6101/orga/issues)
- **Discussions**: Ask questions on [GitHub Discussions](https://github.com/tonic-6101/orga/discussions)

## License

GNU Affero General Public License v3.0 (AGPL-3.0) - See [LICENSE](../LICENSE) file for details.
