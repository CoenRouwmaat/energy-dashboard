"""HTTP client for the NED (Nationaal Energie Dashboard) API."""

import asyncio
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

import httpx

from energy_dashboard.exceptions import NedApiError
from energy_dashboard.models import Utilization, UtilizationPage, UtilizationQuery
from energy_dashboard.settings import NedSettings

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class NedClient:
    """A small, typed client for the NED API.

    Usage:
        async with NedClient(NedSettings()) as client:
            page = await client.get_utilizations(query)
    """

    def __init__(self, settings: NedSettings | None = None) -> None:
        self._settings = settings or NedSettings()
        self._http = httpx.AsyncClient(
            base_url=str(self._settings.base_url),
            timeout=self._settings.timeout_seconds,
            headers={
                "X-AUTH-TOKEN": self._settings.api_key.get_secret_value(),
                "Accept": "application/ld+json",
            },
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.aclose()

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        """Seconds to wait before retry number `attempt` (0-based).

        Honours a numeric `Retry-After` header, else backs off exponentially.
        """
        retry_after = response.headers.get("Retry-After", "")
        if retry_after.isdecimal():
            return float(retry_after)
        return self._settings.retry_backoff_seconds * 2**attempt

    async def _get(self, path: str, params: dict[str, str | int]) -> httpx.Response:
        """GET `path`, retrying 429/5xx responses with backoff.

        Raises `NedApiError` for any error response still failing once
        `max_retries` retries are exhausted, or for non-retryable errors.
        """
        for attempt in range(self._settings.max_retries + 1):
            response = await self._http.get(path, params=params)
            if not response.is_error:
                return response
            if (
                response.status_code not in RETRYABLE_STATUS_CODES
                or attempt == self._settings.max_retries
            ):
                raise NedApiError(response.status_code, response.text)
            await asyncio.sleep(self._retry_delay(response, attempt))
        raise AssertionError("unreachable")  # pragma: no cover

    async def get_utilizations(self, query: UtilizationQuery) -> UtilizationPage:
        """Fetch a single page of utilization records matching `query`."""
        response = await self._get("/utilizations", query.to_params())
        return UtilizationPage.model_validate(response.json())

    async def iter_utilizations(
        self, query: UtilizationQuery
    ) -> AsyncIterator[Utilization]:
        """Fetch all pages of utilization records matching `query`, in order.

        NED caps `itemsPerPage` at 200; this walks `page` forward until a
        page comes back with fewer than `query.items_per_page` records.
        """
        page_query = query
        while True:
            page = await self.get_utilizations(page_query)
            for item in page.items:
                yield item
            if len(page.items) < page_query.items_per_page:
                return
            page_query = page_query.model_copy(update={"page": page_query.page + 1})
