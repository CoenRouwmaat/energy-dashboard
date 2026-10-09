# Dashboard

NiceGUI app on top of `NedClient`. Needs `NED_API_KEY` (see [ned_client.md](ned_client.md)).

```
uv run energy-dashboard-ui     # http://localhost:8080
```

## Renewables vs CO2 (`/`)

Hourly Dutch mix for a date range: stacked solar / onshore wind / offshore wind / other,
renewable share against CO2 intensity over time, and a share-vs-intensity scatter with a
least-squares trend and Pearson r. Share = (solar + wind + offshore wind) / `ELECTRICITY_MIX`;
CO2 comes from the mix's `emission` / `emission_factor`. Biomass, waste and hydro count as
"other", so the share is a lower bound.

## API explorer (`/explorer`)

Runs ad-hoc `/utilizations` queries from a form and shows a summary, a volume-over-time
chart and a sortable/filterable table. The chart is rendered twice, as Plotly and as
ECharts (NiceGUI built-in), in separate tabs so the two can be compared.

Layout: `dashboard/analysis.py` and `figures.py` (renewables maths and Plotly figures),
`renewables.py` (that view), `dashboard/data.py` (pure helpers, tested), `components.py` (table and charts),
`api_explorer.py` (form and results), `app.py` (routes), `__main__.py` (entry point).
