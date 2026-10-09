from nicegui import ui

from energy_dashboard.dashboard import app  # noqa: F401  (registers the pages)


def main() -> None:
    ui.run(title="Energy dashboard", reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
