"""Pure helpers turning NED records into UI-ready data (no NiceGUI imports)."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from enum import IntEnum
from typing import Literal

from energy_dashboard import (
    Activity,
    Classification,
    Granularity,
    Utilization,
    UtilizationQuery,
)


def enum_options(enum: type[IntEnum]) -> dict[int, str]:
    """Map enum values to readable labels, e.g. `{2: "Solar"}`."""
    return {member.value: member.name.replace("_", " ").capitalize() for member in enum}


def build_query(
    *,
    point: int,
    type: int,
    activity: int,
    classification: int,
    granularity: int,
    start: date,
    end: date,
    order: Literal["asc", "desc"] | None = "asc",
    items_per_page: int = 200,
) -> UtilizationQuery:
    """Build a `UtilizationQuery` from plain form values (dates are taken as UTC)."""
    return UtilizationQuery(
        point=point,
        type=type,
        activity=Activity(activity),
        classification=Classification(classification),
        granularity=Granularity(granularity),
        valid_from=datetime.combine(start, time.min, tzinfo=UTC),
        valid_to=datetime.combine(end, time.min, tzinfo=UTC),
        order_by_valid_from=order,
        items_per_page=items_per_page,
    )


def utilization_rows(items: Sequence[Utilization]) -> list[dict]:
    """Flatten records into table rows."""
    return [
        {
            "id": item.id,
            "valid_from": item.valid_from.isoformat(),
            "valid_to": item.valid_to.isoformat(),
            "volume": item.volume,
            "capacity": item.capacity,
            "percentage": round(item.percentage * 100, 2),
            "emission": item.emission,
        }
        for item in items
    ]


def series(items: Sequence[Utilization]) -> tuple[list[str], list[float]]:
    """Return x (ISO timestamps) and y (volume) for charting."""
    return (
        [item.valid_from.isoformat() for item in items],
        [item.volume for item in items],
    )


def summary(items: Sequence[Utilization], total_items: int) -> str:
    """Markdown summary of a result set."""
    if not items:
        return "No records returned for this query."
    volumes = [item.volume for item in items]
    return (
        f"**{len(items)}** of **{total_items}** records loaded. "
        f"Volume: min {min(volumes):,.0f}, mean {sum(volumes) / len(volumes):,.0f}, "
        f"max {max(volumes):,.0f}."
    )
