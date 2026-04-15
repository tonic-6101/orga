# Orga

**Project Management for Frappe Framework**

[![Version](https://img.shields.io/badge/version-0.15.8-blue.svg)](https://github.com/tonic-6101/orga/releases)
[![Frappe](https://img.shields.io/badge/frappe-v16+-green.svg)](https://frappeframework.com)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)

Orga is a project management app built on Frappe Framework. It provides Kanban boards, Gantt charts, resource planning, and automation — designed for teams who need project tracking within their Frappe ecosystem.

Part of the [Tonic ecosystem](https://github.com/tonic-6101). Integrates with [Dock](https://github.com/tonic-6101/dock) for calendar, notifications, search, and the people hub, and with [Watch](https://github.com/tonic-6101/watch) for time tracking.

---

## Features

### Project Management

Organize work into projects with automatic code generation, progress tracking, and health monitoring.

- Auto-generated project codes (ORG-YYYY-NNNN)
- Lifecycle stages: Planning, Active, On Hold, Completed
- Progress calculated automatically from task completion
- Budget tracking
- Project manager assignment and department linking

### Task Tracking

Break down projects into tasks with priorities, assignments, deadlines, and dependencies.

- Four-column Kanban board with drag-and-drop
- List view
- Priority levels (Urgent, High, Medium, Low)
- Task checklists with completion tracking
- Task dependencies with circular detection
- Subtask support

### Gantt Chart

Plan timelines with an interactive Gantt chart showing dependencies and progress.

- Timeline view with task bars and milestones
- Visual dependency lines
- Today marker
- Cascade preview for date change impact
- Click-to-edit via focus panel

### Resource Management

Track team members, skills, and workload allocation across projects.

- Team member profiles with capacity settings
- Skills tracking with proficiency levels
- Workload visualization with utilization percentages
- Assignment management with allocated hours
- Overallocation warnings

### Appointments

Coordinate meetings, deadlines, and milestones with attendee tracking and reminders.

- Meeting, deadline, review, and milestone types
- Invite attendees with RSVP tracking
- Automatic email reminders
- Location and meeting URL support
- Synced to Dock's unified calendar for viewing

### Project Health Monitoring

Automatic health scoring identifies at-risk projects.

- Weighted scoring based on schedule, budget, tasks, and milestones
- Green / Yellow / Red status indicators
- Actionable improvement recommendations

### Automation Rules

Automate repetitive tasks with event-driven rules.

- Trigger on create, update, status change, or assignment
- Condition-based execution
- Actions: set field values, assign users, send notifications, add comments

### Client Portal

Register external clients and grant portal access to view project progress.

- Client management with contact details
- Link clients to projects
- Portal access with automatic user provisioning (via Dock portal framework)
- Clients see only their linked projects

### Reports

- Project Summary
- Resource Utilization
- Task Completion
- Budget Tracking
- Milestone

### Integrations

- **Dock**: Calendar sync, notifications, activity feed, people hub, global search, settings hub
- **Watch**: Time tracking on tasks, projects, and appointments
- **Webhooks**: Notify external systems on 25+ event types with HMAC signing
- **Import/Export**: Bulk operations via CSV and JSON
- **Frappe Projects**: Optional two-way sync with built-in Projects module
- **ERPNext**: Link resources to Employees, export time logs to Timesheets

---

## Installation

### Prerequisites

- Frappe Framework v16+
- [Dock](https://github.com/tonic-6101/dock) (required dependency)
- Python 3.14+
- Node.js 24+
- MariaDB 10.6+

### Install via Bench

```bash
# Get the app
bench get-app orga https://github.com/tonic-6101/orga.git

# Install on your site
bench --site your-site.localhost install-app orga

# Run migrations
bench --site your-site.localhost migrate

# Build assets
bench build --app orga
```

### Access

After installation, access Orga at: `https://your-site.localhost/orga`

---

## Quick Start

1. **Create a Project** — Navigate to Projects and click "New Project"
2. **Add Tasks** — Open your project and add tasks to the Kanban board
3. **Assign Resources** — Create resources and assign them to tasks
4. **Track Progress** — Project progress updates automatically from task completion
5. **Schedule Appointments** — Create appointments that sync to Dock's calendar

---

## Technology Stack

- **Backend**: Frappe Framework v16+, Python
- **Frontend**: Vue 3, TypeScript, Tailwind CSS, FrappeUI
- **Database**: MariaDB

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Support

- **Issues**: [GitHub Issues](https://github.com/tonic-6101/orga/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tonic-6101/orga/discussions)

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for details.

---

Built with [Frappe Framework](https://frappeframework.com) and [FrappeUI](https://github.com/frappe/frappe-ui).
