"""Tests for search_torrents.py functionality."""

import dataclasses
import itertools

import pytest

from beetsplug.redacted.search import (
    BeetsRedFields,
    match_album,
    match_artist_album,
    search,
    torrent_group_matchable,
)
from beetsplug.redacted.types import (
    RedArtist,
    RedArtistResponse,
    RedArtistResponseResults,
    RedArtistTorrent,
    RedArtistTorrentGroup,
    RedSearchResponse,
    RedSearchResult,
    RedSearchResults,
    RedSearchTorrent,
)
from beetsplug.redacted.utils.test_utils import (
    FakeAlbum,
    FakeLibrary,
    FakeLogger,
    FakeRedactedClient,
)

TEST_ARTIST_ID = 1
TEST_GROUP_ID = 2
TEST_TORRENT_ID = 3
TEST_ALBUM_ID = 4
TEST_ARTIST_NAME = "Test Artist"
TEST_ALBUM_NAME = "Test Album"
TEST_ALBUM_YEAR = 2020


@pytest.fixture
def log() -> FakeLogger:
    """Create a fake logger for testing."""
    return FakeLogger()


@pytest.fixture
def client() -> FakeRedactedClient:
    """Create a fake client for testing."""
    return FakeRedactedClient()


@pytest.fixture
def album() -> FakeAlbum:
    """Create a test album for testing."""
    lib = FakeLibrary(
        [
            {
                "id": TEST_ALBUM_ID,
                "albumartist": TEST_ARTIST_NAME,
                "albumartist_sort": "Artist, Test",
                "album": TEST_ALBUM_NAME,
                "albumdisambig": "The Great Test Album",
                "year": TEST_ALBUM_YEAR,
                "media": "CD",
                "format": "FLAC",
            }
        ]
    )
    return lib.albums()[0]


@pytest.fixture
def test_torrent(artist_id: int = TEST_ARTIST_ID) -> RedSearchTorrent:
    """Create a test torrent for testing.

    Returns:
        Test torrent object
    """
    return RedSearchTorrent(
        torrentId=TEST_TORRENT_ID,
        editionId=1,
        artists=[RedArtist(id=artist_id, name="Test Artist", aliasid=artist_id + 500)],
        remastered=False,
        remasterYear=0,
        remasterCatalogueNumber="",
        remasterTitle="",
        media="CD",
        encoding="Lossless",
        format="FLAC",
        hasLog=True,
        logScore=100,
        hasCue=True,
        scene=False,
        vanityHouse=False,
        fileCount=10,
        time="2012-04-14 15:57:00",
        size=1000000,
        snatches=100,
        seeders=50,
        leechers=10,
        isFreeleech=False,
        isNeutralLeech=False,
        isFreeload=False,
        isPersonalFreeleech=False,
        canUseToken=True,
    )


@pytest.fixture
def test_artist_torrent(
    group_id: int = TEST_GROUP_ID, torrent_id: int = TEST_TORRENT_ID
) -> RedArtistTorrent:
    """Create a test artist torrent for testing."""
    return RedArtistTorrent(
        id=torrent_id,
        groupId=group_id,
        media="CD",
        format="FLAC",
        encoding="Lossless",
        remasterYear=TEST_ALBUM_YEAR,
        remastered=False,
        remasterTitle="",
        remasterRecordLabel="",
        scene=False,
        hasLog=True,
        hasCue=True,
        logScore=100,
        fileCount=10,
        size=1000000,
        seeders=50,
        leechers=10,
        snatched=100,
        time="2012-04-14 15:57:00",
    )


@pytest.fixture
def test_artist_group(
    test_artist_torrent: RedArtistTorrent, group_id: int = TEST_GROUP_ID
) -> RedArtistTorrentGroup:
    """Create a test artist group for testing."""
    return RedArtistTorrentGroup(
        groupId=group_id,
        groupName=TEST_ALBUM_NAME,
        groupYear=TEST_ALBUM_YEAR,
        groupRecordLabel="Test Label",
        groupCatalogueNumber="TEST-001",
        tags=["electronic", "test"],
        releaseType=1,
        groupVanityHouse=False,
        hasBookmarked=False,
        torrent=[test_artist_torrent],
    )


