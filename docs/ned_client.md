# NED API client

Thin wrapper around the [NED (Nationaal Energie Dashboard) API](https://ned.nl/nl/api).

## Setup

1. Request an API key from NED and copy `.env.example` to `.env`, filling in `NED_API_KEY`.
2. Install dependencies: `uv sync`.

## Usage

```python
from datetime import UTC, datetime

from energy_dashboard import (
    Activity,
    Classification,
    EnergyType,
    Granularity,
    NedClient,
    Point,
    UtilizationQuery,
)

query = UtilizationQuery(
    point=Point.NETHERLANDS,
    type=EnergyType.SOLAR,
    activity=Activity.PROVIDING,
    classification=Classification.CURRENT,
    granularity=Granularity.DAY,
    valid_from=datetime(2026, 1, 1, tzinfo=UTC),
    valid_to=datetime(2026, 1, 8, tzinfo=UTC),
)

async with NedClient() as client:
    page = await client.get_utilizations(query)
    print(page.total_items, len(page.items))
```

`NedClient` is async (built on `httpx.AsyncClient`): use `async with`, `await`
the request methods, and consume `iter_utilizations` with `async for`.

`NedSettings` loads `NED_API_KEY` (and optional `NED_BASE_URL` / `NED_TIMEOUT_SECONDS`)
from the environment or `.env` automatically.

`point` and `type` are NED-defined integer codes for regions and energy carriers,
enumerated in `energy_dashboard.enums.Point` and `energy_dashboard.enums.EnergyType`.

## Reference data

Besides utilizations, the client covers NED's reference endpoints. Each has a
`get_*` method returning one `Page` and an `iter_*` async iterator over all pages
(`items_per_page` defaults to 200, NED's maximum):

| Endpoint | Methods | Record model |
|---|---|---|
| `/points` | `get_points` / `iter_points` | `PointRecord` |
| `/types` | `get_types` / `iter_types` | `TypeRecord` |
| `/activities` | `get_activities` / `iter_activities` | `ActivityRecord` |
| `/classifications` | `get_classifications` / `iter_classifications` | `ClassificationRecord` |
| `/granularities` | `get_granularities` / `iter_granularities` | `GranularityRecord` |
| `/granularity_time_zones` | `get_granularity_time_zones` / `iter_granularity_time_zones` | `GranularityTimeZoneRecord` |

```python
async with NedClient() as client:
    async for point in client.iter_points():
        print(point.id, point.name)
```

`PointRecord.child_points` and `parent_points` are parsed from NED's IRI references
down to point ids. Filtering and the `/{id}` endpoints are not covered yet.

## Retries and rate limits

NED allows 200 requests per 5 minutes. Responses with status 429, 500, 502, 503 or 504
are retried up to `NED_MAX_RETRIES` times (default 3), waiting for the `Retry-After`
header if present and otherwise `NED_RETRY_BACKOFF_SECONDS` (default 1.0) doubled on
each attempt. Once retries run out, or for any other error status, `NedApiError` is raised.
