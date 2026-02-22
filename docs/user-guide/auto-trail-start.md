# Auto-Trail Start

Auto-Trail Start keeps a task's start date from falling into the past while the task hasn't been worked on yet. When enabled, Orga automatically moves the start date forward to today — and shifts the due date by the same amount to preserve the task's planned duration — as long as the task is still Open with 0% progress.

This prevents your Gantt chart and schedule from showing tasks as "starting last week" when they simply haven't been picked up yet.

## How It Works

When Auto-Trail Start is enabled on a task, Orga checks three conditions:

1. **Status is Open** — once the task moves to In Progress, Review, or any other status, trailing stops
2. **Progress is 0%** — as soon as any progress is recorded, the date locks in place
3. **Start date is in the past** — if the start date is today or in the future, there's nothing to trail

When all three conditions are true, the start date snaps to today. If the task has a due date, it shifts forward by the same number of days, so the task's duration stays the same.

**Example:**
```
Task: "Write user manual"
Start date: Feb 10    Due date: Feb 14    (5-day duration)
Today: Feb 17

Auto-Trail snaps:
Start date → Feb 17   Due date → Feb 21   (still 5-day duration)
```

Once you change the status to In Progress or record any progress, the dates stay where they are — trailing stops permanently until you reset the task to Open with 0% progress.

## Enabling Auto-Trail on a Task

### From the Task Manager

1. Open any task from Kanban, List, or Gantt view
2. Go to the **Details** tab
3. Below the date fields, find the **Auto-Trail Start** checkbox
4. Check it to enable trailing

The checkbox has a blue highlight when active. The setting saves immediately.

### When Creating a Task

1. Click **+ New Task** from any project view
2. Fill in the task details and dates
3. Below the Start Date and End Date fields, check **Auto-Trail Start**
4. Click **Create Task**

If the project has Auto-Trail enabled as a default (see below), the checkbox will already be checked when you open the form. You can uncheck it for individual tasks that shouldn't trail.

## Project-Level Default

You can set Auto-Trail Start as the default for all new tasks in a project, so you don't have to enable it on each task individually.

1. Open your project
2. Click the **gear icon** (settings) in the project toolbar
3. Click **Auto-Trail Start** in the dropdown menu
4. A checkmark appears next to the option when it's active

When this project default is on:
- New tasks created in this project will have Auto-Trail Start enabled automatically
- You can still uncheck it on individual tasks that shouldn't trail
- Existing tasks are not affected — only newly created tasks inherit the default

Click the option again to disable the default. The checkmark disappears and new tasks will no longer have Auto-Trail enabled by default.

## When Trailing Happens

Auto-Trail Start runs at two points:

### On Save

Every time a trailing task is saved (from the Task Manager, API call, or any other edit), the dates snap forward if the start date is in the past. This means the dates update the moment you interact with the task.

### Daily Catch-Up

A daily scheduled job runs overnight and updates all trailing tasks whose start dates have fallen behind. This covers tasks that weren't explicitly opened or edited during the day — they still stay current.

## When Trailing Stops

Trailing stops automatically when any of these happen:

- **Status changes** from Open to anything else (In Progress, Review, Completed, Cancelled)
- **Progress increases** above 0% (even 1% is enough to lock the dates)
- **You uncheck** the Auto-Trail Start checkbox on the task

The checkbox remains visible regardless — you can re-enable it later if needed. But once work has started (status or progress changed), trailing no longer applies even if the checkbox is still checked.

## Tips

- **Use the project default** for projects where most tasks are planned ahead but started on a rolling basis. This saves you from enabling it on each task individually.
- **Pair with Gantt view** to see the effect — trailing tasks always appear at or after today's date line, keeping your timeline clean and forward-looking.
- **Don't use on fixed-date tasks** — if a task must start on a specific date regardless of whether work has begun (e.g. a client deadline, a scheduled deployment), leave Auto-Trail off.
- **Duration is always preserved** — only the position shifts, never the planned work estimate. A 5-day task stays a 5-day task.
