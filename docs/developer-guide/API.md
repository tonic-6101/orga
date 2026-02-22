# Orga API Reference

This document describes the REST API endpoints available in Orga for developers building integrations.

## Authentication

All API calls require authentication. Use Frappe's standard authentication methods:
- Session-based authentication (for web applications)
- API keys (for server-to-server communication)
- OAuth 2.0 (for third-party applications)

## Base URL

All endpoints are prefixed with:
```
/api/method/orga.orga.api
```

## Projects API

### Get Projects

Retrieve a list of projects with optional filters.

```
POST /api/method/orga.orga.api.project.get_projects
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| status | string | Filter by status (Planning, Active, On Hold, Completed, Cancelled) |
| project_type | string | Filter by type (Internal, Client, Mixed) |
| project_manager | string | Filter by manager (User ID) |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset (default: 0) |

**Response:**
```json
{
  "message": {
    "projects": [
      {
        "name": "ORG-2026-0001",
        "project_name": "Website Redesign",
        "project_code": "ORG-2026-0001",
        "status": "Active",
        "project_type": "Client",
        "start_date": "2026-02-01",
        "end_date": "2026-04-30",
        "progress": 35.5,
        "project_manager": "john@example.com",
        "task_count": 12,
        "completed_tasks": 4
      }
    ],
    "total": 1
  }
}
```

### Get Single Project

Retrieve detailed information about a specific project.

```
POST /api/method/orga.orga.api.project.get_project
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Project ID (e.g., "ORG-2026-0001") |

**Response:**
```json
{
  "message": {
    "project": {
      "name": "ORG-2026-0001",
      "project_name": "Website Redesign",
      "description": "Complete website overhaul",
      "status": "Active",
      "progress": 35.5,
      "tasks": [...],
      "milestones": [...]
    }
  }
}
```

### Get Project Statistics

Get task and milestone statistics for a project.

```
POST /api/method/orga.orga.api.project.get_project_stats
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Project ID |

**Response:**
```json
{
  "message": {
    "tasks": {
      "total": 12,
      "open": 4,
      "in_progress": 3,
      "completed": 5,
      "overdue": 1
    },
    "milestones": {
      "total": 3,
      "upcoming": 2,
      "completed": 1
    }
  }
}
```

---

## Milestones API

### Get Milestones

Retrieve milestones for a project with optional status filtering.

```
POST /api/method/orga.orga.api.milestone.get_milestones
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project | string | Yes | Project ID to get milestones for |
| status | string | No | Filter by status (Upcoming, In Progress, Completed, Missed) |
| limit | integer | No | Maximum results (default: 50) |
| offset | integer | No | Pagination offset (default: 0) |

**Response:**
```json
{
  "message": {
    "milestones": [
      {
        "name": "MIL-00001",
        "milestone_name": "Phase 1 Complete",
        "status": "Upcoming",
        "due_date": "2026-03-15",
        "completed_date": null,
        "description": "Complete all Phase 1 deliverables",
        "completion_percentage": 45,
        "task_count": 8
      }
    ],
    "total": 1
  }
}
```

### Get Single Milestone

Retrieve detailed information about a specific milestone, including linked tasks.

```
POST /api/method/orga.orga.api.milestone.get_milestone
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Milestone ID |

**Response:**
```json
{
  "message": {
    "name": "MIL-00001",
    "milestone_name": "Phase 1 Complete",
    "project": "ORG-2026-0001",
    "status": "Upcoming",
    "due_date": "2026-03-15",
    "description": "Complete all Phase 1 deliverables",
    "completion_criteria": "All 8 tasks marked as complete",
    "completion_percentage": 45,
    "tasks": [
      {
        "name": "TASK-00001",
        "subject": "Design mockups",
        "status": "Completed",
        "priority": "High",
        "assigned_to": "designer@example.com",
        "due_date": "2026-02-28"
      }
    ]
  }
}
```

### Create Milestone

Create a new milestone for a project.

```
POST /api/method/orga.orga.api.milestone.create_milestone
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | JSON | Yes | Milestone data (see below) |

**Data Object:**
```json
{
  "milestone_name": "Phase 2 Launch",
  "project": "ORG-2026-0001",
  "due_date": "2026-04-30",
  "description": "Launch phase 2 features",
  "status": "Upcoming"
}
```

**Required Fields:** `milestone_name`, `project`

**Response:**
```json
{
  "message": {
    "name": "MIL-00002",
    "milestone_name": "Phase 2 Launch",
    "status": "Upcoming",
    "due_date": "2026-04-30",
    "project": "ORG-2026-0001"
  }
}
```

### Update Milestone

Update an existing milestone's fields.

```
POST /api/method/orga.orga.api.milestone.update_milestone
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Milestone ID |
| data | JSON | Yes | Fields to update |

**Updatable Fields:** `milestone_name`, `description`, `status`, `due_date`, `completion_criteria`

**Response:**
```json
{
  "message": {
    "name": "MIL-00002",
    "milestone_name": "Phase 2 Launch",
    "status": "In Progress",
    "due_date": "2026-04-30",
    "completion_percentage": 25
  }
}
```

### Delete Milestone

Delete a milestone. Any tasks linked to this milestone will be unlinked (not deleted).

```
POST /api/method/orga.orga.api.milestone.delete_milestone
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Milestone ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "unlinked_tasks": 3
  }
}
```

---

## Tasks API

### Get Tasks

Retrieve tasks with optional filters.

```
POST /api/method/orga.orga.api.task.get_tasks
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project ID |
| status | string | Filter by status |
| priority | string | Filter by priority (Low, Medium, High, Urgent) |
| assigned_to | string | Filter by assignee |
| milestone | string | Filter by milestone |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "tasks": [
      {
        "name": "TASK-00001",
        "subject": "Design homepage mockup",
        "status": "In Progress",
        "priority": "High",
        "due_date": "2026-02-15",
        "assigned_to": "jane@example.com",
        "project": "ORG-2026-0001",
        "progress": 50
      }
    ],
    "total": 1
  }
}
```

### Get Single Task

Retrieve detailed task information.

```
POST /api/method/orga.orga.api.task.get_task
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Task ID (e.g., "TASK-00001") |

### Update Task Status

Quick status update for Kanban-style operations.

```
POST /api/method/orga.orga.api.task.update_task_status
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Task ID |
| status | string | Yes | New status (Open, In Progress, Review, Completed, Cancelled) |

**Response:**
```json
{
  "message": {
    "name": "TASK-00001",
    "status": "In Progress",
    "modified": "2026-02-03 10:30:00"
  }
}
```

### Get Tasks by Status

Get tasks grouped by status (ideal for Kanban views).

```
POST /api/method/orga.orga.api.task.get_tasks_by_status
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project | string | Yes | Project ID |

**Response:**
```json
{
  "message": {
    "Open": [...],
    "In Progress": [...],
    "Review": [...],
    "Completed": [...],
    "Cancelled": [...]
  }
}
```

### Get My Tasks

Get tasks assigned to the current user.

```
POST /api/method/orga.orga.api.task.get_my_tasks
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| status | string | Filter by status |
| limit | integer | Maximum results |

---

## Checklist API

### Get Task Checklist

Get all checklist items for a task.

```
POST /api/method/orga.orga.api.task.get_task_checklist
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |

**Response:**
```json
{
  "message": [
    {
      "name": "abc123",
      "title": "Review requirements",
      "is_completed": 1,
      "completed_by": "jane@example.com",
      "completed_on": "2026-02-03 10:30:00"
    }
  ]
}
```

### Add Checklist Item

Add a new checklist item to a task.

```
POST /api/method/orga.orga.api.task.add_checklist_item
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| title | string | Yes | Item title |

### Toggle Checklist Item

Toggle completion status of a checklist item.

```
POST /api/method/orga.orga.api.task.toggle_checklist_item
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| item_name | string | Yes | Checklist item ID |

### Delete Checklist Item

Remove a checklist item from a task.

```
POST /api/method/orga.orga.api.task.delete_checklist_item
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| item_name | string | Yes | Checklist item ID |

---

## Comments API

### Get Task Comments

Get all comments for a task.

```
POST /api/method/orga.orga.api.task.get_task_comments
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |

**Response:**
```json
{
  "message": [
    {
      "name": "comment123",
      "comment_by": "jane@example.com",
      "comment_by_name": "Jane Smith",
      "comment_time": "2026-02-03 10:30:00",
      "content": "This looks good, moving to review."
    }
  ]
}
```

### Add Task Comment

Add a comment to a task.

```
POST /api/method/orga.orga.api.task.add_task_comment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| content | string | Yes | Comment text |

### Delete Task Comment

Remove a comment from a task. Users can delete their own comments; Orga Managers can delete any comment.

```
POST /api/method/orga.orga.api.task.delete_task_comment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| comment_name | string | Yes | Comment ID |

---

## Dependencies API

### Get Task Dependencies

Get dependency information for a task.

