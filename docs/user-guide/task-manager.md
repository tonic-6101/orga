# Task Manager

The Task Manager is Orga's central panel for viewing and editing everything about a task. Open it by clicking any task in your Kanban board, list view, or Gantt chart. An icon-based tab bar at the top lets you switch between nine sections — from editing details to tracking time to managing files.

## Opening the Task Manager

You can open the Task Manager from any project view:

- **Kanban view** — Click a task card
- **List view** — Click a task row
- **Gantt view** — Click a task bar on the timeline
- **My Tasks page** — Click a task's subject to navigate to its project, then open the task

The Task Manager appears as a side panel. Close it with the X button in the top-right corner.

## Details

The Details tab is the first thing you see when you open a task. It shows all the core information and lets you edit most fields inline.

- **Priority and status badges** — See the current priority (Urgent, High, Medium, Low) and status (Open, In Progress, Review, Completed, Cancelled) at a glance
- **Subject** — Click the task name to edit it inline. Press Enter to save or Escape to cancel
- **Description** — Click to edit. A text area opens with Save and Cancel buttons
- **Task Group** — Assign the task to a group (e.g. "Pre-work", "Finishing") with autocomplete from existing groups. Click the X to remove a group
- **Depends on Group** — Set a group dependency so this task waits until all tasks in that group are complete. Uses the same autocomplete as Task Group
- **Assigned Contact** — Click to open a dropdown picker showing all project contacts. Select a name to assign, or choose "Unassign" to clear the assignment. Contacts with linked Frappe users are also assigned at the system level
- **Start Date and Due Date** — Pick dates using the calendar inputs. Click the X button next to a date to clear it
- **Auto-Trail Start** — A checkbox below the date fields. When enabled, the start date automatically trails forward to today while the task is Open with 0% progress. The due date shifts by the same amount to preserve the task's duration. See [Auto-Trail Start](auto-trail-start.md) for the full guide
- **Time tracking summary** — Shows estimated hours and actual hours logged (read-only; log time in the Time tab)
- **Progress** — A visual progress bar with a slider, number input, and quick-set buttons for 0%, 25%, 50%, 75%, and 100%. Progress editing is disabled for Completed or Cancelled tasks
- **Project** — Shows which project the task belongs to (read-only)

## Dependencies

The Dependencies tab shows which tasks are connected to this one and lets you add, edit, or remove relationships. For a full guide on how dependency scheduling works across your project, see [Dependency Scheduling](dependency-scheduling.md).

### Predecessors (Blocked By)

Tasks that must finish (or start) before this task. Each predecessor shows:

- **Dependency type** — A colored badge: FS (Finish-to-Start), SS (Start-to-Start), FF (Finish-to-Finish), or SF (Start-to-Finish)
- **Task name** and current status
- **Lag days** — Optional delay between the two tasks (e.g. "+2d lag")

Click the pencil icon to edit the type or lag. Click the trash icon to remove the dependency (with a confirmation step).

If all FS predecessors are incomplete, the task shows a **Blocked** badge (amber lock icon) and the card/row is dimmed. Hover to see which tasks are blocking it.

### Successors (Blocking)

