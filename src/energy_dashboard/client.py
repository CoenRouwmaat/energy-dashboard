"""HTTP client for the NED (Nationaal Energie Dashboard) API."""

import asyncio
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

import httpx

from energy_dashboard.exceptions import NedApiError
from energy_dashboard.models import (
    ActivityRecord,
    ClassificationRecord,
    GranularityRecord,
    GranularityTimeZoneRecord,
    Page,
    PointRecord,
    TypeRecord,
    Utilization,
    UtilizationPage,
    UtilizationQuery,
)
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

    async def _get_page[T](
        self, path: str, page_model: type[Page[T]], page: int, items_per_page: int
    ) -> Page[T]:
        response = await self._get(path, {"page": page, "itemsPerPage": items_per_page})
        return page_model.model_validate(response.json())

    async def _iter_all[T](
        self, path: str, page_model: type[Page[T]], items_per_page: int
    ) -> AsyncIterator[T]:
        page = 1
        while True:
            result = await self._get_page(path, page_model, page, items_per_page)
            for item in result.items:
                yield item
            if len(result.items) < items_per_page:
                return
            page += 1

    async def get_points(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[PointRecord]:
        """Fetch a single page of points from `/points`."""
        return await self._get_page("/points", Page[PointRecord], page, items_per_page)

    def iter_points(self, items_per_page: int = 200) -> AsyncIterator[PointRecord]:
        """Fetch all pages of points from `/points`, in order."""
        return self._iter_all("/points", Page[PointRecord], items_per_page)

    async def get_types(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[TypeRecord]:
        """Fetch a single page of types from `/types`."""
        return await self._get_page("/types", Page[TypeRecord], page, items_per_page)

    def iter_types(self, items_per_page: int = 200) -> AsyncIterator[TypeRecord]:
        """Fetch all pages of types from `/types`, in order."""
        return self._iter_all("/types", Page[TypeRecord], items_per_page)

    async def get_activities(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[ActivityRecord]:
        """Fetch a single page of activities from `/activities`."""
        return await self._get_page(
            "/activities", Page[ActivityRecord], page, items_per_page
        )

    def iter_activities(
        self, items_per_page: int = 200
    ) -> AsyncIterator[ActivityRecord]:
        """Fetch all pages of activities from `/activities`, in order."""
        return self._iter_all("/activities", Page[ActivityRecord], items_per_page)

    async def get_classifications(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[ClassificationRecord]:
        """Fetch a single page of classifications from `/classifications`."""
        return await self._get_page(
            "/classifications", Page[ClassificationRecord], page, items_per_page
        )

    def iter_classifications(
        self, items_per_page: int = 200
    ) -> AsyncIterator[ClassificationRecord]:
        """Fetch all pages of classifications from `/classifications`, in order."""
        return self._iter_all(
            "/classifications", Page[ClassificationRecord], items_per_page
        )

    async def get_granularities(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[GranularityRecord]:
        """Fetch a single page of granularities from `/granularities`."""
        return await self._get_page(
            "/granularities", Page[GranularityRecord], page, items_per_page
        )

    def iter_granularities(
        self, items_per_page: int = 200
    ) -> AsyncIterator[GranularityRecord]:
        """Fetch all pages of granularities from `/granularities`, in order."""
        return self._iter_all("/granularities", Page[GranularityRecord], items_per_page)

    async def get_granularity_time_zones(
        self, page: int = 1, items_per_page: int = 200
    ) -> Page[GranularityTimeZoneRecord]:
        """Fetch a single page of granularity time zones from `/granularity_time_zones`."""
        return await self._get_page(
            "/granularity_time_zones",
            Page[GranularityTimeZoneRecord],
            page,
            items_per_page,
        )

    def iter_granularity_time_zones(
        self, items_per_page: int = 200
    ) -> AsyncIterator[GranularityTimeZoneRecord]:
        """Fetch all pages of granularity time zones from `/granularity_time_zones`, in order."""
        return self._iter_all(
            "/granularity_time_zones", Page[GranularityTimeZoneRecord], items_per_page
        )
