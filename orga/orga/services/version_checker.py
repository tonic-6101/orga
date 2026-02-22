# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Version update checker service.

Checks the GitHub releases API for newer versions and caches results in Redis.
"""

import json
import urllib.request
import urllib.error

import frappe

GITHUB_API_URL = "https://api.github.com/repos/tonic-6101/orga/releases/latest"
CACHE_KEY = "orga_latest_release_info"
CACHE_TTL = 86400  # 24 hours
REQUEST_TIMEOUT = 10  # seconds


def _parse_semver(version_str: str) -> tuple[int, ...]:
    """Parse 'v0.13.0' or '0.13.0' into a comparable tuple (0, 13, 0)."""
    cleaned = version_str.lstrip("v").strip()
    try:
        parts = [int(p) for p in cleaned.split(".")[:3]]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _get_current_version() -> str:
    """Read the installed version from orga.__version__."""
    import orga
    return getattr(orga, "__version__", "0.0.0")


def _fetch_latest_release() -> dict | None:
    """Fetch latest release from GitHub API. Returns parsed dict or None on failure."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Orga-Update-Checker",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError) as e:
        frappe.logger("orga").debug(f"Version check failed: {e}")
        return None


def _build_result(release_data: dict | None, current: str) -> dict | None:
    """Build a result dict from GitHub release data and current version."""
    if not release_data:
        return None

    tag = release_data.get("tag_name", "v0.0.0")
    latest = tag.lstrip("v")

    from frappe.utils import now_datetime

    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": _parse_semver(latest) > _parse_semver(current),
        "release_url": release_data.get("html_url", ""),
        "release_notes": (release_data.get("body") or "")[:2000],
        "published_at": release_data.get("published_at", ""),
        "checked_at": str(now_datetime()),
    }


def _get_cached() -> dict | None:
    """Read cached result from Redis, refreshing current_version."""
    cached = frappe.cache.get_value(CACHE_KEY)
    if not cached:
        return None

    result = json.loads(cached) if isinstance(cached, str) else cached
    current = _get_current_version()
    result["current_version"] = current
    result["update_available"] = (
        _parse_semver(result.get("latest_version", "0.0.0"))
        > _parse_semver(current)
    )
    return result


def check_for_updates(force: bool = False) -> dict | None:
    """
    Check for updates. Uses Redis cache unless force=True.

    Returns dict with: current_version, latest_version, update_available,
    release_url, release_notes, published_at, checked_at.
    Returns None if check fails and no cached data exists.
    """
    if not force:
        cached = _get_cached()
        if cached:
            return cached

    current = _get_current_version()
    release_data = _fetch_latest_release()
    result = _build_result(release_data, current)

    if result:
        frappe.cache.set_value(CACHE_KEY, json.dumps(result), expires_in_sec=CACHE_TTL)
        return result

    # Fetch failed — return stale cache if available
    return _get_cached()
