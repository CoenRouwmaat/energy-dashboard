# Future improvements

> **Revisit once the database is up and running.** Almost everything below needs long
> history or many series. Fetching that live would burn through NED's rate limit
> (200 requests per 5 minutes, 200 records per page). Build the ingestion layer first, then
> pick features from this list. Closed past periods never change, so only the newest slice
> needs re-fetching.

## Request budget (hourly data, per series)

| Granularity | Records/year | Requests/year |
|---|---|---|
| 10 min | 52,560 | 263 |
| 15 min | 35,040 | 176 |
| Hour | 8,760 | 44 |
| Day | 365 | 2 |
| Month | 12 | 1 |

A "series" is one point + type + activity + classification. Rough figures, not tested
against the live API: the four series the dashboard uses today cost ~176 requests per year
of hourly data; all national-level carriers ~1,300; adding provinces and wind farms runs
to tens of thousands.

## Ingestion and storage (prerequisite)

- Database (SQLite or DuckDB/parquet) keyed by point, type, activity, classification,
  granularity and `valid_from`.
- Incremental backfill: fetch only periods newer than the latest stored `last_update`.
- Re-fetch recent buckets, since NED revises `current` values and forecasts.
- Respect the rate limit with a queue; log gaps and failed pages.
- Dashboard views read from the database, not from `NedClient`.

## Features using NED data only

1. **Forecast vs actual error.** Compare `FORECAST` and `CURRENT` for solar, wind,
   offshore wind and load. MAE, bias, error by hour of day and by source. Needs 8 series.
2. **Residual load and ramps.** Load (`ELECTRICITY_LOAD`) minus solar and wind: duck curve,
   largest hourly ramps, hours that gas or imports must cover. Needs 4 series.
3. **Clean-hours profile.** Mean `emission_factor` by hour × weekday and hour × month as
   heatmaps, plus a "cleanest window today" read-out. Needs 1 series.
4. **Dunkelflaute detection.** Runs of consecutive hours with wind + solar below a
   threshold; duration and frequency. Needs long hourly history because events are rare.
5. **Capacity factor and buildout.** `percentage` per source, province and wind farm;
   installed `capacity` over time at month/year granularity.
6. **Net import dependence.** Import minus export against load; share of load covered by
   imports.
7. **Marginal emissions.** Regress `emission` on load or residual load, separating the
   average cost of a kWh from the next kWh. Addresses the arithmetic-correlation caveat in
   the renewables-vs-CO2 view.
8. **Diversification.** Correlation between wind farms and provinces to show how much
   geographic spread smooths output.
9. **Generation mix beyond renewables.** Nuclear, gas, coal, biomass and waste shares, with
   emissions per source and fuel-switching over time.
10. **Storage.** Charge/discharge (`STORAGE_IN`/`STORAGE_OUT`/`STORAGE`) patterns, if the
    data is populated.
11. **Gas side.** Gas mix and distribution volumes, seasonality, link to heating demand.

## Features needing external data

| Feature | Source | Notes |
|---|---|---|
| Explain solar/wind output; normalize capacity factors; power curves | Weather (KNMI, Open-Meteo): irradiance, hub-height wind speed | Turns forecast-error and capacity-factor views from descriptive to explanatory. |
| Explain load | Temperature (heating degree days) | Separates weather from calendar effects. |
| Price vs renewable share, negative-price hours, solar cannibalization, "cheap and clean" hours | Day-ahead prices (ENTSO-E, Energy-Charts) | Highest-value addition; NED has no prices. Add before weather. |
| Per-capita / per-area province comparison | CBS population and area | Only for province views. |
| Holiday and weekday effects | `holidays` package | Offline, no API. |
| Gas price context | TTF futures | Optional; ties to fossil dispatch. |

## Suggested order

1. Ingestion and storage.
2. Features 3, 2, 1 (cheapest and most useful once data is local).
3. Features 4 and 5 using the full history.
4. Prices, then weather, then the remaining features.
