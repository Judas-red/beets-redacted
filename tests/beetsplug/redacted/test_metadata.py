"""Tests for the redacted metadata features.

The Redacted plugin exposes metadata for us in the Beets import and autotagging pipeline.

Documentation for plugins can be found here:
  https://beets.readthedocs.io/en/stable/dev/plugins.html#extend-the-autotagger

An example plugin implementation can be found here:
  https://github.com/beetbox/beets/blob/master/beetsplug/chroma.py
"""

import pytest
from beets.library import Item  # type: ignore[import-untyped]

from beetsplug.redacted import metadata
from beetsplug.redacted.types import RedSearchResponse, RedSearchResult, RedSearchResults
from beetsplug.redacted.utils.test_utils import FakeClient, FakeLogger


@pytest.fixture
def log() -> FakeLogger:
    """Create a fake logger for testing."""
    return FakeLogger()


@pytest.fixture
def client() -> FakeClient:
    """Create a fake Redacted client for testing."""
    return FakeClient()


def make_item(
    artist: str = "Test Artist",
    album: str = "Test Album",
    title: str = "Test Track",
    track: int = 1,
) -> Item:
    """Create a test Item with album information."""
    return Item(artist=artist, album=album, title=title, track=track, albumartist=artist)


def make_result(
    id: int = 1, artist: str = "Test Artist", name: str = "Test Album", year: int = 2020
) -> RedSearchResult:
    """Create a test torrent group."""
    return RedSearchResult(groupId=id, artist=artist, groupName=name, groupYear=year)


def test_candidates_no_matches(client: FakeClient, log: FakeLogger) -> None:
    """Test that candidates returns empty list when no matches are found."""
    items = [make_item()]
    albums = metadata.candidates(client, log, items, "Test Artist", "Test Album", False)
    assert len(albums) == 0
    assert "Test Artist Test Album" in client.queries


def test_candidates_with_matches(client: FakeClient, log: FakeLogger) -> None:
    """Test that candidates returns albums when matches are found."""
    items = [make_item()]
    group_1 = make_result(artist="Test Artist", name="Test Album", year=2020)
    group_2 = make_result(artist="Test Artist 2", name="Test Album 2")
    client.search_responses["Test Artist Test Album"] = RedSearchResponse(
        status="success", response=RedSearchResults(results=[group_1, group_2])
    )

    albums = metadata.candidates(client, log, items, "Test Artist", "Test Album", False)
    assert len(albums) == 2

    album = albums[0]
    assert album.albumartist == group_1.artist
    assert album.album == group_1.groupName
    assert album.year == group_1.groupYear

    album = albums[1]
    assert album.albumartist == group_2.artist
    assert album.album == group_2.groupName
    assert album.year == group_2.groupYear


def test_skips_va_albums(client: FakeClient, log: FakeLogger) -> None:
    """Test that candidates skips VA albums."""
    va_likely = True
    albums = metadata.candidates(client, log, [], "Various Artists", "Test Album", va_likely)
    assert len(albums) == 0


def test_candidates_normalizes_query(client: FakeClient, log: FakeLogger) -> None:
    """Test that candidates normalizes the search query."""
    items = [make_item(artist="Test Artist (feat. Someone)", album="Test Album [Remastered]")]
    client.search_responses["Test Artist Test Album"] = RedSearchResponse(
        status="success", response=RedSearchResults(results=[make_result()])
    )

    albums = metadata.candidates(
        client, log, items, "Test Artist (feat. Someone)", "Test Album [Remastered]", False
    )
    assert len(albums) == 1
    assert "Test Artist Test Album" in client.queries


def test_candidates_error_handling(client: FakeClient, log: FakeLogger) -> None:
    """Test that candidates handles API errors gracefully."""
    items = [make_item()]
    client.error_queries.add("Test Artist Test Album")

    albums = metadata.candidates(client, log, items, "Test Artist", "Test Album", False)
    assert len(albums) == 0
