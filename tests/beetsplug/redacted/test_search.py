"""Tests for search_torrents.py functionality."""

import dataclasses
import itertools
from collections.abc import Iterable
from typing import Optional, Union

import pytest
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from beetsplug.redacted.matching import Matchable
from beetsplug.redacted.search import (
    BeetsRedFields,
    RedTorrent,
    match_artist_album,
    red_torrent_matchable,
    search,
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
    RedUserResponse,
    RedUserResponseResults,
    RedUserTorrent,
)
from beetsplug.redacted.utils.test_utils import FakeAlbum, FakeClient, FakeLibrary, FakeLogger

TEST_ARTIST_ID = 1
TEST_GROUP_ID = 2
TEST_TORRENT_ID = 3
TEST_ALBUM_ID = 4
TEST_ARTIST_NAME = "Artist"
TEST_ALBUM_NAME = "Album"
TEST_ALBUM_YEAR = 2020


@pytest.fixture
def log() -> FakeLogger:
    """Create a fake logger for testing."""
    return FakeLogger()


@pytest.fixture
def client() -> FakeClient:
    """Create a fake client for testing."""
    return FakeClient()


def make_album(
    id: int = 0,
    artist: str = TEST_ARTIST_NAME,
    artist_sort: str = TEST_ARTIST_NAME,
    name: str = TEST_ALBUM_NAME,
    year: int = TEST_ALBUM_YEAR,
    media: str = "CD",
    format: str = "FLAC",
) -> FakeAlbum:
    """Create a test album for testing."""
    lib = FakeLibrary(
        [
            {
                "id": id,
                "albumartist": artist,
                "albumartist_sort": artist_sort,
                "album": name,
                "albumdisambig": "The Great Test Album",
                "year": year,
                "media": media,
                "format": format,
            }
        ]
    )
    return lib.albums()[0]


@pytest.fixture
def album() -> FakeAlbum:
    """Create a test album for testing."""
    return make_album()


def make_user_torrent(
    group_id: int = TEST_GROUP_ID,
    name: str = TEST_ALBUM_NAME,
    artist_name: str = TEST_ARTIST_NAME,
    artist_id: int = TEST_ARTIST_ID,
    torrent_id: int = TEST_TORRENT_ID,
) -> RedUserTorrent:
    return RedUserTorrent(
        groupId=group_id,
        name=name,
        torrentId=torrent_id,
        artistName=artist_name,
        artistId=artist_id,
    )


def make_user_response(
    seeding: Iterable[RedUserTorrent] = tuple(),
    leeching: Iterable[RedUserTorrent] = tuple(),
    uploaded: Iterable[RedUserTorrent] = tuple(),
    snatched: Iterable[RedUserTorrent] = tuple(),
) -> RedUserResponse:
    return RedUserResponse(
        status="success",
        response=RedUserResponseResults(
            seeding=list(seeding),
            leeching=list(leeching),
            uploaded=list(uploaded),
            snatched=list(snatched),
        ),
    )


def make_test_torrent(artist_id: int = TEST_ARTIST_ID) -> RedSearchTorrent:
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
def test_torrent() -> RedSearchTorrent:
    """Create a test torrent for testing."""
    return make_test_torrent()


def make_artist_torrent(
    torrent_id: int = TEST_TORRENT_ID,
    group_id: int = TEST_GROUP_ID,
    media: Optional[str] = None,
    format: Optional[str] = None,
    encoding: Optional[str] = None,
    remaster_year: Optional[int] = None,
    remastered: Optional[bool] = None,
) -> RedArtistTorrent:
    """Create a test artist torrent for testing."""
    return RedArtistTorrent(
        id=torrent_id,
        groupId=group_id,
        media=media,
        format=format,
        encoding=encoding,
        remasterYear=remaster_year,
        remastered=remastered,
    )


@pytest.fixture
def test_artist_torrent() -> RedArtistTorrent:
    """Create a test artist torrent for testing."""
    return make_artist_torrent()


