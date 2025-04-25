"""Tests for the redacted plugin."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from beetsplug.redacted.command import RedactedCommand
from beetsplug.redacted.search import BeetsRedFields
from beetsplug.redacted.utils.test_utils import (
    FakeAlbum,
    FakeClient,
    FakeCommandOpts,
    FakeConfig,
    FakeLibrary,
    FakeLogger,
)


@pytest.fixture
def lib() -> FakeLibrary:
    """Create a fake library.

    Returns:
        A FakeLibrary instance
    """
    return FakeLibrary([])


@pytest.fixture
def album() -> FakeAlbum:
    """Create a fake album.

    Returns:
        A FakeAlbum instance
    """
    return FakeAlbum(id=1, albumartist="Test Artist", album="Test Album")


@pytest.fixture
def client() -> FakeClient:
    """Create a fake client.

    Returns:
        A FakeRedactedClient instance
    """
    return FakeClient()


@pytest.fixture
def config() -> FakeConfig:
    """Create a fake config.

    Returns:
        A FakeConfig instance with default values
    """
    return FakeConfig()


@pytest.fixture
def log() -> FakeLogger:
    """Create a fake logger.

    Returns:
        A FakeLogger instance
    """
    return FakeLogger()


@pytest.fixture(autouse=True)
def setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Set up logging for all tests."""
    caplog.set_level(logging.INFO)


@pytest.fixture
def test_album_data() -> dict[str, Any]:
    """Create test album data.

    Returns:
        Dictionary containing test album data
    """
    return {"id": 1, "albumartist": "Test Artist", "album": "Test Album", "year": 2020}


@pytest.fixture
def lib_with_album(test_album_data: dict[str, Any]) -> FakeLibrary:
    """Create a fake library with a test album.

    Args:
        test_album_data: Base test album data to use

    Returns:
        A FakeLibrary instance with a test album
    """
    return FakeLibrary([test_album_data])


@pytest.fixture
def lib_with_red_groupid(test_album_data: dict[str, Any]) -> FakeLibrary:
    """Create a fake library with an album that has a red_groupid.

    Args:
        test_album_data: Base test album data to use

    Returns:
        A FakeLibrary instance with a test album that has red_groupid
    """
    album_data = test_album_data.copy()
    album_data["red_groupid"] = 1
    album_data["red_torrentid"] = 2
    return FakeLibrary([album_data])


def test_command_init(config: FakeConfig, log: FakeLogger, lib: FakeLibrary) -> None:
    """Test command initialization."""
    client = FakeClient()
    command = RedactedCommand(config, log, client)
    assert command.name == "redacted"
    assert command.config == config
    assert command.log == log
    assert command.client == client


def test_command_basic_execution(config: FakeConfig, log: FakeLogger, lib: FakeLibrary) -> None:
    """Test basic command execution searches torrents."""
    client = FakeClient()
    command = RedactedCommand(config, log, client)
    result = command.func(lib, FakeCommandOpts(), [])

    # Verify the return value
    assert result["modified"] == 0
    assert result["unmodified"] == 0
    assert result["total"] == 0


def test_command_with_query(config: FakeConfig, lib: FakeLibrary, log: FakeLogger) -> None:
    """Test command execution with a query."""
    command = RedactedCommand(config, log, FakeClient())
    result = command.func(lib, FakeCommandOpts(), ["artist:testartist"])

    # Verify the return value
    assert result["modified"] == 0
    assert result["unmodified"] == 0
    assert result["total"] == 0


def test_command_with_unchanged_search_results_does_not_modify_albums(
    config: FakeConfig, log: FakeLogger, lib_with_red_groupid: FakeLibrary
) -> None:
    """Test command execution with force flag processes all albums."""
    client = FakeClient()
    command = RedactedCommand(config, log, client)

    # Mock search functions to return same values as album
    with patch("beetsplug.redacted.command.search") as mock_search:
        # These should match the album's existing values.
        album = lib_with_red_groupid.albums()[0]
        assert album.red_groupid == 1
        assert album.red_torrentid == 2

        mock_search.return_value = BeetsRedFields(red_groupid=1, red_torrentid=2)

        # Execute command with force=True so that the album will still be queried.
        result = command.func(lib_with_red_groupid, FakeCommandOpts(force=True), [])

        # Verify the album was processed but not modified.
        assert result["total"] == 1
        assert result["modified"] == 0
        assert result["unmodified"] == 1


def test_command_with_force(
    config: FakeConfig, log: FakeLogger, lib_with_red_groupid: FakeLibrary
) -> None:
    """Test command execution with force flag processes all albums."""
    client = FakeClient()
    command = RedactedCommand(config, log, client)

    # Verify that the library has at least one album.
    assert len(lib_with_red_groupid.albums()) > 0

    # Verify that the album we've set up would not be processed without force=True
    result = command.func(lib_with_red_groupid, FakeCommandOpts(force=False), [])
    assert result["total"] == 0

    # Mock search functions to return values (to simulate finding matches)
    with patch("beetsplug.redacted.command.search") as mock_search:
        mock_search.return_value = BeetsRedFields(red_groupid=1, red_torrentid=2)

        # Verify that the same album is processed with force=True
        result = command.func(lib_with_red_groupid, FakeCommandOpts(force=True), [])

        assert result["total"] == 1


def test_command_without_force(config: FakeConfig, log: FakeLogger, lib: FakeLibrary) -> None:
    """Test command execution without force flag skips albums with red_groupid."""
    client = FakeClient()
    # Create a test album with existing red_groupid
    lib = FakeLibrary(
        [
            {
                "id": 1,
                "albumartist": "Test Artist",
                "album": "Test Album",
                "year": 2020,
                "red_groupid": 1,
            }
        ]
    )
    command = RedactedCommand(config, log, client)

    # Execute command without force=True
    result = command.func(lib, FakeCommandOpts(force=False), [])

    # Verify the return value
    assert result["modified"] == 0
    assert result["unmodified"] == 0  # Should be 0 since we skipped one album with red_groupid
    assert result["total"] == 0  # Total should be 0 since we filtered albums in the database query


def test_command_with_matches(
    config: FakeConfig, log: FakeLogger, lib_with_album: FakeLibrary
) -> None:
    """Test command with matching albums."""
    # Mock the search functions to return fake matches
    with patch("beetsplug.redacted.command.search") as mock_search:

        # Set up mock return values
        mock_search.return_value = BeetsRedFields(red_groupid=1, red_torrentid=1)

        command = RedactedCommand(config, log, FakeClient())
        result = command.func(lib_with_album, FakeCommandOpts(), [])

        # Verify the return value
        assert result["modified"] == 1
        assert result["unmodified"] == 0
        assert result["total"] == 1


def test_command_pretend_mode(
    config: FakeConfig, log: FakeLogger, lib_with_album: FakeLibrary
) -> None:
    """Test command in pretend mode shows changes without making them."""
    # Mock the search functions to return fake matches for pretend mode test
    with patch("beetsplug.redacted.command.search") as mock_search:

        # Set up mock return values
        mock_search.return_value = BeetsRedFields(red_groupid=1, red_torrentid=1)

        command = RedactedCommand(config, log, FakeClient())
        # Execute command in pretend mode
        result = command.func(lib_with_album, FakeCommandOpts(pretend=True), [])

        # Verify the return value - should be unmodified since we're in pretend mode
        assert result["modified"] == 0
        assert result["unmodified"] == 1
        assert result["total"] == 1
