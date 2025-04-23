"""HTTP client implementation for Redacted API."""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Union

import requests
from backoff import expo, full_jitter, on_exception
from diskcache import Cache  # type: ignore[import-untyped]
from ratelimit import RateLimitException, limits, sleep_and_retry  # type: ignore[import-untyped]

from .exceptions import RedactedError, RedactedRateLimitError

# Constants for rate limiting. Redacted requires at most 0.5 qps.
PERIOD_SECONDS = 10
CALLS_PER_PERIOD = 5

# Cache configuration
CACHE_DIR = "/tmp/redacted"
CACHE_EXPIRY = timedelta(days=7)


class HTTPClient(ABC):
    """Abstract base class for HTTP clients."""

    @abstractmethod
    def get(self, params: dict[str, str], headers: dict[str, str]) -> requests.Response:
        """Make a GET request.

        Args:
            params: Query parameters.
            headers: Request headers.

        Returns:
            Response object.
        """
        pass


class RequestsClient(HTTPClient):
    """HTTP client implementation using requests library."""

    def __init__(self, url: str, log: logging.Logger) -> None:
        """Initialize the client.

        Args:
            url: URL for API requests.
            log: Logger instance for logging messages.
        """
        self.url = url
        self.log = log
        self.session = requests.Session()

    def _get(self, params: dict[str, str], headers: dict[str, str]) -> requests.Response:
        """Make a GET request without rate limiting or retries.

        Args:
            params: Query parameters.
            headers: Request headers.

        Returns:
            Response object.

        Raises:
            RedactedError: If the request fails.
            RedactedRateLimitError: If rate limited by the Redacted API.
        """
        self.log.debug("Making GET request to {0}: {1}", self.url, params)
        try:
            response = self.session.get(self.url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.log.debug("Redacted rate limit exceeded response: %s", e.response.text)
                raise RedactedRateLimitError("Rate limit exceeded") from e

            self.log.debug("Redacted API error response: %s", e.response.text)
            raise RedactedError(f"HTTP error: {e}") from e
        except requests.exceptions.RequestException as e:
            self.log.debug("Redacted request error: %s", e)
            raise RedactedError(f"Request error: {e}") from e

    @sleep_and_retry  # type: ignore[misc]
    @limits(calls=CALLS_PER_PERIOD, period=PERIOD_SECONDS)  # type: ignore[misc]
    @on_exception(
        expo,
        (RedactedError, RedactedRateLimitError, RateLimitException),
        max_tries=8,
        jitter=full_jitter,
    )
    def get(self, params: dict[str, str], headers: dict[str, str]) -> requests.Response:
        """Make a GET request with rate limiting and retries.

        Args:
            params: Query parameters.
            headers: Request headers.

        Returns:
            Response object.

        Raises:
            RedactedError: If the request fails.
            RedactedRateLimitError: If rate limited by the Redacted API.
            RateLimitException: If rate limited by the ratelimit library.
        """
        return self._get(params, headers)


class CachedRequestsClient(RequestsClient):
    """HTTP client implementation with disk caching."""

    def __init__(self, url: str, log: logging.Logger, cache_dir: str = CACHE_DIR) -> None:
        """Initialize the client.

        Args:
            url: URL for API requests.
            log: Logger instance for logging messages.
            cache_dir: Directory to store cache files. Defaults to CACHE_DIR.
        """
        super().__init__(url, log)
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = Cache(cache_dir)
        self.cache_dir = cache_dir

    def close(self) -> None:
        """Close the cache connection."""
        self.log.debug("Closing cache connection")
        self.cache.close()

    def _get_cached_response(
        self, params: dict[str, str], headers: dict[str, str]
    ) -> Union[requests.Response, None]:
        """Get a cached response if available and not expired.

        Args:
            params: Query parameters.
            headers: Request headers.

        Returns:
            Cached response if available and valid, None otherwise.
        """
        cache_key = f"{self.url}:{params!s}:{headers!s}"
        cached_data = self.cache.get(cache_key)
        if not cached_data:
            return None

        timestamp, response_data = cached_data
        if datetime.fromtimestamp(timestamp) + CACHE_EXPIRY < datetime.now():
            return None

        response = requests.Response()
        response.status_code = response_data["status_code"]
        response.headers = response_data["headers"]
        response._content = response_data["content"]
        return response

    def _cache_response(
        self, params: dict[str, str], headers: dict[str, str], response: requests.Response
    ) -> None:
        """Cache a response.

        Args:
            params: Query parameters.
            headers: Request headers.
            response: Response to cache.
        """
        cache_key = f"{self.url}:{params!s}:{headers!s}"
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.content,
        }
        self.cache.set(cache_key, (datetime.now().timestamp(), response_data))

    def get(self, params: dict[str, str], headers: dict[str, str]) -> requests.Response:
        """Make a GET request with caching, rate limiting and retries.

        Args:
            params: Query parameters.
            headers: Request headers.

        Returns:
            Response object.

        Raises:
            RedactedError: If the request fails.
            RedactedRateLimitError: If rate limited by the Redacted API.
            RateLimitException: If rate limited by the ratelimit library.
        """
        # Check cache first
        cached_response = self._get_cached_response(params, headers)
        if cached_response:
            return cached_response

        # If not in cache, make the request
        response: requests.Response = super().get(params, headers)
        self._cache_response(params, headers, response)
        return response