Tasks that are waiting for this one. These are read-only — to change them, go to the successor task and edit its predecessors. When you complete this task, its successors may automatically advance (depending on the project's [dependency mode](dependency-scheduling.md#dependency-modes)).

### Adding a Dependency

At the bottom of the tab, select a dependency type and a task from the dropdown, then click the + button to add a new predecessor.

### Visual Dependency Chain (Gantt View)

In Gantt view, the Dependencies tab shows an interactive flowchart instead of the standard list. Click a connected task to navigate to it directly. You can also create Finish-to-Start dependencies by dragging from the connection handle on the right edge of any task bar to another task.

## Time

The Time tab lets you track time spent on the task using a built-in timer or manual entry.

### Timer Control

- **Start Timer** — Click to begin tracking time for this task
- **Switch to this task** — If a timer is already running on a different task, click to stop it and start tracking this one instead
- **Stop & Save** — Stop the running timer and save the time log. You can optionally add a description of what you worked on before stopping
- **Live elapsed time** — A large clock display shows hours, minutes, and seconds while the timer runs

### Time Summary

- **Estimated vs. Actual hours** — Side-by-side comparison. Actual hours turn red when they exceed the estimate
- **Progress bar** — Visual indicator of how much of the estimate has been used
- **Entry count** — Number of individual time log entries

### Time Log List

A scrollable list of all time entries for this task, showing hours, date, and description. Hover over an entry to reveal the delete button.

- **+ Log Time** — Opens the manual time entry form for retrospective logging

## Finance

The Finance tab tracks costs and billing for the task. All monetary fields are click-to-edit.

### Cost Summary

- **Estimated Cost** — Click to enter the planned cost for this task
- **Actual Cost** — Click to enter what has been spent so far
- **Budget Variance** — Automatically calculated as estimated minus actual. Shows the amount and percentage, colored green (under budget) or red (over budget)

### Time & Billing

- **Estimated and Actual Hours** — Read-only summary pulled from time tracking
- **Billable toggle** — Mark whether this task's time is billable to a client
- **Billing Rate** — When billable is enabled, click to set an hourly rate
- **Billable Amount** — Automatically calculated as actual hours multiplied by the billing rate

### Budget Burn Rate (Gantt View)

When viewing from the Gantt chart, tasks with a budget show a visual burn rate bar above the finance details.

## Checklist

The Checklist tab breaks tasks down into smaller items you can tick off.

- **Progress bar** — Shows the percentage of completed items with a visual bar
- **Toggle items** — Click the checkbox to mark items complete or incomplete. Completed items show a strikethrough
- **Add items** — Type in the input at the bottom and press Enter or click the + button
- **Promote to Task** — Hover over any incomplete item to reveal a promote button (arrow icon). One click converts the checklist item into a full Orga Task that inherits the parent's project, priority, and milestone. The original checklist item is removed automatically
- **Delete items** — Hover over any item to reveal the trash icon

## Comments

The Comments tab provides a threaded discussion area for the task.

- **Comment list** — Each comment shows the author's avatar, name, and a relative timestamp (e.g. "5m ago", "2d ago")
- **Add a comment** — Type in the text area at the bottom. Press **Ctrl+Enter** (or **Cmd+Enter** on Mac) to send, or click the send button
- **Delete comments** — Hover over your own comments to reveal the delete button. System Managers can delete any comment

## Files

The Files tab manages file attachments for the task.

- **File list** — Each file shows a type-specific icon (PDF, image, Word, Excel, CAD, archive, etc.), the filename as a clickable download link, and the file size
- **Upload files** — Click the dashed upload area to open a file picker, or drag and drop a file onto it. A progress bar shows upload status
- **Delete files** — Hover over a file to reveal the trash icon

## Actions

The Actions tab provides quick controls for managing the task.

### Change Status

A row of buttons showing all available statuses (Open, In Progress, Review, Completed). The current status is highlighted. Click any button to change the status instantly.

### Change Priority

A row of buttons for Low, Medium, High, and Urgent. The current priority is highlighted with its color. Click to change.

### Quick Actions

- **Open Task Log** — Opens the full Frappe Desk view in a new tab, giving you access to the audit trail, version history, and all system-level details
- **Assign to Me** — One-click self-assignment. If you have a matching contact record, the assignment is created automatically
- **Duplicate Task** — Creates a copy of the task with "(Copy)" appended to the name, keeping the same project, description, priority, and estimated hours
- **Delete Task** — Opens a confirmation dialog. Deletion is permanent and cannot be undone

## Cascade (Gantt View Only)

The Cascade tab appears only in Gantt view and only when the current task has dependent tasks (successors). It shows how date changes ripple through the project schedule. The behavior depends on the project's [dependency mode](dependency-scheduling.md#dependency-modes).

### Flexible Mode

- **Affected tasks list** — Each downstream task is listed with the number of days it would shift (e.g. "+3 days" or "-1 day")
- **Preview** — Highlights the affected tasks on the Gantt timeline
- **Apply Changes** — Commits the cascaded date changes to all affected tasks
- **Cancel** — Discards the cascade without making changes

### Strict Mode

Date changes cascade automatically. A toast notification shows how many tasks were updated — no confirmation step.

### Off Mode

The Cascade tab shows a message that dependency scheduling is disabled. Date changes apply only to the current task.

When no date changes are pending, the tab shows a placeholder message explaining that changes will appear here when you adjust this task's dates.

For details on how completing tasks advances successors, critical path highlighting, and advanced scheduling types, see [Dependency Scheduling](dependency-scheduling.md).
