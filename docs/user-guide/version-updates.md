# Version Updates

Orga checks for new versions automatically and lets you know when an update is available. You'll see an indicator in the sidebar and can review update details on the Settings page.

## How It Works

Once a day, Orga checks the GitHub releases page for a newer version. If one is found, you'll see:

- An **amber "Update" link** next to the version number in the sidebar footer
- A **pulsing amber dot** in the sidebar when it's collapsed
- Full details on the **Updates** tab in Settings

No action is taken automatically — the indicator simply lets you know a newer version exists.

## Checking the Sidebar

The sidebar footer shows your current version:

```
Community Edition
v0.13.0  ↑ Update       ← Amber link appears when update is available
```

Click the **Update** link (or the amber dot when collapsed) to go to the Settings page for details.

If you're up to date, only the version number is shown — no indicator.

## Viewing Update Details

1. Go to **Settings** (sidebar or click the update link)
2. Click the **Updates** tab

You'll see:

- **Installed Version** — the version you're currently running
- **Latest Version** — the newest version available on GitHub
- **Last Checked** — when the update check last ran

### When an Update Is Available

An amber banner shows the version upgrade path and a preview of the release notes:

```
⚠ Update Available

A new version of Orga is available: 0.13.0 → 0.14.0

Release notes preview...

[View Release]  [Dismiss]
```

- **View Release** — opens the GitHub release page in a new tab where you can read the full release notes and find installation instructions
- **Dismiss** — hides the update notification for this specific version

### When You're Up to Date

A green banner confirms your version matches the latest release.

## Manual Check

Click **Check for Updates** on the Settings Updates tab to force a fresh check right now, instead of waiting for the daily automatic check.

This button is only available to users with Settings write permission or System Manager role.

## Dismissing an Update

If you're aware of an update but don't want to install it yet, click **Dismiss**. The sidebar indicator and Settings banner will stop showing for that version.

When a *newer* version is released, the notification will appear again — dismiss only applies to the specific version you dismissed.

Dismiss state is stored in your browser. If you use Orga from another browser or device, you'll see the notification there until you dismiss it separately.

## Tips

- **Updates are informational only.** Orga never installs or downloads anything automatically. The indicator just tells you a newer version exists.
- **Check release notes before updating.** Click "View Release" to read what changed and whether there are any migration steps.
- **The check runs daily.** If you just deployed and want to confirm the indicator clears, click "Check for Updates" to refresh immediately.
- **Offline is fine.** If your server can't reach GitHub, the check fails silently and tries again the next day. No errors are shown to users.
