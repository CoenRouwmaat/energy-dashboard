from datetime import UTC, datetime

from energy_dashboard.enums import (
    Activity,
    Classification,
    EnergyType,
    Granularity,
    Point,
)
from energy_dashboard.models import Utilization, UtilizationPage, UtilizationQuery

# Verbatim worked example from the NED API manual (https://ned.nl/nl/handleiding-api),
# with "emission"/"emissionfactor" filled in as null since the manual leaves them blank.
NED_EXAMPLE_RECORD = {
    "@id": "/v1/utilizations/3844522221",
    "@type": "Utilization",
    "type": "/v1/types/2",
    "granularity": "/v1/granularities/3",
    "granularitytimezone": "/v1/granularity_time_zones/0",
    "id": 3844522221,
    "point": "/v1/points/0",
    "activity": "/v1/activities/1",
    "classification": "/v1/classifications/2",
    "capacity": 438626,
    "volume": 73104,
    "emission": None,
    "emissionfactor": None,
    "percentage": 0.05968400090932846,
    "validfrom": "2020-11-16T14:30:00+00:00",
    "validto": "2020-11-16T14:40:00+00:00",
    "lastupdate": "2020-11-19T14:06:04+00:00",
}


def test_utilization_query_to_params() -> None:
    query = UtilizationQuery(
        point=Point.NETHERLANDS,
        type=EnergyType.SOLAR,
        activity=Activity.PROVIDING,
        classification=Classification.CURRENT,
        granularity=Granularity.TEN_MINUTES,
        valid_from=datetime(2020, 11, 16, tzinfo=UTC),
        valid_to=datetime(2020, 11, 17, tzinfo=UTC),
    )

    params = query.to_params()

    assert params["point"] == 0
    assert params["type"] == 2
    assert params["activity"] == Activity.PROVIDING.value
    assert params["granularity"] == Granularity.TEN_MINUTES.value
    assert params["validfrom[after]"] == "2020-11-16"
    assert params["validfrom[strictly_before]"] == "2020-11-17"


def test_utilization_parses_iri_references() -> None:
    record = Utilization.model_validate(NED_EXAMPLE_RECORD)

    assert record.id == 3844522221
    assert record.point == Point.NETHERLANDS
    assert record.type == EnergyType.SOLAR
    assert record.granularity == Granularity.TEN_MINUTES
    assert record.activity == Activity.PROVIDING
    assert record.classification == Classification.CURRENT
    assert record.capacity == 438626
    assert record.emission is None


def test_utilization_page_parses_hydra_response() -> None:
    payload = {
        "hydra:member": [NED_EXAMPLE_RECORD],
        "hydra:totalItems": 1,
    }

    page = UtilizationPage.model_validate(payload)

    assert page.total_items == 1
    assert len(page.items) == 1
    assert page.items[0].id == 3844522221
