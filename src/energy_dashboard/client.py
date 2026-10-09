"""HTTP client for the NED (Nationaal Energie Dashboard) API."""

from collections.abc import Iterator
from types import TracebackType
from typing import Self

import httpx

from energy_dashboard.exceptions import NedApiError
from energy_dashboard.models import Utilization, UtilizationPage, UtilizationQuery
from energy_dashboard.settings import NedSettings


class NedClient:
    """A small, typed client for the NED API.

    Usage:
        with NedClient(NedSettings()) as client:
            page = client.get_utilizations(query)
    """

    def __init__(self, settings: NedSettings | None = None) -> None:
        self._settings = settings or NedSettings()
        self._http = httpx.Client(
            base_url=str(self._settings.base_url),
            timeout=self._settings.timeout_seconds,
            headers={
                "X-AUTH-TOKEN": self._settings.api_key.get_secret_value(),
                "Accept": "application/ld+json",
            },
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def get_utilizations(self, query: UtilizationQuery) -> UtilizationPage:
        """Fetch a single page of utilization records matching `query`."""
        response = self._http.get("/utilizations", params=query.to_params())
        if response.is_error:
            raise NedApiError(response.status_code, response.text)
        return UtilizationPage.model_validate(response.json())

    def iter_utilizations(self, query: UtilizationQuery) -> Iterator[Utilization]:
        """Fetch all pages of utilization records matching `query`, in order.

        NED caps `itemsPerPage` at 200; this walks `page` forward until a
        page comes back with fewer than `query.items_per_page` records.
        """
        page_query = query
        while True:
            page = self.get_utilizations(page_query)
            yield from page.items
            if len(page.items) < page_query.items_per_page:
                return
            page_query = page_query.model_copy(update={"page": page_query.page + 1})
