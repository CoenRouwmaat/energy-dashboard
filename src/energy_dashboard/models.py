"""Pydantic models for the NED API.

Field shapes are taken from the live OpenAPI schema (`GET /v1/docs.json`) and
the worked example in the NED API manual (https://ned.nl/nl/handleiding-api).
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from energy_dashboard.enums import (
    Activity,
    Classification,
    Granularity,
    GranularityTimeZone,
)

_IRI_ID = re.compile(r"/(\d+)$")


def _iri_to_id(value: object) -> object:
    """Extract the trailing integer id from a NED IRI reference, e.g. `/v1/points/0` -> `0`.

    Values that are already ints (or non-matching strings) pass through unchanged,
    letting pydantic report its own validation error for those.
    """
    if isinstance(value, str) and (match := _IRI_ID.search(value)):
        return int(match.group(1))
    return value


class UtilizationQuery(BaseModel):
    """Query parameters for `GET /utilizations`.

    `point` and `type` are left as plain integers since the NED API defines
    dozens of codes for regions and energy carriers — see
    `energy_dashboard.enums.Point` and `energy_dashboard.enums.EnergyType`.
    """

    point: int
    type: int
    activity: Activity
    classification: Classification
    granularity: Granularity
    granularity_timezone: GranularityTimeZone = GranularityTimeZone.CET
    valid_from: datetime
    valid_to: datetime
    page: int = 1
    items_per_page: int = Field(default=144, le=200, gt=0)

    def to_params(self) -> dict[str, str | int]:
        """Render as the query-string parameters NED expects."""
        return {
            "point": self.point,
            "type": self.type,
            "activity": self.activity.value,
            "classification": self.classification.value,
            "granularity": self.granularity.value,
            "granularitytimezone": self.granularity_timezone.value,
            "validfrom[after]": self.valid_from.date().isoformat(),
            "validfrom[strictly_before]": self.valid_to.date().isoformat(),
            "page": self.page,
            "itemsPerPage": self.items_per_page,
        }


class Utilization(BaseModel):
    """A single utilization record returned by the NED API.

    `point`, `type`, `granularity`, `granularity_timezone`, `activity`, and
    `classification` are returned by the API as IRI references (e.g.
    `/v1/points/0`) and are parsed here down to their integer codes.
    """

    model_config = ConfigDict(populate_by_name=True)

    iri: str = Field(alias="@id")
    id: int
    point: int
    type: int
    granularity: int
    granularity_timezone: int = Field(alias="granularitytimezone")
    activity: int
    classification: int
    capacity: float
    volume: float
    percentage: float
    emission: int | None = None
    emission_factor: float | None = Field(default=None, alias="emissionfactor")
    valid_from: datetime = Field(alias="validfrom")
    valid_to: datetime = Field(alias="validto")
    last_update: datetime = Field(alias="lastupdate")

    @field_validator(
        "point",
        "type",
        "granularity",
        "granularity_timezone",
        "activity",
        "classification",
        mode="before",
    )
    @classmethod
    def _parse_iri(cls, value: object) -> object:
        return _iri_to_id(value)


class UtilizationPage(BaseModel):
    """A single (JSON-LD/Hydra) page of `Utilization` records."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[Utilization] = Field(alias="hydra:member")
    total_items: int = Field(alias="hydra:totalItems")
