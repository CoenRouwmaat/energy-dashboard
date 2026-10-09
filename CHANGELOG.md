# Changelog

<!-- git-cliff: end of header -->

## [0.3.0] - 2026-10-09

`NedClient` now retries failed requests and covers NED's reference data endpoints.

### 🚀 Features

- *(ned)* Requests that fail with 429, 500, 502, 503 or 504 are retried with exponential backoff, honouring the `Retry-After` header. Tune it with `NED_MAX_RETRIES` (default 3) and `NED_RETRY_BACKOFF_SECONDS` (default 1.0); `NedApiError` is raised once retries run out.
- *(ned)* New `get_*` / `iter_*` methods for the `/points`, `/types`, `/activities`, `/classifications`, `/granularities` and `/granularity_time_zones` endpoints, returning typed records such as `PointRecord`.

### 🚜 Refactor

- *(ned)* `NedClient` accepts an optional HTTP transport, and list endpoints share their pagination parameters.

### 📚 Documentation

- The NED client guide documents the reference data endpoints, retries and rate limits.

### 🧪 Testing

- Added tests for retries and backoff, the reference data endpoints, request setup and error handling.

### ⚙️ Miscellaneous Tasks

- Added `/commit` and `/start-issues` skills with a guard hook for atomic commits, and the release skill now asks for approvals with `AskUserQuestion`.

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
