# Getting Started with Orga

This guide will help you set up Orga and create your first project.

## Installation

### Prerequisites
- Frappe Framework v15 or later
- A working Frappe site

### Install the App

```bash
# Get the app
bench get-app orga

# Install on your site
bench --site your-site.localhost install-app orga

# Run migrations
bench --site your-site.localhost migrate
```

After installation, you'll find the **Orga** workspace in your Frappe desk.

## Creating Your First Project

1. **Open Orga Workspace**
   - Click on the Orga icon in the sidebar, or
   - Search for "Orga" in the search bar

2. **Create a New Project**
   - Click **New Orga Project**
   - Fill in the required fields:
     - **Project Name**: Give your project a descriptive name
     - **Start Date**: When work begins
     - **End Date**: Target completion date
     - **Project Manager**: Who's responsible
   - Click **Save**

3. **Your Project Code**
   - Orga automatically generates a unique project code (e.g., `ORG-2026-0001`)
   - Use this code to reference the project

## Adding Tasks

### Quick Method: From Project View

The fastest way to add tasks is directly from your project:

1. **Using the Toolbar Button**
   - Open your project in the Project Detail view
   - Click the **Add Task** button in the toolbar
   - Fill in the task details and click **Create Task**
   - The task appears immediately in your Kanban board

2. **Using Kanban Quick-Add**
   - In Kanban view, find the column for the status you want
   - Click the **+ Add Task** button at the bottom of any column
   - The task form opens with the status already set
   - Great for quickly adding tasks to specific workflow stages

3. **Using Keyboard Shortcuts**
   - Press **Shift+T** anywhere in the project view to open the task form
   - Fill in the details and submit
   - Perfect for power users who prefer keyboard navigation

### Standard Method: From Task List

1. **Create a Task**
   - Go to **Orga Task** → **New**
   - Fill in:
     - **Subject**: What needs to be done
     - **Project**: Link to your project
     - **Priority**: Low, Medium, High, or Urgent
     - **Assigned To**: Team member responsible

### Track Progress

Update task status as work progresses:
- **Open** → Work not started
- **In Progress** → Currently being worked on
- **Review** → Ready for review
- **Completed** → Done!

Drag and drop tasks between columns in Kanban view to change status.

## Setting Up Milestones

Milestones mark key checkpoints in your project.

### Quick Method: From Project View

1. **Using the Toolbar Button**
   - Open your project in the Project Detail view
   - Click the **Add Milestone** button in the toolbar
   - Enter the milestone name, target date, and description
   - Click **Create Milestone**
   - The milestone appears in your project's milestone section

2. **Using Keyboard Shortcut**
   - Press **Shift+M** anywhere in the project view
   - Fill in the milestone details
   - Submit to create the milestone instantly

### Standard Method: From Milestone List

1. **Create a Milestone**
   - Go to **Orga Milestone** → **New**
   - Set:
     - **Milestone Name**: What you're delivering
     - **Project**: Which project this belongs to
     - **Due Date**: When it should be complete

### Link Tasks to Milestones

- When creating or editing tasks, select the relevant milestone
- This helps track what needs to be done for each deliverable
- Milestone completion percentage automatically updates based on linked task progress

## Managing Resources

Resources represent your team members and contractors.

### Adding Team Members

1. **Create a Resource**
   - Navigate to **Orga Resource** → **New**
   - Fill in:
     - **Resource Name**: Full name
     - **Type**: Employee, Contractor, or External
     - **Status**: Active, Inactive, or On Leave
     - **Weekly Capacity**: Available hours per week (default: 40)
   - Optionally link to a Frappe User for system integration

2. **Add Skills**
   - In the resource form, scroll to the Skills section
   - Add skills with:
     - **Skill Name**: e.g., "Project Management", "Python"
     - **Proficiency**: Beginner, Intermediate, Advanced, or Expert
     - **Years Experience**: How long they've had this skill

### Assigning Resources to Tasks

1. **Create an Assignment**
   - Go to **Orga Assignment** → **New**
   - Select:
     - **Task**: Which task needs this resource
     - **Resource**: Who will work on it
     - **Allocated Hours**: How many hours for this task
     - **Role**: Their role (Lead, Support, etc.)

2. **Track Workload**
   - View the Resources page to see workload bars
   - Green = Available
   - Yellow = Moderate load
   - Orange = Busy
   - Red = Overallocated

## Understanding Project Health

Orga automatically calculates health status for your projects:

- **Green**: Project is on track (score 75 or higher)
- **Yellow**: Project needs attention (score 50-74)
- **Red**: Project is at risk (score below 50)

Health is calculated based on:
- Schedule adherence (are you on track with the timeline?)
- Budget utilization (spending aligned with progress?)
- Task completion (are tasks being completed on time?)
- Milestone achievement (are milestones being met?)

View project health on the Dashboard.

## Viewing Your Dashboard

The Orga dashboard provides an overview of your projects and tasks:

- **Project Statistics**: Total projects by status
- **Task Overview**: Tasks by status and priority
- **Project Health**: Visual breakdown of Green/Yellow/Red projects
- **At-Risk Projects**: Projects needing immediate attention
- **Overdue Items**: Tasks and milestones that need attention
- **Team Workload**: Who's working on what

## User Roles

Orga includes two roles:

### Orga Manager
- Create, edit, and delete projects
- Manage all tasks and milestones
- Configure settings
- Full access to all Orga features

### Orga User
- Create projects and tasks
- Edit tasks assigned to them
- View project information
- Cannot delete projects or others' tasks

Your system administrator can assign these roles to users.

## Next Steps

- Explore the [FAQ](faq.md) for common questions
- Check [Troubleshooting](troubleshooting.md) if you encounter issues
- Developers can review the [API Reference](../developer-guide/API.md)
