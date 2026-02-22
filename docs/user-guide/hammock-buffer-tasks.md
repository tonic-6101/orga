# Hammock & Buffer Tasks

In addition to standard tasks with fixed dates, Orga supports two advanced scheduling types: **hammock tasks** that automatically fill gaps in your schedule, and **buffer tasks** that protect your timeline with explicit padding.

## Task Scheduling Types

Every task has a scheduling type that controls how its dates work:

| Type | How dates work | Draggable on Gantt |
|------|---------------|-------------------|
| **Fixed Duration** (default) | You set the start and end dates manually | Yes |
| **Hammock** | Dates are calculated automatically from dependencies | No |
| **Buffer** | You set the start date and buffer size; end is calculated | No |

To change a task's scheduling type, open the task and look for the **Scheduling Type** field.

## Hammock Tasks

A hammock task automatically spans the gap between two anchoring tasks. You don't set its dates — they're calculated from its dependencies.

### How It Works

A hammock task needs at least one predecessor and one successor:

```
Task A (ends Jan 10)
  |
  Hammock X (Jan 11 – Jan 19, auto-calculated)
  |
Task B (starts Jan 20)
```

- **Start date** = day after the latest predecessor ends (+ any lag)
- **End date** = day before the earliest successor starts (- any lag)
- **Duration** = calculated automatically

### When Dates Recalculate

Hammock dates update automatically when:
- A predecessor's end date changes
- A successor's start date changes
- A dependency is added or removed

If Task A slips from Jan 10 to Jan 15, the hammock shrinks accordingly:

```
Before: Hammock X = Jan 11 – Jan 19 (9 days)
After:  Hammock X = Jan 16 – Jan 19 (4 days)
```

### On the Gantt Chart

Hammock tasks appear with a **hatched stripe pattern** and an arrows icon. You cannot drag them — their position is determined entirely by their dependencies.

### When to Use Hammock Tasks

- **Review periods** between design completion and development start
- **Resource availability windows** between two fixed milestones
- **Integration periods** that absorb scheduling slack naturally

## Buffer Tasks

Buffer tasks represent explicit schedule padding using the Critical Chain Method. They protect your project timeline by absorbing delays from upstream tasks.

### How It Works

A buffer task has two key fields:

- **Buffer Size** (days) — How much padding you've planned
- **Buffer Consumed** (%) — How much of that padding has been eaten by upstream delays (calculated automatically)

### Buffer Consumption

The consumed percentage shows how much of your planned padding has been used by delays in predecessor tasks:

| Consumed | Color | What It Means |
|----------|-------|---------------|
| 0–33% | Green | Schedule is healthy |
| 34–66% | Yellow | Delays are accumulating — pay attention |
| 67–100% | Red | Buffer nearly exhausted — the deadline is at risk |

### On the Gantt Chart

Buffer tasks appear with a **striped pattern** and a shield icon. A small progress bar inside the task bar shows the consumption level using the traffic-light colors above.

### When to Use Buffer Tasks

- **End of a critical chain** — Place a buffer before the final milestone to absorb delays from the longest task chain
- **Before handoff points** — Add a buffer between your team's work and an external dependency
- **Before fixed deadlines** — Protect a hard deadline by placing a buffer upstream

### Example

```
Backend API (10 days)
  →  Frontend UI (8 days)
    →  Integration Buffer (5 days, buffer task)
      →  Release Milestone
```

If the Backend API takes 12 days (+2 day delay), the buffer absorbs it:
- Buffer consumed = 40% (yellow)
- The release date hasn't moved — yet

If total delays reach 5 days, the buffer is 100% consumed and the release date is at risk.

## Tips

- **Start with fixed-duration tasks.** Only use hammock and buffer tasks when you have a well-defined dependency chain.
- **One buffer per chain.** Place a single buffer task at the end of each critical chain rather than multiple small buffers.
- **Watch the traffic light.** The buffer consumption indicator is your early warning system — yellow means it's time to look at what's causing delays.
- **Hammock tasks are great for "whatever time is left" work** — code review, documentation, polish — activities that can expand or contract with the schedule.
