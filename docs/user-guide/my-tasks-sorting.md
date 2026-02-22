# Sorting Your Task List

The My Tasks page lets you sort your task list by any column — due date, task name, project, priority, or status — so you can focus on what matters right now.

Your sort preference is remembered across sessions. Come back tomorrow and the list is still ordered the way you left it.

## Changing the Sort Order

### Toolbar Dropdown

The filter bar includes a **Sort** dropdown and a **direction toggle** button, visible on every screen size.

1. Open **My Tasks** from the sidebar
2. Find the **Sort** dropdown in the filter bar (after the search box)
3. Select a sort field:
   - **Sort: Due Date** — nearest deadlines first (default)
   - **Sort: Task** — alphabetical by task name
   - **Sort: Project** — alphabetical by project name
   - **Sort: Priority** — Urgent → High → Medium → Low
   - **Sort: Status** — alphabetical by status label
4. Click the **arrow button** next to the dropdown to reverse the direction

The arrow icon changes to reflect the current direction — up-arrow for ascending, down-arrow for descending.

### Column Headers

On desktop, you can also click any sortable column header in the task table to sort by that column.

- **First click** on a column → sorts by that column in its natural direction (ascending for most fields, descending for Priority so that Urgent tasks appear first)
- **Click the same column again** → reverses the direction
- **Click a different column** → switches to that column with its natural default

The active column header is highlighted and shows a directional arrow (up or down). Inactive sortable columns show a faint sort icon.

Both controls stay in sync — clicking a column header updates the toolbar dropdown, and vice versa.

## Sort Fields

| Sort Option | Ascending (↑) | Descending (↓) |
|-------------|----------------|-----------------|
| **Due Date** | Nearest deadline first | Farthest deadline first |
| **Task** | A → Z by task name | Z → A by task name |
| **Project** | A → Z by project name | Z → A by project name |
| **Priority** | Low → Medium → High → Urgent | Urgent → High → Medium → Low |
| **Status** | A → Z by status label | Z → A by status label |

Priority sort uses semantic ordering rather than alphabetical — Urgent is always treated as "highest" regardless of direction.

## Persistence

Your sort preference (field and direction) is saved in your browser's local storage. It persists across page refreshes and browser restarts. Each browser keeps its own preference independently.

If you clear your browser data, the sort resets to the default (Due Date, ascending).

## Tips

- **Triage by priority** — sort by Priority (descending) to see your most urgent work at the top.
- **Group by project** — sort by Project to see all tasks for each project clustered together.
- **Find overdue tasks** — sort by Due Date (ascending) and look for the red "overdue" badges at the top.
- **Combine with filters** — sorting works with all other filters (status, priority, project, assignee, search). Filter first, then sort the remaining results.
- **Load More preserves sort** — when you click "Load More" to see additional tasks, the new batch follows the same sort order.
- **Mobile-friendly** — on small screens, column headers are hidden but the toolbar dropdown and direction button are always available.

## Related

- [Task Manager](task-manager.md) — click any task in the sorted list to open the full Task Manager panel
- [Getting Started](getting-started.md) — first steps with Orga
