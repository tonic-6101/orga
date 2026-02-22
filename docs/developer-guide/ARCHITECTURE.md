# Orga Architecture

This document provides a technical overview of Orga's architecture for developers extending or integrating with the module.

## Overview

Orga is built as a standard Frappe application, following Frappe's conventions for DocTypes, APIs, and permissions. The frontend is a Vue 3 Single Page Application written in TypeScript.

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│        (Vue 3 SPA with TypeScript + Vite)           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   REST API Layer                     │
│              (orga/orga/api/*.py)                   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                  DocType Layer                       │
│            (Controllers & Validation)               │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                    Database                          │
│                   (MariaDB)                         │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

```
orga/
├── orga/
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── project.py          # Project API
│   │   ├── task.py             # Task API
│   │   └── dashboard.py        # Dashboard API
│   │
│   ├── doctype/                # DocType definitions
│   │   ├── orga_project/       # Project DocType
│   │   ├── orga_task/          # Task DocType
│   │   ├── orga_milestone/     # Milestone DocType
│   │   └── orga_settings/      # Settings (Single)
│   │
│   ├── fixtures/               # Default data
│   │   └── custom_roles.json   # Role definitions
│   │
│   └── tests/                  # Test suite
│       └── test_api.py
│
├── frontend/                   # Vue 3 + TypeScript SPA
│   ├── src/
│   │   ├── pages/              # Route views
│   │   ├── components/         # Reusable components
│   │   ├── composables/        # Vue composition hooks (.ts)
│   │   └── types/              # TypeScript definitions
│   │       ├── frappe.d.ts     # Frappe framework types
│   │       └── orga.ts         # Orga DocType interfaces
│   ├── tsconfig.json           # TypeScript configuration
│   └── vite.config.ts          # Vite build config
│
├── hooks.py                    # Frappe hooks
├── install.py                  # Installation scripts
└── docs/                       # Documentation
```

## Frontend Architecture

Orga uses a modern Vue 3 Single Page Application with full TypeScript support.

### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Vue | 3.4.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 7.x | Build tool |
| Vue Router | 4.x | Client-side routing |
| Tailwind CSS | 3.4.x | Styling |
| FrappeUI | 0.1.x | Frappe component library |

### Type Definitions

All Orga data types are defined in `frontend/src/types/`:

```typescript
// orga.ts - Orga DocType interfaces
export interface OrgaProject {
  name: string
  project_name: string
  status: 'Planning' | 'Active' | 'On Hold' | 'Completed' | 'Cancelled'
  progress: number
  // ... other fields
}

export interface OrgaTask {
  name: string
  subject: string
  project: string
  status: 'Open' | 'In Progress' | 'Review' | 'Completed' | 'Cancelled'
  priority: 'Low' | 'Medium' | 'High' | 'Urgent'
  // ... other fields
}
```

Frappe framework types are in `frappe.d.ts`:

```typescript
// frappe.d.ts - Frappe globals
declare const frappe: {
  call: <T>(options: FrappeCallOptions) => Promise<FrappeCallResponse<T>>
  session: { user: string; user_email: string }
  // ... other methods
}
```

### Building the Frontend

```bash
# Install dependencies
cd apps/orga/frontend
npm install

# Development server
npm run dev

# Production build
npm run build

# Type checking
npx vue-tsc --noEmit
```

### Extending the Frontend

When adding new components or pages:

1. Create Vue components with `<script setup lang="ts">`
2. Import types from `@/types/orga`
3. Use typed refs: `const projects = ref<OrgaProject[]>([])`
4. Define typed props and emits

Example component:

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { OrgaProject } from '@/types/orga'

const props = defineProps<{
  projectId: string
}>()

const project = ref<OrgaProject | null>(null)
</script>
```

---

## DocTypes

### Orga Project

The main container for project data.

**Key Features:**
- Auto-generated project codes (`ORG-YYYY-NNNN`)
- Date validation (end date must be after start date)
- Progress calculation from linked tasks
- Deletion protection when tasks exist

**Naming:** `field:project_code`

### Orga Task

Individual work items within projects.

**Key Features:**
- Naming series (`TASK-.#####`)
- Status workflow with automatic completion date
- Circular reference prevention for parent tasks
- Triggers project progress recalculation

**Hooks:**
- `before_save`: Sets completion date
- `on_update`: Updates project progress
- `validate`: Checks parent task references

### Orga Milestone

Key deliverables and checkpoints.

**Key Features:**
- Naming series (`MS-.#####`)
- Auto-missed status for overdue items
- Completion date tracking

### Orga Settings

Module-wide configuration (Single DocType).

**Sections:**
- Defaults (task status, project status, priority)
- Features (auto-calculate progress, time tracking)
- Notifications (assignment, status change, due date)

## API Layer

APIs are organized by domain:

### project.py
- `get_projects()` - List with filters and pagination
- `get_project(name)` - Single project with details
- `create_project(data)` - Create new project
- `update_project(name, data)` - Update existing
- `delete_project(name)` - Delete (with protection)
- `get_project_stats(name)` - Statistics

### task.py
- `get_tasks()` - List with filters
- `get_task(name)` - Single task details
- `create_task(data)` - Create task
- `update_task(name, data)` - Update task
- `delete_task(name)` - Delete task
- `update_task_status(name, status)` - Quick status change
- `get_tasks_by_status(project)` - Kanban grouping
- `get_my_tasks()` - Current user's tasks
- `bulk_update_status(tasks, status)` - Batch operations

### dashboard.py
- `get_stats()` - Comprehensive statistics
- `get_recent_activity()` - Activity feed
- `get_overdue_tasks()` - Overdue items
- `get_upcoming_milestones()` - Upcoming milestones
- `get_project_summary()` - Project overview
- `get_workload_by_user()` - Workload distribution

## Permissions Model

### Roles

| Role | Purpose |
|------|---------|
| System Manager | Full access (Frappe built-in) |
| Orga Manager | Full access to Orga features |
| Orga User | Limited access (no delete, own tasks only) |

### Permission Matrix

| DocType | Role | Create | Read | Write | Delete |
|---------|------|--------|------|-------|--------|
| Orga Project | Orga Manager | ✓ | ✓ | ✓ | ✓ |
| Orga Project | Orga User | ✓ | ✓ | ✓ | ✗ |
| Orga Task | Orga Manager | ✓ | ✓ | ✓ | ✓ |
| Orga Task | Orga User | ✓ | ✓ | ✓ | ✓* |
| Orga Milestone | Orga Manager | ✓ | ✓ | ✓ | ✓ |
| Orga Milestone | Orga User | ✓ | ✓ | ✓ | ✗ |
| Orga Settings | Orga Manager | - | ✓ | ✓ | - |
| Orga Settings | Orga User | - | ✓ | ✗ | - |

*Orga User can only delete tasks they own (`if_owner: 1`)

## Data Flow

### Creating a Task

```
1. API receives create_task(data)
2. Validates required fields (subject, project)
3. Creates Orga Task document
4. Task.validate() runs validation
5. Task.before_save() sets defaults
6. Document saved to database
7. Task.on_update() triggers project progress update
8. Response returned to client
```

### Updating Task Status (Kanban)

```
1. API receives update_task_status(name, status)
2. Validates status is in allowed list
3. Loads task document
4. Updates status field
5. before_save() sets/clears completion date
6. Document saved
7. on_update() recalculates project progress
8. Returns updated task data
```

## Extending Orga

### Adding Custom Fields

Use Frappe's Customize Form to add fields to Orga DocTypes without modifying core code.

### Custom Hooks

In your app's `hooks.py`:

```python
doc_events = {
    "Orga Task": {
        "on_update": "your_app.handlers.on_task_update"
    }
}
```

### Custom API Endpoints

Create new endpoints in your app:

```python
# your_app/api/custom.py
import frappe

@frappe.whitelist()
def custom_task_report(project):
    # Your custom logic
    pass
```

## Testing

Run tests with:

```bash
bench run-tests --app orga
```

Test files are located in:
- `orga/orga/doctype/*/test_*.py` - DocType tests
- `orga/tests/test_api.py` - API tests

## Performance Considerations

- Project progress calculation runs on every task save
- Large projects may benefit from background jobs for progress updates
- Use pagination for list endpoints with large datasets
- Consider caching for dashboard statistics
