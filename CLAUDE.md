# Orga — Claude Code Context

## What Orga Is

Orga is the organization management app (Layer 2) in the Tonic ecosystem. It depends on Dock (Layer 1).

- **License:** AGPL-3.0-or-later
- **Stack:** Frappe v16+, Python 3.14+, Vue 3 + TypeScript + Tailwind CSS + FrappeUI

---

## Git Workflow

- **Remote:** `upstream` → `git@github.com:tonic-6101/orga.git`
- **Default branch:** `develop`
- **ALWAYS** specify remote and branch explicitly:

```bash
git pull upstream develop --rebase
git push upstream develop
```

- **NEVER** use bare `git push` / `git pull`
- **NEVER** force push unless the user explicitly requests it

### Version Bump Before Push

Every push with functional changes MUST include a version bump:

```bash
python3 bump_version.py patch
git add -A
git commit -m "feat(scope): description"
git push upstream develop
```

---

## Commit Guidelines

- Do not include Co-Authored-By trailers in commit messages
- Do not include @claude in commit messages
- Use the standard commit format: `type(scope): description`

---

## Version Management

| File | What it controls |
|------|-----------------|
| `VERSION` | Canonical source of truth |
| `orga/__init__.py` | `__version__` |
| `pyproject.toml` | `version` (dynamic) |
| `frontend/package.json` | `"version":` |

Use `bump_version.py` — NEVER edit version in just one file.

---

## License Headers

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic
```

```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic
```

---

## Workspace Context

This app is part of the Tonic ecosystem workspace at `dock16.localhost`. The workspace-level `CLAUDE.md` at `/home/tonic/frappe/sites/dock16.localhost/CLAUDE.md` has the full ecosystem context including specs, architecture, and cross-app rules.
