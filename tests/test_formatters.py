"""Unit tests for BCRP MCP formatters — no network required."""

import pytest

from bcrp_mcp.formatters import (
    _detect_frequency,
    _safe_float,
    format_latest_response,
    format_metadata_only,
    format_series_response,
)


class TestSafeFloat:
    def test_valid_number(self):
        assert _safe_float("126.014256") == pytest.approx(126.014256)

    def test_integer_string(self):
        assert _safe_float("4.25") == pytest.approx(4.25)

    def test_no_data_marker(self):
        assert _safe_float("n.d.") is None

    def test_empty_string(self):
        assert _safe_float("") is None

    def test_none_input(self):
        assert _safe_float(None) is None

    def test_dash(self):
        assert _safe_float("-") is None

    def test_comma_decimal(self):
        assert _safe_float("98309,08") == pytest.approx(98309.08)

    def test_large_number(self):
        assert _safe_float("455566.40821636") == pytest.approx(455566.40821636)


class TestDetectFrequency:
    def test_daily(self):
        assert _detect_frequency("01.Ene.25") == "daily"
        assert _detect_frequency("24.Jun.26") == "daily"

    def test_monthly(self):
        assert _detect_frequency("Ene.2024") == "monthly"
        assert _detect_frequency("Dic.2021") == "monthly"
        assert _detect_frequency("Oct.2024") == "monthly"

    def test_quarterly(self):
        assert _detect_frequency("T1.2024") == "quarterly"
        assert _detect_frequency("T4.25") == "quarterly"

    def test_annual(self):
        assert _detect_frequency("2024") == "annual"

    def test_unknown(self):
        assert _detect_frequency("") == "unknown"


class TestFormatSeriesResponse:
    def _make_raw(self, periods: list, series_names: list[str] | None = None) -> dict:
        series_names = series_names or ["Test Series"]
        return {
            "config": {
                "title": "Test Category",
                "series": [{"name": n, "dec": "2"} for n in series_names],
            },
            "periods": periods,
        }

    def test_basic_monthly_response(self):
        raw = self._make_raw([
            {"name": "Ene.2024", "values": ["100.5"]},
            {"name": "Feb.2024", "values": ["101.2"]},
        ])
        result = format_series_response(raw, ["PN00001MM"])

        assert result["title"] == "Test Category"
        assert result["frequency"] == "monthly"
        assert result["count"] == 2
        assert result["first_period"] == "Ene.2024"
        assert result["last_period"] == "Feb.2024"
        # values is a list; position 0 corresponds to series[0]
        assert result["data"][0]["values"][0] == pytest.approx(100.5)

    def test_multiple_series(self):
        raw = self._make_raw(
            [{"name": "Ene.2024", "values": ["3.5", "4.25"]}],
            ["Series A", "Series B"],
        )
        result = format_series_response(raw, ["PD04637PD", "PD12301MD"])

        assert result["series"][0]["code"] == "PD04637PD"
        assert result["series"][1]["code"] == "PD12301MD"
        # values is positional — values[i] corresponds to series[i]
        assert result["data"][0]["values"][0] == pytest.approx(3.5)
        assert result["data"][0]["values"][1] == pytest.approx(4.25)

    def test_no_data_marker(self):
        raw = self._make_raw([
            {"name": "Ene.2024", "values": ["n.d."]},
            {"name": "Feb.2024", "values": ["100.0"]},
        ])
        result = format_series_response(raw, ["PN00001MM"])
        assert result["data"][0]["values"][0] is None
        assert result["data"][1]["values"][0] == pytest.approx(100.0)

    def test_latest_field(self):
        raw = self._make_raw([
            {"name": "Ene.2024", "values": ["10.0"]},
            {"name": "Feb.2024", "values": ["20.0"]},
            {"name": "Mar.2024", "values": ["30.0"]},
        ])
        result = format_series_response(raw, ["PN00001MM"])
        assert result["latest"]["period"] == "Mar.2024"
        assert result["latest"]["values"][0] == pytest.approx(30.0)

    def test_empty_periods(self):
        raw = self._make_raw([])
        result = format_series_response(raw, ["PN00001MM"])
        assert result["count"] == 0
        assert result["data"] == []
        assert "first_period" not in result
        assert "latest" not in result

    def test_daily_frequency_detection(self):
        raw = self._make_raw([
            {"name": "01.Ene.25", "values": ["3.80"]},
            {"name": "02.Ene.25", "values": ["3.81"]},
        ])
        result = format_series_response(raw, ["PD04637PD"])
        assert result["frequency"] == "daily"

    def test_quarterly_frequency_detection(self):
        raw = self._make_raw([
            {"name": "T1.2024", "values": ["5.2"]},
            {"name": "T2.2024", "values": ["4.8"]},
        ])
        result = format_series_response(raw, ["PN03503MQ"])
        assert result["frequency"] == "quarterly"

    def test_series_metadata(self):
        raw = self._make_raw(
            [{"name": "Ene.2024", "values": ["100.0"]}],
            ["Liquidez Total (M2)"],
        )
        result = format_series_response(raw, ["PN00196MM"])
        assert result["series"][0]["name"] == "Liquidez Total (M2)"
        assert result["series"][0]["code"] == "PN00196MM"
        assert result["series"][0]["decimals"] == 2

    def test_uppercase_codes(self):
        raw = self._make_raw([{"name": "Ene.2024", "values": ["100.0"]}])
        result = format_series_response(raw, ["pn00001mm"])
        # Code in series metadata should be uppercased
        assert result["series"][0]["code"] == "PN00001MM"
        # Values list should have a valid entry
        assert result["data"][0]["values"][0] == pytest.approx(100.0)

    def test_values_list_length_matches_series(self):
        """Each period's values list length must equal the number of series."""
        raw = self._make_raw(
            [{"name": "Ene.2024", "values": ["3.5", "4.25", "98000.0"]}],
            ["Series A", "Series B", "Series C"],
        )
        result = format_series_response(raw, ["PD04637PD", "PD12301MD", "PD04650MD"])
        assert len(result["data"][0]["values"]) == 3
        assert len(result["series"]) == 3

    def test_api_reorder_values_by_position(self):
        """When API returns series in different order than requested, values remain
        positionally aligned with the API's config.series ordering."""
        # Simulates API returning series in a different order than requested
        # Requested: [A, B, C] but API puts them as [C, A, B]
        raw = {
            "config": {
                "title": "Mixed Categories",
                "series": [
                    {"name": "Series C name", "dec": "2"},  # API position 0
                    {"name": "Series A name", "dec": "2"},  # API position 1
                    {"name": "Series B name", "dec": "2"},  # API position 2
                ],
            },
            "periods": [{"name": "Ene.2024", "values": ["3.0", "1.0", "2.0"]}],
        }
        result = format_series_response(raw, ["A", "B", "C"])
        # series[0] gets code "A" (positional — may differ from semantic match)
        # values[0] = 3.0 (what API returned at position 0, which is actually Series C)
        # The 'name' field from API config tells you what values[0] REALLY is
        assert result["data"][0]["values"][0] == pytest.approx(3.0)
        assert result["series"][0]["name"] == "Series C name"
        assert result["series"][0]["code"] == "A"