@pytest.fixture
def test_artist_response(
    test_artist_group: RedArtistTorrentGroup, artist_id: int = TEST_ARTIST_ID
) -> RedArtistResponse:
    """Create a test artist response."""
    return RedArtistResponse(
        status="success",
        response=RedArtistResponseResults(
            id=artist_id,
            name=TEST_ARTIST_NAME,
            notificationsEnabled=False,
            hasBookmarked=False,
            image="https://example.com/artist.jpg",
            body="Artist bio",
            vanityHouse=False,
            torrentgroup=[test_artist_group],
            requests=[],
        ),
    )


def _make_test_group(
    group_id: int = TEST_GROUP_ID,
    artist_id: int = TEST_ARTIST_ID,
    artist: str = TEST_ARTIST_NAME,
    name: str = TEST_ALBUM_NAME,
    year: int = TEST_ALBUM_YEAR,
    torrent: RedSearchTorrent | None = None,
) -> RedSearchResult:
    """Create a test group for testing.

    Args:
        artist: Artist name
        name: Album name
        year: Release year
        torrent: Test torrent to include in group (used for fixture injection)
        group_id: Group ID
        artist_id: Artist ID to include in torrent artists

    Returns:
        Test group object
    """
    test_torrent = torrent or RedSearchTorrent(
        torrentId=TEST_TORRENT_ID,
        editionId=1,
        remastered=False,
        media="CD",
        format="FLAC",
        encoding="Lossless",
    )

    # Add artist ID if specified
    if artist_id is not None and test_torrent.artists is None:
        test_torrent.artists = [RedArtist(id=artist_id, name=artist, aliasid=artist_id + 500)]

    return RedSearchResult(
        groupId=group_id,
        groupName=name,
        artist=artist,
        tags=["electronic"],
        bookmarked=False,
        vanityHouse=False,
        groupYear=year,
        releaseType="Album",
        groupTime=1339117820,
        maxSize=237970,
        totalSnatched=318,
        totalSeeders=14,
        totalLeechers=0,
        torrents=[test_torrent] if test_torrent else [],
    )


def _setup_search_responses(
    client: FakeRedactedClient, query: str, groups: list[RedSearchResult]
) -> None:
    """Set up search responses for the client.

    Args:
        client: The client to configure
        query: The query to respond to
        groups: The groups to include in the response
    """
    client.search_responses[query] = RedSearchResponse(
        status="success", response=RedSearchResults(results=groups)
    )


def _setup_artist_response(
    client: FakeRedactedClient,
    artist_id: int = TEST_ARTIST_ID,
    artist_name: str = TEST_ARTIST_NAME,
    torrent_groups: list[RedArtistTorrentGroup] | None = None,
) -> None:
    """Set up artist response for the client.

    Args:
        client: The client to configure
        artist_id: The artist ID to respond to
        artist_name: The artist name
        torrent_groups: The torrent groups to include in the response
    """
    client.artist_responses[artist_id] = RedArtistResponse(
        status="success",
        response=RedArtistResponseResults(
            id=artist_id,
            name=artist_name,
            notificationsEnabled=False,
            hasBookmarked=False,
            torrentgroup=torrent_groups or [],
            requests=[],
        ),
    )


def test_all_beets_fields_mapped() -> None:
    """Test that all BeetsRedFields are mapped to either artist or torrent fields."""
    # Get all the fields from the response data dataclasses
    response_fields = set()
    for field in itertools.chain(
        dataclasses.fields(RedArtistResponseResults),
        dataclasses.fields(RedSearchResult),
        dataclasses.fields(RedSearchTorrent),
    ):
        response_fields.add(field.name)
    assert None not in response_fields

    # Get the field names from the dataclass fields used as dictionary keys
    mapped_red_fields = set()
    unmapped_fields = set()

    for field in dataclasses.fields(BeetsRedFields):
        if field.name == "red_mtime":  # Skip mtime as it's not mapped to a response field
            continue
        if "from" in field.metadata:
            mapped_red_fields.add(field.name)
        else:
            unmapped_fields.add(field.name)

    if unmapped_fields:
        raise ValueError(f"BeetsRedFields without 'from' metadata: {unmapped_fields}")


