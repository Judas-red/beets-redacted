"""
Main client class for interacting with Redacted.
"""

import logging
from typing import Any

from pydantic import ValidationError

from .exceptions import RedactedError
from .http import HTTPClient
from .types import RedAction, RedArtistResponse, RedSearchResponse


class RedactedClient:
    """Client for interacting with the Redacted private tracker."""

    def __init__(self, api_key: str, http_client: HTTPClient, log: logging.Logger) -> None:
        """Initialize the client.

        Args:
            api_key: API key for authentication.
            http_client: HTTP client implementation.
            log: Logger instance for logging messages.
        """
        self.log = log
        self.log.debug("Initializing RedactedClient")

        self.api_key = api_key
        self.http_client = http_client

    def _make_api_request(self, action: RedAction, params: dict[str, str]) -> dict[str, Any]:
        """Make an API request to Redacted.

        Args:
            action: The API action to perform.
            **params: Additional parameters for the request.

        Returns:
            The API response data.

        Raises:
            RedactedError: If the request fails.
            RedactedRateLimitError: If rate limited by the Redacted API.
        """
        api_params: dict[str, str] = {"action": action.value, **params}
        headers: dict[str, str] = {"Authorization": self.api_key}

        response = self.http_client.get(params=api_params, headers=headers)
        try:
            data: dict[str, Any] = response.json()
        except ValueError as e:
            self.log.debug(
                "Invalid JSON response from API: {0}\n\t{1}", str(e), str(response.content)
            )
            raise RedactedError("Invalid JSON response from API") from e

        if data.get("status") != "success":
            raise RedactedError(f"API error: {data.get('error', 'Unknown error')}")

        return data

    def browse(self, query: str) -> RedSearchResponse:
        """Search for torrents on Redacted.

        Args:
            query: Search query string. Can be a general search term, an artist name,
                  or in the format "Artist - Album" for specific album searches.

        Returns:
            Search results.

        Raises:
            RedactedError: If the response is not in the expected format or indicates failure.
        """
        response = self._make_api_request(RedAction.BROWSE, {"searchstr": query})
        try:
            return RedSearchResponse(**response)
        except ValidationError as e:
            import json

            self.log.debug(
                "Couldn't parse RedactedSearchResponse from:\n%s", json.dumps(response, indent=2)
            )
            raise RedactedError(f"Invalid response format: {e}") from e

    def get_artist(self, artist_id: int) -> RedArtistResponse:
        """Get detailed information about an artist by ID.

        Args:
            artist_id: The artist ID to look up.

        Returns:
            Detailed artist information including releases and statistics.

        Raises:
            RedactedError: If the response is not in the expected format or indicates failure.
        """
        response = self._make_api_request(RedAction.ARTIST, {"id": str(artist_id)})

        if response["status"] == "failure":
            raise RedactedError(f"API error: {response.get('error', 'Unknown error')}")

        try:
            return RedArtistResponse(**response)
        except ValidationError as e:
            import json

            self.log.debug(
                "Couldn't parse RedactedArtistResponse from:\n%s", json.dumps(response, indent=2)
            )
            raise RedactedError(f"Invalid response format: {e}") from e
