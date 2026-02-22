# Dependency Scheduling

Dependency scheduling controls how completing or rescheduling tasks affects their successors. When a task's dates shift or it's marked complete, dependent tasks can shift too — automatically, with your confirmation, or not at all, depending on your project's dependency mode.

## Setting Up Dependencies

### Add a Dependency

1. Open a task from any view (Kanban, List, or Gantt)
2. Go to the **Dependencies** tab in the Task Manager
3. Select a dependency type (Finish-to-Start is the most common)
4. Choose the predecessor task from the dropdown
5. Click the **+** button

The most common type is **Finish-to-Start (FS)**: the predecessor must finish before the successor can start. Optionally set **lag days** to add a buffer between the two tasks (e.g. "+2d" means the successor starts 2 days after the predecessor ends).

### Dependency Types

| Type | Code | Meaning |
|------|------|---------|
| Finish-to-Start | FS | Successor starts after predecessor finishes |
| Start-to-Start | SS | Successor starts when predecessor starts |
| Finish-to-Finish | FF | Successor finishes when predecessor finishes |
| Start-to-Finish | SF | Successor finishes when predecessor starts |

### Create Dependencies on the Gantt Chart

You can also create Finish-to-Start dependencies visually:

1. Hover over a task bar to reveal a small circle on the right edge
2. Drag from that circle to another task bar
3. The target task highlights green when hovered
4. Release to create the dependency

An arrow will appear connecting the two tasks.

## Dependency Modes

Each project has a **Dependency Mode** setting that controls how date changes ripple through the schedule. You can change the mode from the project detail page header.

### Flexible (Default)

When you change a task's dates, Orga calculates which successor tasks would be affected and shows you a confirmation dialog:

> "This affects 3 dependent task(s). Apply cascade?"

- Click **Apply** to shift all affected successors
- Click **Cancel** to keep only the original change

This is the safest option for most teams — you see the impact before anything changes.

### Strict

Date changes automatically cascade to all successor tasks. No confirmation dialog appears. A toast notification tells you how many tasks were updated.

Best for projects with hard sequential dependencies (construction, manufacturing) where delays must propagate immediately.

### Off

Dependencies are informational only. Dates never cascade. You can still see dependency arrows and blocked status, but changing one task's dates won't affect any other task.

Best for agile teams who track relationships for visibility but manage dates independently.

## What Happens When You Complete a Task

When you mark a predecessor task as **Completed** and your project's dependency mode is Flexible or Strict:

1. Orga checks all Finish-to-Start successors of the completed task
2. For each successor, it calculates the earliest valid start date:
   - **Anchor** = the later of today or the day after the predecessor's due date
   - **New start** = anchor + lag days
3. The successor's start date moves to the new start, and the due date shifts by the same amount (preserving the task's duration)

Successors are only moved when **all** their FS predecessors are complete. If a successor depends on two tasks and only one is done, it stays where it is.

**Example — Early Completion:**
```
Task A planned:  Jan 1 – Jan 10
Task A completed: Jan 7 (3 days early)
  |
  FS dependency (1 day lag)
  |
Task B planned:  Jan 12 – Jan 16
Task B moves to: Jan 8 – Jan 12  (anchor = today Jan 7 → Jan 8 + 0 lag for next day)
```

**Example — On-Time Completion:**
```
Task A planned:  Jan 1 – Jan 10
Task A completed: Jan 10 (on time)
  |
  FS dependency (0 lag)
  |
Task B planned:  Jan 15 – Jan 20  (had a gap)
Task B moves to: Jan 11 – Jan 16  (anchor = Jan 11, the day after due date)
```

Duration is always preserved — only the position shifts, not the work estimate.

## Blocked Tasks

A task is **blocked** when it has incomplete Finish-to-Start predecessors. Blocked tasks display visual indicators across all views:

- **Kanban**: Amber lock badge next to priority, card dimmed to 60% opacity
- **List**: Amber lock badge next to status, row dimmed
- **Gantt**: Lock icon on the task bar

Hover over a blocked task to see which predecessors are blocking it:

> "Blocked by: Design Review, API Integration"

When all predecessors are complete, the blocked status clears automatically and the assignee receives an in-app notification:

> "Your task 'QA Testing' is no longer blocked and can now be started."

## Group Dependencies

Tasks can depend on an entire group instead of individual tasks. Set the **Depends on Group** field to a group name — the task stays blocked until all tasks in that group are complete.

This is useful for milestone-like gates: "Don't start the Testing phase until all Development tasks are done."

## Critical Path

The Gantt chart includes a **Critical Path** toggle that highlights the longest chain of dependent tasks. Any delay on a critical task pushes back the project end date.

When enabled:
- Critical tasks get a red ring outline
- Non-critical tasks dim to 40% opacity
- Dependency arrows between critical tasks turn red and thicker
- Non-critical arrows fade out

This helps you focus effort on the tasks that matter most for your deadline.

## Task Scheduling Types

Each task has a scheduling type that controls how its dates are managed.

### Fixed Duration (Default)

Standard tasks with manually-set start and end dates. You can change dates by editing the task or dragging the bar on the Gantt chart.

### Hammock

A hammock task automatically spans the gap between its predecessor's end and its successor's start. You don't set the dates — they're calculated:

- **Start** = latest predecessor end + 1 day + lag
- **End** = earliest successor start - 1 day - lag

Hammock tasks appear with a hatched stripe pattern on the Gantt chart and cannot be dragged. They absorb schedule slack between anchoring tasks.

### Buffer

Buffer tasks represent explicit schedule padding (Critical Chain Method). They have:

- **Buffer size**: Planned padding in days
- **Buffer consumed**: Percentage consumed by upstream delays (read-only)

The consumption bar uses traffic-light colors:
- **Green** (0-33%): Schedule is healthy
- **Yellow** (34-66%): Caution — delays are eating into the buffer
- **Red** (67-100%): Critical — buffer nearly exhausted

Buffer tasks appear with a striped pattern and shield icon on the Gantt chart.

## Tips

- Start with **Flexible** mode. Switch to Strict only when you're confident in your dependency chain.
- Use **lag days** to build in natural gaps (e.g. drying time, review periods) without creating separate buffer tasks.
- Keep dependency chains short. Long chains amplify small delays.
- Use the **Critical Path** toggle to identify which tasks can't slip without affecting the project end date.
- **Group dependencies** work well for phase gates — "all design tasks done before development starts."