def test_match_album_exact_match(
    log: FakeLogger, album: FakeAlbum, test_torrent: RedSearchTorrent
) -> None:
    """Test matching an album with exact match."""
    # Create multiple groups with one exact match and others that are close
    group1 = _make_test_group(
        artist="Different Artist", name="Different Album", year=2020, torrent=test_torrent
    )
    group2 = _make_test_group(year=2020, torrent=test_torrent)  # Exact match
    group3 = _make_test_group(
        artist=TEST_ARTIST_NAME, name="Test Album 2", year=2019, torrent=test_torrent
    )

    results = RedSearchResponse(
        status="success", response=RedSearchResults(results=[group1, group2, group3])
    )
    match, score = match_album(album, results, log, min_score=0.75)
    assert match is not None

    # Now match only returns the group, not a tuple of (group, torrent)
    assert match.groupId == TEST_GROUP_ID
    assert match.artist == TEST_ARTIST_NAME
    assert match.groupName == TEST_ALBUM_NAME
    assert score > 0


def test_search_torrents_with_artist_lookup(
    log: FakeLogger,
    client: FakeRedactedClient,
    album: FakeAlbum,
    test_torrent: RedSearchTorrent,
    test_artist_group: RedArtistTorrentGroup,
) -> None:
    """Test searching for torrents with artist lookup flow."""
    # Set up the browse response with artist ID in the torrent
    initial_match = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=100,
        artist_id=TEST_ARTIST_ID,
    )

    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [initial_match])
    _setup_artist_response(client, TEST_ARTIST_ID, TEST_ARTIST_NAME, [test_artist_group])

    # Search for torrents - should use both browse and get_artist
    result = search(album, client, log, min_score=0.75)

    # Verify the results
    assert result is not None
    assert result.red_artistid == TEST_ARTIST_ID
    assert result.red_groupid == TEST_GROUP_ID
    assert result.red_torrentid == TEST_TORRENT_ID
    assert result.red_media == "CD"
    assert result.red_format == "FLAC"

    # Verify both API methods were called
    assert f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}" in client.queries
    assert TEST_ARTIST_ID in client.artist_queries


def test_search_torrents_artist_lookup_better_match(
    log: FakeLogger,
    client: FakeRedactedClient,
    album: FakeAlbum,
    test_torrent: RedSearchTorrent,
    test_artist_torrent: RedArtistTorrent,
) -> None:
    """Test that artist lookup finds a better match than initial browse."""
    # Set up test response for initial browse search with a so-so match
    initial_match = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=f"{TEST_ALBUM_NAME} (Deluxe)",
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=3,
        artist_id=TEST_ARTIST_ID,
    )
    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [initial_match])

    # Create a better match in the artist response
    initial_group = RedArtistTorrentGroup(
        groupId=3,
        groupName=f"{TEST_ALBUM_NAME} (Deluxe)",
        groupYear=TEST_ALBUM_YEAR,
        torrent=[test_artist_torrent],
    )
    better_match_torrent = RedArtistTorrent(
        id=TEST_TORRENT_ID, groupId=TEST_GROUP_ID, media="CD", format="FLAC", encoding="Lossless"
    )
    better_match_group = RedArtistTorrentGroup(
        groupId=TEST_GROUP_ID,
        groupName=TEST_ALBUM_NAME,
        groupYear=TEST_ALBUM_YEAR,
        torrent=[better_match_torrent],
    )
    _setup_artist_response(
        client, TEST_ARTIST_ID, TEST_ARTIST_NAME, [better_match_group, initial_group]
    )

    # Search for torrents
    result = search(album, client, log, min_score=0.75)

    # Verify the results - should find the exact match from artist's discography
    assert result is not None
    assert result.red_groupid == TEST_GROUP_ID
    assert result.red_torrentid == TEST_TORRENT_ID