```
POST /api/method/orga.orga.api.task.get_task_dependencies
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |

**Response:**
```json
{
  "message": {
    "depends_on": [
      {
        "name": "TASK-00002",
        "subject": "Complete design",
        "status": "Completed",
        "dependency_type": "Finish to Start",
        "lag_days": 0
      }
    ],
    "depended_by": [
      {
        "parent": "TASK-00004",
        "subject": "QA Testing",
        "status": "Open"
      }
    ],
    "is_blocked": false
  }
}
```

### Add Task Dependency

Create a dependency between tasks.

```
POST /api/method/orga.orga.api.task.add_task_dependency
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task that depends on another |
| depends_on | string | Yes | Task that must complete first |
| dependency_type | string | No | Type (default: "Finish to Start") |
| lag_days | integer | No | Days between tasks (default: 0) |

**Dependency Types:**
- `Finish to Start` - Task B starts when Task A finishes
- `Start to Start` - Task B starts when Task A starts
- `Finish to Finish` - Task B finishes when Task A finishes
- `Start to Finish` - Task B finishes when Task A starts

### Remove Task Dependency

Remove a dependency relationship.

```
POST /api/method/orga.orga.api.task.remove_task_dependency
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |
| depends_on | string | Yes | Dependency to remove |

---

## Time Tracking API

### Get Time Logs

Retrieve time log entries with optional filters.

```
POST /api/method/orga.orga.api.timelog.get_time_logs
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| task | string | Filter by task ID |
| project | string | Filter by project ID |
| user | string | Filter by user |
| limit | integer | Maximum results (default: 50) |

**Response:**
```json
{
  "message": [
    {
      "name": "TL-00001",
      "task": "TASK-00001",
      "task_subject": "Design homepage",
      "project": "ORG-2026-0001",
      "user": "jane@example.com",
      "user_name": "Jane Smith",
      "from_time": "2026-02-03 09:00:00",
      "to_time": "2026-02-03 12:00:00",
      "hours": 3.0,
      "description": "Initial mockups"
    }
  ]
}
```

### Create Time Log

Log time against a task.

```
POST /api/method/orga.orga.api.timelog.create_time_log
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task | string | Yes | Task ID |
| hours | float | Yes | Hours to log |
| description | string | No | Work description |
| from_time | datetime | No | Start time (defaults to now) |

### Get Time Summary

Get aggregated time statistics.

```
POST /api/method/orga.orga.api.timelog.get_time_summary
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project |
| user | string | Filter by user |

**Response:**
```json
{
  "message": {
    "total_hours": 45.5,
    "log_count": 12
  }
}
```

### Get My Time Logs

Get time logs for the current user.

```
POST /api/method/orga.orga.api.timelog.get_my_time_logs
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | integer | Maximum results (default: 20) |

---

## Settings API

### Get Settings

Retrieve Orga configuration settings.

```
POST /api/method/orga.orga.api.settings.get_settings
```

**Response:**
```json
{
  "message": {
    "default_task_status": "Open",
    "default_project_status": "Planning",
    "default_priority": "Medium",
    "enable_time_tracking": 1,
    "notify_on_task_assignment": 1
  }
}
```

### Update Settings

Modify Orga settings (requires Orga Manager role).

```
POST /api/method/orga.orga.api.settings.update_settings
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | object | Yes | Settings to update (JSON) |

**Allowed Fields:**
- `default_task_status`
- `default_project_status`
- `default_priority`
- `enable_time_tracking`
- `notify_on_task_assignment`
- `notify_on_status_change`
- `notify_on_due_date`

---

## Dashboard API

### Get Statistics

Get comprehensive dashboard statistics.

```
POST /api/method/orga.orga.api.dashboard.get_stats
```

**Response:**
```json
{
  "message": {
    "projects": {
      "total": 10,
      "by_status": {
        "planning": 2,
        "active": 5,
        "on_hold": 1,
        "completed": 2
      }
    },
    "tasks": {
      "total": 50,
      "by_status": {...},
      "by_priority": {...},
      "overdue": 3,
      "due_this_week": 8
    },
    "milestones": {
      "total": 15,
      "upcoming": 5
    }
  }
}
```

### Get Recent Activity

Get recent changes across projects and tasks.

```
POST /api/method/orga.orga.api.dashboard.get_recent_activity
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | integer | Maximum results (default: 20) |

### Get Overdue Tasks

Get all tasks past their due date.

```
POST /api/method/orga.orga.api.dashboard.get_overdue_tasks
```

### Get Upcoming Milestones

Get milestones due within a specified period.

```
POST /api/method/orga.orga.api.dashboard.get_upcoming_milestones
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| days | integer | Days ahead to look (default: 30) |

### Get Workload by User

Get task distribution across team members.

```
POST /api/method/orga.orga.api.dashboard.get_workload_by_user
```

---

## Resources API

### Get Resources

Retrieve a list of team resources with optional filters.

```
POST /api/method/orga.orga.api.resource.get_resources
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| status | string | Filter by status (Active, Inactive, On Leave) |
| department | string | Filter by department |
| resource_type | string | Filter by type (Employee, Contractor, External) |
| skill | string | Filter by skill name |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "resources": [
      {
        "name": "RES-00001",
        "resource_name": "Jane Smith",
        "email": "jane@example.com",
        "resource_type": "Employee",
        "status": "Active",
        "weekly_capacity": 40,
        "active_assignments": 3,
        "allocated_hours": 32.5,
        "utilization_percent": 81.3,
        "workload_status": "busy",
        "initials": "JS",
        "skills": [
          {
            "skill_name": "Project Management",
            "proficiency": "Expert",
            "years_experience": 5
          }
        ]
      }
    ],
    "total": 1
  }
}
```

### Get Single Resource

Retrieve detailed information about a specific resource.

```
POST /api/method/orga.orga.api.resource.get_resource
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Resource ID (e.g., "RES-00001") |

**Response:**
```json
{
  "message": {
    "name": "RES-00001",
    "resource_name": "Jane Smith",
    "email": "jane@example.com",
    "status": "Active",
    "weekly_capacity": 40,
    "skills": [...],
    "assignments": [...],
    "workload": {
      "allocated_hours": 32.5,
      "assignment_count": 3,
      "utilization_percent": 81.3
    }
  }
}
```

### Create Resource

Create a new team resource.

```
POST /api/method/orga.orga.api.resource.create_resource
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | object | Yes | Resource data (JSON) |

**Data Fields:**
- `resource_name` (required) - Full name
- `user` - Link to Frappe User
- `email` - Email address
- `resource_type` - Employee, Contractor, or External
- `status` - Active, Inactive, or On Leave
- `department` - Link to Department
- `designation` - Job title
- `weekly_capacity` - Hours per week (default: 40)

### Update Resource

Update an existing resource.

```
POST /api/method/orga.orga.api.resource.update_resource
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Resource ID |
| data | object | Yes | Fields to update (JSON) |

### Delete Resource

Remove a resource. Resources with active assignments cannot be deleted.

```
POST /api/method/orga.orga.api.resource.delete_resource
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Resource ID |

### Get Resource Workload

Get workload and utilization for a specific time period.

```
POST /api/method/orga.orga.api.resource.get_resource_workload
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Resource ID |
| start_date | date | No | Period start (default: today) |
| end_date | date | No | Period end (default: 7 days from start) |

**Response:**
```json
{
  "message": {
    "resource": "RES-00001",
    "resource_name": "Jane Smith",
    "period": {"start": "2026-02-03", "end": "2026-02-10"},
    "weekly_capacity": 40,
    "allocated_hours": 32.5,
    "utilization_percent": 81.3,
    "status": "busy",
    "assignments": [...]
  }
}
```

### Search Resources by Skill

Find resources with specific skills.

```
POST /api/method/orga.orga.api.resource.search_resources_by_skill
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| skill | string | Yes | Skill name to search |
| min_proficiency | string | No | Minimum level (Beginner, Intermediate, Advanced, Expert) |
| status | string | No | Filter by status (default: Active) |

**Response:**
```json
{
  "message": [
    {
      "name": "RES-00001",
      "resource_name": "Jane Smith",
      "email": "jane@example.com",
      "status": "Active",
      "matched_skill": {
        "skill_name": "Python",
        "proficiency": "Advanced",
        "years_experience": 3
      }
    }
  ]
}
```

### Add Resource Skill

Add a skill to a resource.

```
POST /api/method/orga.orga.api.resource.add_resource_skill
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_name | string | Yes | Resource ID |
| skill_name | string | Yes | Skill name |
| proficiency | string | No | Level (default: Intermediate) |
| years_experience | float | No | Years of experience |

### Remove Resource Skill

Remove a skill from a resource.

```
POST /api/method/orga.orga.api.resource.remove_resource_skill
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_name | string | Yes | Resource ID |
| skill_name | string | Yes | Skill to remove |

---

## Assignments API

### Get Assignments

Retrieve task assignments with optional filters.

```
POST /api/method/orga.orga.api.assignment.get_assignments
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| task | string | Filter by task ID |
| resource | string | Filter by resource ID |
| project | string | Filter by project ID |
| status | string | Filter by status |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "assignments": [
      {
        "name": "ASN-00001",
        "task": "TASK-00001",
        "task_subject": "Design homepage",
        "resource": "RES-00001",
        "resource_name": "Jane Smith",
        "project": "ORG-2026-0001",
        "project_name": "Website Redesign",
        "status": "In Progress",
        "allocated_hours": 20,
        "start_date": "2026-02-01",
        "end_date": "2026-02-15"
      }
    ],
    "total": 1
  }
}
```

