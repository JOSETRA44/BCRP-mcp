"""Unit tests for `bcrp_mcp.periods` — frequency inference, period
normalisation, TTL selection and label → ISO conversion. No network."""

from datetime import date

import pytest

from bcrp_mcp.periods import (
    CACHE_TTL_BY_FREQUENCY,
    cache_ttl_for_codes,
    frequency_for_codes,
    frequency_from_code,
    full_history_range,
    label_to_iso,
    normalize_request_period,
)


class TestFrequencyFromCode:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("PD04637PD", "daily"),
            ("PN00196MM", "monthly"),
            ("PN01288PM", "monthly"),
            ("PN03503MQ", "quarterly"),
            ("PM05000AA", "annual"),
            ("PN00000SW", "weekly"),
        ],
    )
    def test_last_character_of_the_code_names_the_frequency(self, code, expected):
        assert frequency_from_code(code) == expected

    def test_lowercase_code_is_normalised_before_inference(self):
        assert frequency_from_code("pd04637pd") == "daily"

    def test_surrounding_whitespace_is_ignored(self):
        assert frequency_from_code("  PD04637PD  ") == "daily"

    def test_unrecognised_suffix_reports_unknown_rather_than_guessing(self):
        assert frequency_from_code("PD04637PX") == "unknown"

    def test_empty_code_reports_unknown(self):
        assert frequency_from_code("") == "unknown"


class TestFrequencyForCodes:
    def test_a_uniform_batch_reports_its_shared_frequency(self):
        assert frequency_for_codes(["PD04637PD", "PD04638PD"]) == "daily"

    def test_a_mismatched_batch_reports_unknown_instead_of_the_first_code(self):
        # This is the CLI's only signal that a caller mixed frequencies in one
        # request: rather than silently adopting the first code's frequency
        # (and normalising the other code's periods into nonsense), the batch
        # is declared unknown so downstream defaults stay conservative.
        assert frequency_for_codes(["PD04637PD", "PN00196MM"]) == "unknown"

    def test_an_empty_batch_reports_unknown(self):
        assert frequency_for_codes([]) == "unknown"


class TestCacheTTL:
    def test_daily_and_monthly_series_do_not_share_one_ttl(self):
        # A daily series is republished every business day; a monthly
        # aggregate lands weeks after the month closes. Caching them for the
        # same span would either serve a stale exchange rate or re-fetch GDP
        # pointlessly.
        daily = cache_ttl_for_codes(["PD04637PD"], default=300)
        monthly = cache_ttl_for_codes(["PN00196MM"], default=300)
        assert daily != monthly
        assert daily == CACHE_TTL_BY_FREQUENCY["daily"]
        assert monthly == CACHE_TTL_BY_FREQUENCY["monthly"]

    def test_slower_series_are_cached_for_longer_than_faster_ones(self):
        assert (
            cache_ttl_for_codes(["PD04637PD"], 300)
            < cache_ttl_for_codes(["PN00196MM"], 300)
            <= cache_ttl_for_codes(["PN03503MQ"], 300)
        )

    def test_a_mismatched_batch_falls_back_to_the_configured_default(self):
        assert cache_ttl_for_codes(["PD04637PD", "PN00196MM"], default=42) == 42

    def test_an_unknown_suffix_falls_back_to_the_configured_default(self):
        assert cache_ttl_for_codes(["ZZZZZZZZ"], default=99) == 99


