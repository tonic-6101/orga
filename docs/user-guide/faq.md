# Frequently Asked Questions

## General

### What is Orga?
Orga is a project management module for Frappe that helps teams organize projects, track tasks, and manage workloads.

### Does Orga require ERPNext?
No. Orga is a standalone Frappe app and works with any Frappe installation. ERPNext is not required.

### What Frappe version is required?
Orga requires Frappe v15 or later.

## Projects

### How are project codes generated?
Project codes are automatically generated in the format `ORG-YYYY-NNNN` (e.g., `ORG-2026-0001`). You can also specify a custom code when creating a project.

### Can I change a project code after creation?
Project codes are used as document identifiers. Changing them may affect linked tasks and milestones. It's recommended to use the auto-generated code or set a custom code at creation time.

### What do the project statuses mean?
- **Planning**: Project is being planned, work hasn't started
- **Active**: Project is in progress
- **On Hold**: Project is temporarily paused
- **Completed**: Project is finished
- **Cancelled**: Project was cancelled

### How is project progress calculated?
Progress is automatically calculated based on the percentage of completed tasks. If a project has 10 tasks and 5 are completed, progress shows 50%.

## Tasks

### What's the difference between task statuses?
- **Open**: Task is ready to be worked on
- **In Progress**: Someone is actively working on it
- **Review**: Work is done, waiting for review
- **Completed**: Task is finished and approved
- **Cancelled**: Task was cancelled or not needed

### Can I create subtasks?
Yes. When editing a task, you can set a "Parent Task" to create a hierarchy. This helps organize complex work into smaller pieces.

### What happens when I complete a task?
When you change a task status to "Completed", the completion date is automatically recorded. The parent project's progress is also recalculated.

### Can I assign a task to multiple people?
Currently, each task can have one assignee. For work requiring multiple people, consider creating separate subtasks for each person's portion.

### What's the fastest way to create tasks?
The fastest methods are:
1. **Kanban Quick-Add**: Click "+ Add Task" at the bottom of any Kanban column
2. **Keyboard Shortcut**: Press **Shift+T** in the project view
3. **Toolbar Button**: Click "Add Task" in the project toolbar

All these methods create tasks without leaving your project view.

### Are there keyboard shortcuts?
Yes! In the Project Detail view:
- **Shift+T** - Open the task creation form
- **Shift+M** - Open the milestone creation form

Shortcuts are disabled when you're typing in form fields.

## Milestones

### What happens when a milestone is overdue?
If a milestone's due date passes and it's not marked as "Completed", Orga automatically changes its status to "Missed" to highlight it needs attention.

### Can I have milestones without tasks?
Yes. Milestones can exist independently as project checkpoints. However, linking tasks to milestones helps track what work is needed for each deliverable.

## Project Health

### How is project health calculated?
Health is calculated using four factors:
- **Schedule (30%)**: Is actual progress keeping pace with the timeline?
- **Budget (25%)**: Is spending aligned with progress?
- **Tasks (25%)**: Are tasks being completed on time?
- **Milestones (20%)**: Are milestones being achieved?

### What do the health colors mean?
- **Green**: Score of 75 or higher - project is healthy
- **Yellow**: Score of 50-74 - project needs attention
- **Red**: Score below 50 - project is at risk

### How often is health updated?
Health status is automatically recalculated every 4 hours. You can also manually trigger a recalculation from the API.

### What should I do if a project turns Red?
Review the health breakdown to see which factors are low. Common issues include:
- Overdue tasks that need to be completed or rescheduled
- Budget overruns that need to be addressed
- Missed milestones that need to be rescheduled
- Timeline delays that require project adjustment

## Permissions

### Who can delete projects?
Only users with the "Orga Manager" role or "System Manager" can delete projects. Additionally, projects with linked tasks cannot be deleted until the tasks are removed first.

### Can I see only my assigned tasks?
Yes. Use the "My Tasks" view or filter the task list by your username in the "Assigned To" field.

## Technical

### How do I access Orga via API?
See the [API Reference](../developer-guide/API.md) for details on available endpoints and how to use them.

### Where is data stored?
Orga data is stored in your Frappe/MariaDB database in tables prefixed with `tabOrga` (e.g., `tabOrga Project`, `tabOrga Task`).

### Can I customize the fields?
Yes. As standard Frappe DocTypes, you can add custom fields through Frappe's Customize Form feature. However, modifying core fields may affect functionality.
