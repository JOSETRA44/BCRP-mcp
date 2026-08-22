"""Shared fixtures for the BCRP test suite.

Everything here is hermetic: no socket is ever opened (every HTTP call goes
through ``httpx.MockTransport``) and no test may touch the developer's real
cache directory (see the autouse ``isolated_cache_dir`` fixture).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

import httpx
import pytest

from bcrp_mcp import cache as cache_module
from bcrp_mcp.client import BCRPClient
from bcrp_mcp.config import BCRPSettings

# Accented Spanish text is the whole point of spec section 9 — reuse the same
# strings everywhere so a regression shows up in every format's tests at once.
ACCENTED_TITLE = "Tipo de cambio · Perú"
ACCENTED_SERIES_NAME = "Tipo de cambio - promedio (S/ por US$)"


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the default cache directory at ``tmp_path`` for every test.

    ``DiskCache()`` with no argument resolves through ``default_cache_dir()``.
    Any test (or production code path a test reaches) that forgets to pass an
    explicit directory would otherwise read and write the user's real cache,
    which would make the suite both non-hermetic and destructive.
    """
    sandbox = tmp_path / "cache-sandbox"
    monkeypatch.setattr(cache_module, "default_cache_dir", lambda: sandbox)
    return sandbox


# --- BCRP API payload builders ---------------------------------------------


def make_payload(
    periods: Iterable[tuple[str, list[str]]] = (),
    series: Iterable[tuple[str, int]] = ((ACCENTED_SERIES_NAME, 3),),
    title: str = ACCENTED_TITLE,
) -> dict[str, Any]:
    """Build a raw BCRP API body.

    Shape mirrors the live API exactly: ``config.series[i]`` describes
    ``periods[p].values[i]``, and every value arrives as a *string* (with
    ``"n.d."`` standing in for a missing observation).
    """
    return {
        "config": {
            "title": title,
            "series": [{"name": name, "dec": str(dec)} for name, dec in series],
        },
        "periods": [{"name": name, "values": list(values)} for name, values in periods],
    }


def codes_from_url(url: httpx.URL | str) -> list[str]:
    """Recover the requested series codes from a BCRP URL.

    The API addresses series positionally in the path
    (``/api/{CODE-CODE}/json/...``), so a mock handler that wants to answer
    per-code has to parse them back out.
    """
    parts = [p for p in str(httpx.URL(url).path).split("/") if p]
    try:
        codes_segment = parts[parts.index("json") - 1]
    except ValueError:
        codes_segment = parts[-1]
    return codes_segment.split("-")


def payload_handler(
    body: dict[str, Any] | None = None,
    *,
    per_code: dict[str, dict[str, Any]] | None = None,
    status: int = 200,
    calls: list[str] | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """A ``MockTransport`` handler returning canned BCRP JSON.

    ``per_code`` lets one handler serve a different body per series code, which
    is what the long-format export needs (it fetches one code per request).
    ``calls``, when given, records every URL for request-count assertions.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if per_code is not None:
            code = codes_from_url(request.url)[0].upper()
            if code not in per_code:
                return httpx.Response(404, text=f"unknown series {code}")
            return httpx.Response(status, json=per_code[code])
        return httpx.Response(status, json=body if body is not None else make_payload())

    return handler


@pytest.fixture
async def make_client():
    """Factory for a ``BCRPClient`` wired to a ``MockTransport`` handler.

    Retries default to 0 so a test asserting on a 5xx does not pay the client's
    exponential backoff.
    """
    opened: list[httpx.AsyncClient] = []

    def _make(handler, cache=None, **settings_kwargs: Any) -> BCRPClient:
        settings_kwargs.setdefault("max_retries", 0)
        http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        opened.append(http)
        return BCRPClient(BCRPSettings(**settings_kwargs), cache=cache, http_client=http)

    yield _make

    for http in opened:
        await http.aclose()
