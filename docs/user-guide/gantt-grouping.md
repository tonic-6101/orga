# Gantt Chart Grouping

When your project has many tasks, the Gantt chart can become hard to scan. Grouping organizes tasks under collapsible headers so you can focus on what matters.

## How to Group Tasks

1. Open a project and switch to the **Gantt** view
2. Find the **grouping dropdown** in the Gantt toolbar (it says "No Grouping" by default)
3. Select a grouping mode:

| Mode | Groups tasks by |
|------|----------------|
| **No Grouping** | Tasks appear in their natural order |
| **By Group** | The task's group field |
| **By Status** | Open, In Progress, Review, Completed, etc. |
| **By Priority** | Urgent, High, Medium, Low |
| **By Milestone** | Which milestone the task is linked to |
| **By Assignee** | Who the task is assigned to |

Tasks without a value for the selected field are placed in a group at the bottom (e.g., "Unassigned" or "No Milestone").

## Collapsing and Expanding Groups

Each group has a header row showing the group name and item count:

```
▼ IN PROGRESS (5)
    Task A    ████████████
    Task B         ██████████
► COMPLETED (12)               ← Collapsed — 12 tasks hidden
▼ OPEN (3)
    Task D    ██████
```

- Click a group header to **collapse** it — all tasks in that group are hidden
- Click again to **expand** and show the tasks
- The chevron icon shows the current state: `▼` expanded, `►` collapsed

## How Milestones Are Grouped

- When grouping by **Status**, milestones appear in their own status groups (Upcoming, In Progress, Completed, Missed)
- When grouping by **any other mode**, milestones are placed in a separate "Milestones" group at the bottom

## Dependency Arrows

Dependency arrows automatically adjust when you collapse or expand groups. If a task's group is collapsed, arrows pointing to or from that task are hidden. When you expand the group, the arrows reappear in the correct positions.

## What Changes When Grouping Is Active

- **Drag-to-reorder is disabled.** When grouping is active, you can't drag tasks to change their order, because the group determines their position. Switch back to "No Grouping" to reorder tasks manually.
- **Drag-to-create dependencies still works.** You can still drag from a task's connection handle to another task to create a dependency.
- **Switching group modes resets collapsed state.** If you collapse some groups and then switch to a different grouping mode, all groups start expanded.

## Tips

- **Use Status grouping for daily standups** — quickly see what's open, in progress, and completed
- **Use Assignee grouping for workload reviews** — see how tasks are distributed across the team
- **Use Priority grouping to focus on urgent work** — collapse Low and Medium to see only what's critical
- **Collapse completed groups** to reduce visual noise and focus on active work
