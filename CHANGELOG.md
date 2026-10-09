# Changelog

<!-- git-cliff: end of header -->

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
