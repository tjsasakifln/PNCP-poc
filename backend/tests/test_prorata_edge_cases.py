"""Tests for pro-rata calculation edge cases (STORY-171).

Tests timezone-aware calculations, last day of month, defer logic,
and annual → monthly downgrade prevention.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo


class TestProRataCalculations:
    """Test pro-rata credit calculations."""

    def test_calculate_daily_rate_monthly(self):
        """Test daily rate calculation for monthly billing."""
        from services.billing import calculate_daily_rate

        # Monthly plan: R$ 297 / 30 days = R$ 9.90/day
        daily_rate = calculate_daily_rate(Decimal("297.00"), "monthly")
        assert daily_rate == Decimal("9.90")

    def test_calculate_daily_rate_annual(self):
        """Test daily rate calculation for annual billing (20% discount)."""
        from services.billing import calculate_daily_rate

        # Annual plan: R$ 297 * 9.6 / 365 = R$ 6.50/day (with 20% discount)
        # 297 * 9.6 = 2851.2, 2851.2 / 365 = 7.81
        daily_rate = calculate_daily_rate(Decimal("297.00"), "annual")
        expected = (Decimal("297.00") * Decimal("9.6") / 365).quantize(Decimal("0.01"))
        assert daily_rate == expected

    def test_prorata_calculation_15_days_remaining(self):
        """Test pro-rata credit with 15 days until renewal."""
        from services.billing import calculate_prorata_credit

        now = datetime.now(timezone.utc)
        next_billing = now + timedelta(days=15)

        result = calculate_prorata_credit(
            current_billing_period="monthly",
            new_billing_period="annual",
            current_price_brl=Decimal("297.00"),
            new_price_brl=Decimal("2376.00"),  # Annual price (297 * 9.6)
            next_billing_date=next_billing,
            user_timezone="America/Sao_Paulo",
        )

        # days_until_renewal may be 15 or 16 depending on time-of-day rounding
        assert result.deferred is False
        assert 14 <= result.days_until_renewal <= 16
        expected_credit = Decimal("9.90") * result.days_until_renewal
        assert result.prorated_credit == expected_credit

    def test_prorata_deferred_when_less_than_7_days(self):
        """Test that pro-rata calculation defers when < 7 days until renewal."""
        from services.billing import calculate_prorata_credit

        now = datetime.now(timezone.utc)
        next_billing = now + timedelta(days=5)  # Only 5 days left

        result = calculate_prorata_credit(
            current_billing_period="monthly",
            new_billing_period="annual",
            current_price_brl=Decimal("297.00"),
            new_price_brl=Decimal("2376.00"),
            next_billing_date=next_billing,
            user_timezone="America/Sao_Paulo",
        )

        # Should be deferred (days_until_renewal may be 5 or 6 due to time-of-day rounding)
        assert result.deferred is True
        assert result.days_until_renewal <= 7  # Must be under the defer threshold
        assert result.prorated_credit == Decimal("0.00")
        assert "próximo ciclo" in result.reason.lower()

    def test_prorata_with_timezone_awareness_sao_paulo(self):
        """Test timezone-aware calculation for Brazil (UTC-3)."""
        from services.billing import calculate_prorata_credit

        # Use Brazil timezone (America/Sao_Paulo = UTC-3)
        sao_paulo_tz = ZoneInfo("America/Sao_Paulo")
        now_sao_paulo = datetime.now(sao_paulo_tz)
        next_billing = now_sao_paulo + timedelta(days=10)

        # Convert to UTC for storage (but calculation should use local timezone)
        next_billing_utc = next_billing.astimezone(timezone.utc)

        result = calculate_prorata_credit(
            current_billing_period="monthly",
            new_billing_period="annual",
            current_price_brl=Decimal("297.00"),
            new_price_brl=Decimal("2376.00"),
            next_billing_date=next_billing_utc,
            user_timezone="America/Sao_Paulo",
        )

        # days_until_renewal may be 10 or 11 due to timezone/rounding
        assert 9 <= result.days_until_renewal <= 11
        expected_credit = Decimal("9.90") * result.days_until_renewal
        assert result.prorated_credit == expected_credit

    def test_prorata_prevents_annual_to_monthly_downgrade(self):
        """Test that annual → monthly downgrade raises ValueError."""
        from services.billing import calculate_prorata_credit

        now = datetime.now(timezone.utc)
        next_billing = now + timedelta(days=30)

        with pytest.raises(ValueError) as exc_info:
            calculate_prorata_credit(
                current_billing_period="annual",
                new_billing_period="monthly",
                current_price_brl=Decimal("2376.00"),
                new_price_brl=Decimal("297.00"),
                next_billing_date=next_billing,
            )

        assert "downgrade" in str(exc_info.value).lower()
        assert "not supported" in str(exc_info.value).lower()

    def test_prorata_last_day_of_month(self):
        """Test pro-rata calculation on last day of month (edge case)."""
        from services.billing import calculate_prorata_credit

        # Set next_billing_date to last day of month
        next_billing = datetime(2026, 2, 28, 23, 59, 59, tzinfo=timezone.utc)

        # Assume today is 2026-02-15 (13 days until end of month)
        with patch("services.billing.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 2, 15, 0, 0, 0, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = calculate_prorata_credit(
                current_billing_period="monthly",
                new_billing_period="annual",
                current_price_brl=Decimal("297.00"),
                new_price_brl=Decimal("2376.00"),
                next_billing_date=next_billing,
            )

            # Should handle last day correctly (inclusive counting)
            assert result.days_until_renewal >= 13
            assert not result.deferred

    def test_prorata_with_invalid_timezone_fallback(self):
        """Test that invalid timezone falls back to UTC without error."""
        from services.billing import calculate_prorata_credit

        now = datetime.now(timezone.utc)
        next_billing = now + timedelta(days=10)

        # Should not raise exception, just log warning and use UTC
        result = calculate_prorata_credit(
            current_billing_period="monthly",
            new_billing_period="annual",
            current_price_brl=Decimal("297.00"),
            new_price_brl=Decimal("2376.00"),
            next_billing_date=next_billing,
            user_timezone="Invalid/Timezone",  # Invalid timezone
        )

        # days_until_renewal may be 10 or 11 due to time-of-day rounding
        assert 9 <= result.days_until_renewal <= 11
        expected_credit = Decimal("9.90") * result.days_until_renewal
        assert result.prorated_credit == expected_credit
