# energy-dashboard

A Python toolkit for fetching and working with Dutch energy data from the
[NED (Nationaal Energie Dashboard) API](https://ned.nl/nl/handleiding-api).

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- A NED API key (create one in your [ned.nl](https://ned.nl) account)

## Setup

```bash
uv sync
cp .env.example .env
```

Fill in `NED_API_KEY` in `.env`.

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

See [docs/ned_client.md](docs/ned_client.md) for a full usage guide and
[notebooks/test_ned_client.ipynb](notebooks/test_ned_client.ipynb) for a runnable example.

## Project layout

```
src/energy_dashboard/   # NED API client: settings, enums, models, client
tests/                  # unit tests
docs/                   # usage guides and future improvements
notebooks/              # runnable examples
```

## Development

```bash
uv run pytest      # run tests
uv run ruff check   # lint
uv run ty check     # type-check
```
