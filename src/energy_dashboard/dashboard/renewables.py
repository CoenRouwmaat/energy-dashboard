"""Renewables vs CO2 view: hourly mix, renewable share and CO2 intensity."""

import asyncio
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
from energy_dashboard.dashboard.analysis import combine, fit_share_vs_factor, kpis
from energy_dashboard.dashboard.data import build_query
from energy_dashboard.dashboard.figures import (
    mix_figure,
    scatter_figure,
    share_figure,
)

INTRO = """
Hourly Dutch electricity, from NED. **Renewable** here means solar + onshore wind +
offshore wind; its **share** is that volume divided by the total electricity mix
(`ELECTRICITY_MIX`). **CO2 intensity** is NED's emission factor for the mix, in kg CO2
per kWh. Biomass, waste and hydro are counted in "other", so the share is a
*lower bound* on the true renewable share.
"""

SCATTER_NOTE = """
Each dot is one hour. A strongly **negative** correlation means hours with more wind and
sun are cleaner. Part of that is arithmetic rather than causation: the mix's CO2 comes
from fossil plants, so every extra renewable kWh lowers the average per kWh. It also
does not control for demand, imports or the order in which plants are dispatched.
"""


def _kpi(label: str, value: str, hint: str) -> None:
    with ui.card().classes("min-w-48 grow"):
        ui.label(label).classes("text-caption text-grey-7")
        ui.label(value).classes("text-h5")
        ui.label(hint).classes("text-caption text-grey-6")


async def _fetch(start: date, end: date):
    def query(kind: EnergyType):
        return build_query(
            point=Point.NETHERLANDS,
            type=kind,
            activity=Activity.PROVIDING,
            classification=Classification.CURRENT,
            granularity=Granularity.HOUR,
            start=start,
            end=end,
        )

    async def load(client: NedClient, kind: EnergyType):
        return [item async for item in client.iter_utilizations(query(kind))]

    async with NedClient() as client:
        return await asyncio.gather(
            load(client, EnergyType.SOLAR),
            load(client, EnergyType.WIND),
            load(client, EnergyType.WIND_OFFSHORE),
            load(client, EnergyType.ELECTRICITY_MIX),
        )


def renewables_view() -> None:
    """Build the view inside the current page."""
    ui.markdown(INTRO)
    today = datetime.now(UTC).date()
    with ui.row().classes("items-end"):
        start = ui.date_input("From", value=(today - timedelta(days=7)).isoformat())
        end = ui.date_input("To (exclusive)", value=today.isoformat())
        run = ui.button("Update", icon="refresh")
    results = ui.column().classes("w-full gap-4")

    async def update() -> None:
        run.props("loading")
        try:
            solar, wind, offshore, mix = await _fetch(
                date.fromisoformat(start.value), date.fromisoformat(end.value)
            )
        except (NedApiError, ValueError) as exc:
            ui.notify(f"Query failed: {exc}", type="negative")
            return
        finally:
            run.props(remove="loading")

        rows = combine(solar, wind, offshore, mix)
        results.clear()
        with results:
            if not rows:
                ui.label("No complete hours returned for this range.")
                return
            fit = fit_share_vs_factor(rows)
            stats = kpis(rows)
            with ui.row().classes("w-full"):
                _kpi("Renewable share", f"{stats['mean_share']:.0%}", "mean over hours")
                _kpi(
                    "CO2 intensity",
                    f"{stats['emission_factor'] * 1000:.0f} g/kWh",
                    "volume-weighted",
                )
                _kpi("Emissions", f"{stats['emissions_tonnes']:,.0f} t", "CO2 in range")
                _kpi(
                    "Correlation",
                    f"{fit.r:.2f}" if fit else "n/a",
                    "share vs intensity",
                )
            for title, figure in (
                ("Electricity mix", mix_figure(rows)),
                ("Renewable share and CO2 intensity", share_figure(rows)),
            ):
                with ui.card().classes("w-full"):
                    ui.label(title).classes("text-h6")
                    ui.plotly(figure).classes("w-full h-96")
            with ui.card().classes("w-full"):
                ui.label("Does more renewable power mean lower CO2?").classes("text-h6")
                ui.plotly(scatter_figure(rows, fit)).classes("w-full h-96")
                ui.markdown(SCATTER_NOTE)

    run.on_click(update)
    ui.timer(0.1, update, once=True)
