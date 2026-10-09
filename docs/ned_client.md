# NED API client

Thin wrapper around the [NED (Nationaal Energie Dashboard) API](https://ned.nl/nl/api).

## Setup

1. Request an API key from NED and copy `.env.example` to `.env`, filling in `NED_API_KEY`.
2. Install dependencies: `uv sync`.

## Usage

```python
from datetime import datetime

from energy_dashboard import NedClient, UtilizationQuery
from energy_dashboard.enums import Activity, Classification, Granularity

query = UtilizationQuery(
    point=0,  # Netherlands — see NED docs for regional codes
    type=2,  # energy carrier code — see NED docs
    activity=Activity.PRODUCTION,
    classification=Classification.CURRENT,
    granularity=Granularity.DAY,
    valid_from=datetime(2026, 1, 1),
    valid_to=datetime(2026, 1, 8),
)

with NedClient() as client:
    page = client.get_utilizations(query)
    print(page.total_items, len(page.items))
```

`NedSettings` loads `NED_API_KEY` (and optional `NED_BASE_URL` / `NED_TIMEOUT_SECONDS`)
from the environment or `.env` automatically.

The `point` and `type` codes are NED-defined integers (region and energy-carrier
codes) that aren't enumerated here — look them up in the NED API documentation.
