"""Persistent-cache behaviour (spec section 3).

Every test writes into ``tmp_path``; the autouse ``isolated_cache_dir``
fixture in ``conftest.py`` additionally redirects the *default* cache
directory, so nothing here can reach the developer's real cache.
"""

from __future__ import annotations

import json
import time

import httpx
import pytest

from bcrp_mcp import cache as cache_module
from bcrp_mcp.cache import (
    DiskCache,
    MemoryCache,
    NullCache,
    build_cache,
    cache_key,
)
from bcrp_mcp.cli.app import build_parser
from bcrp_mcp.cli.output import Options
from bcrp_mcp.exceptions import BCRPNotFoundError
from bcrp_mcp.periods import CACHE_TTL_BY_FREQUENCY

from .conftest import make_payload, payload_handler


class RecordingCache:
    """A cache backend that remembers the TTL and status it was handed."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, int, int]] = []
        self._store: dict[str, object] = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value, ttl: int, status: int = 200) -> None:
        self.writes.append((key, ttl, status))
        self._store[key] = value


@pytest.fixture
def frozen_clock(monkeypatch):
    """Replace ``cache.time`` with a clock the test drives by hand.

    Expiry is the one cache behaviour that cannot be tested by waiting.
    """

    class Clock:
        def __init__(self) -> None:
            self.now = 1_000_000.0

        def time(self) -> float:
            return self.now

        def advance(self, seconds: float) -> None:
            self.now += seconds

    clock = Clock()
    monkeypatch.setattr(cache_module, "time", clock)
    return clock


class TestCacheKey:
    def test_the_same_request_produces_the_same_key(self):
        url = "https://example.test/api/PD04637PD/json"
        assert cache_key(url) == cache_key(url)

    def test_query_parameters_in_a_different_order_share_one_entry(self):
        a = cache_key("https://example.test/api?b=2&a=1")
        b = cache_key("https://example.test/api?a=1&b=2")
        assert a == b

    def test_a_different_path_produces_a_different_key(self):
        assert cache_key("https://example.test/a") != cache_key("https://example.test/b")

    def test_a_different_host_produces_a_different_key(self):
        assert cache_key("https://a.test/x") != cache_key("https://b.test/x")

    def test_the_http_method_is_part_of_the_key(self):
        url = "https://example.test/x"
        assert cache_key(url, "GET") != cache_key(url, "POST")

    def test_the_key_is_an_opaque_digest_that_leaks_no_request_material(self):
        # Spec section 3: nothing secret may end up in the key material. The
        # key being a bare sha256 hex digest is what guarantees that even if
        # the API grows credentials one day.
        key = cache_key("https://example.test/api/PD04637PD/json?token=s3cret")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)
        assert "s3cret" not in key
        assert "PD04637PD" not in key


class TestDiskCacheEntries:
    def test_a_miss_returns_none(self, tmp_path):
        assert DiskCache(tmp_path).get("nope") is None

    def test_a_write_then_read_returns_the_stored_body(self, tmp_path):
        cache = DiskCache(tmp_path)
        cache.set("k", {"hello": "Perú"}, ttl=60)
        assert cache.get("k") == {"hello": "Perú"}

    def test_the_entry_on_disk_has_the_shape_the_spec_names(self, tmp_path):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60)
        entry = json.loads((tmp_path / "k.json").read_text(encoding="utf-8"))
        assert set(entry) >= {"fetched_at", "expires_at", "status", "body"}
        assert entry["status"] == 200
        assert entry["body"] == {"a": 1}

    def test_the_cache_file_stores_no_url_or_key_material(self, tmp_path):
        cache = DiskCache(tmp_path)
        cache.set(cache_key("https://example.test/x?token=s3cret"), {"a": 1}, ttl=60)
        blob = (tmp_path / f"{cache_key('https://example.test/x?token=s3cret')}.json").read_text(
            encoding="utf-8"
        )
        assert "s3cret" not in blob
        assert "example.test" not in blob

    def test_an_expired_entry_reads_as_a_miss(self, tmp_path, frozen_clock):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60)
        frozen_clock.advance(61)
        assert cache.get("k") is None

    def test_an_expired_entry_is_deleted_on_read(self, tmp_path, frozen_clock):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60)
        frozen_clock.advance(61)
        cache.get("k")
        assert not (tmp_path / "k.json").exists()

    def test_an_entry_is_still_live_one_second_before_expiry(self, tmp_path, frozen_clock):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60)
        frozen_clock.advance(59)
        assert cache.get("k") == {"a": 1}

    @pytest.mark.parametrize("status", [200, 201, 204, 299])
    def test_successful_responses_are_cached(self, tmp_path, status):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60, status=status)
        assert cache.get("k") == {"a": 1}

    @pytest.mark.parametrize("status", [301, 400, 401, 404, 429, 500, 503])
    def test_non_2xx_responses_are_never_cached(self, tmp_path, status):
        # Spec section 3: "Only successful (2xx) responses are cached. Never
        # cache auth failures." A cached 401 would survive a fixed credential.
        cache = DiskCache(tmp_path)
        cache.set("k", {"error": "no"}, ttl=60, status=status)
        assert cache.get("k") is None
        assert list(tmp_path.glob("*.json")) == []

    def test_a_zero_ttl_disables_writing(self, tmp_path):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=0)
        assert cache.get("k") is None

    def test_a_corrupt_entry_reads_as_a_miss_instead_of_raising(self, tmp_path):
        cache = DiskCache(tmp_path)
        (tmp_path / "k.json").write_text("{not json", encoding="utf-8")
        assert cache.get("k") is None

    def test_an_unserialisable_body_does_not_break_the_query(self, tmp_path):
        # Caching is best-effort: a write failure must never surface as an
        # error to someone who only asked for data.
        cache = DiskCache(tmp_path)
        cache.set("k", {"bad": object()}, ttl=60)
        assert cache.get("k") is None

    def test_accented_bodies_survive_the_round_trip(self, tmp_path):
        cache = DiskCache(tmp_path)
        body = make_payload([("Ene.2024", ["3.75"])])
        cache.set("k", body, ttl=60)
        assert cache.get("k") == body


class TestDiskCacheAdmin:
    def test_stats_separate_live_from_expired_entries(self, tmp_path, frozen_clock):
        cache = DiskCache(tmp_path)
        cache.set("short", {"a": 1}, ttl=10)
        cache.set("long", {"a": 2}, ttl=1000)
        frozen_clock.advance(11)
        stats = cache.stats()
        assert stats["entries"] == 2
        assert stats["live_entries"] == 1
        assert stats["expired_entries"] == 1

    def test_stats_report_the_directory_and_a_nonzero_size(self, tmp_path):
        cache = DiskCache(tmp_path)
        cache.set("k", {"a": 1}, ttl=60)
        stats = cache.stats()
        assert stats["path"] == str(tmp_path)
        assert stats["size_bytes"] > 0

    def test_stats_on_an_empty_cache_report_zero(self, tmp_path):
        assert DiskCache(tmp_path).stats()["entries"] == 0

    def test_clear_removes_every_entry_and_reports_how_many(self, tmp_path):
        cache = DiskCache(tmp_path)
        for i in range(3):
            cache.set(f"k{i}", {"a": i}, ttl=60)
        assert cache.clear() == 3
        assert cache.stats()["entries"] == 0

    def test_the_default_directory_is_redirected_away_from_the_real_one(
        self, isolated_cache_dir
    ):
        # Proves the hermetic-cache fixture is actually in force; without it
        # every cache test here would pollute the developer's machine.
        # (looked up through the module so the monkeypatch is visible here)
        assert cache_module.default_cache_dir() == isolated_cache_dir
        assert DiskCache().dir == isolated_cache_dir


class TestMemoryAndNullBackends:
    def test_memory_cache_reads_back_what_it_stored(self):
        cache = MemoryCache()
        cache.set("k", {"a": 1}, ttl=60)
        assert cache.get("k") == {"a": 1}

    def test_memory_cache_expires_entries(self, frozen_clock):
        cache = MemoryCache()
        cache.set("k", {"a": 1}, ttl=60)
        frozen_clock.advance(61)
        assert cache.get("k") is None

    def test_memory_cache_ignores_non_2xx_responses(self):
        cache = MemoryCache()
        cache.set("k", {"a": 1}, ttl=60, status=500)
        assert cache.get("k") is None

    def test_null_cache_stores_nothing(self):
        cache = NullCache()
        cache.set("k", {"a": 1}, ttl=60)
        assert cache.get("k") is None

    @pytest.mark.parametrize(
        "name,expected",
        [("disk", DiskCache), ("none", NullCache), ("memory", MemoryCache), ("", MemoryCache)],
    )
    def test_the_factory_returns_the_named_backend(self, name, expected, tmp_path):
        assert isinstance(build_cache(name, tmp_path), expected)


class TestClientCacheIntegration:
    def _handler(self, calls):
        return payload_handler(make_payload([("Ene.2024", ["100.5"])]), calls=calls)

    async def test_a_first_fetch_is_a_miss_that_writes_the_cache(self, make_client, tmp_path):
        calls: list[str] = []
        cache = DiskCache(tmp_path)
        client = make_client(self._handler(calls), cache=cache)

        await client.fetch(["PN00196MM"])

        assert len(calls) == 1
        assert client.cache_misses == 1 and client.cache_hits == 0
        assert len(list(tmp_path.glob("*.json"))) == 1

    async def test_a_repeat_fetch_is_a_hit_that_makes_no_request(self, make_client, tmp_path):
        calls: list[str] = []
        cache = DiskCache(tmp_path)
        client = make_client(self._handler(calls), cache=cache)

        first = await client.fetch(["PN00196MM"])
        second = await client.fetch(["PN00196MM"])

        assert len(calls) == 1
        assert first == second
        assert client.cache_hits == 1

    async def test_a_second_process_reads_the_first_processs_entry(
        self, make_client, tmp_path
    ):
        # The whole point of a disk cache: a CLI exits after one call, so the
        # hit has to survive across client (and process) boundaries.
        calls: list[str] = []
        writer = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await writer.fetch(["PN00196MM"])

        reader = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await reader.fetch(["PN00196MM"])

        assert len(calls) == 1
        assert reader.cache_hits == 1

    async def test_an_expired_entry_triggers_a_refetch(
        self, make_client, tmp_path, frozen_clock
    ):
        calls: list[str] = []
        cache = DiskCache(tmp_path)
        client = make_client(self._handler(calls), cache=cache)

        await client.fetch(["PN00196MM"])
        frozen_clock.advance(CACHE_TTL_BY_FREQUENCY["monthly"] + 1)
        await client.fetch(["PN00196MM"])

        assert len(calls) == 2

    async def test_refresh_bypasses_the_cache_and_rewrites_the_entry(
        self, make_client, tmp_path
    ):
        bodies = [
            make_payload([("Ene.2024", ["1.0"])]),
            make_payload([("Ene.2024", ["2.0"])]),
        ]
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return httpx.Response(200, json=bodies[min(len(calls) - 1, 1)])

        cache = DiskCache(tmp_path)
        client = make_client(handler, cache=cache)

        await client.fetch(["PN00196MM"])
        client.refresh = True  # what the CLI's --refresh sets
        refreshed = await client.fetch(["PN00196MM"])

        assert len(calls) == 2
        assert refreshed["periods"][0]["values"] == ["2.0"]
        # The refetched body replaced the stale entry rather than being dropped.
        client.refresh = False
        assert (await client.fetch(["PN00196MM"]))["periods"][0]["values"] == ["2.0"]

    async def test_the_per_call_refresh_argument_also_bypasses_the_cache(
        self, make_client, tmp_path
    ):
        calls: list[str] = []
        client = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await client.fetch(["PN00196MM"])
        await client.fetch(["PN00196MM"], refresh=True)
        assert len(calls) == 2

    async def test_no_cache_neither_reads_nor_writes(self, make_client, tmp_path):
        calls: list[str] = []
        client = make_client(self._handler(calls), cache=NullCache())

        await client.fetch(["PN00196MM"])
        await client.fetch(["PN00196MM"])

        assert len(calls) == 2
        assert list(tmp_path.glob("*.json")) == []

    async def test_a_failed_request_leaves_the_cache_empty(self, make_client, tmp_path):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="nope")

        cache = DiskCache(tmp_path)
        client = make_client(handler, cache=cache)
        with pytest.raises(BCRPNotFoundError):
            await client.fetch(["NOSUCHXX"])

        assert list(tmp_path.glob("*.json")) == []

    async def test_different_date_ranges_do_not_share_a_cache_entry(
        self, make_client, tmp_path
    ):
        calls: list[str] = []
        client = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await client.fetch(["PN00196MM"], "2020-1", "2020-12")
        await client.fetch(["PN00196MM"], "2021-1", "2021-12")
        assert len(calls) == 2

    async def test_all_cached_is_false_when_anything_was_fetched(self, make_client, tmp_path):
        calls: list[str] = []
        client = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await client.fetch(["PN00196MM"])
        assert client.all_cached is False
        await client.fetch(["PN00196MM"])
        assert client.all_cached is False  # the first call was a real fetch

    async def test_all_cached_is_true_when_every_call_was_served_from_disk(
        self, make_client, tmp_path
    ):
        calls: list[str] = []
        make_first = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await make_first.fetch(["PN00196MM"])

        second = make_client(self._handler(calls), cache=DiskCache(tmp_path))
        await second.fetch(["PN00196MM"])
        assert second.all_cached is True


class TestPerFrequencyTTL:
    """A daily series and a monthly one must not share one lifetime."""

    async def _ttl_for(self, make_client, code: str, **settings):
        recorder = RecordingCache()
        client = make_client(payload_handler(make_payload([("Ene.2024", ["1.0"])])), cache=recorder, **settings)
        await client.fetch([code])
        return recorder.writes[0][1]

    async def test_a_daily_series_is_cached_with_the_daily_ttl(self, make_client):
        assert await self._ttl_for(make_client, "PD04637PD") == CACHE_TTL_BY_FREQUENCY["daily"]

    async def test_a_monthly_series_is_cached_with_the_monthly_ttl(self, make_client):
        assert await self._ttl_for(make_client, "PN00196MM") == CACHE_TTL_BY_FREQUENCY["monthly"]

    async def test_a_quarterly_series_is_cached_with_the_quarterly_ttl(self, make_client):
        assert await self._ttl_for(make_client, "PN03503MQ") == CACHE_TTL_BY_FREQUENCY["quarterly"]

    async def test_daily_and_monthly_ttls_actually_differ_at_the_client(self, make_client):
        daily = await self._ttl_for(make_client, "PD04637PD")
        monthly = await self._ttl_for(make_client, "PN00196MM")
        assert daily != monthly

    async def test_an_unknown_frequency_falls_back_to_the_configured_default(self, make_client):
        assert await self._ttl_for(make_client, "ZZZZZZZZ", cache_ttl=123) == 123


class TestCacheFlagPlumbing:
    """`--refresh` / `--no-cache` have to survive the trip from argv to the
    resolved `Options` and on to the backend the client is handed."""

    def test_refresh_flag_reaches_the_options(self):
        args = build_parser().parse_args(["series", "latest", "PD04637PD", "--refresh"])
        assert cli_options(args).refresh is True

    def test_no_cache_flag_reaches_the_options(self):
        args = build_parser().parse_args(["series", "latest", "PD04637PD", "--no-cache"])
        assert cli_options(args).no_cache is True

    def test_neither_flag_is_set_by_default(self):
        args = build_parser().parse_args(["series", "latest", "PD04637PD"])
        opts = cli_options(args)
        assert opts.refresh is False and opts.no_cache is False

    async def test_no_cache_never_constructs_the_disk_cache(self, monkeypatch):
        import argparse as _argparse

        from bcrp_mcp.cli import app as cli_app
        from bcrp_mcp.cli.output import CommandResult

        constructed: list[object] = []
        monkeypatch.setattr(
            cli_app, "DiskCache", lambda *a, **k: constructed.append(a) or DiskCache(*a, **k)
        )

        seen: dict[str, object] = {}

        async def fake_command(client, args):
            seen["cache"] = client._cache
            return CommandResult(data={}, rows=[])

        args = _argparse.Namespace(
            command="series", action="latest", func=fake_command, needs_client=True
        )
        code = await cli_app._run_data_command(args, Options(fmt="json", no_cache=True))

        assert code == 0
        assert constructed == []
        assert isinstance(seen["cache"], MemoryCache)

    async def test_the_default_run_installs_the_disk_cache(self, monkeypatch):
        import argparse as _argparse

        from bcrp_mcp.cli import app as cli_app
        from bcrp_mcp.cli.output import CommandResult

        seen: dict[str, object] = {}

        async def fake_command(client, args):
            seen["cache"] = client._cache
            seen["refresh"] = client.refresh
            return CommandResult(data={}, rows=[])

        args = _argparse.Namespace(
            command="series", action="latest", func=fake_command, needs_client=True
        )
        await cli_app._run_data_command(args, Options(fmt="json", refresh=True))

        assert isinstance(seen["cache"], DiskCache)
        assert seen["refresh"] is True


def cli_options(args):
    from bcrp_mcp.cli.app import _options_from

    return _options_from(args)
