from datetime import UTC, date, datetime

from energy_dashboard import Activity, Granularity, Point, Utilization
from energy_dashboard.dashboard.data import (
    build_query,
    enum_options,
    series,
    summary,
    utilization_rows,
)
from tests.test_models import NED_EXAMPLE_RECORD


def make_items(n: int = 2) -> list[Utilization]:
    return [Utilization.model_validate(NED_EXAMPLE_RECORD) for _ in range(n)]


def test_enum_options_use_readable_labels() -> None:
    options = enum_options(Point)
    assert options[Point.NETHERLANDS] == "Netherlands"
    assert options[Point.NOORD_HOLLAND] == "Noord holland"


def test_build_query_makes_timezone_aware_bounds() -> None:
    query = build_query(
        point=0,
        type=2,
        activity=1,
        classification=2,
        granularity=6,
        start=date(2026, 1, 1),
        end=date(2026, 1, 8),
    )
    assert query.activity is Activity.PROVIDING
    assert query.granularity is Granularity.DAY
    assert query.valid_from == datetime(2026, 1, 1, tzinfo=UTC)
    assert query.valid_to == datetime(2026, 1, 8, tzinfo=UTC)
    assert query.order_by_valid_from == "asc"


def test_utilization_rows_and_series_match_items() -> None:
    items = make_items()
    rows = utilization_rows(items)
    x, y = series(items)
    assert len(rows) == len(x) == len(y) == 2
    assert rows[0]["volume"] == y[0]
    assert rows[0]["valid_from"] == x[0]


def test_summary_handles_empty_and_populated() -> None:
    assert "No records" in summary([], 0)
    assert "**2** of **5**" in summary(make_items(), 5)
