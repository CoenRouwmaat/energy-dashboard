"""Exceptions raised by the NED API client."""


class NedApiError(Exception):
    """Raised when the NED API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"NED API error ({status_code}): {message}")
