"""Hourly renewable-share vs CO2 analysis built from NED `/utilizations` records."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import StatisticsError, correlation, fmean, linear_regression
from zoneinfo import ZoneInfo

from energy_dashboard import Utilization

LOCAL_TZ = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True, slots=True)
class HourlyMix:
    """One hour of the Dutch electricity mix. Volumes in kWh, emissions in kg CO2."""

    start: datetime
    solar_kwh: float
    wind_kwh: float
    offshore_wind_kwh: float
    total_kwh: float
    emission_kg: float
    emission_factor: float  # kg CO2 per kWh

    @property
    def renewable_kwh(self) -> float:
        return self.solar_kwh + self.wind_kwh + self.offshore_wind_kwh

    @property
    def other_kwh(self) -> float:
        return max(self.total_kwh - self.renewable_kwh, 0.0)

    @property
    def renewable_share(self) -> float:
        return self.renewable_kwh / self.total_kwh


@dataclass(frozen=True, slots=True)
class Fit:
    """Least-squares line through (renewable share, emission factor) plus Pearson r."""

    slope: float
    intercept: float
    r: float


def combine(
    solar: Sequence[Utilization],
    wind: Sequence[Utilization],
    offshore_wind: Sequence[Utilization],
    mix: Sequence[Utilization],
) -> list[HourlyMix]:
    """Align the four series on `valid_from`, keeping only hours present in all of them.

    Hours with a zero total or missing emission data are dropped.
    """
    by_start = [{u.valid_from: u for u in s} for s in (solar, wind, offshore_wind)]
    rows = []
    for item in sorted(mix, key=lambda u: u.valid_from):
        s, w, o = (series.get(item.valid_from) for series in by_start)
        if (
            s is None
            or w is None
            or o is None
            or item.volume <= 0
            or item.emission is None
            or item.emission_factor is None
        ):
            continue
        rows.append(
            HourlyMix(
                start=item.valid_from.astimezone(LOCAL_TZ),
                solar_kwh=s.volume,
                wind_kwh=w.volume,
                offshore_wind_kwh=o.volume,
                total_kwh=item.volume,
                emission_kg=item.emission,
                emission_factor=item.emission_factor,
            )
        )
    return rows


def fit_share_vs_factor(rows: Sequence[HourlyMix]) -> Fit | None:
    """Regress emission factor on renewable share; `None` if there is too little variation."""
    if len(rows) < 3:
        return None
    x = [row.renewable_share for row in rows]
    y = [row.emission_factor for row in rows]
    try:
        r = correlation(x, y)
        slope, intercept = linear_regression(x, y)
    except StatisticsError:  # constant input
        return None
    return Fit(slope=slope, intercept=intercept, r=r)


def kpis(rows: Sequence[HourlyMix]) -> dict[str, float]:
    """Headline numbers: mean share, volume-weighted emission factor, total tonnes CO2."""
    total_kwh = sum(row.total_kwh for row in rows)
    total_kg = sum(row.emission_kg for row in rows)
    return {
        "mean_share": fmean(row.renewable_share for row in rows),
        "emission_factor": total_kg / total_kwh,
        "emissions_tonnes": total_kg / 1000,
        "renewable_gwh": sum(row.renewable_kwh for row in rows) / 1e6,
    }
