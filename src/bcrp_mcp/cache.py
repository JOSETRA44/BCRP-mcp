"""Pluggable cache backends for BCRP responses.

The MCP server is a long-lived process, so an in-memory dict is ideal there.
The CLI is a fresh process on every invocation, so it needs a disk-backed
cache to make a repeated query instant across runs.

Both backends satisfy the same ``CacheBackend`` protocol, so ``BCRPClient``
neither knows nor cares which one it was handed.

BCRPData needs no API key, so nothing secret ever reaches the key material or
the cache file — but the key is still built only from the request identity
(base URL, method, path, sorted query params) so that stays true if that ever
changes.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from urllib.parse import parse_qsl, urlsplit

import platformdirs

APP_NAME = "bcrp-mcp"


def cache_key(url: str, method: str = "GET") -> str:
    """SHA-256 over ``(base_url, method, path, sorted query params)``.

    Query params are sorted so that two spellings of the same request share a
    cache entry, and credentials — should the API ever grow them — are never
    part of the key material.
    """
    parts = urlsplit(url)
    query = "&".join(f"{k}={v}" for k, v in sorted(parse_qsl(parts.query)))
    material = f"{method.upper()}|{parts.scheme}://{parts.netloc}|{parts.path}|{query}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def default_cache_dir() -> Path:
    """Per-user cache directory, resolved by platformdirs."""
    return Path(platformdirs.user_cache_dir(APP_NAME))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _iso_at(offset: float) -> str:
    stamp = datetime.fromtimestamp(time.time() + offset, tz=timezone.utc)
    return stamp.isoformat(timespec="seconds").replace("+00:00", "Z")


@runtime_checkable
class CacheBackend(Protocol):
    """Minimal contract every cache backend must satisfy."""

    def get(self, key: str) -> Any | None:
        """Return the cached body for ``key``, or ``None`` if missing/expired."""
        ...

    def set(self, key: str, value: Any, ttl: int, status: int = 200) -> None:
        """Store ``value`` for ``ttl`` seconds (a no-op when ``ttl <= 0``)."""
        ...


class NullCache:
    """Reads nothing, writes nothing — what ``--no-cache`` installs."""

    def get(self, key: str) -> Any | None:
        return None

    def set(self, key: str, value: Any, ttl: int, status: int = 200) -> None:
        return None


class MemoryCache:
    """In-process cache. Fast, ephemeral — used by the long-lived MCP server."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() >= entry["_expires"]:
            del self._store[key]
            return None
        return entry["body"]

    def set(self, key: str, value: Any, ttl: int, status: int = 200) -> None:
        if ttl <= 0 or not (200 <= status < 300):
            return
        self._store[key] = {
            "fetched_at": _now_iso(),
            "expires_at": _iso_at(ttl),
            "status": status,
            "body": value,
            "_expires": time.time() + ttl,
        }


class DiskCache:
    """Filesystem cache. Survives between processes — used by the CLI.

    Each entry is one small JSON file named after the SHA-256 of its key,
    holding ``{fetched_at, expires_at, status, body}`` plus an absolute expiry
    timestamp for cheap comparison. Only successful (2xx) responses are stored.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self.dir = Path(cache_dir) if cache_dir else default_cache_dir()
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        path = self._path(key)
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() >= entry.get("_expires", 0):
            # Expired — clean it up opportunistically.
            path.unlink(missing_ok=True)
            return None
        return entry.get("body")

    def set(self, key: str, value: Any, ttl: int, status: int = 200) -> None:
        if ttl <= 0 or not (200 <= status < 300):
            return
        entry = {
            "fetched_at": _now_iso(),
            "expires_at": _iso_at(ttl),
            "status": status,
            "body": value,
            "_expires": time.time() + ttl,
        }
        try:
            self._path(key).write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        except (OSError, TypeError):
            # Caching is best-effort; never let a cache write break a query.
            pass

    # --- `bcrp cache` support ---------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Entry counts and on-disk size, split live vs expired."""
        live = expired = 0
        size = 0
        oldest: str | None = None
        now = time.time()
        for path in self.dir.glob("*.json"):
            try:
                size += path.stat().st_size
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if now >= entry.get("_expires", 0):
                expired += 1
                continue
            live += 1
            fetched = entry.get("fetched_at")
            if fetched and (oldest is None or fetched < oldest):
                oldest = fetched
        return {
            "path": str(self.dir),
            "entries": live + expired,
            "live_entries": live,
            "expired_entries": expired,
            "size_bytes": size,
            "oldest_entry": oldest,
        }

    def clear(self) -> int:
        """Delete every entry; returns how many files were removed."""
        removed = 0
        for path in self.dir.glob("*.json"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        return removed


def build_cache(backend: str, cache_dir: str | Path | None = None) -> CacheBackend:
    """Factory: return the cache backend named by ``backend``."""
    if backend == "disk":
        return DiskCache(cache_dir)
    if backend == "none":
        return NullCache()
    return MemoryCache()
