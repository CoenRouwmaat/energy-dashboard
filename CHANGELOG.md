# Changelog

<!-- git-cliff: end of header -->

## [0.2.0] - 2026-10-09

`NedClient` is now async, and the repository gained release and changelog tooling.

### ⚠️ Breaking changes

- *(ned)* `NedClient` is built on `httpx.AsyncClient`. Use `async with NedClient() as client`, `await client.get_utilizations(query)` and `async for item in client.iter_utilizations(query)`; `close()` is now a coroutine too. Synchronous `with` blocks and plain calls no longer work, so wrap existing code in an event loop (e.g. `asyncio.run`).

### 📚 Documentation

- README and the NED client guide show the async usage, with timezone-aware datetimes in the examples; a stale example was fixed
- Added `CLAUDE.md` with the project conventions, including the release workflow

### ⚙️ Miscellaneous Tasks

- Added `prek` hooks (ruff, ty), `git-cliff` changelog configuration and a `/release` skill with guard scripts
- Applied `ruff format` to the models

## [0.1.0] - 2026-10-09

Initial release: a typed Python client for the [NED (Nationaal Energie Dashboard) API](https://ned.nl/nl/handleiding-api).

### 🚀 Features

- *(ned)* `NedClient` for fetching historical, current, and forecast energy utilization data, with automatic pagination (`iter_utilizations`) and NED-specific error handling (`NedApiError`)
- *(ned)* Pydantic models (`UtilizationQuery`, `Utilization`, `UtilizationPage`) for building type-safe queries and parsing NED's JSON-LD/Hydra responses, including automatic resolution of NED's IRI references (e.g. `/v1/points/0`) to plain integer codes
- *(ned)* `NedSettings` for loading the NED API key and client config from the environment or a `.env` file, plus enums (`Point`, `EnergyType`, `Activity`, `Classification`, `Granularity`, `GranularityTimeZone`) covering NED's documented parameter codes

### 📚 Documentation

- *(ned)* Usage guide and a runnable example notebook demonstrating single-page and fully-paginated fetches

### 🧪 Testing

- *(ned)* Unit tests covering query-parameter building and response parsing, using NED's own worked example as a fixture

### ⚙️ Miscellaneous Tasks

- Project scaffolded with `uv`, targeting Python 3.14
