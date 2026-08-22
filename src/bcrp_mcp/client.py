import asyncio
import logging
import urllib.parse
from typing import Any

import httpx

from .cache import CacheBackend, MemoryCache, cache_key
from .config import BCRPSettings
from .exceptions import (
    BCRPAPIError,
    BCRPNetworkError,
    BCRPNotFoundError,
    BCRPRateLimitError,
)
from .periods import cache_ttl_for_codes, frequency_for_codes, normalize_request_period

logger = logging.getLogger(__name__)

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
USER_AGENT = "bcrp-mcp/0.1.0 (https://github.com/JOSETRA44/bcrp-mcp)"


class BCRPClient:
    """Async BCRP API client with a pluggable cache and retry logic.

    BCRPData is a public API — no authentication required.

    The cache backend is injected: the MCP server keeps the default in-memory
    cache, while the CLI hands in a disk cache so a repeated query is instant
    across process boundaries.
    """

    def __init__(
        self,
        settings: BCRPSettings,
        cache: CacheBackend | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._cache: CacheBackend = cache if cache is not None else MemoryCache()
        self._http: httpx.AsyncClient | None = http_client
        self._owns_http = http_client is None
        self.cache_hits = 0
        self.cache_misses = 0
        # Set by the CLI's --refresh: every fetch bypasses the cache read.
        self.refresh = False

    async def __aenter__(self) -> "BCRPClient":
        if self._http is None:
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
        if self._http and self._owns_http:
            await self._http.aclose()
            self._http = None

    @property
    def all_cached(self) -> bool:
        """True when every fetch this client served came from the cache."""
        return self.cache_misses == 0 and self.cache_hits > 0

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

        Daily periods are rewritten from the documented ``DD-MM-YYYY`` to the
        ``YYYY-M-D`` the API actually honours — see ``periods.py``.
        """
        codes_str = "-".join(c.strip().upper() for c in series_codes)
        parts = [BASE_URL, codes_str, "json"]

        frequency = frequency_for_codes(series_codes)
        start_period = normalize_request_period(start_period, frequency)
        end_period = normalize_request_period(end_period, frequency)

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
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Fetch series data from the BCRP API.

        ``refresh=True`` ignores any cached copy and rewrites the entry, which
        is what the CLI's ``--refresh`` flag maps to.
        """
        assert self._http is not None, "BCRPClient must be used as async context manager"

        lang = language or self._settings.language
        url = self.build_url(series_codes, start_period, end_period, lang)

        key = cache_key(url)
        if not (refresh or self.refresh):
            cached = self._cache.get(key)
            if cached is not None:
                self.cache_hits += 1
                logger.debug("Cache hit: %s", url)
                return cached
        self.cache_misses += 1

        data = await self._request(url, series_codes)
        self._cache.set(key, data, cache_ttl_for_codes(series_codes, self._settings.cache_ttl))
        return data

    async def _request(self, url: str, series_codes: list[str]) -> dict[str, Any]:
        """One GET with retry/backoff, translated into domain exceptions."""
        assert self._http is not None
        last_error: Exception | None = None

        for attempt in range(self._settings.max_retries + 1):
            try:
                response = await self._http.get(url)
            except httpx.TimeoutException as exc:
                raise BCRPNetworkError(f"Request timed out after {self._settings.timeout}s") from exc
            except httpx.TransportError as exc:
                raise BCRPNetworkError(f"Could not connect to BCRP API: {exc}") from exc

            if response.status_code == 200:
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
                return data

            if response.status_code in (503, 429, 500):
                wait = 2 ** (attempt + 1)
                logger.warning("BCRP API error %d; retrying in %ds", response.status_code, wait)
                last_error = self._status_error(response.status_code, response.text)
                if attempt < self._settings.max_retries:
                    await asyncio.sleep(wait)
                    continue

            raise self._status_error(response.status_code, response.text)

        raise last_error or BCRPAPIError("Request failed after retries")

    @staticmethod
    def _status_error(status_code: int, body: str) -> BCRPAPIError:
        if status_code == 429:
            return BCRPRateLimitError("BCRP API rate limit reached (HTTP 429)", status_code)
        if status_code == 404:
            return BCRPNotFoundError(f"BCRP API returned 404: {body[:200]}", status_code)
        if status_code in (503, 500, 502, 504):
            return BCRPNetworkError(f"BCRP API unavailable (HTTP {status_code})", status_code)
        return BCRPAPIError(f"BCRP API error {status_code}: {body[:200]}", status_code=status_code)
