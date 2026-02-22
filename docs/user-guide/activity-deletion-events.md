# Deletion Events in the Activity Feed

When you delete a project, the activity feed records the event so your team can see what was removed, when, and by whom. Without this, deleted projects would simply vanish — no trace, no accountability.

## What Gets Logged

When a project is deleted through the **Delete Project** action (from the settings gear menu), Orga creates a permanent activity entry that includes:

- The project's name
- The number of tasks and milestones that were deleted with it
- Who performed the deletion
- When it happened

This entry persists in the activity feed even though the project itself no longer exists.

## How It Appears

On the Activity page, deletion events show up alongside regular task and milestone updates. They're visually distinct:

- A **red "Deleted" badge** with a trash icon replaces the usual type badge
- The deletion details appear in red text, for example: *Deleted project "Website Redesign" (12 tasks, 3 milestones)*
- The user who performed the deletion appears as the activity author with their avatar and timestamp

## Filtering

The Activity page filter bar includes a **Projects** filter. Clicking it shows only project-related events, including deletions. You can also use the existing project dropdown filter, though deletion events are not associated with a project (since it no longer exists) — they appear under "All Projects."

## What Isn't Logged

Currently, deletion events are created for **project deletions** only. Individual task or milestone deletions within a project do not create separate activity entries — they are summarized in the project deletion event.

## Viewing Old Deletion Events

Deletion events are stored as system notes and appear in the activity feed like any other activity. They can be:

- **Pinned** to keep them visible at the top of the feed
- **Archived** to hide them from the default view (toggle "Show Archived" to see them again)
- **Reacted to** — your team can acknowledge, flag, or comment on deletion events just like any other activity

## Tips

- **Check the Activity page after a deletion** to confirm the event was logged, especially if other team members need to be informed.
- **Use the Manager panel** to add a comment explaining why the project was deleted — click on the deletion event and use the comment thread.
- **Pin important deletion events** if the team needs to be aware of the change for a period of time.
