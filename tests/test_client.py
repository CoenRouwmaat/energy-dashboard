import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from energy_dashboard import (
    Activity,
    Classification,
    EnergyType,
    Granularity,
    NedApiError,
    NedClient,
    NedSettings,
    Point,
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


def make_client(handler: httpx.MockTransport) -> NedClient:
    client = NedClient(NedSettings(api_key="test-key"))
    client._http = httpx.AsyncClient(base_url="https://ned.test", transport=handler)
    return client


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