def make_artist_group(
    group_id: int = TEST_GROUP_ID,
    name: str = TEST_ALBUM_NAME,
    year: int = TEST_ALBUM_YEAR,
    torrents: Iterable[RedArtistTorrent] = tuple(),
) -> RedArtistTorrentGroup:
    """Create a test artist group for testing."""
    return RedArtistTorrentGroup(
        groupId=group_id, groupName=name, groupYear=year, torrent=list(torrents)
    )


@pytest.fixture
def test_artist_group() -> RedArtistTorrentGroup:
    """Create a test artist group for testing."""
    return make_artist_group()


def make_group(
    group_id: int = TEST_GROUP_ID,
    artist: str = TEST_ARTIST_NAME,
    name: str = TEST_ALBUM_NAME,
    torrent_id: int = TEST_TORRENT_ID,
    year: Optional[int] = TEST_ALBUM_YEAR,
    artist_id: Optional[int] = TEST_ARTIST_ID,
    torrent: Union[RedSearchTorrent, None] = None,
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
        torrentId=torrent_id,
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


def make_search_response(groups: list[RedSearchResult]) -> RedSearchResponse:
    """Set up search responses for the client.

    Args:
        groups: The groups to include in the response
    """
    return RedSearchResponse(status="success", response=RedSearchResults(results=groups))


@pytest.fixture
def test_search_responses() -> RedSearchResponse:
    """Create a test search response."""
    return make_search_response([make_group()])


def make_artist_response(
    artist_id: int = TEST_ARTIST_ID,
    name: str = TEST_ARTIST_NAME,
    groups: Iterable[RedArtistTorrentGroup] = tuple(),
) -> RedArtistResponse:
    """Set up artist response for the client.

    Args:
        artist_id: The artist ID to respond to
        artist_name: The artist name
        torrent_groups: The torrent groups to include in the response
    """
    return RedArtistResponse(
        status="success",
        response=RedArtistResponseResults(
            id=artist_id,
            name=name,
            notificationsEnabled=False,
            hasBookmarked=False,
            torrentgroup=list(groups),
            requests=[],
        ),
    )


@pytest.fixture
def test_artist_response() -> RedArtistResponse:
    """Create a test artist response."""
    return make_artist_response()


def make_beets_fields(
    artist_id: int,
    artist_name: str,
    group_id: int,
    group_name: str,
    group_year: int,
    torrent_id: int,
) -> BeetsRedFields:
    return BeetsRedFields(
        red_artistid=artist_id,
        red_groupid=group_id,
        red_torrentid=torrent_id,
        red_artist=artist_name,
        red_groupname=group_name,
        red_groupyear=group_year,
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


@pytest.mark.parametrize(
    "artist,name,year,expected_fields",
    [
        pytest.param(
            TEST_ARTIST_NAME,
            TEST_ALBUM_NAME,
            TEST_ALBUM_YEAR,
            Matchable(artist=TEST_ARTIST_NAME, title=TEST_ALBUM_NAME, year=TEST_ALBUM_YEAR),
            id="valid_group",
        ),
        pytest.param("", TEST_ALBUM_NAME, TEST_ALBUM_YEAR, None, id="missing_artist"),
        pytest.param(TEST_ARTIST_NAME, "", TEST_ALBUM_YEAR, None, id="missing_name"),
        pytest.param(
            TEST_ARTIST_NAME,
            TEST_ALBUM_NAME,
            None,
            Matchable(artist=TEST_ARTIST_NAME, title=TEST_ALBUM_NAME, year=None),
            id="missing_year",
        ),
    ],
)
def test_extract_group_fields(
    artist: str, name: str, year: Optional[int], expected_fields: Optional[Matchable]
) -> None:
    """Test extracting fields from a group with various field combinations."""
    # Create group with provided fields
    group = RedTorrent(artist=artist, group=name, year=year)

    fields = red_torrent_matchable(group)
    assert fields == expected_fields


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
    "group_config, preferred_torrents, expected",
    [
        pytest.param({"torrentgroup": []}, [], (None, None), id="no_torrent_groups"),
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
            [],
            (None, None),
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
            [],
            (None, None),
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
            [],
            (None, None),
            id="low_score_match",
        ),
        pytest.param(
            {
                "torrentgroup": [
                    RedArtistTorrentGroup(
                        groupId=TEST_GROUP_ID,
                        groupName=TEST_ALBUM_NAME,
                        groupYear=TEST_ALBUM_YEAR,
                        torrent=[
                            RedArtistTorrent(id=TEST_TORRENT_ID, groupId=TEST_GROUP_ID),
                            RedArtistTorrent(id=TEST_TORRENT_ID + 1, groupId=TEST_GROUP_ID),
                            RedArtistTorrent(id=TEST_TORRENT_ID + 2, groupId=TEST_GROUP_ID),
                        ],
                    )
                ]
            },
            [RedTorrent(torrent_id=TEST_TORRENT_ID + 1, group_id=TEST_GROUP_ID)],
            (
                RedArtistTorrentGroup(
                    groupId=TEST_GROUP_ID,
                    groupName=TEST_ALBUM_NAME,
                    groupYear=TEST_ALBUM_YEAR,
                    torrent=[],
                ),
                RedArtistTorrent(id=TEST_TORRENT_ID + 1, groupId=TEST_GROUP_ID),
            ),
            id="preferred_torrent",
        ),
    ],
)
def test_match_artist_album_edge_cases(
    log: FakeLogger,
    album: FakeAlbum,
    group_config: dict,
    preferred_torrents: list[RedTorrent],
    expected: Union[tuple[RedArtistTorrentGroup, RedArtistTorrent], None],
) -> None:
    """Test match_artist_album with parameterized edge cases."""
    response = RedArtistResponse(
        status="success",
        response=RedArtistResponseResults(id=TEST_ARTIST_ID, name=TEST_ARTIST_NAME, **group_config),
    )

    result = match_artist_album(album, response, preferred_torrents, log, min_score=0.75)
    if result and result[0]:
        # Clear the torrent list from the group to simplify testing.
        result[0].torrent = []
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


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class SearchTestParams:
    album: FakeAlbum
    user_response: Optional[RedUserResponse] = None
    search_responses: list[RedSearchResponse] = Field(default_factory=list)
    search_query_errors: list[str] = Field(default_factory=list)
    artist_responses: list[RedArtistResponse] = Field(default_factory=list)
    artist_query_errors: list[int] = Field(default_factory=list)
    expected: Optional[BeetsRedFields] = None


