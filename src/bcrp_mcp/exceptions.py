class BCRPError(Exception):
    """Base exception for all BCRP MCP errors."""


class BCRPConfigError(BCRPError):
    """Invalid or missing configuration."""


class BCRPAPIError(BCRPError):
    """API returned an unexpected response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BCRPNotFoundError(BCRPAPIError):
    """Series code does not exist or returned no data."""


class BCRPFrequencyError(BCRPError):
    """Series codes have mismatched frequencies."""


class BCRPPeriodError(BCRPError):
    """Period format is invalid or out of range."""
