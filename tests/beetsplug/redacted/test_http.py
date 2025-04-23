# type: ignore
"""Tests for the HTTP client."""

import tempfile
from unittest.mock import patch

import pytest
import requests

from beetsplug.redacted.exceptions import RedactedError, RedactedRateLimitError
from beetsplug.redacted.http import CachedRequestsClient, HTTPClient, RequestsClient
from beetsplug.redacted.utils.test_utils import FakeLogger


@pytest.fixture
def log():
    """Create a fake logger."""
    return FakeLogger()


def test_abstract_base_class():
    """Test that HTTPClient is an abstract base class."""
    with pytest.raises(TypeError):
        HTTPClient()  # type: ignore


def test_requests_client_get_success(log: FakeLogger):
    """Test successful GET request."""
    client = RequestsClient("https://redacted.ch/api", log)
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response._content = b'{"test": "data"}'
    mock_response.headers["content-type"] = "application/json"

    with patch("requests.Session.get", return_value=mock_response):
        response = client.get({"param": "value"}, {"header": "value"})
        assert response.status_code == 200
        assert response.json() == {"test": "data"}


def test_requests_client_get_rate_limit(log: FakeLogger):
    """Test rate limited GET request."""
    client = RequestsClient("https://redacted.ch/api", log)
    mock_response = requests.Response()
    mock_response.status_code = 429
    mock_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("requests.Session.get", side_effect=mock_error):
        with pytest.raises(RedactedRateLimitError, match="Rate limit exceeded"):
            client._get({"param": "value"}, {"header": "value"})


def test_requests_client_get_http_error(log: FakeLogger):
    """Test HTTP error in GET request."""
    client = RequestsClient("https://redacted.ch/api", log)
    mock_response = requests.Response()
    mock_response.status_code = 500
    mock_error = requests.exceptions.HTTPError(response=mock_response)

    with patch("requests.Session.get", side_effect=mock_error):
        with pytest.raises(RedactedError, match="HTTP error"):
            client._get({"param": "value"}, {"header": "value"})


def test_cached_client_basic_functionality(log: FakeLogger):
    """Test basic functionality of the cached client."""
    # Get a temporary directory for the test
    with tempfile.TemporaryDirectory(prefix="redacted_test_cache") as temp_dir:
        # Set up mock response
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"test": "data"}'
        mock_response.headers["content-type"] = "application/json"

        with patch("requests.Session.get", return_value=mock_response):
            client = CachedRequestsClient("https://redacted.ch/api", log, cache_dir=temp_dir)
            params = {"test": "value"}
            headers = {"Authorization": "test"}

            # First request should work
            response1 = client.get(params, headers)
            assert response1.status_code == mock_response.status_code
            assert response1.content == mock_response.content

            # Second request should also work (whether from cache or not)
            response2 = client.get(params, headers)
            assert response2.status_code == mock_response.status_code
            assert response2.content == mock_response.content

            # Make sure to close the cache connection before the temporary directory is cleaned up
            client.cache.close()
