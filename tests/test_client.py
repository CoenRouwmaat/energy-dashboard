import asyncio
from datetime import UTC, datetime
from typing import Protocol

import httpx
import pytest
from pydantic import ValidationError


class _HasId(Protocol):
    id: int


from energy_dashboard import (
    Activity,
    Classification,
    EnergyType,
    Granularity,
    NedApiError,
    NedClient,
    NedSettings,
    Page,
    Point,
    PointQuery,
    Utilization,
    UtilizationPage,
    UtilizationQuery,
)
from tests.test_models import NED_EXAMPLE_RECORD


def make_query(items_per_page: int = 2) -> UtilizationQuery:
    return UtilizationQuery(
        point=Point.NETHERLANDS,
        type=EnergyType.SOLAR,
        activity=Activity.PROVIDING,
        classification=Classification.CURRENT,
        granularity=Granularity.DAY,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_to=datetime(2026, 1, 8, tzinfo=UTC),
        items_per_page=items_per_page,
    )


def make_client(
    handler: httpx.MockTransport, settings: NedSettings | None = None
) -> NedClient:
    settings = settings or NedSettings(api_key="test-key", base_url="https://ned.test")
    return NedClient(settings, transport=handler)


def page_body(n: int) -> dict:
    return {
        "hydra:member": [NED_EXAMPLE_RECORD] * n,
        "hydra:totalItems": n,
    }


def test_get_utilizations_returns_parsed_page() -> None:
    async def run():
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, json=page_body(2))
        )
        async with make_client(transport) as client:
            return await client.get_utilizations(make_query())

    page = asyncio.run(run())
    assert len(page.items) == 2


def test_get_utilizations_raises_on_error() -> None:
    async def run():
        transport = httpx.MockTransport(lambda r: httpx.Response(401, text="nope"))
        async with make_client(transport) as client:
            await client.get_utilizations(make_query())

    with pytest.raises(NedApiError):
        asyncio.run(run())


def test_iter_utilizations_walks_pages() -> None:
    pages_requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["page"]
        pages_requested.append(page)
        return httpx.Response(200, json=page_body(2 if page == "1" else 1))

    async def run():
        async with make_client(httpx.MockTransport(handler)) as client:
            return [r async for r in client.iter_utilizations(make_query())]

    records = asyncio.run(run())
    assert len(records) == 3
    assert pages_requested == ["1", "2"]


def run_with_sleeps(
    responses: list[httpx.Response], monkeypatch: pytest.MonkeyPatch
) -> tuple[UtilizationPage, list[float], list[httpx.Request]]:
    sleeps: list[float] = []
    requests: list[httpx.Request] = []
    queue = iter(responses)

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return next(queue)

    async def run():
        async with make_client(httpx.MockTransport(handler)) as client:
            return await client.get_utilizations(make_query())

    return asyncio.run(run()), sleeps, requests


def test_get_utilizations_retries_5xx_with_exponential_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, sleeps, requests = run_with_sleeps(
        [
            httpx.Response(503),
            httpx.Response(502),
            httpx.Response(200, json=page_body(2)),
        ],
        monkeypatch,
    )
    assert len(page.items) == 2
    assert len(requests) == 3
    assert sleeps == [1.0, 2.0]


def test_get_utilizations_honours_retry_after_on_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page, sleeps, _ = run_with_sleeps(
        [
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, json=page_body(1)),
        ],
        monkeypatch,
    )
    assert len(page.items) == 1
    assert sleeps == [7.0]


def test_get_utilizations_raises_after_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(NedApiError) as exc_info:
        run_with_sleeps([httpx.Response(429)] * 4, monkeypatch)
    assert exc_info.value.status_code == 429


def test_get_utilizations_does_not_retry_client_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(NedApiError):
        run_with_sleeps([httpx.Response(401)], monkeypatch)


POINT_RECORD = {
    "@id": "/v1/points/1",
    "@type": "Point",
    "id": 1,
    "identifier": 1,
    "name": "Groningen",
    "nameshort": "GRNG",
    "validfrom": "2020-01-01T00:00:00+00:00",
    "validto": None,
    "childpoints": ["/v1/points/20", "/v1/points/21"],
    "parentpoints": ["/v1/points/0"],
}

REFERENCE_ENDPOINTS = [
    ("points", POINT_RECORD),
    ("types", {"id": 2, "identifier": 2, "name": "Solar", "nameshort": "ZON"}),
    ("activities", {"id": 1, "name": "Providing"}),
    ("classifications", {"id": 2, "name": "Current"}),
    ("granularities", {"id": 5, "name": "Hour"}),
    ("granularity_time_zones", {"id": 1, "name": "CET"}),
]


