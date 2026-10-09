"""Page routes and shared layout."""

from contextlib import contextmanager

from nicegui import ui

from energy_dashboard.dashboard.api_explorer import explorer
from energy_dashboard.dashboard.renewables import renewables_view


@contextmanager
def layout(title: str):
    ui.colors(primary="#1f9d8f")
    with ui.header().classes("items-center gap-6"):
        ui.label("Energy dashboard").classes("text-h6")
        ui.link("Renewables vs CO2", "/").classes("text-white")
        ui.link("API explorer", "/explorer").classes("text-white")
    with ui.column().classes("w-full max-w-5xl mx-auto"):
        ui.label(title).classes("text-h5")
        yield


@ui.page("/")
def index() -> None:
    with layout("Renewables vs CO2"):
        renewables_view()


@ui.page("/explorer")
def api_explorer() -> None:
    with layout("NED API explorer"):
        explorer()
