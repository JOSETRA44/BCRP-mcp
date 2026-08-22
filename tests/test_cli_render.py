"""Unit tests for the CLI rendering layer — no network required."""

import pytest

from bcrp_mcp.cli import render
from bcrp_mcp.cli.render import Column, fmt_number, fmt_value, table, truncate


@pytest.fixture(autouse=True)
def deterministic_style():
    """Pin colour/unicode so assertions don't depend on the test terminal."""
    render.configure(color=False, ascii_mode=False)
    yield
    render.configure(color=False, ascii_mode=False)


class TestFmtNumber:
    def test_respects_declared_decimals(self):
        # BCRP publishes the exchange rate at 3 decimals; extra digits are noise.
        assert fmt_number(3.3974, 3) == "3.397"

    def test_zero_decimals_rounds_to_integer(self):
        assert fmt_number(100181.8021, 0) == "100,182"

    def test_thousands_separator(self):
        assert fmt_number(572774.7932, 2) == "572,774.79"

    def test_none_becomes_placeholder(self):
        assert fmt_number(None, 2) == render.placeholder()

    def test_without_decimals_trims_trailing_zeros(self):
        assert fmt_number(4.2500) == "4.25"

    def test_integer_value(self):
        assert fmt_number(42, 0) == "42"


class TestFmtValue:
    def test_none(self):
        assert fmt_value(None) == render.placeholder()

    def test_bool(self):
        assert fmt_value(True) == "yes"

    def test_empty_list(self):
        assert fmt_value([]) == render.placeholder()

    def test_list_joins(self):
        assert fmt_value(["a", "b"]) == "a, b"


class TestTruncate:
    def test_short_text_untouched(self):
        assert truncate("abc", 10) == "abc"

    def test_long_text_gets_ellipsis(self):
        out = truncate("abcdefghij", 5)
        assert len(out) == 5
        assert out.endswith("…")

    def test_exact_fit_untouched(self):
        assert truncate("abcde", 5) == "abcde"


class TestTable:
    COLUMNS = [Column("code", "Code"), Column("value", "Value", align="right")]

    def test_empty_rows_render_placeholder(self):
        assert "(no data)" in table([], self.COLUMNS)

    def test_contains_headers_and_values(self):
        out = table([{"code": "PD04637PD", "value": 3.397}], self.COLUMNS)
        assert "Code" in out
        assert "PD04637PD" in out
        assert "3.397" in out

    def test_all_lines_share_width(self):
        rows = [{"code": "A", "value": 1}, {"code": "BBBBBBBB", "value": 22222}]
        lines = table(rows, self.COLUMNS, width=80).splitlines()
        assert len({len(line) for line in lines}) == 1

    def test_fits_narrow_terminal(self):
        rows = [{"code": "PD04637PD", "value": "x" * 200}]
        for line in table(rows, self.COLUMNS, width=40).splitlines():
            assert len(line) <= 40

    def test_ascii_mode_uses_no_box_characters(self):
        render.configure(color=False, ascii_mode=True)
        out = table([{"code": "A", "value": 1}], self.COLUMNS)
        assert "─" not in out and "│" not in out
        assert "+" in out and "|" in out

    def test_max_width_caps_column(self):
        rows = [{"code": "A" * 50, "value": 1}]
        columns = [Column("code", "Code", max_width=10), Column("value", "Value")]
        out = table(rows, columns, width=200)
        assert "A" * 11 not in out

    def test_right_align_pads_left(self):
        rows = [{"code": "A", "value": 1}, {"code": "B", "value": 1000}]
        out = table(rows, self.COLUMNS, width=80)
        # The shorter number is padded so both values end at the same column.
        assert "│     1 │" in out
        assert "│ 1,000 │" in out


class TestColorConfiguration:
    def test_color_disabled_emits_no_ansi(self):
        render.configure(color=False)
        out = table([{"code": "A", "value": 1}], TestTable.COLUMNS)
        assert "\x1b[" not in out

    def test_color_enabled_emits_ansi(self):
        render.configure(color=True)
        out = table([{"code": "A", "value": 1}], TestTable.COLUMNS)
        assert "\x1b[" in out
