"""Tests for the Redacted import functionality."""

import time
from typing import Union
from unittest.mock import patch

import pytest

from beetsplug.redacted import RedactedPlugin
from beetsplug.redacted.types import BeetsRedFields
from beetsplug.redacted.utils.test_utils import (
    FakeAlbum,
    FakeClient,
    FakeConfig,
    FakeLibrary,
    FakeLogger,
)


class FakeImportTask:
    """Mock import task for testing."""

    def __init__(self, album: Union[FakeAlbum, None] = None, is_album: bool = True) -> None:
        """Initialize fake import task.

        Args:
            album: Album associated with this task
            is_album: Whether this task is for an album
        """
        self.album = album
        self.is_album = is_album


@pytest.fixture
def config() -> FakeConfig:
    """Create a fake config with auto import enabled."""
    return FakeConfig()


@pytest.fixture
def test_album() -> FakeAlbum:
    """Create a test album."""
    library = FakeLibrary(
        [{"id": 1, "albumartist": "Test Artist", "album": "Test Album", "year": 2020}]
    )
    return library.albums()[0]


@pytest.fixture
def log() -> FakeLogger:
    """Create a fake logger."""
    return FakeLogger()


def test_import_stage_not_album_skips(log: FakeLogger) -> None:
    """Test that import_stage skips non-album tasks."""
    plugin = RedactedPlugin()
    plugin._log = log

    # Create a task that isn't an album
    task = FakeImportTask(is_album=False)

    # Call the import_stage method
    plugin.import_stage(None, task)

    # Verify that nothing about the task's (nonexistent) album was modified
    assert task.album is None


def test_import_stage_no_album_object_skips(log: FakeLogger) -> None:
    """Test that import_stage skips tasks with no album object."""
    plugin = RedactedPlugin()
    plugin._log = log

    # Create a task with no album object
    task = FakeImportTask(album=None, is_album=True)

    # Call the import_stage method
    plugin.import_stage(None, task)

    # Verify that nothing about the task's (nonexistent) album was modified
    assert task.album is None


def test_import_stage_no_match_skips(log: FakeLogger, test_album: FakeAlbum) -> None:
    """Test that import_stage skips albums with no match found."""
    plugin = RedactedPlugin()
    plugin._log = log
    plugin._client = FakeClient()
    plugin._min_score = 0.75

    # Create a task with an album
    task = FakeImportTask(album=test_album, is_album=True)

    # Mock search function to return None (no match)
    with patch("beetsplug.redacted.search") as mock_search:
        mock_search.return_value = None

        # Call the import_stage method
        plugin.import_stage(None, task)

    # Verify album wasn't modified
    assert "red_mtime" not in test_album


def test_import_stage_with_match_applies_fields(log: FakeLogger, test_album: FakeAlbum) -> None:
    """Test that import_stage applies fields when a match is found."""
    plugin = RedactedPlugin()
    plugin._log = log
    plugin._client = FakeClient()
    plugin._min_score = 0.75

    # Create a task with an album
    task = FakeImportTask(album=test_album, is_album=True)

    # Current time for timestamp comparison
    current_time = time.time()

    # Mock search function to return fields
    with patch("beetsplug.redacted.search") as mock_search:
        # Create fields to return from search
        red_fields = BeetsRedFields(
            red_groupid=123, red_torrentid=456, red_format="FLAC", red_encoding="Lossless"
        )
        mock_search.return_value = red_fields

        # Call the import_stage method
        plugin.import_stage(None, task)

    # Verify that the fields were added to the album
    assert test_album.red_groupid == 123
    assert test_album.red_torrentid == 456
    assert test_album.red_format == "FLAC"
    assert test_album.red_encoding == "Lossless"
    assert "red_mtime" in test_album
    assert test_album.red_mtime >= current_time


def test_import_stage_with_unchanged_fields_no_update(
    log: FakeLogger, test_album: FakeAlbum
) -> None:
    """Test that import_stage doesn't update if fields haven't changed."""
    plugin = RedactedPlugin()
    plugin._log = log
    plugin._client = FakeClient()
    plugin._min_score = 0.75

    # Set existing values on the album
    test_album.red_groupid = 123

    # Create a task with an album
    task = FakeImportTask(album=test_album, is_album=True)

    # Mock search function to return the same fields
    with patch("beetsplug.redacted.search") as mock_search:
        # Create fields to return from search with same values
        red_fields = BeetsRedFields(red_groupid=123)
        mock_search.return_value = red_fields

        # Call the import_stage method
        plugin.import_stage(None, task)

    # Verify that red_mtime wasn't updated since no fields changed
    assert test_album.get("red_mtime") is None
