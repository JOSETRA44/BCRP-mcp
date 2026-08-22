"""Exception → error-code → exit-status mapping (spec section 2).

One test per documented exit code, plus the HTTP statuses that produce them.
No network: every response comes from ``httpx.MockTransport``.
"""

from __future__ import annotations

import argparse

import httpx
import pytest

from bcrp_mcp.cli import app as cli_app
from bcrp_mcp.cli.output import Options
from bcrp_mcp.exceptions import (
    EXIT_CODE_MEANINGS,
    EXIT_CODES,
    BCRPAPIError,
    BCRPConfigError,
    BCRPError,
    BCRPFrequencyError,
    BCRPNetworkError,
    BCRPNotFoundError,
    BCRPPeriodError,
    BCRPRateLimitError,
    BCRPValidationError,
    error_code_for,
    exit_code_for,
)

from .conftest import make_payload, payload_handler


class TestExitCodeTable:
    def test_success_is_exit_zero(self):
        assert EXIT_CODES["ok"] == 0

    def test_api_error_is_exit_one(self):
        assert exit_code_for(BCRPAPIError("boom")) == 1

    @pytest.mark.parametrize(
        "exc",
        [BCRPValidationError("bad flag"), BCRPFrequencyError("mixed"), BCRPPeriodError("bad period")],
    )
    def test_usage_errors_are_exit_two(self, exc):
        assert error_code_for(exc) == "usage"
        assert exit_code_for(exc) == 2

    def test_not_found_is_exit_three(self):
        exc = BCRPNotFoundError("no such series")
        assert error_code_for(exc) == "not_found"
        assert exit_code_for(exc) == 3

    def test_config_error_is_exit_four(self):
        exc = BCRPConfigError("missing setting")
        assert error_code_for(exc) == "auth"
        assert exit_code_for(exc) == 4

    def test_rate_limit_is_exit_five(self):
        exc = BCRPRateLimitError("slow down")
        assert error_code_for(exc) == "rate_limit"
        assert exit_code_for(exc) == 5

    def test_network_failure_is_exit_six(self):
        exc = BCRPNetworkError("timed out")
        assert error_code_for(exc) == "network"
        assert exit_code_for(exc) == 6

    def test_api_error_maps_to_api_not_auth(self):
        # Regression guard: this mapping was previously wrong, sending every
        # ordinary API failure out as exit 4 ("check your API key") for an API
        # that has no key at all. An agent retrying on 4 would loop forever.
        exc = BCRPAPIError("BCRP API error 500")
        assert error_code_for(exc) == "api"
        assert exit_code_for(exc) == 1
        assert exit_code_for(exc) != EXIT_CODES["auth"]

    def test_not_found_subclasses_api_error_but_keeps_its_own_code(self):
        # BCRPNotFoundError inherits from BCRPAPIError; if the mapping were
        # done with isinstance checks in the wrong order it would degrade to 1.
        assert isinstance(BCRPNotFoundError("x"), BCRPAPIError)
        assert exit_code_for(BCRPNotFoundError("x")) == 3

    def test_base_error_defaults_to_the_api_code(self):
        assert exit_code_for(BCRPError("something")) == 1

    def test_a_non_domain_exception_is_internal_and_still_exits_nonzero(self):
        exc = ValueError("unexpected")
        assert error_code_for(exc) == "internal"
        # "internal" has no row in the table, so the generic failure code wins.
        assert exit_code_for(exc) == 1

    def test_every_documented_exit_code_is_reachable_from_the_code_table(self):
        assert sorted(EXIT_CODES.values()) == sorted(int(c) for c in EXIT_CODE_MEANINGS)

    def test_all_seven_exit_codes_are_documented(self):
        assert set(EXIT_CODE_MEANINGS) == {"0", "1", "2", "3", "4", "5", "6"}


class TestEveryDomainErrorCarriesAHint:
    @pytest.mark.parametrize(
        "exc",
        [
            BCRPError("x"),
            BCRPConfigError("x"),
            BCRPAPIError("x"),
            BCRPNotFoundError("x"),
            BCRPRateLimitError("x"),
            BCRPNetworkError("x"),
            BCRPFrequencyError("x"),
            BCRPPeriodError("x"),
            BCRPValidationError("x"),
        ],
    )
    def test_hint_is_present_and_actionable(self, exc):
        # Spec section 1: "Every error carries a hint telling the caller what
        # to do next" — an empty hint is as useless as no hint.
        assert exc.hint
        assert len(exc.hint) > 10

    def test_a_caller_supplied_hint_overrides_the_class_default(self):
        exc = BCRPAPIError("x", hint="Do the other thing.")
        assert exc.hint == "Do the other thing."