@pytest.mark.parametrize(("name", "record"), REFERENCE_ENDPOINTS)
def test_get_reference_endpoint_returns_parsed_page(name: str, record: dict) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = {"hydra:member": [record, record], "hydra:totalItems": 2}
        return httpx.Response(200, json=body)

    async def run() -> Page:
        async with make_client(httpx.MockTransport(handler)) as client:
            return await getattr(client, f"get_{name}")()

    page = asyncio.run(run())
    assert requests[0].url.path == f"/{name}"
    assert requests[0].url.params["itemsPerPage"] == "200"
    assert len(page.items) == 2
    assert page.total_items == 2
    assert page.items[0].id == record["id"]


def test_point_record_parses_iri_references() -> None:
    async def run() -> Page:
        body = {"hydra:member": [POINT_RECORD], "hydra:totalItems": 1}
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json=body))
        async with make_client(transport) as client:
            return await client.get_points()

    point = asyncio.run(run()).items[0]
    assert point.name_short == "GRNG"
    assert point.valid_to is None
    assert point.child_points == [20, 21]
    assert point.parent_points == [0]


@pytest.mark.parametrize(("name", "record"), REFERENCE_ENDPOINTS)
def test_iter_reference_endpoint_walks_pages(name: str, record: dict) -> None:
    pages_requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["page"]
        pages_requested.append(page)
        n = 2 if page == "1" else 1
        return httpx.Response(
            200, json={"hydra:member": [record] * n, "hydra:totalItems": 3}
        )

    async def run() -> list:
        async with make_client(httpx.MockTransport(handler)) as client:
            iterator = getattr(client, f"iter_{name}")
            kwargs = (
                {"query": PointQuery(items_per_page=2)}
                if name == "points"
                else {"items_per_page": 2}
            )
            return [r async for r in iterator(**kwargs)]

    assert len(asyncio.run(run())) == 3
    assert pages_requested == ["1", "2"]


def test_reference_endpoint_retries_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    responses = iter(
        [
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"hydra:member": [], "hydra:totalItems": 0}),
        ]
    )

    async def run() -> Page:
        transport = httpx.MockTransport(lambda r: next(responses))
        async with make_client(transport) as client:
            return await client.get_types()

    assert asyncio.run(run()).items == []
    assert sleeps == [3.0]


def test_client_sends_auth_and_accept_headers_to_configured_base_url() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=page_body(1))

    async def run() -> None:
        # Default base_url, so the real constructor configuration is what is tested.
        client = NedClient(
            NedSettings(api_key="secret-key"), transport=httpx.MockTransport(handler)
        )
        async with client:
            await client.get_utilizations(make_query())

    asyncio.run(run())
    request = requests[0]
    assert request.url.host == "api.ned.nl"
    assert request.url.path == "/v1/utilizations"
    assert request.headers["X-AUTH-TOKEN"] == "secret-key"
    assert request.headers["Accept"] == "application/ld+json"


def test_get_utilizations_sends_query_params() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=page_body(1))

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            await client.get_utilizations(make_query())

    asyncio.run(run())
    params = requests[0].url.params
    assert params["point"] == str(Point.NETHERLANDS.value)
    assert params["type"] == str(EnergyType.SOLAR.value)
    assert params["validfrom[after]"] == "2026-01-01"
    assert params["validfrom[strictly_before]"] == "2026-01-08"
    assert params["page"] == "1"
    assert params["itemsPerPage"] == "2"


def test_api_error_carries_status_code_and_body() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(lambda r: httpx.Response(404, text="no such"))
        async with make_client(transport) as client:
            await client.get_points()

    with pytest.raises(NedApiError) as exc_info:
        asyncio.run(run())
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "no such"
    assert "404" in str(exc_info.value)


def test_get_utilizations_returns_empty_page() -> None:
    async def run():
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, json=page_body(0))
        )
        async with make_client(transport) as client:
            return await client.get_utilizations(make_query())

    page = asyncio.run(run())
    assert page.items == []
    assert page.total_items == 0


def test_get_utilizations_raises_on_malformed_body() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, json={"unexpected": []})
        )
        async with make_client(transport) as client:
            await client.get_utilizations(make_query())

    with pytest.raises(ValidationError):
        asyncio.run(run())