class TestNormalizeRequestPeriod:
    def test_documented_daily_format_is_rewritten_to_what_the_api_honours(self):
        # BCRP documents DD-MM-YYYY but answers such a range with a wall of
        # `n.d.`; the API really wants YYYY-M-D.
        assert normalize_request_period("01-02-2025", "daily") == "2025-2-1"

    def test_daily_format_already_in_api_form_is_left_alone(self):
        assert normalize_request_period("2025-2-1", "daily") == "2025-2-1"

    def test_daily_format_with_slashes_is_accepted(self):
        assert normalize_request_period("01/02/2025", "daily") == "2025-2-1"

    def test_daily_rewrite_strips_zero_padding(self):
        assert normalize_request_period("05-09-2024", "daily") == "2024-9-5"

    def test_weekly_series_are_rewritten_like_daily_ones(self):
        assert normalize_request_period("01-02-2025", "weekly") == "2025-2-1"

    @pytest.mark.parametrize(
        "period,frequency",
        [
            ("2024-1", "monthly"),
            ("2024-12", "monthly"),
            ("2024-1", "quarterly"),
            ("2024-4", "quarterly"),
            ("2024", "annual"),
        ],
    )
    def test_monthly_quarterly_and_annual_periods_pass_through_untouched(self, period, frequency):
        assert normalize_request_period(period, frequency) == period

    def test_a_monthly_period_sent_with_a_daily_code_is_not_mangled(self):
        # Mismatched frequency: "2024-1" has no day component, so the daily
        # rewrite must decline rather than invent one.
        assert normalize_request_period("2024-1", "daily") == "2024-1"

    def test_non_numeric_text_is_returned_unchanged(self):
        assert normalize_request_period("last-tuesday-ish", "daily") == "last-tuesday-ish"

    def test_surrounding_whitespace_is_trimmed(self):
        assert normalize_request_period("  2024-1  ", "monthly") == "2024-1"

    def test_none_stays_none(self):
        assert normalize_request_period(None, "daily") is None

    def test_empty_string_stays_empty(self):
        assert normalize_request_period("", "daily") == ""


class TestFullHistoryRange:
    def test_daily_range_spans_whole_days(self):
        start, end = full_history_range("daily", today=date(2026, 8, 20))
        assert start == "1970-1-1"
        assert end == "2027-12-31"

    def test_monthly_range_uses_month_precision(self):
        start, end = full_history_range("monthly", today=date(2026, 8, 20))
        assert start == "1900-1"
        assert end == "2027-12"

    def test_quarterly_range_uses_quarter_numbers(self):
        start, end = full_history_range("quarterly", today=date(2026, 8, 20))
        assert start == "1900-1"
        assert end == "2027-4"

    def test_annual_range_is_bare_years(self):
        assert full_history_range("annual", today=date(2026, 8, 20)) == ("1900", "2027")

    def test_unknown_frequency_falls_back_to_monthly_bounds(self):
        assert full_history_range("unknown", today=date(2026, 8, 20)) == ("1900-1", "2027-12")

    def test_end_reaches_into_next_year_so_todays_observation_is_included(self):
        _, end = full_history_range("monthly", today=date(2026, 12, 31))
        assert end.startswith("2027")


class TestLabelToIso:
    @pytest.mark.parametrize(
        "label,expected",
        [
            ("02.Ene.25", "2025-01-02"),
            ("31.Dic.24", "2024-12-31"),
            ("01.Jan.25", "2025-01-01"),
            ("15.Set.24", "2024-09-15"),
        ],
    )
    def test_daily_labels_become_full_iso_dates(self, label, expected):
        assert label_to_iso(label) == expected

    @pytest.mark.parametrize(
        "label,expected",
        [("Ene.2024", "2024-01"), ("Dic.2021", "2021-12"), ("Ago.99", "1999-08")],
    )
    def test_monthly_labels_become_year_month(self, label, expected):
        assert label_to_iso(label) == expected

    @pytest.mark.parametrize("label,expected", [("T1.26", "2026-Q1"), ("T4.2024", "2024-Q4")])
    def test_quarterly_labels_become_year_quarter(self, label, expected):
        assert label_to_iso(label) == expected

    def test_annual_labels_pass_through(self):
        assert label_to_iso("2024") == "2024"

    def test_two_digit_years_below_seventy_are_this_century(self):
        assert label_to_iso("Ene.25") == "2025-01"

    def test_two_digit_years_from_seventy_up_are_last_century(self):
        assert label_to_iso("Ene.70") == "1970-01"

    def test_iso_rendering_sorts_chronologically(self):
        labels = ["02.Ene.25", "31.Dic.24", "15.Jun.24"]
        assert sorted(label_to_iso(x) for x in labels) == [
            "2024-06-15",
            "2024-12-31",
            "2025-01-02",
        ]

    @pytest.mark.parametrize("label", ["", "not a period", "Xyz.2024", "13.Foo.25"])
    def test_unrecognised_labels_return_none_rather_than_a_wrong_date(self, label):
        assert label_to_iso(label) is None

    def test_none_input_returns_none(self):
        assert label_to_iso(None) is None