def test_search_torrents_artist_lookup_failed(
    log: FakeLogger, client: FakeRedactedClient, album: FakeAlbum, test_torrent: RedSearchTorrent
) -> None:
    """Test handling case where artist lookup fails but we still use initial match."""
    # Set up test response for initial browse search
    initial_match = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=1,
        artist_id=TEST_ARTIST_ID,
    )

    # Setup browse response
    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [initial_match])

    # Configure client to return error for artist lookup
    client.error_artist_queries = {TEST_ARTIST_ID}

    # Search for torrents - should use browse and attempt artist lookup
    result = search(album, client, log, min_score=0.75)

    # Should return None when artist lookup fails (per project requirements)
    assert result is None

    # Verify both API methods were attempted
    assert f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}" in client.queries
    assert TEST_ARTIST_ID in client.artist_queries


def test_search_torrents_no_artist_id_in_torrent(
    log: FakeLogger, client: FakeRedactedClient, album: FakeAlbum
) -> None:
    """Test handling case where torrent has no artist ID for lookup."""
    # Create a torrent with no artist ID
    torrent_without_artist = RedSearchTorrent(
        artists=[],
        torrentId=TEST_TORRENT_ID,
        editionId=1,
        media="CD",
        format="FLAC",
        encoding="Lossless",
    )

    # Set up test response for initial browse search
    initial_match = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=torrent_without_artist,
        group_id=TEST_GROUP_ID,
    )

    # Setup browse response
    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [initial_match])

    # Search for torrents - should return None because artist ID is required
    result = search(album, client, log, min_score=0.75)

    # Should return None when no artist ID is available
    assert result is None

    # Verify only browse was called, not artist lookup
    assert f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}" in client.queries
    assert len(client.artist_queries) == 0


def test_search_torrents_no_match(
    log: FakeLogger, client: FakeRedactedClient, album: FakeAlbum
) -> None:
    """Test searching for torrents with no match."""
    # Set up test response with no matching groups
    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [])

    # Search for torrents - should return None
    result = search(album, client, log, min_score=0.75)
    assert result is None


def test_search_torrents_with_error(
    log: FakeLogger, client: FakeRedactedClient, album: FakeAlbum
) -> None:
    """Test searching for torrents with an error."""
    # Set up test response with an error
    client.error_queries.add(f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}")

    # Search for torrents with error - should return None
    result = search(album, client, log, min_score=0.75)
    assert result is None


def test_search_torrents_with_variants(
    log: FakeLogger,
    client: FakeRedactedClient,
    test_torrent: RedSearchTorrent,
    test_artist_group: RedArtistTorrentGroup,
) -> None:
    """Test searching for torrents with artist/album variants."""
    # Create a test album with variants
    lib = FakeLibrary(
        [
            {
                "id": TEST_ALBUM_ID,
                "albumartist": "Artist, Test",
                "albumartist_sort": "Test Artist",
                "album": "Test Album",
                "albumdisambig": "Album, Test (2020)",
                "year": TEST_ALBUM_YEAR,
            }
        ]
    )
    album = lib.albums()[0]

    # Set up browse result with artist ID for lookup
    exact_match = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=TEST_GROUP_ID,
        artist_id=TEST_ARTIST_ID,
    )

    # Set empty responses for most variants
    for artist, album_name in itertools.product(
        ["Artist, Test", "Test Artist"], ["Test Album", "Album, Test"]
    ):
        query = f"{artist} {album_name}"
        _setup_search_responses(client, query, [])

    # Set a response with results for one query that should match
    _setup_search_responses(client, f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}", [exact_match])

    # Set up artist response
    _setup_artist_response(client, TEST_ARTIST_ID, TEST_ARTIST_NAME, [test_artist_group])

    # Search for torrents
    result = search(album, client, log, min_score=0.75)

    assert result is not None
    assert result.red_groupid == TEST_GROUP_ID
    assert result.red_torrentid == test_torrent.torrentId
    assert TEST_ARTIST_ID in client.artist_queries


def test_extract_group_fields_valid(test_torrent: RedSearchTorrent) -> None:
    """Test extracting fields from a valid group."""
    group = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=TEST_GROUP_ID,
    )
    fields = torrent_group_matchable(group)
    assert fields is not None
    assert fields.artist == TEST_ARTIST_NAME
    assert fields.title == TEST_ALBUM_NAME
    assert fields.year == TEST_ALBUM_YEAR