### Get Single Assignment

Retrieve detailed assignment information.

```
POST /api/method/orga.orga.api.assignment.get_assignment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Assignment ID (e.g., "ASN-00001") |

### Create Assignment

Allocate a resource to a task.

```
POST /api/method/orga.orga.api.assignment.create_assignment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task | string | Yes | Task ID |
| resource | string | Yes | Resource ID |
| allocated_hours | float | No | Hours to allocate |
| start_date | date | No | Assignment start |
| end_date | date | No | Assignment end |
| role | string | No | Role on this task (e.g., "Lead", "Support") |

**Response:**
```json
{
  "message": {
    "name": "ASN-00001",
    "task": "TASK-00001",
    "resource": "RES-00001",
    "status": "Assigned",
    "allocated_hours": 20
  }
}
```

### Update Assignment

Update an existing assignment.

```
POST /api/method/orga.orga.api.assignment.update_assignment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Assignment ID |
| data | object | Yes | Fields to update (JSON) |

**Allowed Fields:**
- `status` - Assigned, In Progress, Completed, Cancelled
- `role` - Role description
- `start_date` / `end_date` - Date range
- `allocated_hours` - Hours allocation
- `notes` - Additional notes

### Delete Assignment

Remove a task assignment.

```
POST /api/method/orga.orga.api.assignment.delete_assignment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Assignment ID |

### Get Task Assignments

Get all resources assigned to a task.

```
POST /api/method/orga.orga.api.assignment.get_task_assignments
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task ID |

**Response:**
```json
{
  "message": [
    {
      "name": "ASN-00001",
      "resource": "RES-00001",
      "resource_name": "Jane Smith",
      "resource_email": "jane@example.com",
      "initials": "JS",
      "status": "In Progress",
      "role": "Lead",
      "allocated_hours": 20
    }
  ]
}
```

### Get Resource Assignments

Get all tasks assigned to a resource.

```
POST /api/method/orga.orga.api.assignment.get_resource_assignments
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_name | string | Yes | Resource ID |
| status | string | No | Filter by status |
| include_completed | boolean | No | Include completed assignments (default: false) |

**Response:**
```json
{
  "message": [
    {
      "name": "ASN-00001",
      "task": "TASK-00001",
      "task_subject": "Design homepage",
      "task_status": "In Progress",
      "task_priority": "High",
      "project": "ORG-2026-0001",
      "project_name": "Website Redesign",
      "allocated_hours": 20,
      "start_date": "2026-02-01"
    }
  ]
}
```

---

## Appointments API

### Get Appointments

Retrieve appointments with optional filters.

```
POST /api/method/orga.orga.api.appointment.get_appointments
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project ID |
| event_type | string | Filter by type (Meeting, Deadline, Review, Milestone, Other) |
| status | string | Filter by status (Scheduled, Completed, Cancelled) |
| start_date | date | Filter by start date (on or after) |
| end_date | date | Filter by end date (on or before) |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "appointments": [
      {
        "name": "APT-00001",
        "title": "Sprint Planning",
        "event_type": "Meeting",
        "status": "Scheduled",
        "start_date": "2026-02-10",
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "is_all_day": 0,
        "project": "ORG-2026-0001",
        "project_name": "Website Redesign",
        "location": "Conference Room A",
        "meeting_url": "https://meet.example.com/abc123",
        "attendee_count": 5
      }
    ],
    "total": 1
  }
}
```

### Get Single Appointment

Retrieve detailed appointment information including attendees.

```
POST /api/method/orga.orga.api.appointment.get_appointment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Appointment ID (e.g., "APT-00001") |

**Response:**
```json
{
  "message": {
    "name": "APT-00001",
    "title": "Sprint Planning",
    "description": "Bi-weekly sprint planning meeting",
    "event_type": "Meeting",
    "status": "Scheduled",
    "start_date": "2026-02-10",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "is_all_day": 0,
    "project": "ORG-2026-0001",
    "location": "Conference Room A",
    "meeting_url": "https://meet.example.com/abc123",
    "organizer": "john@example.com",
    "organizer_name": "John Doe",
    "attendees": [
      {
        "resource": "RES-00001",
        "resource_name": "Jane Smith",
        "email": "jane@example.com",
        "is_required": 1,
        "rsvp_status": "Accepted"
      }
    ]
  }
}
```

### Create Appointment

Create a new appointment.

```
POST /api/method/orga.orga.api.appointment.create_appointment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | object | Yes | Appointment data (JSON) |

**Data Fields:**
- `title` (required) - Event title
- `event_type` (required) - Meeting, Deadline, Review, Milestone, or Other
- `start_date` (required) - Event date (YYYY-MM-DD)
- `start_time` - Start time (HH:MM:SS) for timed events
- `end_time` - End time (HH:MM:SS) for timed events
- `is_all_day` - Set to 1 for all-day events
- `description` - Event details
- `location` - Physical location
- `meeting_url` - Video conference link
- `project` - Link to Orga Project
- `task` - Link to Orga Task
- `milestone` - Link to Orga Milestone
- `send_reminder` - Set to 1 to enable email reminders
- `reminder_minutes` - Minutes before event to send reminder (default: 60)

**Response:**
```json
{
  "message": {
    "name": "APT-00001",
    "title": "Sprint Planning",
    "status": "Scheduled"
  }
}
```

### Create Appointment with Invitations

Create an appointment and send email invitations in one call.

```
POST /api/method/orga.orga.api.appointment.create_appointment_with_invitations
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | object | Yes | Appointment data (JSON) |
| attendees | array | No | List of attendee objects |
| send_invitations | boolean | No | Whether to send email invitations |

**Attendees Array Format:**
```json
[
  {"resource": "RES-00001", "required": true},
  {"resource": "RES-00002", "required": false}
]
```

### Update Appointment

Update an existing appointment.

```
POST /api/method/orga.orga.api.appointment.update_appointment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Appointment ID |
| data | object | Yes | Fields to update (JSON) |

### Delete Appointment

Remove an appointment.

```
POST /api/method/orga.orga.api.appointment.delete_appointment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Appointment ID |

### Get Calendar Events

Retrieve appointments for calendar display.

```
POST /api/method/orga.orga.api.appointment.get_calendar_events
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| start_date | date | Yes | Calendar period start |
| end_date | date | Yes | Calendar period end |
| project | string | No | Filter by project |
| event_type | string | No | Filter by event type |

**Response:**
```json
{
  "message": [
    {
      "name": "APT-00001",
      "title": "Sprint Planning",
      "event_type": "Meeting",
      "start_date": "2026-02-10",
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "is_all_day": 0,
      "project": "ORG-2026-0001"
    }
  ]
}
```

---

## Attendees API

### Add Attendee

Add an attendee to an appointment.

```
POST /api/method/orga.orga.api.appointment.add_attendee
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment_name | string | Yes | Appointment ID |
| resource | string | Yes | Resource ID |
| is_required | boolean | No | Required attendee (default: true) |

### Remove Attendee

Remove an attendee from an appointment.

```
POST /api/method/orga.orga.api.appointment.remove_attendee
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment_name | string | Yes | Appointment ID |
| resource | string | Yes | Resource ID |

### Update RSVP

Update an attendee's RSVP status.

```
POST /api/method/orga.orga.api.appointment.update_rsvp
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment_name | string | Yes | Appointment ID |
| resource | string | Yes | Resource ID |
| rsvp_status | string | Yes | Status (Accepted, Declined, Tentative) |

**Response:**
```json
{
  "message": {
    "appointment": "APT-00001",
    "resource": "RES-00001",
    "rsvp_status": "Accepted"
  }
}
```

### Send Invitations

Send email invitations to appointment attendees.

```
POST /api/method/orga.orga.api.appointment.send_invitations
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment_name | string | Yes | Appointment ID |

This sends invitation emails to all attendees with "Pending" RSVP status.

---

## Health API

### Get Project Health

Get detailed health analysis for a project.

```
POST /api/method/orga.orga.api.dashboard.get_project_health
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_name | string | Yes | Project ID |

**Response:**
```json
{
  "message": {
    "score": 72.5,
    "status": "Yellow",
    "factors": {
      "schedule": 65,
      "budget": 80,
      "tasks": 75,
      "milestones": 70
    },
    "recommendations": [
      {
        "area": "Schedule",
        "message": "Project is behind schedule. Consider adding resources or adjusting timeline.",
        "severity": "medium"
      }
    ]
  }
}
```

### Get Health Overview

Get health summary across all projects.

```
POST /api/method/orga.orga.api.dashboard.get_health_overview
```

**Response:**
```json
{
  "message": {
    "summary": {"Green": 5, "Yellow": 2, "Red": 1, "Unknown": 0},
    "total": 8,
    "at_risk": [
      {
        "name": "ORG-2026-0003",
        "project_name": "API Integration",
        "health_status": "Red",
        "progress": 20
      }
    ],
    "at_risk_count": 3
  }
}
```

### Recalculate Project Health

Force recalculation of a project's health status.

```
POST /api/method/orga.orga.api.dashboard.recalculate_project_health
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_name | string | Yes | Project ID |

---

## Reports API

### Project Summary Report

Generate a summary report of all projects.

```
POST /api/method/orga.orga.api.reports.get_project_summary_report
```