class TestHttpStatusToExitCode:
    """The client translates HTTP failures into the domain exceptions that
    drive the exit codes, so this is where 404 → 3 is actually decided."""

    @pytest.mark.parametrize(
        "status,expected_exit",
        [
            (404, 3),
            (429, 5),
            (500, 6),
            (502, 6),
            (503, 6),
            (504, 6),
            (418, 1),
            (400, 1),
        ],
    )
    async def test_status_maps_to_exit_code(self, make_client, status, expected_exit):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status, text="upstream said no")

        client = make_client(handler)
        with pytest.raises(BCRPError) as excinfo:
            await client.fetch(["PD04637PD"])
        assert exit_code_for(excinfo.value) == expected_exit

    async def test_an_html_body_means_the_series_does_not_exist(self, make_client):
        # BCRP answers an unknown code with its 200-OK HTML error page rather
        # than a 404, so the body has to be sniffed.
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<!DOCTYPE html><html>error</html>")

        client = make_client(handler)
        with pytest.raises(BCRPNotFoundError) as excinfo:
            await client.fetch(["NOSUCHXX"])
        assert exit_code_for(excinfo.value) == 3

    async def test_a_non_json_body_is_an_api_error(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="not json at all")

        client = make_client(handler)
        with pytest.raises(BCRPAPIError) as excinfo:
            await client.fetch(["PD04637PD"])
        assert exit_code_for(excinfo.value) == 1

    async def test_a_timeout_is_a_network_error(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("too slow", request=request)

        client = make_client(handler)
        with pytest.raises(BCRPNetworkError) as excinfo:
            await client.fetch(["PD04637PD"])
        assert exit_code_for(excinfo.value) == 6

    async def test_a_connection_failure_is_a_network_error(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("no route to host", request=request)

        client = make_client(handler)
        with pytest.raises(BCRPNetworkError) as excinfo:
            await client.fetch(["PD04637PD"])
        assert exit_code_for(excinfo.value) == 6


class TestCliDispatcherExitCodes:
    """`_run_data_command` is the single place the CLI turns a failure into a
    process status, so it gets its own end-to-end (still offline) checks."""

    def _args(self, func, needs_client=False, **extra):
        return argparse.Namespace(
            command="catalog", action="search", func=func, needs_client=needs_client, **extra
        )

    async def test_a_successful_command_exits_zero(self, capsys):
        args = argparse.Namespace(
            command="catalog",
            action="search",
            func=None,
            needs_client=False,
            query="tipo de cambio",
            category=None,
            frequency=None,
        )
        from bcrp_mcp.cli import commands

        args.func = commands.cmd_catalog_search
        code = await cli_app._run_data_command(args, Options(fmt="json"))
        assert code == 0

    async def test_an_empty_result_set_is_still_a_success(self, capsys):
        import json

        from bcrp_mcp.cli import commands

        args = argparse.Namespace(
            command="catalog",
            action="search",
            func=commands.cmd_catalog_search,
            needs_client=False,
            query="zzzzz-no-such-series",
            category=None,
            frequency=None,
        )
        code = await cli_app._run_data_command(args, Options(fmt="json"))
        assert code == 0
        envelope = json.loads(capsys.readouterr().out)
        assert envelope["ok"] is True
        assert envelope["count"] == 0
        assert envelope["rows"] == []

    @pytest.mark.parametrize(
        "exc,expected",
        [
            (BCRPAPIError("boom"), 1),
            (BCRPValidationError("boom"), 2),
            (BCRPNotFoundError("boom"), 3),
            (BCRPConfigError("boom"), 4),
            (BCRPRateLimitError("boom"), 5),
            (BCRPNetworkError("boom"), 6),
        ],
    )
    async def test_a_failing_command_exits_with_its_mapped_code(self, capsys, exc, expected):
        async def failing(client, args):
            raise exc

        code = await cli_app._run_data_command(self._args(failing), Options(fmt="json"))
        assert code == expected
        assert f'"code": "{error_code_for(exc)}"' in capsys.readouterr().out

    async def test_an_unknown_describe_target_is_a_usage_error(self, capsys):
        parser = cli_app.build_parser()
        args = parser.parse_args(["describe", "no-such-command", "--json"])
        assert cli_app._run_describe(parser, args) == 2

    async def test_describe_exits_zero(self, capsys):
        parser = cli_app.build_parser()
        args = parser.parse_args(["describe", "--json"])
        assert cli_app._run_describe(parser, args) == 0

    def test_an_unknown_format_is_rejected_by_the_parser_as_a_usage_error(self):
        parser = cli_app.build_parser()
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["catalog", "categories", "-f", "yaml"])
        assert excinfo.value.code == 2


class TestRetriesBeforeGivingUp:
    async def test_a_transient_503_is_retried_then_succeeds(self, make_client, monkeypatch):
        # Retry backoff is real sleeping; stub it so the test stays fast.
        import asyncio

        async def no_sleep(_seconds):
            return None

        monkeypatch.setattr(asyncio, "sleep", no_sleep)

        attempts: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            attempts.append(1)
            if len(attempts) == 1:
                return httpx.Response(503, text="unavailable")
            return httpx.Response(200, json=make_payload([("Ene.2024", ["1.0"])]))

        client = make_client(handler, max_retries=2)
        result = await client.fetch(["PN00196MM"])
        assert len(attempts) == 2
        assert result["periods"][0]["name"] == "Ene.2024"

    async def test_a_persistent_503_gives_up_with_the_network_exit_code(
        self, make_client, monkeypatch
    ):
        import asyncio

        async def no_sleep(_seconds):
            return None

        monkeypatch.setattr(asyncio, "sleep", no_sleep)
        calls: list[str] = []
        client = make_client(payload_handler(status=503, calls=calls), max_retries=2)

        with pytest.raises(BCRPNetworkError) as excinfo:
            await client.fetch(["PN00196MM"])
        assert exit_code_for(excinfo.value) == 6
        assert len(calls) == 3  # initial attempt + 2 retries
