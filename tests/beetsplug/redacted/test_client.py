# type: ignore
"""Tests for the Redacted API client."""

from collections.abc import Generator

import pytest

from beetsplug.redacted.client import Client
from beetsplug.redacted.exceptions import RedactedError
from beetsplug.redacted.types import RedAction
from beetsplug.redacted.utils.test_utils import FakeHTTPClient, FakeLogger


@pytest.fixture
def log():
    """Create a fake logger."""
    return FakeLogger()


@pytest.fixture
def client(log: FakeLogger) -> Generator[Client, None, None]:
    """Create a test client.

    Args:
        log: Fake logger instance.

    Yields:
        A RedactedClient instance configured for testing.
    """
    yield Client(api_key="test_key", http_client=FakeHTTPClient(), log=log)


def test_make_api_request_success(client: Client) -> None:
    """Test making a successful API request."""
    assert isinstance(client.http_client, FakeHTTPClient)
    client.http_client.add(
        params={"action": "browse"},
        headers={"Authorization": "test_key"},
        response={"status": "success", "response": {"test": "data"}},
    )

    response = client._make_api_request(RedAction.BROWSE, {})
    assert response == {"status": "success", "response": {"test": "data"}}


def test_make_api_request_rate_limit(client: Client) -> None:
    """Test making an API request that hits rate limit."""
    assert isinstance(client.http_client, FakeHTTPClient)
    client.http_client.add(
        params={"action": "browse"},
        headers={"Authorization": "test_key"},
        response={"status": "error", "error": "Rate limit exceeded"},
        status_code=429,
    )

    with pytest.raises(RedactedError):
        client._make_api_request(RedAction.BROWSE, {})


def test_make_api_request_json_parse_error(client: Client) -> None:
    """Test making an API request with invalid JSON response."""
    assert isinstance(client.http_client, FakeHTTPClient)
    client.http_client.add(
        params={"action": "browse"},
        headers={"Authorization": "test_key"},
        response={"invalid": "json"},
    )

    with pytest.raises(RedactedError):
        client._make_api_request(RedAction.BROWSE, {})


def test_browse(client: Client) -> None:
    """Test browsing torrents."""
    assert isinstance(client.http_client, FakeHTTPClient)
    mock_response = {
        "status": "success",
        "response": {
            "results": [
                {
                    "groupId": 410618,
                    "groupName": "Test Album",
                    "artist": "Test Artist",
                    "tags": ["drum.and.bass", "electronic"],
                    "bookmarked": False,
                    "vanityHouse": False,
                    "groupYear": 2009,
                    "releaseType": "Single",
                    "groupTime": 1339117820,
                    "maxSize": 237970,
                    "totalSnatched": 318,
                    "totalSeeders": 14,
                    "totalLeechers": 0,
                    "torrents": [
                        {
                            "torrentId": 959473,
                            "editionId": 1,
                            "artists": [{"id": 1460, "name": "Test Artist", "aliasid": 1460}],
                            "remastered": False,
                            "remasterYear": 0,
                            "remasterCatalogueNumber": "",
                            "remasterTitle": "",
                            "media": "CD",
                            "encoding": "Lossless",
                            "format": "FLAC",
                            "hasLog": False,
                            "logScore": 79,
                            "hasCue": False,
                            "scene": False,
                            "vanityHouse": False,
                            "fileCount": 3,
                            "time": "2009-06-06 19:04:22",
                            "size": 243680994,
                            "snatches": 10,
                            "seeders": 3,
                            "leechers": 0,
                            "isFreeleech": False,
                            "isNeutralLeech": False,
                            "isFreeload": False,
                            "isPersonalFreeleech": False,
                            "trumpable": False,
                            "canUseToken": True,
                        }
                    ],
                }
            ]
        },
    }
    client.http_client.add(
        params={"action": "browse", "searchstr": "test query"},
        headers={"Authorization": "test_key"},
        response=mock_response,
    )

    response = client.search("test query")
    assert response.status == "success"
    assert len(response.response.results) == 1
    result = response.response.results[0]
    assert result.groupId == 410618
    assert result.groupName == "Test Album"
    assert result.artist == "Test Artist"
    assert len(result.torrents) == 1
    torrent = result.torrents[0]
    assert torrent.torrentId == 959473
    assert torrent.media == "CD"
    assert torrent.format == "FLAC"