def test_extract_group_fields_missing_artist(test_torrent: RedSearchTorrent) -> None:
    """Test extracting fields from a group missing artist."""
    group = _make_test_group(
        artist="",
        name=TEST_ALBUM_NAME,
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=TEST_GROUP_ID,
    )
    fields = torrent_group_matchable(group)
    assert fields is None


def test_extract_group_fields_missing_name(test_torrent: RedSearchTorrent) -> None:
    """Test extracting fields from a group missing name."""
    group = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name="",
        year=TEST_ALBUM_YEAR,
        torrent=test_torrent,
        group_id=TEST_GROUP_ID,
    )
    fields = torrent_group_matchable(group)
    assert fields is None


def test_extract_group_fields_missing_year(test_torrent: RedSearchTorrent) -> None:
    """Test extracting fields from a group missing year."""
    # Create a group with a default year since _make_test_group requires an int
    group = _make_test_group(
        artist=TEST_ARTIST_NAME,
        name=TEST_ALBUM_NAME,
        year=0,
        torrent=test_torrent,
        group_id=TEST_GROUP_ID,
    )
    # Then override the groupYear to be None
    group.groupYear = None

    fields = torrent_group_matchable(group)
    assert fields is not None
    assert fields.artist == TEST_ARTIST_NAME
    assert fields.title == TEST_ALBUM_NAME
    assert fields.year is None


@pytest.mark.parametrize(
    "group_name, expected_result",
    [
        pytest.param(TEST_ALBUM_NAME, True, id="valid_name"),
        pytest.param("", False, id="empty_string_name"),
        pytest.param("None", True, id="string_none_name"),
    ],
)
def test_artist_torrent_group_matchable(group_name: str, expected_result: bool) -> None:
    """Test artist_torrent_group_matchable with parameterized inputs."""
    from beetsplug.redacted.search import artist_torrent_group_matchable

    group = RedArtistTorrentGroup(
        groupId=TEST_GROUP_ID, groupName=group_name, groupYear=TEST_ALBUM_YEAR, torrent=[]
    )

    fields = artist_torrent_group_matchable(group, TEST_ARTIST_NAME)

    if expected_result:
        assert fields is not None
        assert fields.artist == TEST_ARTIST_NAME
        assert fields.title == group_name
        assert fields.year == TEST_ALBUM_YEAR
    else:
        assert fields is None


@pytest.mark.parametrize(
    "group_config, expected",
    [
        pytest.param({"torrentgroup": []}, None, id="no_torrent_groups"),
        pytest.param(
            {
                "torrentgroup": [
                    RedArtistTorrentGroup(
                        groupId=TEST_GROUP_ID,
                        groupName=TEST_ALBUM_NAME,
                        groupYear=TEST_ALBUM_YEAR,
                        torrent=[],
                    )
                ]
            },
            None,
            id="missing_name",
        ),
        pytest.param(
            {
                "torrentgroup": [
                    RedArtistTorrentGroup(
                        groupId=TEST_GROUP_ID,
                        groupName="",
                        groupYear=TEST_ALBUM_YEAR,
                        torrent=[RedArtistTorrent(id=TEST_TORRENT_ID, groupId=TEST_GROUP_ID)],
                    )
                ]
            },
            None,
            id="low_score_match",
        ),
        pytest.param(
            {
                "torrentgroup": [
                    RedArtistTorrentGroup(
                        groupId=TEST_GROUP_ID,
                        groupName="Completely Different Album",
                        groupYear=TEST_ALBUM_YEAR,
                        torrent=[RedArtistTorrent(id=TEST_TORRENT_ID, groupId=TEST_GROUP_ID)],
                    )
                ]
            },
            None,
            id="low_score_match",
        ),
    ],
)
def test_match_artist_album_edge_cases(
    log: FakeLogger, album: FakeAlbum, group_config: dict, expected: tuple | None
) -> None:
    """Test match_artist_album with parameterized edge cases."""
    response = RedArtistResponse(
        status="success",
        response=RedArtistResponseResults(id=TEST_ARTIST_ID, name=TEST_ARTIST_NAME, **group_config),
    )

    result = match_artist_album(album, response, log, min_score=0.75)
    assert result == expected