search_test_album = make_album(artist=TEST_ARTIST_NAME, name=TEST_ALBUM_NAME)
search_test_user_response = make_user_response(
    snatched=[
        make_user_torrent(
            artist_id=TEST_ARTIST_ID,
            artist_name=TEST_ARTIST_NAME,
            group_id=TEST_GROUP_ID,
            name=TEST_ALBUM_NAME,
            torrent_id=TEST_TORRENT_ID,
        )
    ]
)
search_test_search_response = make_search_response(
    [
        make_group(
            group_id=TEST_GROUP_ID,
            artist_id=TEST_ARTIST_ID,
            artist=TEST_ARTIST_NAME,
            name=TEST_ALBUM_NAME,
            year=TEST_ALBUM_YEAR,
            torrent_id=TEST_TORRENT_ID,
        )
    ]
)
search_test_artist_response = make_artist_response(
    artist_id=TEST_ARTIST_ID,
    name=TEST_ARTIST_NAME,
    groups=[
        make_artist_group(
            group_id=TEST_GROUP_ID,
            name=TEST_ALBUM_NAME,
            year=TEST_ALBUM_YEAR,
            torrents=[make_artist_torrent(torrent_id=TEST_TORRENT_ID, group_id=TEST_GROUP_ID)],
        )
    ],
)
search_test_expected = make_beets_fields(
    artist_id=TEST_ARTIST_ID,
    artist_name=TEST_ARTIST_NAME,
    group_id=TEST_GROUP_ID,
    group_name=TEST_ALBUM_NAME,
    group_year=TEST_ALBUM_YEAR,
    torrent_id=TEST_TORRENT_ID,
)