**Response:**
```json
{
  "message": {
    "summary": {
      "total_projects": 10,
      "by_status": {"Planning": 2, "Active": 5, "Completed": 3},
      "by_health": {"Green": 6, "Yellow": 3, "Red": 1},
      "total_budget": 500000,
      "total_spent": 175000,
      "avg_progress": 45.5
    },
    "projects": [...],
    "generated_at": "2026-02-03 10:30:00"
  }
}
```

### Resource Utilization Report

Generate a report on resource workload and availability.

```
POST /api/method/orga.orga.api.reports.get_resource_utilization_report
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| date_from | date | Period start (default: 30 days ago) |
| date_to | date | Period end (default: today) |
| department | string | Filter by department |

**Response:**
```json
{
  "message": {
    "resources": [
      {
        "resource": "RES-00001",
        "resource_name": "Jane Smith",
        "weekly_capacity": 40,
        "allocated_hours": 38,
        "utilization_percent": 95,
        "status": "busy"
      }
    ],
    "summary": {
      "total_resources": 10,
      "overallocated": 2,
      "busy": 5,
      "available": 3
    },
    "generated_at": "2026-02-03 10:30:00"
  }
}
```

### Task Completion Report

Generate a report on task completion rates.

```
POST /api/method/orga.orga.api.reports.get_task_completion_report
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project ID |
| date_from | date | Period start (default: 30 days ago) |
| date_to | date | Period end (default: today) |

**Response:**
```json
{
  "message": {
    "summary": {
      "total_completed": 25,
      "on_time": 20,
      "late": 5,
      "on_time_rate": 80,
      "total_estimated_hours": 150,
      "total_actual_hours": 165,
      "efficiency": 90.9
    },
    "by_priority": {"High": 8, "Medium": 12, "Low": 5},
    "by_project": {...},
    "tasks": [...],
    "generated_at": "2026-02-03 10:30:00"
  }
}
```

### Budget Tracking Report

Generate a report on budget utilization across projects.

```
POST /api/method/orga.orga.api.reports.get_budget_tracking_report
```

**Response:**
```json
{
  "message": {
    "projects": [
      {
        "name": "ORG-2026-0001",
        "project_name": "Website Redesign",
        "budget": 50000,
        "spent": 35000,
        "remaining": 15000,
        "utilization_percent": 70,
        "progress": 65,
        "budget_status": "on_track"
      }
    ],
    "summary": {
      "total_budget": 200000,
      "total_spent": 95000,
      "total_remaining": 105000,
      "overall_utilization": 47.5,
      "projects_over_budget": 1,
      "projects_on_track": 7,
      "projects_under_budget": 2
    },
    "generated_at": "2026-02-03 10:30:00"
  }
}
```

**Budget Status Values:**
- `over` - Spending exceeds progress by more than 10%
- `on_track` - Spending aligns with progress (within 10%)
- `under` - Spending is more than 10% below progress

### Milestone Report

Generate a report on milestone status.

```
POST /api/method/orga.orga.api.reports.get_milestone_report
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project ID |
| days_ahead | integer | Days to look ahead for upcoming (default: 30) |

**Response:**
```json
{
  "message": {
    "upcoming": [
      {
        "name": "MS-00001",
        "milestone_name": "Phase 1 Complete",
        "project": "ORG-2026-0001",
        "due_date": "2026-02-15",
        "days_until_due": 12
      }
    ],
    "overdue": [...],
    "summary": {
      "total": 15,
      "upcoming": 5,
      "overdue": 2,
      "completed": 8
    },
    "generated_at": "2026-02-03 10:30:00"
  }
}
```

---

## Workflows API

### Get Workflows

Retrieve a list of workflows with optional filters.

```
POST /api/method/orga.orga.api.workflow.get_workflows
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| applies_to | string | Filter by DocType (Orga Task, Orga Project) |
| is_active | integer | Filter by active status (0 or 1) |

**Response:**
```json
{
  "message": [
    {
      "name": "Task Review Workflow",
      "workflow_name": "Task Review Workflow",
      "applies_to": "Orga Task",
      "is_active": 1,
      "description": "Standard task review process",
      "state_count": 4,
      "transition_count": 5
    }
  ]
}
```

### Get Single Workflow

Retrieve a workflow with all states and transitions.

```
POST /api/method/orga.orga.api.workflow.get_workflow
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Workflow name |

### Get Active Workflow

Get the active workflow for a specific DocType.

```
POST /api/method/orga.orga.api.workflow.get_active_workflow
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | DocType name (Orga Task or Orga Project) |

### Get Allowed Actions

Get available workflow actions for a document based on current state and user permissions.

```
POST /api/method/orga.orga.api.workflow.get_allowed_actions
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| name | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "current_state": "Open",
    "workflow_name": "Task Review Workflow",
    "allowed_actions": [
      {
        "to_state": "In Progress",
        "action_label": "Start Working"
      },
      {
        "to_state": "Cancelled",
        "action_label": "Cancel"
      }
    ],
    "has_workflow": true
  }
}
```

### Perform Workflow Action

Execute a workflow transition on a document.

```
POST /api/method/orga.orga.api.workflow.perform_workflow_action
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| name | string | Yes | Document name |
| action | string | Yes | Target state name |

**Response:**
```json
{
  "message": {
    "name": "TASK-00001",
    "workflow_state": "In Progress",
    "status": "In Progress"
  }
}
```

### Create Workflow

Create a new workflow definition.

```
POST /api/method/orga.orga.api.workflow.create_workflow
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| workflow_name | string | Yes | Unique workflow name |
| applies_to | string | Yes | Target DocType |
| states | array | Yes | List of state definitions |
| transitions | array | No | List of transition definitions |
| description | string | No | Workflow description |

**States Array Format:**
```json
[
  {"state_name": "Open", "is_initial": 1, "is_final": 0, "color": "#3B82F6"},
  {"state_name": "Completed", "is_initial": 0, "is_final": 1, "color": "#10B981"}
]
```

**Transitions Array Format:**
```json
[
  {
    "from_state": "Open",
    "to_state": "In Progress",
    "action_label": "Start Working",
    "allowed_roles": "Orga User, Orga Manager"
  }
]
```

### Activate Workflow

Activate a workflow (automatically deactivates other workflows for the same DocType).

```
POST /api/method/orga.orga.api.workflow.activate_workflow
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Workflow name |

---

## Notifications API

### Get My Notifications

Retrieve notifications for the current user.

```
POST /api/method/orga.orga.api.notification.get_my_notifications
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | integer | Maximum results (default: 50) |
| offset | integer | Pagination offset |
| unread_only | boolean | Only return unread notifications |

**Response:**
```json
{
  "message": {
    "notifications": [
      {
        "name": "abc123",
        "notification_type": "Assignment",
        "subject": "You have been assigned to: Design homepage",
        "message": "You have been assigned to task 'Design homepage' in project 'Website Redesign'.",
        "is_read": 0,
        "reference_doctype": "Orga Task",
        "reference_name": "TASK-00001",
        "from_user": "john@example.com",
        "from_user_name": "John Doe",
        "creation": "2026-02-03 10:30:00"
      }
    ],
    "total": 15,
    "unread_count": 3
  }
}
```

### Get Unread Count

Get the count of unread notifications for the current user.

```
POST /api/method/orga.orga.api.notification.get_unread_count
```

**Response:**
```json
{
  "message": 5
}
```

### Mark as Read

Mark a specific notification as read.

```
POST /api/method/orga.orga.api.notification.mark_as_read
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Notification ID |

### Mark All as Read

Mark all notifications as read for the current user.

```
POST /api/method/orga.orga.api.notification.mark_all_as_read
```

### Delete Notification

Remove a notification.

```
POST /api/method/orga.orga.api.notification.delete_notification
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Notification ID |

---

## Automation API

### Get Automation Rules

Retrieve automation rules with optional filters.

```
POST /api/method/orga.orga.api.automation.get_rules
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| applies_to | string | Filter by DocType |
| is_active | integer | Filter by active status |
| limit | integer | Maximum results (default: 50) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "rules": [
      {
        "name": "Auto-assign urgent tasks",
        "rule_name": "Auto-assign urgent tasks",
        "description": "Automatically assign urgent tasks to the project manager",
        "applies_to": "Orga Task",
        "trigger_event": "On Create",
        "is_active": 1,
        "last_run": "2026-02-03 10:30:00",
        "run_count": 15,
        "condition_count": 1,
        "action_count": 2
      }
    ],
    "total": 3
  }
}
```

### Get Single Rule

Retrieve a rule with full conditions and actions.

```
POST /api/method/orga.orga.api.automation.get_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Rule name |

### Create Automation Rule

Create a new automation rule.

```
POST /api/method/orga.orga.api.automation.create_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| rule_name | string | Yes | Unique rule name |
| applies_to | string | Yes | Target DocType |
| trigger_event | string | Yes | When to trigger |
| actions | array | Yes | List of actions |
| conditions | array | No | List of conditions |
| description | string | No | Rule description |

**Trigger Events:**
- `On Create` - When document is created
- `On Update` - When document is modified
- `On Status Change` - When status field changes
- `On Assignment` - When document is assigned
- `Scheduled` - Based on schedule (Daily, Weekly, Monthly)

