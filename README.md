# Orga

**Project Management for Frappe Framework**

[![Version](https://img.shields.io/badge/version-0.14.0-blue.svg)](https://github.com/tonic-6101/orga/releases)
[![Frappe](https://img.shields.io/badge/frappe-v15+-green.svg)](https://frappeframework.com)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)

Orga is a comprehensive project management application built on Frappe Framework. Designed for teams who need powerful project tracking without leaving their Frappe ecosystem, Orga offers everything from simple task management to team coordination.

---

## Features

### Project Management

Organize your work into projects with automatic code generation, visual progress tracking, and health monitoring.

- Create projects with auto-generated codes (ORG-YYYY-NNNN)
- Track status through lifecycle stages (Planning, Active, On Hold, Completed)
- Monitor progress calculated automatically from task completion
- Set budgets and track spending
- Assign project managers and link to departments

### Task Tracking

Break down projects into actionable tasks with priorities, assignments, and deadlines. Track progress through customizable workflows.

- Four-column Kanban board with drag-and-drop
- List and Gantt chart views
- Priority levels (Urgent, High, Medium, Low)
- Task checklists with completion tracking
- Threaded comments and discussions
- Task dependencies with circular detection
- Subtask support for complex work breakdown

### Gantt Chart Visualization

Plan timelines with an interactive Gantt chart view showing task dependencies and progress at a glance.

- Timeline view with task bars and milestones
- Visual dependency lines between tasks
- Today marker for current date orientation
- Cascade preview shows impact of date changes
- Click any task to edit in the focus panel

### Resource Management

Build a registry of your team members, track skills, and manage workload allocation across projects.

- Team member profiles with capacity settings
- Skills tracking with proficiency levels
- Workload visualization with utilization percentages
- Assignment management with allocated hours
- Overallocation warnings

### Appointment Scheduling

Coordinate meetings, deadlines, and milestones with a visual calendar and automatic reminders.

- Monthly calendar view with event colors
- Meeting, deadline, review, and milestone types
- Invite attendees with RSVP tracking
- Automatic email reminders
- Location and meeting URL support

### Project Health Monitoring

Automatic health calculation helps identify at-risk projects before they become problems.

- Weighted scoring based on schedule, budget, tasks, and milestones
- Green/Yellow/Red status indicators
- Actionable improvement recommendations
- Dashboard widgets for quick overview

### Custom Workflows

Define workflows that match your team's processes with states, transitions, and role-based permissions.

- Create custom states with colors
- Define allowed transitions
- Role-based permissions per transition
- Workflow action buttons on documents

### Automation Rules

Automate repetitive tasks with rules that trigger on document events.

- Trigger on create, update, status change, or assignment
- Condition-based execution
- Actions: set field values, assign users, send notifications, add comments

### In-App Notifications

Stay informed with real-time notifications for assignments, mentions, and deadlines.

- Notification bell with unread count
- Assignment and status change alerts
- @mention support in comments
- Deadline reminders

### Client Portal

Register external clients and grant them portal access to view their project progress.

- Client management with contact details
- Link clients to projects
- Portal access with automatic user provisioning
- Clients see only their linked projects

### Reports

Generate insights on project status, resource utilization, and task completion.

- Project Summary Report
- Resource Utilization Report
- Task Completion Report
- Budget Tracking Report
- Milestone Report

### Integrations

Connect Orga to external systems and other Frappe applications.

- **Webhooks**: Notify external systems on 25+ event types with HMAC signing
- **Import/Export**: Bulk operations via CSV and JSON
- **Frappe Projects**: Optional sync with built-in Projects module
- **ERPNext**: Link resources to Employees, export time logs to Timesheets

---

## Installation

### Prerequisites

- Frappe Framework v15 or higher
- Python 3.10+
- Node.js 18+
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

### Access the Application

After installation, access Orga at: `https://your-site.localhost/orga`

---

## Quick Start

1. **Create a Project**: Navigate to Projects and click "New Project"
2. **Add Tasks**: Open your project and add tasks to the Kanban board
3. **Assign Team Members**: Create resources and assign them to tasks
4. **Track Progress**: Watch your project progress update automatically
5. **Schedule Meetings**: Use the calendar to coordinate team appointments

---

## Documentation

- [Getting Started Guide](docs/user-guide/getting-started.md)
- [API Reference](docs/developer-guide/API.md)
- [Changelog](docs/CHANGELOG.md)
- [FAQ](docs/user-guide/faq.md)

---

## Technology Stack

- **Backend**: Frappe Framework, Python 3.10+
- **Frontend**: Vue 3, TypeScript, Tailwind CSS
- **UI Components**: FrappeUI
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

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/tonic-6101/orga/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tonic-6101/orga/discussions)

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with [Frappe Framework](https://frappeframework.com) and [FrappeUI](https://github.com/frappe/frappe-ui).
