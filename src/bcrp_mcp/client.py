import asyncio
import hashlib
import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from .config import BCRPSettings
from .exceptions import BCRPAPIError, BCRPNotFoundError

logger = logging.getLogger(__name__)

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
USER_AGENT = "bcrp-mcp/0.1.0 (https://github.com/JOSETRA44/bcrp-mcp)"


@dataclass
class _CacheEntry:
    data: dict[str, Any]
    expires_at: datetime


class _TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if datetime.now() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.data

    def set(self, key: str, data: dict[str, Any]) -> None:
        if self._ttl > 0:
            self._store[key] = _CacheEntry(
                data=data,
                expires_at=datetime.now() + timedelta(seconds=self._ttl),
            )

    def clear_expired(self) -> None:
        now = datetime.now()
        expired = [k for k, e in self._store.items() if now >= e.expires_at]
        for k in expired:
            del self._store[k]


class BCRPClient:
    """Async BCRP API client with TTL cache and retry logic.

    BCRPData is a public API — no authentication required.
    """

    def __init__(self, settings: BCRPSettings) -> None:
        self._settings = settings
        self._cache = _TTLCache(settings.cache_ttl)
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BCRPClient":
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    @staticmethod
    def _cache_key(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def build_url(
        self,
        series_codes: list[str],
        start_period: str | None = None,
        end_period: str | None = None,
        language: str = "esp",
    ) -> str:
        """Build the BCRP API URL.

        URL structure: /api/{codes}/json[/{start}/{end}/{lang}]
        - Only {codes} is required.
        - Language MUST come after BOTH start and end periods.
        - If no periods, language cannot be specified (omit it).
        """
        codes_str = "-".join(c.strip().upper() for c in series_codes)
        parts = [BASE_URL, codes_str, "json"]

        if start_period and end_period:
            parts.append(urllib.parse.quote(start_period, safe="-./"))
            parts.append(urllib.parse.quote(end_period, safe="-./"))
            parts.append(language)
        elif start_period:
            # Single period — language cannot follow without end period
            parts.append(urllib.parse.quote(start_period, safe="-./"))

        return "/".join(parts)

    async def fetch(
        self,
        series_codes: list[str],
        start_period: str | None = None,
        end_period: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Fetch series data from the BCRP API."""
        assert self._http is not None, "BCRPClient must be used as async context manager"

        lang = language or self._settings.language
        url = self.build_url(series_codes, start_period, end_period, lang)

        key = self._cache_key(url)
        cached = self._cache.get(key)
        if cached is not None:
            logger.debug("Cache hit: %s", url)
            return cached

        last_error: Exception | None = None
        for attempt in range(self._settings.max_retries + 1):
            try:
                response = await self._http.get(url)
            except httpx.TimeoutException as exc:
                raise BCRPAPIError(f"Request timed out after {self._settings.timeout}s") from exc
            except httpx.ConnectError as exc:
                raise BCRPAPIError(f"Could not connect to BCRP API: {exc}") from exc

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                text = response.text.strip()

                # BCRP returns HTML for invalid/empty series — detect this
                if text.startswith("<!DOCTYPE") or text.startswith("<html"):
                    raise BCRPNotFoundError(
                        f"Series not found or returned no data: {', '.join(series_codes)}. "
                        "Verify the series codes exist at https://estadisticas.bcrp.gob.pe"
                    )

                try:
                    data: dict[str, Any] = response.json()
                except Exception as exc:
                    raise BCRPAPIError(f"Unexpected response format from BCRP API: {text[:100]}") from exc

                self._cache.set(key, data)
                return data

            if response.status_code in (503, 429, 500):
                wait = 2 ** (attempt + 1)
                logger.warning("BCRP API error %d; retrying in %ds", response.status_code, wait)
                last_error = BCRPAPIError(f"BCRP API returned {response.status_code}", response.status_code)
                if attempt < self._settings.max_retries:
                    await asyncio.sleep(wait)
                    continue

            raise BCRPAPIError(
                f"BCRP API error {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )

        raise last_error or BCRPAPIError("Request failed after retries")