class TestFormatLatestResponse:
    def _make_raw_monthly(self, n: int) -> dict:
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        periods = []
        for i in range(n):
            month_name = months[i % 12]
            year = 2024 + (i // 12)
            periods.append({"name": f"{month_name}.{year}", "values": [str(100 + i)]})
        return {
            "config": {
                "title": "Test",
                "series": [{"name": "Test Series", "dec": "2"}],
            },
            "periods": periods,
        }

    def test_returns_last_n(self):
        raw = self._make_raw_monthly(10)
        result = format_latest_response(raw, ["PN00001MM"], n=3)
        assert result["count"] == 3
        assert len(result["data"]) == 3

    def test_n_larger_than_available(self):
        raw = self._make_raw_monthly(4)
        result = format_latest_response(raw, ["PN00001MM"], n=10)
        assert result["count"] == 4

    def test_last_period_is_most_recent(self):
        raw = self._make_raw_monthly(12)
        result = format_latest_response(raw, ["PN00001MM"], n=3)
        assert result["last_period"] == "Dic.2024"


class TestFormatMetadataOnly:
    def test_metadata_no_data(self):
        raw = {
            "config": {
                "title": "Reservas Internacionales",
                "series": [{"name": "Reservas Netas (millones US$)", "dec": "2"}],
            },
            "periods": [
                {"name": "01.Ene.25", "values": ["98000.0"]},
                {"name": "02.Ene.25", "values": ["98100.0"]},
            ],
        }
        result = format_metadata_only(raw, ["PD04650MD"])
        assert result["title"] == "Reservas Internacionales"
        assert result["series"][0]["code"] == "PD04650MD"
        assert result["total_available_periods"] == 2
        assert result["frequency"] == "daily"
        assert result["first_available"] == "01.Ene.25"
        assert result["last_available"] == "02.Ene.25"
        # Should NOT have 'data' field
        assert "data" not in result
