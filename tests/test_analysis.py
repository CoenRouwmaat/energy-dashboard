from datetime import UTC, datetime

import pytest

from energy_dashboard import Utilization
from energy_dashboard.dashboard.analysis import combine, fit_share_vs_factor, kpis
from tests.test_models import NED_EXAMPLE_RECORD


def util(hour: int, volume: float, **extra) -> Utilization:
    record = {
        **NED_EXAMPLE_RECORD,
        "validfrom": datetime(2026, 1, 1, hour, tzinfo=UTC).isoformat(),
        "validto": datetime(2026, 1, 1, hour + 1, tzinfo=UTC).isoformat(),
        "volume": volume,
        "emission": extra.get("emission", 0),
        "emissionfactor": extra.get("emissionfactor", 0.0),
    }
    return Utilization.model_validate(record)


def hours(volumes: list[float], **extra) -> list[Utilization]:
    return [util(h, v, **extra) for h, v in enumerate(volumes)]


def make_mix(shares: list[float], factors: list[float]):
    """Total 100 kWh per hour; all renewables come from solar."""
    solar = hours([100 * s for s in shares])
    zero = hours([0.0] * len(shares))
    mix = [
        util(h, 100, emission=int(100 * f), emissionfactor=f)
        for h, f in enumerate(factors)
    ]
    return combine(solar, zero, zero, mix)


def test_combine_keeps_only_complete_hours() -> None:
    solar, wind, offshore = hours([10, 10]), hours([10, 10]), hours([10])
    mix = [
        util(0, 100, emission=5, emissionfactor=0.05),
        util(1, 100, emission=5, emissionfactor=0.05),
    ]
    rows = combine(solar, wind, offshore, mix)
    assert len(rows) == 1  # hour 1 has no offshore record
    assert rows[0].renewable_share == pytest.approx(0.3)


def test_combine_drops_hours_without_emission() -> None:
    zero = hours([0.0])
    mix = [util(0, 100, emission=None, emissionfactor=None)]
    assert combine(zero, zero, zero, mix) == []


def test_negative_correlation_is_detected() -> None:
    rows = make_mix([0.1, 0.3, 0.5, 0.7], [0.5, 0.4, 0.3, 0.2])
    fit = fit_share_vs_factor(rows)
    assert fit is not None
    assert fit.r == pytest.approx(-1.0)
    assert fit.slope == pytest.approx(-0.5)


def test_fit_is_none_for_constant_or_tiny_input() -> None:
    assert fit_share_vs_factor(make_mix([0.5, 0.5, 0.5], [0.3, 0.3, 0.3])) is None
    assert fit_share_vs_factor(make_mix([0.1, 0.2], [0.3, 0.2])) is None


def test_kpis_weight_emission_factor_by_volume() -> None:
    stats = kpis(make_mix([0.2, 0.4], [0.4, 0.2]))
    assert stats["mean_share"] == pytest.approx(0.3)
    assert stats["emission_factor"] == pytest.approx(0.3)
    assert stats["emissions_tonnes"] == pytest.approx(0.06)