**Conditions Array Format:**
```json
[
  {"field_name": "priority", "operator": "equals", "value": "Urgent"},
  {"field_name": "assigned_to", "operator": "is not set"}
]
```

**Condition Operators:**
- `equals`, `not equals`
- `greater than`, `less than`
- `contains`, `not contains`
- `is set`, `is not set`

**Actions Array Format:**
```json
[
  {"action_type": "Set Field Value", "field_name": "assigned_to", "value": "john@example.com"},
  {"action_type": "Send Notification", "target_user": "manager@example.com", "message": "New urgent task created"}
]
```

**Action Types:**
- `Set Field Value` - Update a field on the document
- `Assign To` - Assign to a specific user
- `Send Notification` - Send in-app notification
- `Add Comment` - Add a comment to the document
- `Update Status` - Change the status field

### Update Rule

Update an existing automation rule.

```
POST /api/method/orga.orga.api.automation.update_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Rule name |
| data | object | Yes | Fields to update (JSON) |

### Delete Rule

Remove an automation rule.

```
POST /api/method/orga.orga.api.automation.delete_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Rule name |

### Activate/Deactivate Rule

Enable or disable an automation rule.

```
POST /api/method/orga.orga.api.automation.activate_rule
POST /api/method/orga.orga.api.automation.deactivate_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Rule name |

### Test Rule

Test an automation rule without executing actions.

```
POST /api/method/orga.orga.api.automation.test_rule
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Rule name |
| doc_name | string | No | Specific document to test on |

**Response:**
```json
{
  "message": {
    "rule_name": "Auto-assign urgent tasks",
    "is_active": 1,
    "applies_to": "Orga Task",
    "trigger_event": "On Create",
    "conditions": 1,
    "actions": 2,
    "test_results": [
      {
        "document": "TASK-00001",
        "conditions_met": true,
        "would_execute": true
      },
      {
        "document": "TASK-00002",
        "conditions_met": false,
        "would_execute": false
      }
    ]
  }
}
```

---

## Gantt, Cascade & Dependency Scheduling API

### Preview Cascade

Preview the impact of date changes on dependent tasks before applying.

```
POST /api/method/orga.orga.api.task.preview_cascade
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task being modified |
| new_start_date | date | No | New start date (if changing) |
| new_end_date | date | No | New end date (if changing) |

**Response:**
```json
{
  "message": [
    {
      "task_id": "TASK-00002",
      "task_name": "QA Testing",
      "current_start": "2026-02-15",
      "current_end": "2026-02-20",
      "new_start": "2026-02-17",
      "new_end": "2026-02-22",
      "shift_days": 2
    }
  ]
}
```

### Apply Cascade

Apply cascade date changes to all affected tasks atomically.

```
POST /api/method/orga.orga.api.task.apply_cascade
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Original task being modified |
| new_start_date | date | No | New start date |
| new_end_date | date | No | New end date |
| changes | string | No | JSON array of changes from preview_cascade |

**Response:**
```json
{
  "message": {
    "success": true,
    "updated_tasks": ["TASK-00002", "TASK-00003"]
  }
}
```

### Check Circular Dependency

Validate that adding a dependency won't create a circular reference.

```
POST /api/method/orga.orga.api.task.check_circular_dependency
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task to add dependency to |
| depends_on | string | Yes | Task that would become a dependency |

**Response:**
```json
{
  "message": {
    "is_circular": false,
    "path": null
  }
}
```

If circular:
```json
{
  "message": {
    "is_circular": true,
    "path": ["TASK-00001", "TASK-00002", "TASK-00003", "TASK-00001"]
  }
}
```

### Get Gantt Tasks

Get tasks formatted for Gantt chart display with dependency info.

```
POST /api/method/orga.orga.api.task.get_gantt_tasks
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project | string | Yes | Project ID |

**Response:**
```json
{
  "message": [
    {
      "id": "TASK-00001",
      "name": "Design Phase",
      "start_date": "2026-02-01",
      "end_date": "2026-02-10",
      "progress": 50,
      "dependencies": [
        {
          "task_id": "TASK-00000",
          "task_name": "Planning",
          "type": "FS",
          "lag": 0
        }
      ],
      "dependents": [
        {
          "task_id": "TASK-00002",
          "task_name": "Development",
          "type": "FS",
          "lag": 0
        }
      ]
    }
  ]
}
```

### Batch Update Task Dates

Update multiple task dates in a single transaction.

```
POST /api/method/orga.orga.api.task.batch_update_task_dates
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| updates | string | Yes | JSON array of updates |

**Updates Array Format:**
```json
[
  {"task_name": "TASK-00001", "start_date": "2026-02-05", "due_date": "2026-02-15"},
  {"task_name": "TASK-00002", "start_date": "2026-02-16", "due_date": "2026-02-25"}
]
```

**Response:**
```json
{
  "message": {
    "success": true,
    "updated": 2,
    "tasks": ["TASK-00001", "TASK-00002"]
  }
}
```

### Reschedule Dependents

Trigger dependency cascade based on the project's dependency mode. In Flexible mode, returns a preview. In Strict mode, applies changes automatically.

```
POST /api/method/orga.orga.api.task.reschedule_dependents
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_name | string | Yes | Task whose dates changed |
| old_start_date | date | No | Previous start date |
| old_end_date | date | No | Previous end date |

**Response (Flexible mode — preview):**
```json
{
  "message": {
    "mode": "Flexible",
    "preview": [
      {
        "task_id": "TASK-00002",
        "task_name": "QA Testing",
        "current_start": "2026-02-15",
        "current_end": "2026-02-20",
        "new_start": "2026-02-17",
        "new_end": "2026-02-22",
        "shift_days": 2
      }
    ]
  }
}
```

**Response (Strict mode — auto-applied):**
```json
{
  "message": {
    "mode": "Strict",
    "updated": 3
  }
}
```

**Response (Off mode):**
```json
{
  "message": {
    "mode": "Off"
  }
}
```

### Get Critical Path

Calculate the critical path for a project using the Critical Path Method (CPM). Returns the set of tasks where any delay would push back the project end date.

```
POST /api/method/orga.orga.api.project.get_critical_path
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_name | string | Yes | Project ID |

**Response:**
```json
{
  "message": {
    "critical_tasks": ["TASK-00001", "TASK-00003", "TASK-00005"],
    "task_floats": {
      "TASK-00001": 0,
      "TASK-00002": 3,
      "TASK-00003": 0,
      "TASK-00004": 5,
      "TASK-00005": 0
    }
  }
}
```

Tasks with `float <= 0` are on the critical path. Float represents how many days a task can slip without affecting the project end date.

---

## Frappe Projects Sync API

These endpoints enable synchronization between Orga and Frappe Projects module.

### Sync Project to Frappe

Push an Orga Project to Frappe Projects.

```
POST /api/method/orga.orga.integrations.frappe_projects.sync_project_to_frappe
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| orga_project | string | Yes | Orga Project ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "frappe_project": "Website Redesign",
    "action": "updated"
  }
}
```

### Sync Project from Frappe

Pull a Frappe Project into Orga.

```
POST /api/method/orga.orga.integrations.frappe_projects.sync_project_from_frappe
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| frappe_project | string | Yes | Frappe Project name |

**Response:**
```json
{
  "message": {
    "success": true,
    "orga_project": "ORG-2026-0001",
    "action": "created"
  }
}
```

### Sync All Projects

Synchronize all projects based on settings.

```
POST /api/method/orga.orga.integrations.frappe_projects.sync_all_projects
```

**Response:**
```json
{
  "message": {
    "success": true,
    "synced": 5,
    "failed": 0,
    "errors": []
  }
}
```

### Sync Project Tasks

Sync all tasks for a specific project.

```
POST /api/method/orga.orga.integrations.frappe_projects.sync_project_tasks
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| orga_project | string | Yes | Orga Project ID |

---

## Migration API

These endpoints support one-time migration from Frappe Projects to Orga.

### Preview Migration

Preview what will be migrated before executing.

```
POST /api/method/orga.orga.integrations.migration.preview_migration
```

**Response:**
```json
{
  "message": {
    "success": true,
    "projects": [
      {
        "name": "PROJ-001",
        "project_name": "Website Redesign",
        "task_count": 12,
        "already_migrated": false
      }
    ],
    "total_projects": 5,
    "total_tasks": 45,
    "already_migrated": 2,
    "warnings": [
      {"type": "info", "message": "2 projects already migrated"}
    ]
  }
}
```

### Migrate from Frappe Projects

Execute migration from Frappe Projects.

```
POST /api/method/orga.orga.integrations.migration.migrate_from_frappe_projects
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| skip_existing | boolean | Skip already migrated projects (default: true) |
| dry_run | boolean | Preview only, don't create records (default: false) |

**Response:**
```json
{
  "message": {
    "success": true,
    "migration_id": "MIG-20260203-103000",
    "dry_run": false,
    "projects_created": 3,
    "projects_updated": 0,
    "projects_skipped": 2,
    "tasks_created": 25,
    "tasks_updated": 0,
    "errors": []
  }
}
```

### Rollback Migration

Undo a migration by deleting created records.