@pytest.mark.parametrize(
    "description, parameters",
    [
        pytest.param(
            "Both user and search queries fail; No path to Artist so no results.",
            SearchTestParams(
                album=search_test_album,
                user_response=None,
                search_query_errors=["Artist Album"],
                expected=None,
            ),
            id="all_fail",
        ),
        pytest.param(
            "User lookup fails, search succeeds, artist succeeds; "
            "Results from search -> Artist path.",
            SearchTestParams(
                album=search_test_album,
                user_response=None,
                search_responses=[search_test_search_response],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="user_fails",
        ),
        pytest.param(
            "User lookup succeeds, search fails, artist succeeds; "
            "Results from user -> Artist path.",
            SearchTestParams(
                album=search_test_album,
                user_response=search_test_user_response,
                search_query_errors=["Artist Album"],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="search_fails",
        ),
        pytest.param(
            "User lookup succeeds, search succeeds, artist fails; "
            "No artist results to draw from, so no results.",
            SearchTestParams(
                album=search_test_album,
                user_response=search_test_user_response,
                search_responses=[search_test_search_response],
                artist_query_errors=[TEST_ARTIST_ID],
                expected=None,
            ),
            id="artist_fails",
        ),
        pytest.param(
            "Search returns relevant groups that don't have artist values; No results.",
            SearchTestParams(
                album=make_album(artist="Artist", name="Album"),
                search_responses=[
                    make_search_response(
                        [
                            make_group(
                                group_id=TEST_GROUP_ID,
                                artist_id=None,
                                artist=TEST_ARTIST_NAME,
                                name=TEST_ALBUM_NAME,
                                year=TEST_ALBUM_YEAR,
                                torrent=RedSearchTorrent(
                                    artists=[],
                                    torrentId=TEST_TORRENT_ID,
                                    editionId=1,
                                    media="CD",
                                    format="FLAC",
                                    encoding="Lossless",
                                ),
                            )
                        ]
                    )
                ],
                expected=None,
            ),
            id="search_returns_groups_without_artist_id",
        ),
        # Success cases
        pytest.param(
            "User lookup succeeds, search succeeds, artist succeeds; "
            "Results from user + search -> artist path.",
            SearchTestParams(
                album=search_test_album,
                user_response=search_test_user_response,
                search_responses=[search_test_search_response],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="nominal",
        ),
        pytest.param(
            "User lookup doesn't have matching snatched torrent; "
            "Results from search -> artist path.",
            SearchTestParams(
                album=search_test_album,
                user_response=make_user_response(
                    snatched=[
                        make_user_torrent(
                            group_id=TEST_GROUP_ID + 20,
                            artist_id=TEST_ARTIST_ID + 20,
                            artist_name="A different artist",
                            name="A different album",
                            torrent_id=TEST_TORRENT_ID + 20,
                        )
                    ]
                ),
                search_responses=[search_test_search_response],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="no_matching_snatches",
        ),
        pytest.param(
            "Search doesn't have matching groups; " "Results from user -> artist path.",
            SearchTestParams(
                album=search_test_album,
                user_response=search_test_user_response,
                search_responses=[
                    make_search_response(
                        [
                            make_group(
                                group_id=TEST_GROUP_ID + 20,
                                artist_id=TEST_ARTIST_ID + 20,
                                artist="A different artist",
                                name="A different album",
                                year=TEST_ALBUM_YEAR,
                            )
                        ]
                    )
                ],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="no_matching_search_results",
        ),
        pytest.param(
            "User snatches match a specific torrent, which should be selected from "
            "the artist's groups' torrents.",
            SearchTestParams(
                album=search_test_album,
                user_response=make_user_response(
                    snatched=[
                        make_user_torrent(
                            group_id=TEST_GROUP_ID,
                            artist_id=TEST_ARTIST_ID,
                            artist_name=TEST_ARTIST_NAME,
                            name=TEST_ALBUM_NAME,
                            # Specific torrent id; should be selected and used.
                            torrent_id=17,
                        )
                    ]
                ),
                search_responses=[search_test_search_response],
                artist_responses=[
                    make_artist_response(
                        artist_id=TEST_ARTIST_ID,
                        name=TEST_ARTIST_NAME,
                        groups=[
                            make_artist_group(
                                group_id=TEST_GROUP_ID,
                                torrents=[
                                    make_artist_torrent(
                                        torrent_id=TEST_TORRENT_ID, group_id=TEST_GROUP_ID
                                    ),
                                    make_artist_torrent(torrent_id=17, group_id=TEST_GROUP_ID),
                                ],
                            )
                        ],
                    )
                ],
                expected=make_beets_fields(
                    artist_id=TEST_ARTIST_ID,
                    artist_name=TEST_ARTIST_NAME,
                    group_id=TEST_GROUP_ID,
                    group_name=TEST_ALBUM_NAME,
                    group_year=TEST_ALBUM_YEAR,
                    torrent_id=17,
                ),
            ),
            id="user_snatches_match_torrent",
        ),
        pytest.param(
            "Search has a relevant group, but the artist response has a better match.",
            SearchTestParams(
                album=make_album(artist="Artist", name="Album"),
                user_response=None,
                search_responses=[
                    make_search_response(
                        [
                            make_group(
                                group_id=TEST_GROUP_ID + 1,
                                artist_id=TEST_ARTIST_ID,
                                artist="Artist",
                                # Close match, but not exactly right.
                                name="Album Covers",
                                year=TEST_ALBUM_YEAR,
                            )
                        ]
                    )
                ],
                artist_responses=[
                    make_artist_response(
                        artist_id=TEST_ARTIST_ID,
                        name="Artist",
                        groups=[
                            make_artist_group(
                                group_id=TEST_GROUP_ID,
                                # Exact match.
                                name="Album",
                                year=TEST_ALBUM_YEAR,
                                torrents=[
                                    make_artist_torrent(
                                        torrent_id=TEST_TORRENT_ID, group_id=TEST_GROUP_ID
                                    )
                                ],
                            ),
                            make_artist_group(
                                group_id=TEST_GROUP_ID + 1,
                                name="Album Covers",
                                year=TEST_ALBUM_YEAR + 10,
                                torrents=[
                                    make_artist_torrent(
                                        torrent_id=TEST_TORRENT_ID + 1, group_id=TEST_GROUP_ID + 1
                                    )
                                ],
                            ),
                        ],
                    )
                ],
                expected=search_test_expected,
            ),
            id="artist_has_better_match",
        ),
        pytest.param(
            "Search returns values for a variant of the artist's name.",
            SearchTestParams(
                album=make_album(
                    artist="Artist Variant", artist_sort=TEST_ARTIST_NAME, name=TEST_ALBUM_NAME
                ),
                user_response=search_test_user_response,
                search_responses=[search_test_search_response],
                artist_responses=[search_test_artist_response],
                expected=search_test_expected,
            ),
            id="search_artist_name_variants",
        ),
    ],
)
def test_search(log: FakeLogger, description: str, parameters: SearchTestParams) -> None:
    client = FakeClient()

    if parameters.user_response:
        client.user_response = parameters.user_response

    for search_response in parameters.search_responses:
        client.search_responses[f"{TEST_ARTIST_NAME} {TEST_ALBUM_NAME}"] = search_response

    for search_query_error in parameters.search_query_errors:
        client.error_queries.add(search_query_error)

    for artist_response in parameters.artist_responses:
        assert artist_response.response.id is not None
        client.artist_responses[artist_response.response.id] = artist_response

    for artist_query_error in parameters.artist_query_errors:
        client.error_artist_queries.add(artist_query_error)

    result = search(parameters.album, client, log, min_score=0.75)

    if parameters.expected is None:
        assert result is None
    elif result is None:
        raise ValueError(f"{description}: got None, expected {parameters.expected}")
    else:
        expected = parameters.expected
        for field, expected_value in expected.__dict__.items():
            if field == "red_mtime":
                continue

            if not hasattr(result, field):
                raise ValueError(
                    f"{description}: expected field {field} not found in result: {result}"
                )

            actual_value = getattr(result, field)
            assert (
                actual_value == expected_value
            ), f"{description}: expected {expected_value} for field {field}, got {actual_value}"
