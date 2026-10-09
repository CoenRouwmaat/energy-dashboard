"""Plotly figures for the renewables-vs-CO2 view (no NiceGUI imports)."""

from collections.abc import Sequence

import plotly.graph_objects as go

from energy_dashboard.dashboard.analysis import Fit, HourlyMix

SOLAR, WIND, OFFSHORE, OTHER = "#f2b01e", "#3b82c4", "#1f9d8f", "#9aa3ad"
CO2 = "#d6453d"


def _style(fig: go.Figure, *, x_title: str | None, y_title: str) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        margin={"l": 60, "r": 20, "t": 20, "b": 50},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif", "size": 13},
        legend={"orientation": "h", "y": 1.12, "x": 0},
        hovermode="x unified",
        xaxis_title=x_title,
        yaxis_title=y_title,
    )
    return fig


def mix_figure(rows: Sequence[HourlyMix]) -> go.Figure:
    """Stacked area of solar, wind, offshore wind and the rest, in MWh per hour."""
    x = [row.start for row in rows]
    fig = go.Figure()
    for name, colour, values in (
        ("Solar", SOLAR, [row.solar_kwh for row in rows]),
        ("Wind (onshore)", WIND, [row.wind_kwh for row in rows]),
        ("Wind (offshore)", OFFSHORE, [row.offshore_wind_kwh for row in rows]),
        ("Other (mostly fossil)", OTHER, [row.other_kwh for row in rows]),
    ):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=[v / 1000 for v in values],
                name=name,
                stackgroup="mix",
                line={"width": 0.5, "color": colour},
                fillcolor=colour,
            )
        )
    return _style(fig, x_title=None, y_title="MWh per hour")


def share_figure(rows: Sequence[HourlyMix]) -> go.Figure:
    """Renewable share and emission factor over time on twin axes."""
    x = [row.start for row in rows]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=[row.renewable_share * 100 for row in rows],
            name="Renewable share (%)",
            line={"color": OFFSHORE, "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=[row.emission_factor for row in rows],
            name="CO2 intensity (kg/kWh)",
            line={"color": CO2, "width": 2},
            yaxis="y2",
        )
    )
    _style(fig, x_title=None, y_title="Renewable share (%)")
    fig.update_layout(
        yaxis2={"title": "kg CO2 per kWh", "overlaying": "y", "side": "right"}
    )
    return fig


def scatter_figure(rows: Sequence[HourlyMix], fit: Fit | None) -> go.Figure:
    """Hourly renewable share vs CO2 intensity, with the least-squares line."""
    x = [row.renewable_share * 100 for row in rows]
    y = [row.emission_factor for row in rows]
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="Hours",
            marker={"color": CO2, "opacity": 0.6, "size": 7},
            text=[row.start.strftime("%a %d %b %H:%M") for row in rows],
            hovertemplate="%{text}<br>%{x:.1f}% renewable<br>%{y:.3f} kg/kWh<extra></extra>",
        )
    )
    if fit is not None:
        x0, x1 = min(x), max(x)
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[
                    fit.intercept + fit.slope * x0 / 100,
                    fit.intercept + fit.slope * x1 / 100,
                ],
                mode="lines",
                name=f"Trend (r = {fit.r:.2f})",
                line={"color": "#333", "dash": "dash"},
            )
        )
    _style(fig, x_title="Renewable share (%)", y_title="kg CO2 per kWh")
    fig.update_layout(hovermode="closest")
    return fig