```
POST /api/method/orga.orga.integrations.migration.rollback_migration
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| migration_id | string | Yes | Migration ID to rollback |

**Response:**
```json
{
  "message": {
    "success": true,
    "projects_deleted": 3,
    "tasks_deleted": 25
  }
}
```

### Get Migration History

Retrieve history of all migrations.

```
POST /api/method/orga.orga.integrations.migration.get_migration_history
```

**Response:**
```json
{
  "message": [
    {
      "migration_id": "MIG-20260203-103000",
      "timestamp": "2026-02-03 10:30:00",
      "user": "Administrator",
      "projects_created": 3,
      "tasks_created": 25,
      "rolled_back": false
    }
  ]
}
```

### Get Migration Details

Get detailed information about a specific migration.

```
POST /api/method/orga.orga.integrations.migration.get_migration_details
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| migration_id | string | Yes | Migration ID |

---

## ERPNext Integration API

These endpoints integrate Orga with ERPNext HR and Billing modules.

### Get Employees

Search for ERPNext employees to link with resources.

```
POST /api/method/orga.orga.integrations.erpnext.get_employees
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| search_text | string | Search in employee name |
| filters | object | Additional filters (e.g., {"status": "Active"}) |
| limit | integer | Maximum results (default: 20) |

**Response:**
```json
{
  "message": {
    "success": true,
    "employees": [
      {
        "name": "EMP-00001",
        "employee_name": "Jane Smith",
        "status": "Active",
        "department": "Engineering",
        "designation": "Software Engineer",
        "user_id": "jane@example.com",
        "already_linked": false
      }
    ]
  }
}
```

### Get Employee Details

Get full employee details for auto-populating a resource.

```
POST /api/method/orga.orga.integrations.erpnext.get_employee_details
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| employee_name | string | Yes | Employee ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "data": {
      "resource_name": "Jane Smith",
      "email": "jane@example.com",
      "user": "jane@example.com",
      "department": "Engineering",
      "designation": "Software Engineer",
      "status": "Active"
    }
  }
}
```

### Sync Resource from Employee

Sync an Orga Resource's details from linked ERPNext Employee.

```
POST /api/method/orga.orga.integrations.erpnext.sync_resource_from_employee
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_name | string | Yes | Orga Resource ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "message": "Resource synced from employee Jane Smith"
  }
}
```

### Sync All Resources from Employees

Sync all resources that have linked employees and sync enabled.

```
POST /api/method/orga.orga.integrations.erpnext.sync_all_resources_from_employees
```

**Response:**
```json
{
  "message": {
    "success": true,
    "synced": 10,
    "failed": 0,
    "errors": []
  }
}
```

### Export Time Log to Timesheet

Export an Orga Time Log to an ERPNext Timesheet.

```
POST /api/method/orga.orga.integrations.erpnext.export_time_log_to_timesheet
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| time_log_name | string | Yes | Orga Time Log ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "timesheet": "TS-00001",
    "message": "Exported to timesheet TS-00001"
  }
}
```

### Export Project Time Logs

Export all time logs for a project to ERPNext timesheets.

```
POST /api/method/orga.orga.integrations.erpnext.export_project_time_logs
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_name | string | Yes | Orga Project ID |
| from_date | date | No | Filter by start date |
| to_date | date | No | Filter by end date |

**Response:**
```json
{
  "message": {
    "success": true,
    "exported": 15,
    "skipped": 5,
    "errors": []
  }
}
```

### Get Project Billing Summary

Get billing summary for a project including billable hours and estimated revenue.

```
POST /api/method/orga.orga.integrations.erpnext.get_project_billing_summary
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_name | string | Yes | Orga Project ID |

**Response:**
```json
{
  "message": {
    "success": true,
    "project": "ORG-2026-0001",
    "project_name": "Website Redesign",
    "summary": {
      "total_hours": 150.5,
      "billable_hours": 120.0,
      "non_billable_hours": 30.5,
      "estimated_billing": 12000.00,
      "budget": 50000,
      "spent": 35000,
      "budget_remaining": 15000,
      "progress": 65,
      "total_tasks": 20,
      "completed_tasks": 13,
      "billing_ready": false
    }
  }
}
```

### Get Resource Billing Summary

Get billing summary for a specific resource.

```
POST /api/method/orga.orga.integrations.erpnext.get_resource_billing_summary
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| resource_name | string | Yes | Orga Resource ID |
| from_date | date | No | Period start |
| to_date | date | No | Period end |

**Response:**
```json
{
  "message": {
    "success": true,
    "resource": "RES-00001",
    "resource_name": "Jane Smith",
    "summary": {
      "total_hours": 160.0,
      "billable_hours": 140.0,
      "billable_rate": 100.00,
      "hourly_cost": 50.00,
      "estimated_revenue": 14000.00,
      "estimated_cost": 8000.00,
      "gross_margin": 6000.00
    },
    "by_project": {
      "ORG-2026-0001": {"total": 80, "billable": 70},
      "ORG-2026-0002": {"total": 80, "billable": 70}
    }
  }
}
```

---

## Webhooks API

### Get Webhooks

Retrieve list of configured webhooks.

```
POST /api/method/orga.orga.api.webhook.get_webhooks
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| limit | integer | Maximum results (default: 50) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "webhooks": [
      {
        "name": "My Webhook",
        "webhook_name": "My Webhook",
        "url": "https://example.com/webhook",
        "is_active": 1,
        "last_status": "Success",
        "success_count": 150,
        "failure_count": 2,
        "event_count": 3
      }
    ],
    "total": 1
  }
}
```

### Create Webhook

Create a new webhook subscription.

```
POST /api/method/orga.orga.api.webhook.create_webhook
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | object | Yes | Webhook configuration (JSON) |

**Data Fields:**
- `webhook_name` (required) - Unique name
- `url` (required) - Endpoint URL
- `events` (required) - Array of event names
- `secret` - HMAC signing secret
- `is_active` - Enable/disable (default: 1)
- `request_timeout` - Timeout in seconds (default: 30)
- `retry_count` - Retries on failure (default: 3)

**Available Events:**
- `*` - All events
- `project.created`, `project.updated`, `project.completed`, `project.deleted`
- `task.created`, `task.updated`, `task.completed`, `task.assigned`, `task.deleted`
- `resource.created`, `resource.updated`, `resource.deleted`
- `assignment.created`, `assignment.updated`, `assignment.deleted`
- `appointment.created`, `appointment.updated`, `appointment.deleted`, `appointment.rsvp`
- `milestone.created`, `milestone.completed`
- `time_log.created`
- `workflow.action`

### Test Webhook

Send a test payload to verify webhook configuration.

```
POST /api/method/orga.orga.api.webhook.test_webhook
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Webhook name |
| event | string | No | Event to simulate (default: test.ping) |

**Response:**
```json
{
  "message": {
    "success": true,
    "status_code": 200,
    "response_time_ms": 150,
    "response_body": "OK"
  }
}
```

### Get Available Events

Get list of webhook events with descriptions.

```
POST /api/method/orga.orga.api.webhook.get_available_events
```

**Response:**
```json
{
  "message": [
    {"event_name": "*", "description": "All events"},
    {"event_name": "project.created", "description": "When a new project is created"},
    {"event_name": "task.completed", "description": "When a task status changes to Completed"}
  ]
}
```

### Webhook Payload Format

All webhook payloads follow this structure:

```json
{
  "event": "task.created",
  "timestamp": "2026-02-04T10:30:00",
  "site": "orga.localhost",
  "data": {
    "doctype": "Orga Task",
    "name": "TASK-00001",
    "doc": {
      "name": "TASK-00001",
      "subject": "New Task",
      "status": "Open",
      "priority": "Medium"
    }
  }
}
```

For update events, a `changes` object is included:

```json
{
  "event": "task.updated",
  "data": {
    "doc": {...},
    "changes": {
      "status": {"from": "Open", "to": "In Progress"}
    }
  }
}
```

### Webhook Signature Verification

If a secret is configured, payloads are signed with HMAC-SHA256. Verify the signature:

```python
import hmac
import hashlib

def verify_signature(payload_body, signature_header, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature_header == f"sha256={expected}"

# Usage
signature = request.headers.get('X-Orga-Signature')
if verify_signature(request.body, signature, your_secret):
    # Valid webhook
    process_webhook(request.json())
```

---

## Import/Export API

### Export Projects

Export projects to CSV or JSON.

```
POST /api/method/orga.orga.api.import_export.export_projects
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| format | string | Output format: 'csv' or 'json' (default: csv) |
| status | string | Filter by status |

**Response:**
```json
{
  "message": {
    "file_url": "/private/files/orga_projects_export_20260204_103000.csv",
    "filename": "orga_projects_export_20260204_103000.csv"
  }
}
```

### Export Tasks

Export tasks to CSV or JSON.

```
POST /api/method/orga.orga.api.import_export.export_tasks
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project |
| status | string | Filter by status |
| format | string | Output format: 'csv' or 'json' |

### Export Time Logs

Export time logs with optional date range filter.

```
POST /api/method/orga.orga.api.import_export.export_time_logs
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project |
| resource | string | Filter by resource |
| from_date | date | Period start |
| to_date | date | Period end |
| format | string | Output format: 'csv' or 'json' |

### Export Timesheet Report

Export aggregated timesheet data by resource and date.

```
POST /api/method/orga.orga.api.import_export.export_timesheet_report
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| project | string | Filter by project |
| from_date | date | Report start date |
| to_date | date | Report end date |
| format | string | Output format: 'csv' or 'json' |

