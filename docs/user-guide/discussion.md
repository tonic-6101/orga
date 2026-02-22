# Discussion

Every task and activity in Orga has a Discussion tab where your team can have threaded conversations, resolve questions, and pin important messages — all without leaving the current view.

## Where to Find It

- **Task Manager panel** — click any task in Kanban, List, or Gantt view, then select the Discussion tab (speech bubble icon)
- **Activity Manager panel** — click any activity on the Activity page, then select the Discussion tab

Both use the same underlying system. Comments you post on a task's Discussion tab are stored as `Orga Activity Comment` records and appear in the same format everywhere.

## Adding a Comment

1. Type your message in the text editor at the bottom of the Discussion tab.
2. Use the formatting toolbar for bold, italic, lists, links, and code blocks.
3. Press **Ctrl+Enter** (or **Cmd+Enter** on Mac) to submit, or click the Send button.

### @Mentions

Type `@` followed by a name or email to mention a team member. A dropdown appears with matching users. Selecting a user inserts a mention and sends them a notification.

### Notes vs. Comments

When viewing the Discussion tab in the **Activity Manager**, you can toggle between Comment mode and Note mode using the input toggle. Notes have distinct visual treatment (tinted background, "Note" badge) and support note types like General, Due Diligence, Offer, and Decision.

In the **Task Manager**, the Discussion tab works in comment-only mode — no note toggle is shown.

## Filtering the Stream

A filter dropdown at the top of the tab lets you narrow what you see:

| Filter | Shows |
|--------|-------|
| **All** | Every comment and note (resolved comments shown faded) |
| **Comments** | Comments only, excluding resolved |
| **Notes** | Notes only (Activity Manager context) |
| **Resolved** | Only resolved threads |

The resolved count is displayed next to the filter dropdown so you can see at a glance how many threads have been closed.

## Threaded Replies

Click **Reply** on any comment to start a nested thread. Replies appear indented under the parent comment. Click "View X replies" to expand a collapsed thread.

## Resolving Threads

When a discussion reaches a conclusion or a question is answered, mark it as resolved:

1. Click the **Resolve** button (checkmark icon) on the comment.
2. The comment gains a green "Resolved" badge and is visually dimmed in the default view.
3. To reopen a resolved thread, click **Reopen**.

Resolved threads are hidden by default in the "Comments" filter mode. Switch to "All" or "Resolved" to see them again.

## Pinning a Comment

Pin an important comment to keep it visible at the top of the discussion stream:

1. Click the **Pin** button (thumbtack icon) on the comment.
2. The comment moves to the top of the list with a "Pinned" badge.
3. Only one comment can be pinned per document at a time — pinning a new comment automatically unpins the previous one.
4. Click **Unpin** to remove the pin.

Pinned comments are useful for decisions, meeting outcomes, or reference information that everyone should see first.

## Deleting Comments

You can delete your own comments. Users with the System Manager role can delete any comment. Click the trash icon on a comment to remove it.

## Tips

- **Use Resolve liberally** — it keeps the active discussion focused on open questions and reduces noise for teammates scanning the thread.
- **Pin decisions, not questions** — the pinned comment is the first thing everyone sees, so make it something actionable or conclusive.
- **@Mention for attention** — if you need a specific person to weigh in, mention them rather than hoping they'll check the thread.
- **Ctrl+Enter is fastest** — you can type and submit without reaching for the mouse.
