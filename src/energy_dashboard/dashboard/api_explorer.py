"""Ad-hoc `NedClient` utilization queries: form -> summary, chart(s) and table."""

from datetime import UTC, date, datetime, timedelta

from nicegui import ui

from energy_dashboard import (
    Activity,
    Classification,
    EnergyType,
    Granularity,
    NedApiError,
    NedClient,
    Point,
)
from energy_dashboard.dashboard.components import (
    echart_chart,
    plotly_chart,
    results_table,
)
from energy_dashboard.dashboard.data import build_query, enum_options, summary

HELP = """
### How to use
Pick a **point** (region), **type** (energy carrier), **activity**, **classification**
(forecast or current) and **granularity**, then a date range. The end date is exclusive.

- **Volume** is the energy produced/consumed in the bucket; **capacity** the installed
  maximum; **utilization %** is volume / capacity.
- Day, month and year granularities are only available for CET bucketing, which the
  explorer always uses.
- NED allows 200 requests per 5 minutes; *Load all pages* issues one request per page.
"""


def explorer() -> None:
    """Build the explorer UI inside the current page."""
    with ui.card().classes("w-full"):
        with ui.row().classes("w-full items-end"):
            point = ui.select(
                enum_options(Point), value=Point.NETHERLANDS, label="Point"
            )
            kind = ui.select(
                enum_options(EnergyType), value=EnergyType.SOLAR, label="Type"
            )
            activity = ui.select(
                enum_options(Activity), value=Activity.PROVIDING, label="Activity"
            )
            classification = ui.select(
                enum_options(Classification),
                value=Classification.CURRENT,
                label="Classification",
            )
            granularity = ui.select(
                enum_options(Granularity), value=Granularity.DAY, label="Granularity"
            )
        with ui.row().classes("w-full items-end"):
            today = datetime.now(UTC).date()
            start = ui.date_input("From", value=(today - timedelta(days=7)).isoformat())
            end = ui.date_input("To (exclusive)", value=today.isoformat())
            order = ui.select(
                {"asc": "Oldest first", "desc": "Newest first"}, value="asc"
            )
            load_all = ui.switch("Load all pages")
            run = ui.button("Run query", icon="play_arrow")

    results = ui.column().classes("w-full")

    async def run_query() -> None:
        run.props("loading")
        try:
            query = build_query(
                point=point.value,
                type=kind.value,
                activity=activity.value,
                classification=classification.value,
                granularity=granularity.value,
                start=date.fromisoformat(start.value),
                end=date.fromisoformat(end.value),
                order=order.value,
            )
            async with NedClient() as client:
                if load_all.value:
                    items = [item async for item in client.iter_utilizations(query)]
                    total = len(items)
                else:
                    page = await client.get_utilizations(query)
                    items, total = page.items, page.total_items
        except (NedApiError, ValueError) as exc:
            ui.notify(f"Query failed: {exc}", type="negative")
            return
        finally:
            run.props(remove="loading")

        results.clear()
        with results:
            ui.markdown(summary(items, total))
            if not items:
                return
            with ui.tabs().classes("w-full") as tabs:
                plotly_tab = ui.tab("Plotly")
                echart_tab = ui.tab("ECharts")
                table_tab = ui.tab("Table")
            with ui.tab_panels(tabs, value=plotly_tab).classes("w-full"):
                with ui.tab_panel(plotly_tab):
                    plotly_chart(items)
                with ui.tab_panel(echart_tab):
                    echart_chart(items)
                with ui.tab_panel(table_tab):
                    results_table(items)

    run.on_click(run_query)
    ui.markdown(HELP)
