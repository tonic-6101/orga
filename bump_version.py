#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Version bump script for Orga apps.

Updates all version references in a single command:
  - VERSION file
  - <app>/__init__.py (__version__)
  - setup.py (version=)
  - frontend/package.json ("version":)
  - README.md (badge)

Usage:
  python bump_version.py 0.14.0
  python bump_version.py 0.14.0 --dry-run
  python bump_version.py --from-changelog
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def get_app_root() -> Path:
    """Return the app root directory (where this script lives)."""
    return Path(__file__).resolve().parent


def detect_app_name(app_root: Path) -> str:
    """Detect the Frappe app name from hooks.py."""
    hooks_path = None
    for child in app_root.iterdir():
        candidate = child / "hooks.py"
        if child.is_dir() and candidate.exists():
            hooks_path = candidate
            return child.name
    # Fallback: directory name
    return app_root.name


def read_current_version(app_root: Path) -> str:
    """Read current version from VERSION file."""
    version_file = app_root / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def get_latest_changelog_version(app_root: Path) -> str | None:
    """Extract latest version from docs/CHANGELOG.md."""
    changelog = app_root / "docs" / "CHANGELOG.md"
    if not changelog.exists():
        return None
    content = changelog.read_text()
    match = re.search(r"##\s*\[(\d+\.\d+\.\d+)\]", content)
    if match:
        return match.group(1)
    return None


def validate_version(version: str) -> bool:
    """Check that version follows semver format."""
    return bool(re.match(r"^\d+\.\d+\.\d+(-[\w.]+)?$", version))


def update_version_file(app_root: Path, new_version: str, dry_run: bool) -> bool:
    """Update the VERSION file."""
    path = app_root / "VERSION"
    if dry_run:
        print(f"  [dry-run] VERSION -> {new_version}")
        return True
    path.write_text(new_version + "\n")
    print(f"  VERSION -> {new_version}")
    return True


def update_init_py(app_root: Path, app_name: str, new_version: str, dry_run: bool) -> bool:
    """Update __version__ in <app>/__init__.py."""
    path = app_root / app_name / "__init__.py"
    if not path.exists():
        print(f"  [skip] {app_name}/__init__.py not found")
        return False

    content = path.read_text()
    new_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']*["\']',
        f'__version__ = "{new_version}"',
        content,
    )

    if content == new_content:
        # No __version__ line found, prepend it
        new_content = f'__version__ = "{new_version}"\n{content}'

    if dry_run:
        print(f"  [dry-run] {app_name}/__init__.py -> {new_version}")
        return True
    path.write_text(new_content)
    print(f"  {app_name}/__init__.py -> {new_version}")
    return True


def update_setup_py(app_root: Path, new_version: str, dry_run: bool) -> bool:
    """Update version in setup.py."""
    path = app_root / "setup.py"
    if not path.exists():
        print(f"  [skip] setup.py not found")
        return False

    content = path.read_text()
    new_content = re.sub(
        r'version\s*=\s*["\'][^"\']*["\']',
        f'version="{new_version}"',
        content,
    )

    if content == new_content:
        if re.search(r'version\s*=\s*["\']', content):
            print(f"  [skip] setup.py - already at {new_version}")
        else:
            print(f"  [skip] setup.py - no version= line found")
        return False

    if dry_run:
        print(f"  [dry-run] setup.py -> {new_version}")
        return True
    path.write_text(new_content)
    print(f"  setup.py -> {new_version}")
    return True


def update_package_json(app_root: Path, new_version: str, dry_run: bool) -> bool:
    """Update version in frontend/package.json."""
    path = app_root / "frontend" / "package.json"
    if not path.exists():
        print(f"  [skip] frontend/package.json not found")
        return False

    with open(path) as f:
        data = json.load(f)

    old_version = data.get("version", "0.0.0")
    data["version"] = new_version

    if dry_run:
        print(f"  [dry-run] frontend/package.json -> {new_version} (was {old_version})")
        return True

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"  frontend/package.json -> {new_version} (was {old_version})")
    return True


def update_readme_badge(app_root: Path, new_version: str, dry_run: bool) -> bool:
    """Update version badge in README.md."""
    path = app_root / "README.md"
    if not path.exists():
        print(f"  [skip] README.md not found")
        return False

    content = path.read_text()
    new_content = re.sub(
        r"version-[\d.]+(-[\w.]+)?-blue\.svg",
        f"version-{new_version}-blue.svg",
        content,
    )

    if content == new_content:
        if re.search(r"version-[\d.]+-blue\.svg", content):
            print(f"  [skip] README.md badge - already at {new_version}")
        else:
            print(f"  [skip] README.md - no version badge found")
        return False

    if dry_run:
        print(f"  [dry-run] README.md badge -> {new_version}")
        return True
    path.write_text(new_content)
    print(f"  README.md badge -> {new_version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bump version across all Orga app files")
    parser.add_argument("version", nargs="?", help="New version (e.g., 0.14.0)")
    parser.add_argument("--from-changelog", action="store_true",
                        help="Read version from latest CHANGELOG.md entry")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be changed without writing")
    args = parser.parse_args()

    app_root = get_app_root()
    app_name = detect_app_name(app_root)
    current_version = read_current_version(app_root)

    # Determine target version
    if args.from_changelog:
        new_version = get_latest_changelog_version(app_root)
        if not new_version:
            print("Error: Could not find version in docs/CHANGELOG.md")
            sys.exit(1)
    elif args.version:
        new_version = args.version
    else:
        parser.print_help()
        sys.exit(1)

    if not validate_version(new_version):
        print(f"Error: '{new_version}' is not a valid semver version")
        sys.exit(1)

    print(f"App: {app_name}")
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    if args.dry_run:
        print("Mode: DRY RUN")
    print()

    if current_version == new_version and not args.dry_run:
        print("Version is already up to date.")
        sys.exit(0)

    update_version_file(app_root, new_version, args.dry_run)
    update_init_py(app_root, app_name, new_version, args.dry_run)
    update_setup_py(app_root, new_version, args.dry_run)
    update_package_json(app_root, new_version, args.dry_run)
    update_readme_badge(app_root, new_version, args.dry_run)

    print()
    if args.dry_run:
        print("Dry run complete. No files were modified.")
    else:
        print(f"Done! All files bumped to {new_version}.")
        print("Don't forget to commit the changes.")


if __name__ == "__main__":
    main()