def test_browse_validation_error(client: Client) -> None:
    """Test handling validation errors when browsing torrents."""
    assert isinstance(client.http_client, FakeHTTPClient)
    # Missing required fields in the response
    mock_response = {
        "status": "success",
        "response": {
            "results": [
                {
                    # Missing required groupId field
                    "groupName": "Test Album",
                    "artist": "Test Artist",
                    "torrents": [
                        {
                            # Missing required torrentId
                            "media": "CD",
                            "format": "FLAC",
                        }
                    ],
                }
            ]
        },
    }
    client.http_client.add(
        params={"action": "browse", "searchstr": "test query"},
        headers={"Authorization": "test_key"},
        response=mock_response,
    )

    with pytest.raises(RedactedError) as excinfo:
        client.search("test query")
    assert "Invalid response format" in str(excinfo.value)


def test_get_artist(client: Client) -> None:
    """Test getting artist details by ID."""
    assert isinstance(client.http_client, FakeHTTPClient)
    mock_response = {
        "status": "success",
        "response": {
            "id": 1460,
            "name": "Test Artist",
            "notificationsEnabled": False,
            "hasBookmarked": False,
            "image": "https://example.com/artist.jpg",
            "body": "Artist biography text",
            "vanityHouse": False,
            "tags": [{"name": "electronic", "count": 15}, {"name": "drum.and.bass", "count": 10}],
            "statistics": {
                "numGroups": 25,
                "numTorrents": 42,
                "numSeeders": 150,
                "numLeechers": 10,
                "numSnatches": 500,
            },
            "torrentgroup": [
                {
                    "groupId": 12345,
                    "groupName": "Test Album",
                    "groupYear": 2020,
                    "groupRecordLabel": "Test Label",
                    "groupCatalogueNumber": "TL-001",
                    "tags": ["electronic", "ambient"],
                    "releaseType": 1,
                    "groupVanityHouse": False,
                    "hasBookmarked": False,
                    "torrent": [
                        {
                            "id": 98765,
                            "groupId": 12345,
                            "media": "CD",
                            "format": "FLAC",
                            "encoding": "Lossless",
                            "remasterYear": 2020,
                            "remastered": False,
                            "remasterTitle": "",
                            "remasterRecordLabel": "",
                            "scene": False,
                            "hasLog": True,
                            "hasCue": True,
                            "logScore": 100,
                            "fileCount": 10,
                            "freeTorrent": False,
                            "size": 500000000,
                            "leechers": 2,
                            "seeders": 10,
                            "snatched": 25,
                            "time": "2020-05-01 12:30:45",
                            "hasFile": 0,
                        }
                    ],
                }
            ],
            "requests": [
                {
                    "requestId": 54321,
                    "categoryId": 1,
                    "title": "Unreleased Album",
                    "year": 2023,
                    "timeAdded": "2023-01-15 08:45:30",
                    "votes": 5,
                    "bounty": 100000,
                }
            ],
        },
    }

    client.http_client.add(
        params={"action": "artist", "id": "1460"},
        headers={"Authorization": "test_key"},
        response=mock_response,
    )

    response = client.get_artist(1460)
    assert response.status == "success"
    assert response.response.id == 1460
    assert response.response.name == "Test Artist"
    assert len(response.response.torrentgroup) == 1
    assert response.response.torrentgroup[0].groupName == "Test Album"
    assert len(response.response.torrentgroup[0].torrent) == 1
    assert response.response.torrentgroup[0].torrent[0].id == 98765


def test_get_artist_validation_error(client: Client) -> None:
    """Test handling validation errors when getting artist details."""
    assert isinstance(client.http_client, FakeHTTPClient)
    # Missing required fields in the response
    mock_response = {"status": "success", "response": {"id": "not a numeric value"}}
    client.http_client.add(
        params={"action": "artist", "id": "1460"},
        headers={"Authorization": "test_key"},
        response=mock_response,
    )

    with pytest.raises(RedactedError) as excinfo:
        client.get_artist(1460)
    assert "Invalid response format" in str(excinfo.value)


def test_get_artist_error_response(client: Client) -> None:
    """Test handling error response when getting artist details."""
    assert isinstance(client.http_client, FakeHTTPClient)
    mock_response = {"status": "failure", "error": "Artist not found"}
    client.http_client.add(
        params={"action": "artist", "id": "999999"},
        headers={"Authorization": "test_key"},
        response=mock_response,
    )

    with pytest.raises(RedactedError) as excinfo:
        client.get_artist(999999)
    assert "Artist not found" in str(excinfo.value)