### Import Tasks

Import tasks from a CSV file.

```
POST /api/method/orga.orga.api.import_export.import_tasks
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_url | string | Yes | URL of uploaded CSV file |
| project | string | Yes | Target project for imported tasks |
| update_existing | boolean | No | Update existing tasks by name |

**Response:**
```json
{
  "message": {
    "success": true,
    "imported": 15,
    "updated": 3,
    "total_rows": 20,
    "error_count": 2,
    "errors": [
      {"row": 5, "error": "Subject is required"},
      {"row": 12, "error": "Invalid status value"}
    ]
  }
}
```

**Required CSV Columns:**
- `subject` - Task title

**Optional CSV Columns:**
- `description`, `status`, `priority`, `start_date`, `due_date`, `estimated_hours`, `assigned_to`, `milestone`

### Import Resources

Import resources from a CSV file.

```
POST /api/method/orga.orga.api.import_export.import_resources
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_url | string | Yes | URL of uploaded CSV file |
| update_existing | boolean | No | Update existing resources |

**Required CSV Columns:**
- `resource_name` - Resource full name

**Optional CSV Columns:**
- `email`, `resource_type`, `status`, `department`, `designation`, `weekly_capacity`, `hourly_cost`, `billable_rate`

### Get Import Template

Download a CSV template for importing data.

```
POST /api/method/orga.orga.api.import_export.get_import_template
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | DocType name ('Orga Task', 'Orga Resource', 'Orga Time Log') |

**Response:**
```json
{
  "message": {
    "file_url": "/private/files/orga_orga_task_template.csv",
    "filename": "orga_orga_task_template.csv"
  }
}
```

### Validate Import File

Validate a CSV file before importing.

```
POST /api/method/orga.orga.api.import_export.validate_import_file
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_url | string | Yes | URL of uploaded CSV file |
| doctype | string | Yes | Target DocType |

**Response:**
```json
{
  "message": {
    "valid": true,
    "headers": ["subject", "status", "priority", "start_date"],
    "row_count": 25,
    "required_fields": ["subject"],
    "sample_row": {"subject": "Example Task", "status": "Open"}
  }
}
```

---

## Clients API

### Get Clients

Retrieve a list of clients with optional filtering.

```
POST /api/method/orga.orga.api.client.get_clients
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| status | string | Filter by status (Active, Inactive, Pending) |
| company | string | Filter by company name (partial match) |
| portal_enabled | integer | Filter by portal access (0 or 1) |
| limit | integer | Maximum results (default: 100) |
| offset | integer | Pagination offset |

**Response:**
```json
{
  "message": {
    "clients": [
      {
        "name": "CLT-00001",
        "client_name": "Jane Doe",
        "company": "Acme Corp",
        "email": "jane@acme.com",
        "phone": "+1-555-0100",
        "status": "Active",
        "portal_enabled": 1,
        "user": "jane@acme.com",
        "project_count": 3,
        "last_login": "2026-02-04 09:30:00"
      }
    ],
    "total": 1
  }
}
```

### Get Single Client

Retrieve detailed information about a client including linked projects.

```
POST /api/method/orga.orga.api.client.get_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID (e.g., "CLT-00001") |

**Response:**
```json
{
  "message": {
    "name": "CLT-00001",
    "client_name": "Jane Doe",
    "company": "Acme Corp",
    "email": "jane@acme.com",
    "status": "Active",
    "projects": [
      {
        "name": "ORG-2026-0001",
        "project_name": "Website Redesign",
        "status": "Active",
        "progress": 45
      }
    ],
    "milestones": [...]
  }
}
```

### Create Client

Create a new client record.

```
POST /api/method/orga.orga.api.client.create_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_name | string | Yes | Client's full name |
| email | string | Yes | Client's email (must be unique) |
| company | string | No | Company name |
| phone | string | No | Phone number |
| status | string | No | Initial status (default: Pending) |
| portal_enabled | integer | No | Enable portal access (default: 0) |
| address_line1 | string | No | Street address |
| city | string | No | City |
| state | string | No | State/Province |
| country | string | No | Country |
| notes | string | No | Additional notes |

**Response:**
```json
{
  "message": {
    "name": "CLT-00001",
    "client_name": "Jane Doe",
    "email": "jane@acme.com",
    "status": "Pending"
  }
}
```

### Update Client

Update an existing client.

```
POST /api/method/orga.orga.api.client.update_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |
| Any field | various | No | Field to update |

### Delete Client

Remove a client. Clients with linked projects cannot be deleted.

```
POST /api/method/orga.orga.api.client.delete_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |

### Get Client Projects

Get all projects linked to a specific client.

```
POST /api/method/orga.orga.api.client.get_client_projects
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |

**Response:**
```json
{
  "message": [
    {
      "name": "ORG-2026-0001",
      "project_name": "Website Redesign",
      "status": "Active",
      "progress": 45,
      "start_date": "2026-01-15",
      "end_date": "2026-04-30"
    }
  ]
}
```

### Invite Client to Portal

Create a portal user for the client and send welcome email.

```
POST /api/method/orga.orga.api.client.invite_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |
| send_email | integer | No | Send welcome email (default: 1) |

**Response:**
```json
{
  "message": {
    "success": true,
    "user": "jane@acme.com",
    "message": "Portal user created successfully. Welcome email sent"
  }
}
```

### Revoke Portal Access

Disable a client's portal access.

```
POST /api/method/orga.orga.api.client.revoke_portal_access
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |

### Get Client Milestones

Get milestones for a client's projects.

```
POST /api/method/orga.orga.api.client.get_client_milestones
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| client_id | string | Yes | Client ID |
| project | string | No | Filter by specific project |

### Link Project to Client

Associate a project with a client.

```
POST /api/method/orga.orga.api.client.link_project_to_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project ID |
| client_id | string | Yes | Client ID |

### Unlink Project from Client

Remove client association from a project.

```
POST /api/method/orga.orga.api.client.unlink_project_from_client
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project ID |

---

## Activity API

Manage activity feed interactions including notes, pins, and archives.

### Get Activity Details

Retrieve detailed information about an activity including changes, notes, and user preferences.

```
POST /api/method/orga.orga.api.activity.get_activity_details
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type (e.g., Orga Task) |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "doctype": "Orga Task",
    "name": "TASK-00001",
    "title": "Implement feature",
    "modified": "2026-02-04 10:30:00",
    "modified_by": "john@example.com",
    "modified_by_name": "John Smith",
    "changes": [
      {
        "field": "status",
        "field_label": "Status",
        "old_value": "Open",
        "new_value": "Working",
        "modified": "2026-02-04 10:30:00",
        "modified_by": "john@example.com"
      }
    ],
    "notes": [
      {
        "name": "abc123",
        "content": "Reviewed with team",
        "created_by": "john@example.com",
        "created_by_name": "John Smith",
        "creation": "2026-02-04 11:00:00"
      }
    ],
    "is_pinned": true,
    "is_archived": false,
    "can_delete": false
  }
}
```

### Add Activity Note

Add an annotation note to an activity.

```
POST /api/method/orga.orga.api.activity.add_activity_note
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |
| content | string | Yes | Note content |

**Response:**
```json
{
  "message": {
    "name": "abc123",
    "content": "Note content here",
    "created_by": "john@example.com",
    "created_by_name": "John Smith",
    "creation": "2026-02-04 11:00:00"
  }
}
```

### Delete Activity Note

Delete a note from an activity. Users can delete their own notes; administrators can delete any note.

```
POST /api/method/orga.orga.api.activity.delete_activity_note
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| note_name | string | Yes | Comment name (ID) |

### Toggle Activity Pin

Toggle the pinned status of an activity for the current user.

```
POST /api/method/orga.orga.api.activity.toggle_activity_pin
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "is_pinned": true
  }
}
```

### Toggle Activity Archive

Toggle the archived status of an activity for the current user.

```
POST /api/method/orga.orga.api.activity.toggle_activity_archive
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "is_archived": true
  }
}
```

### Get Pinned Activities

Retrieve all pinned activities for the current user.

```
POST /api/method/orga.orga.api.activity.get_pinned_activities
```

**Response:**
```json
{
  "message": [
    {
      "doctype": "Orga Task",
      "name": "TASK-00001"
    },
    {
      "doctype": "Orga Milestone",
      "name": "MILE-00002"
    }
  ]
}
```

### Get Archived Activities

Retrieve all archived activities for the current user.

```
POST /api/method/orga.orga.api.activity.get_archived_activities
```

**Response:**
```json
{
  "message": [
    {
      "doctype": "Orga Task",
      "name": "TASK-00005"
    }
  ]
}
```

### Delete Activity (Admin Only)

Permanently delete activity data including all associated notes. Requires System Manager role.

```
POST /api/method/orga.orga.api.activity.delete_activity
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

### Get Activity Comments

Retrieve threaded comments for an activity.

