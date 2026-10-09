"""Pydantic models for the NED API.

Field shapes are taken from the live OpenAPI schema (`GET /v1/docs.json`) and
the worked example in the NED API manual (https://ned.nl/nl/handleiding-api).
"""

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

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


class Page[T](BaseModel):
    """A single (JSON-LD/Hydra) page of records of type `T`."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[T] = Field(alias="hydra:member")
    total_items: int = Field(alias="hydra:totalItems")


class PageQuery(BaseModel):
    """Pagination parameters shared by every NED list endpoint."""

    page: int = Field(default=1, ge=1)
    items_per_page: int = Field(default=200, le=200, gt=0)

    def to_params(self) -> dict[str, str | int]:
        """Render as the query-string parameters NED expects."""
        return {"page": self.page, "itemsPerPage": self.items_per_page}


class UtilizationQuery(PageQuery):
    """Query parameters for `GET /utilizations`.

    `point` and `type` are left as plain integers since the NED API defines
    dozens of codes for regions and energy carriers — see
    `energy_dashboard.enums.Point` and `energy_dashboard.enums.EnergyType`.
    """

    id: int | None = None
    point: int
    type: int
    activity: Activity
    classification: Classification
    granularity: Granularity
    granularity_timezone: GranularityTimeZone = GranularityTimeZone.CET
    valid_from: datetime
    valid_to: datetime
    order_by_valid_from: Literal["asc", "desc"] | None = None
    items_per_page: int = Field(default=144, le=200, gt=0)

    def to_params(self) -> dict[str, str | int]:
        """Render as the query-string parameters NED expects."""
        params: dict[str, str | int] = {
            **super().to_params(),
            "point": self.point,
            "type": self.type,
            "activity": self.activity.value,
            "classification": self.classification.value,
            "granularity": self.granularity.value,
            "granularitytimezone": self.granularity_timezone.value,
            "validfrom[after]": self.valid_from.date().isoformat(),
            "validfrom[strictly_before]": self.valid_to.date().isoformat(),
        }
        if self.id is not None:
            params["id"] = self.id
        if self.order_by_valid_from is not None:
            params["order[validfrom]"] = self.order_by_valid_from
        return params


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


UtilizationPage = Page[Utilization]


def _iris_to_ids(value: object) -> object:
    if isinstance(value, list):
        return [_iri_to_id(item) for item in value]
    return value


class PointRecord(BaseModel):
    """A region from `GET /points`; parent/child points are parsed to their ids."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    identifier: int
    name: str
    name_short: str = Field(alias="nameshort")
    valid_from: datetime = Field(alias="validfrom")
    valid_to: datetime | None = Field(default=None, alias="validto")
    child_points: Annotated[list[int], BeforeValidator(_iris_to_ids)] = Field(
        default_factory=list, alias="childpoints"
    )
    parent_points: Annotated[list[int], BeforeValidator(_iris_to_ids)] = Field(
        default_factory=list, alias="parentpoints"
    )


class PointQuery(PageQuery):
    """Query parameters for `GET /points`."""

    id: int | None = None
    identifier: int | None = None
    name: str | None = None
    parent_points: int | None = None
    child_points: int | None = None

    def to_params(self) -> dict[str, str | int]:
        """Render as the query-string parameters NED expects."""
        params = super().to_params()
        if self.id is not None:
            params["id"] = self.id
        if self.identifier is not None:
            params["identifier"] = self.identifier
        if self.name is not None:
            params["name"] = self.name
        if self.parent_points is not None:
            params["parentpoints"] = self.parent_points
        if self.child_points is not None:
            params["childpoints"] = self.child_points
        return params


class TypeRecord(BaseModel):
    """An energy carrier from `GET /types`."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    identifier: int
    name: str
    name_short: str = Field(alias="nameshort")


class ActivityRecord(BaseModel):
    """An activity from `GET /activities`."""

    id: int
    name: str


class ClassificationRecord(BaseModel):
    """A classification from `GET /classifications`."""

    id: int
    name: str


class GranularityRecord(BaseModel):
    """A granularity from `GET /granularities`."""

    id: int
    name: str


class GranularityTimeZoneRecord(BaseModel):
    """A time zone from `GET /granularity_time_zones`."""

    id: int
    name: str