def test_iter_utilizations_stops_on_empty_page_after_full_pages() -> None:
    pages_requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["page"]
        pages_requested.append(page)
        return httpx.Response(200, json=page_body(0 if page == "3" else 2))

    async def run():
        async with make_client(httpx.MockTransport(handler)) as client:
            return [r async for r in client.iter_utilizations(make_query())]

    assert len(asyncio.run(run())) == 4
    assert pages_requested == ["1", "2", "3"]


def test_iter_utilizations_propagates_error_mid_iteration() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params["page"] == "1":
            return httpx.Response(200, json=page_body(2))
        return httpx.Response(403, text="forbidden")

    seen: list[object] = []

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            async for record in client.iter_utilizations(make_query()):
                seen.append(record)

    with pytest.raises(NedApiError):
        asyncio.run(run())
    assert len(seen) == 2


def test_retries_are_bounded_by_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(503)

    settings = NedSettings(
        api_key="test-key",
        base_url="https://ned.test",
        max_retries=2,
        retry_backoff_seconds=0.5,
    )

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler), settings) as client:
            await client.get_utilizations(make_query())

    with pytest.raises(NedApiError):
        asyncio.run(run())
    assert len(requests) == 3
    assert sleeps == [0.5, 1.0]


def test_max_retries_zero_disables_retrying(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []

    async def fake_sleep(delay: float) -> None:
        raise AssertionError("should not sleep")

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(429)

    settings = NedSettings(
        api_key="test-key", base_url="https://ned.test", max_retries=0
    )

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler), settings) as client:
            await client.get_utilizations(make_query())

    with pytest.raises(NedApiError):
        asyncio.run(run())
    assert len(requests) == 1


def test_get_utilizations_sends_id_and_order_when_set() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=page_body(1))

    query = make_query()
    query = query.model_copy(update={"id": 42, "order_by_valid_from": "asc"})

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            await client.get_utilizations(query)

    asyncio.run(run())
    params = requests[0].url.params
    assert params["id"] == "42"
    assert params["order[validfrom]"] == "asc"


def test_get_utilizations_omits_id_and_order_by_default() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=page_body(1))

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            await client.get_utilizations(make_query())

    asyncio.run(run())
    params = requests[0].url.params
    assert "id" not in params
    assert "order[validfrom]" not in params


def test_get_utilization_fetches_single_record_by_id() -> None:
    async def run() -> Utilization:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/utilizations/7"
            return httpx.Response(200, json=NED_EXAMPLE_RECORD)

        async with make_client(httpx.MockTransport(handler)) as client:
            return await client.get_utilization(7)

    record = asyncio.run(run())
    assert record.id == NED_EXAMPLE_RECORD["id"]


def test_get_points_sends_filter_params() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"hydra:member": [], "hydra:totalItems": 0})

    query = PointQuery(name="Groningen", identifier=1, parent_points=0, child_points=20)

    async def run() -> None:
        async with make_client(httpx.MockTransport(handler)) as client:
            await client.get_points(query)

    asyncio.run(run())
    params = requests[0].url.params
    assert params["name"] == "Groningen"
    assert params["identifier"] == "1"
    assert params["parentpoints"] == "0"
    assert params["childpoints"] == "20"


SINGLE_RECORD_ENDPOINTS = [
    ("point", "points", POINT_RECORD),
    ("type", "types", {"id": 2, "identifier": 2, "name": "Solar", "nameshort": "ZON"}),
    ("activity", "activities", {"id": 1, "name": "Providing"}),
    ("classification", "classifications", {"id": 2, "name": "Current"}),
    ("granularity", "granularities", {"id": 5, "name": "Hour"}),
    ("granularity_time_zone", "granularity_time_zones", {"id": 1, "name": "CET"}),
]


@pytest.mark.parametrize(("name", "plural", "record"), SINGLE_RECORD_ENDPOINTS)
def test_get_by_id_fetches_single_record(name: str, plural: str, record: dict) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=record)

    async def run() -> _HasId:
        async with make_client(httpx.MockTransport(handler)) as client:
            return await getattr(client, f"get_{name}")(record["id"])

    result = asyncio.run(run())
    assert requests[0].url.path == f"/{plural}/{record['id']}"
    assert result.id == record["id"]


def test_context_manager_closes_http_client() -> None:
    async def run() -> NedClient:
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, json=page_body(0))
        )
        async with make_client(transport) as client:
            assert not client._http.is_closed
        return client

    assert asyncio.run(run())._http.is_closed