```
POST /api/method/orga.orga.api.activity.get_activity_comments
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type (e.g., Orga Task) |
| docname | string | Yes | Document name |
| limit | integer | No | Maximum comments to return (default: 50) |

**Response:**
```json
{
  "message": [
    {
      "name": "cmt-001",
      "content": "Great progress on this task!",
      "parent_comment": null,
      "created_by": "john@example.com",
      "created_by_name": "John Smith",
      "creation": "2026-02-04 10:30:00",
      "reply_count": 2,
      "mentioned_users": ["jane@example.com"]
    }
  ]
}
```

### Add Activity Comment

Add a comment to an activity with optional @mention support.

```
POST /api/method/orga.orga.api.activity.add_activity_comment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |
| content | string | Yes | Comment content (supports @mentions) |
| parent_comment | string | No | Parent comment name for replies |

**Response:**
```json
{
  "message": {
    "name": "cmt-002",
    "content": "Thanks @jane@example.com for the review!",
    "parent_comment": null,
    "created_by": "john@example.com",
    "created_by_name": "John Smith",
    "creation": "2026-02-04 11:00:00",
    "mentioned_users": ["jane@example.com"]
  }
}
```

### Delete Activity Comment

Delete a comment. Users can delete their own comments; managers can delete any comment.

```
POST /api/method/orga.orga.api.activity.delete_activity_comment
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| comment_name | string | Yes | Comment name (ID) |

### Get Comment Replies

Retrieve replies to a specific comment.

```
POST /api/method/orga.orga.api.activity.get_comment_replies
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| parent_comment | string | Yes | Parent comment name |
| limit | integer | No | Maximum replies to return (default: 20) |

**Response:**
```json
{
  "message": [
    {
      "name": "cmt-003",
      "content": "I'll take a look at this today",
      "parent_comment": "cmt-001",
      "created_by": "jane@example.com",
      "created_by_name": "Jane Doe",
      "creation": "2026-02-04 11:15:00"
    }
  ]
}
```

### Get Users for Mention

Search users for @mention autocomplete.

```
POST /api/method/orga.orga.api.activity.get_users_for_mention
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| search_term | string | Yes | Search query (name or email) |
| limit | integer | No | Maximum results (default: 10) |

**Response:**
```json
{
  "message": [
    {
      "name": "jane@example.com",
      "full_name": "Jane Doe",
      "user_image": "/files/jane.jpg"
    }
  ]
}
```

### Toggle Reaction

Toggle a reaction on an activity. Calling again removes the reaction.

```
POST /api/method/orga.orga.api.activity.toggle_reaction
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |
| reaction_type | string | Yes | Reaction type: acknowledge, celebrate, seen, flag |

**Response:**
```json
{
  "message": {
    "action": "added",
    "reaction_type": "celebrate",
    "counts": {
      "acknowledge": 3,
      "celebrate": 5,
      "seen": 2,
      "flag": 0
    }
  }
}
```

### Get Reactions

Retrieve reaction counts and users for an activity.

```
POST /api/method/orga.orga.api.activity.get_reactions
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "counts": {
      "acknowledge": 3,
      "celebrate": 5,
      "seen": 2,
      "flag": 1
    },
    "user_reactions": ["celebrate"],
    "users_by_type": {
      "acknowledge": ["john@example.com", "jane@example.com", "bob@example.com"],
      "celebrate": ["john@example.com", "jane@example.com"],
      "seen": ["alice@example.com"],
      "flag": ["manager@example.com"]
    }
  }
}
```

### Add Due Diligence Note

Add a typed note with visibility control for due diligence workflows.

```
POST /api/method/orga.orga.api.activity.add_due_diligence_note
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |
| content | string | Yes | Note content |
| note_type | string | No | Type: General, Due Diligence, Offer, Decision (default: General) |
| visibility | string | No | Visibility: Internal, Team, Public (default: Internal) |
| linked_company | string | No | Linked company reference |

**Response:**
```json
{
  "message": {
    "name": "note-001",
    "content": "Completed financial review",
    "note_type": "Due Diligence",
    "visibility": "Team",
    "linked_company": "ACME Corp",
    "created_by": "john@example.com",
    "created_by_name": "John Smith",
    "creation": "2026-02-04 14:00:00"
  }
}
```

### Get Due Diligence Notes

Retrieve typed notes for an activity, filtered by visibility permissions.

```
POST /api/method/orga.orga.api.activity.get_due_diligence_notes
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |
| note_type | string | No | Filter by note type |

**Response:**
```json
{
  "message": [
    {
      "name": "note-001",
      "content": "Completed financial review",
      "note_type": "Due Diligence",
      "visibility": "Team",
      "linked_company": "ACME Corp",
      "created_by": "john@example.com",
      "created_by_name": "John Smith",
      "creation": "2026-02-04 14:00:00"
    }
  ]
}
```

### Get Compliance Status

Retrieve due diligence completion status for an activity.

```
POST /api/method/orga.orga.api.activity.get_compliance_status
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": {
    "checklist": {
      "initial_review": true,
      "documentation_review": true,
      "risk_assessment": false,
      "offer_prepared": false,
      "final_decision": false
    },
    "completion_percentage": 40,
    "flagged": false,
    "last_updated": "2026-02-04 14:30:00"
  }
}
```

### Get Related Documents

Retrieve documents linked to an activity.

```
POST /api/method/orga.orga.api.activity.get_related_documents
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| doctype | string | Yes | Document type |
| docname | string | Yes | Document name |

**Response:**
```json
{
  "message": [
    {
      "doctype": "Orga Project",
      "name": "PROJ-00001",
      "title": "Website Redesign",
      "status": "Active",
      "relationship": "parent"
    },
    {
      "doctype": "Orga Milestone",
      "name": "MILE-00003",
      "title": "Phase 1 Complete",
      "status": "In Progress",
      "relationship": "linked"
    }
  ]
}
```

### Update RSVP (Enhanced)

Update RSVP status for an appointment with optional message.

```
POST /api/method/orga.orga.api.activity.update_rsvp_enhanced
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment | string | Yes | Appointment name |
| status | string | Yes | Status: Accepted, Declined, Tentative |
| message | string | No | Optional response message |

**Response:**
```json
{
  "message": {
    "status": "Accepted",
    "message": "Looking forward to it!",
    "updated_at": "2026-02-04 15:00:00"
  }
}
```

### Propose New Time

Propose an alternative time for an appointment.

```
POST /api/method/orga.orga.api.activity.propose_new_time
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment | string | Yes | Appointment name |
| proposed_datetime | string | Yes | Proposed datetime (ISO format) |
| message | string | No | Explanation for the proposed time |

**Response:**
```json
{
  "message": {
    "proposal_id": "prop-001",
    "proposed_datetime": "2026-02-05 14:00:00",
    "message": "Could we move this to Tuesday afternoon?",
    "status": "Pending"
  }
}
```

### Get Appointment RSVP Info

Retrieve RSVP summary for an appointment.

```
POST /api/method/orga.orga.api.activity.get_appointment_rsvp_info
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| appointment | string | Yes | Appointment name |

**Response:**
```json
{
  "message": {
    "total_attendees": 5,
    "accepted": 3,
    "declined": 1,
    "pending": 1,
    "attendees": [
      {
        "user": "john@example.com",
        "name": "John Smith",
        "status": "Accepted",
        "is_required": true
      },
      {
        "user": "jane@example.com",
        "name": "Jane Doe",
        "status": "Pending",
        "is_required": false
      }
    ],
    "user_status": "Accepted"
  }
}
```

---

## Error Handling

All endpoints return standard Frappe error responses:

```json
{
  "exc_type": "ValidationError",
  "exception": "frappe.exceptions.ValidationError",
  "_server_messages": "[\"End date cannot be before start date\"]"
}
```

Common error types:
- `ValidationError`: Invalid input data
- `DoesNotExistError`: Requested resource not found
- `PermissionError`: User lacks required permissions

## Rate Limiting

API calls are subject to Frappe's standard rate limiting. For high-volume integrations, consider:
- Caching responses where appropriate
- Using batch operations when available
- Implementing exponential backoff on errors

## Examples

### Python (using requests)

```python
import requests

session = requests.Session()

# Login
session.post('http://your-site.localhost:8000/api/method/login', data={
    'usr': 'your@email.com',
    'pwd': 'your-password'
})

# Get projects
response = session.post(
    'http://your-site.localhost:8000/api/method/orga.orga.api.project.get_projects',
    json={'status': 'Active'}
)
print(response.json())
```

### TypeScript (Orga frontend)

The Orga frontend uses TypeScript with FrappeUI. Import types from `@/types/orga`:

```typescript
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import type { OrgaProject } from '@/types/orga'

const projects = ref<OrgaProject[]>([])

const projectsResource = createResource({
  url: 'orga.orga.api.project.get_projects',
  params: { status: 'Active', limit: 10 },
  onSuccess: (data: { projects: OrgaProject[] }) => {
    projects.value = data.projects
  }
})

onMounted(() => projectsResource.fetch())
```

### JavaScript (Frappe Desk)

```javascript
frappe.call({
    method: 'orga.orga.api.project.get_projects',
    args: {
        status: 'Active',
        limit: 10
    },
    callback: function(r) {
        console.log(r.message.projects);
    }
});
```

### cURL

```bash
curl -X POST http://your-site.localhost:8000/api/method/orga.orga.api.dashboard.get_stats \
  -H "Authorization: token api_key:api_secret" \
  -H "Content-Type: application/json"
```
