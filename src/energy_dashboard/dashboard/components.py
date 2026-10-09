"""Reusable NiceGUI pieces: results table plus two interchangeable chart backends."""

from collections.abc import Sequence

import plotly.graph_objects as go
from nicegui import ui

from energy_dashboard import Utilization
from energy_dashboard.dashboard.data import series, utilization_rows

_COLUMNS = [
    {"field": "valid_from", "headerName": "Valid from", "filter": True},
    {"field": "valid_to", "headerName": "Valid to"},
    {"field": "volume", "headerName": "Volume", "filter": "agNumberColumnFilter"},
    {"field": "capacity", "headerName": "Capacity", "filter": "agNumberColumnFilter"},
    {"field": "percentage", "headerName": "Utilization %"},
    {"field": "emission", "headerName": "Emission"},
    {"field": "id", "headerName": "ID"},
]


def results_table(items: Sequence[Utilization]) -> ui.aggrid:
    """Sortable, filterable AG Grid of the records."""
    return ui.aggrid(
        {
            "columnDefs": _COLUMNS,
            "rowData": utilization_rows(items),
            "defaultColDef": {"sortable": True, "resizable": True},
        }
    ).classes("w-full h-96")


def plotly_chart(items: Sequence[Utilization]) -> ui.plotly:
    """Volume over time as a Plotly line chart."""
    x, y = series(items)
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers", name="Volume"))
    fig.update_layout(
        margin={"l": 40, "r": 10, "t": 10, "b": 40},
        xaxis_title="Valid from",
        yaxis_title="Volume",
    )
    return ui.plotly(fig).classes("w-full h-96")


def echart_chart(items: Sequence[Utilization]) -> ui.echart:
    """Volume over time as an ECharts line chart (NiceGUI built-in)."""
    x, y = series(items)
    return ui.echart(
        {
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 60, "right": 20, "top": 20, "bottom": 60},
            "xAxis": {"type": "category", "data": x, "name": "Valid from"},
            "yAxis": {"type": "value", "name": "Volume"},
            "dataZoom": [{"type": "inside"}, {"type": "slider"}],
            "series": [
                {"type": "line", "name": "Volume", "data": y, "showSymbol": False}
            ],
        }
    ).classes("w-full h-96")
