"""Domain exceptions, plus the error-code / exit-code mapping they drive.

Every exception carries two extra pieces of metadata the CLI needs and the
MCP server is free to ignore: ``code`` (the machine-readable label that goes
into the JSON error envelope) and ``hint`` (what the caller should do next).
"""

from __future__ import annotations

# error code -> process exit status
EXIT_CODES: dict[str, int] = {
    "ok": 0,
    "api": 1,
    "usage": 2,
    "not_found": 3,
    "auth": 4,
    "rate_limit": 5,
    "network": 6,
}

EXIT_CODE_MEANINGS: dict[str, str] = {
    "0": "success (including an empty result set)",
    "1": "API returned an error or an unexpected response",
    "2": "usage error (bad flag, bad argument, unknown format)",
    "3": "resource not found (unknown series code)",
    "4": "auth or configuration error",
    "5": "rate limited or quota exhausted",
    "6": "network failure or timeout",
}


class BCRPError(Exception):
    """Base exception for all BCRP MCP errors."""

    code = "api"
    hint = "Retry the request; if it keeps failing, check https://estadisticas.bcrp.gob.pe"

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        if hint:
            self.hint = hint


class BCRPConfigError(BCRPError):
    """Invalid or missing configuration."""

    code = "auth"
    hint = "Check your .env / BCRP_* environment variables."


class BCRPAPIError(BCRPError):
    """API returned an unexpected response."""

    code = "api"
    hint = "The BCRP API answered unexpectedly. Retry, or verify the request at https://estadisticas.bcrp.gob.pe"

    def __init__(self, message: str, status_code: int | None = None, hint: str | None = None) -> None:
        super().__init__(message, hint)
        self.status_code = status_code


class BCRPNotFoundError(BCRPAPIError):
    """Series code does not exist or returned no data."""

    code = "not_found"
    hint = "Verify the code with `bcrp series describe CODE`, or find one with `bcrp catalog search <term>`."


class BCRPRateLimitError(BCRPAPIError):
    """BCRP throttled the request."""

    code = "rate_limit"
    hint = "Wait a minute and retry; reduce concurrency with --concurrency."


class BCRPNetworkError(BCRPAPIError):
    """Connection failure or timeout reaching the BCRP API."""

    code = "network"
    hint = "Check connectivity to estadisticas.bcrp.gob.pe, or raise BCRP_TIMEOUT."


class BCRPFrequencyError(BCRPError):
    """Series codes have mismatched frequencies."""

    code = "usage"
    hint = "Split the codes into one call per frequency, or use `bcrp series export` which handles mixed frequencies."


class BCRPPeriodError(BCRPError):
    """Period format is invalid or out of range."""

    code = "usage"
    hint = "Daily: DD-MM-YYYY · Monthly/Quarterly: YYYY-M · Annual: YYYY."


class BCRPValidationError(BCRPError):
    """Invalid input parameters (e.g. too many series codes, bad flag combination)."""

    code = "usage"
    hint = "Run `bcrp <command> --help`, or `bcrp describe --json` for the full manifest."


def error_code_for(exc: BaseException) -> str:
    """Machine-readable error code for ``exc`` (spec section 1)."""
    return getattr(exc, "code", "internal")


def exit_code_for(exc: BaseException) -> int:
    """Process exit status for ``exc`` (spec section 2)."""
    return EXIT_CODES.get(error_code_for(exc), 1)