@pytest.mark.parametrize(
    "artist, group, torrent, expected",
    [
        pytest.param(
            RedArtistResponseResults(id=TEST_ARTIST_ID, name=TEST_ARTIST_NAME),
            RedArtistTorrentGroup(groupId=TEST_GROUP_ID, groupName=TEST_ALBUM_NAME),
            RedArtistTorrent(id=TEST_TORRENT_ID, media="CD", format="FLAC", encoding="Lossless"),
            BeetsRedFields(
                red_artistid=TEST_ARTIST_ID,
                red_groupid=TEST_GROUP_ID,
                red_torrentid=TEST_TORRENT_ID,
                red_artist=TEST_ARTIST_NAME,
                red_groupname=TEST_ALBUM_NAME,
                red_media="CD",
                red_format="FLAC",
                red_encoding="Lossless",
            ),
            id="nominal",
        ),
        pytest.param(
            RedArtistResponseResults(id=TEST_ARTIST_ID, name=TEST_ARTIST_NAME),
            RedArtistTorrentGroup(groupId=TEST_GROUP_ID, groupName=TEST_ALBUM_NAME),
            RedArtistTorrent(media="CD", format="FLAC", encoding="Lossless"),
            None,
            id="missing_artist_id",
        ),
        pytest.param(
            RedArtistResponseResults(id=TEST_ARTIST_ID, name=TEST_ARTIST_NAME),
            RedArtistTorrentGroup(groupName=TEST_ALBUM_NAME),
            RedArtistTorrent(id=TEST_TORRENT_ID, media="CD", format="FLAC", encoding="Lossless"),
            None,
            id="missing_group_id",
        ),
        pytest.param(
            RedArtistResponseResults(name=TEST_ARTIST_NAME),
            RedArtistTorrentGroup(groupId=TEST_GROUP_ID, groupName=TEST_ALBUM_NAME),
            RedArtistTorrent(id=TEST_TORRENT_ID, media="CD", format="FLAC", encoding="Lossless"),
            None,
            id="missing_torrent_id",
        ),
    ],
)
def test_beets_fields_from_artist_torrent_groups(
    log: FakeLogger,
    artist: RedArtistResponseResults,
    group: RedArtistTorrentGroup,
    torrent: RedArtistTorrent,
    expected: BeetsRedFields,
) -> None:
    """Test extracting Beets fields from artist torrent groups with parameterized inputs."""
    from beetsplug.redacted.search import beets_fields_from_artist_torrent_groups

    # Extract fields
    red_fields = beets_fields_from_artist_torrent_groups(artist, group, torrent, log)
    assert red_fields == expected


@pytest.mark.parametrize(
    "group_config, torrent_config, expected_result",
    [
        pytest.param(
            {
                "groupId": TEST_GROUP_ID,
                "groupName": TEST_ALBUM_NAME,
                "artist": TEST_ARTIST_NAME,
                "torrents": [],
            },
            {},
            None,
            id="test_group_with_no_torrents",
        ),
        pytest.param(
            {"groupId": TEST_GROUP_ID, "groupName": TEST_ALBUM_NAME, "artist": TEST_ARTIST_NAME},
            {"torrentId": TEST_TORRENT_ID, "editionId": 1},
            None,
            id="test_torrent_with_no_artists",
        ),
        pytest.param(
            {"groupId": TEST_GROUP_ID, "groupName": TEST_ALBUM_NAME, "artist": TEST_ARTIST_NAME},
            {"torrentId": TEST_TORRENT_ID, "editionId": 1, "artists": []},
            None,
            id="test_torrent_with_empty_artists",
        ),
    ],
)
def test_get_artist_id_from_red_group_exceptions(
    log: FakeLogger, group_config: dict, torrent_config: dict, expected_result: int | None
) -> None:
    """Test exception handling in get_artist_id_from_red_group with parameterized inputs."""
    from beetsplug.redacted.search import get_artist_id_from_red_group

    # If there are torrents in config, create and add the torrent
    if "torrents" not in group_config:
        torrent = RedSearchTorrent(**torrent_config)
        group_config["torrents"] = [torrent]

    # Create the group with the config
    group = RedSearchResult(**group_config)

    # Call the function
    artist_id = get_artist_id_from_red_group(group, log)
    assert artist_id == expected_result
