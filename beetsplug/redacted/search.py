"""Module for searching and matching albums against Redacted torrents."""

import dataclasses
import functools
import itertools
import logging
from collections.abc import Generator, Iterable
from typing import Callable, Optional, Union

from beets.library import Album  # type: ignore[import-untyped]
from pydantic import ValidationError
from ratelimit import RateLimitException  # type: ignore[import-untyped]

from beetsplug.redacted.client import Client
from beetsplug.redacted.exceptions import RedactedError
from beetsplug.redacted.matching import Matchable, extract_album_fields, score_match
from beetsplug.redacted.types import (
    BeetsRedFields,
    RedArtistResponse,
    RedArtistResponseResults,
    RedArtistTorrent,
    RedArtistTorrentGroup,
    RedSearchResult,
    RedUserTorrent,
    TorrentType,
)
from beetsplug.redacted.utils.search_utils import normalize_query


@dataclasses.dataclass
class RedTorrent:
    # Whether this torrent is preferred for matching, e.g. was drawn from the user's snatched
    # torrents, making it more likely to be in their library.
    preferred: bool = False

    artist_id: Optional[int] = None
    artist: Optional[str] = None

    group_id: Optional[int] = None
    group: Optional[str] = None
    year: Optional[int] = None

    torrent_id: Optional[int] = None
    edition_id: Optional[int] = None
    remastered: Optional[bool] = None
    remaster_year: Optional[int] = None
    remaster_catalogue_number: Optional[str] = None
    remaster_title: Optional[str] = None
    media: Optional[str] = None
    encoding: Optional[str] = None
    format: Optional[str] = None
    has_log: Optional[bool] = None
    log_score: Optional[int] = None
    has_cue: Optional[bool] = None
    scene: Optional[bool] = None
    vanity_house: Optional[bool] = None
    file_count: Optional[int] = None
    torrent_time: Optional[str] = None
    size: Optional[int] = None
    snatches: Optional[int] = None
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    is_freeleech: Optional[bool] = None
    is_neutral_leech: Optional[bool] = None
    is_freeload: Optional[bool] = None
    is_personal_freeleech: Optional[bool] = None
    trumpable: Optional[bool] = None
    can_use_token: Optional[bool] = None

    tags: Optional[list[str]] = None
    bookmarked: Optional[bool] = None
    release_type: Optional[str] = None
    group_time: Optional[int] = None

    @classmethod
    def from_search_result(
        cls, result: RedSearchResult, log: logging.Logger
    ) -> Generator["RedTorrent", None, None]:
        log.debug("Creating RedTorrent from search result: {0}", result)
        base = cls(
            preferred=False,
            group_id=result.groupId,
            group=result.groupName,
            artist=result.artist,
            tags=result.tags,
            bookmarked=result.bookmarked,
            vanity_house=result.vanityHouse,
            year=result.groupYear,
            release_type=result.releaseType,
            group_time=result.groupTime,
        )
        if result.torrents is None:
            yield base
        else:
            for torrent in result.torrents:
                copy = dataclasses.replace(
                    base,
                    torrent_id=torrent.torrentId,
                    artist_id=torrent.artists[0].id if torrent.artists else None,
                    edition_id=torrent.editionId,
                    remastered=torrent.remastered,
                    remaster_year=torrent.remasterYear,
                    remaster_catalogue_number=torrent.remasterCatalogueNumber,
                    remaster_title=torrent.remasterTitle,
                    media=torrent.media,
                    encoding=torrent.encoding,
                    format=torrent.format,
                    has_log=torrent.hasLog,
                    log_score=torrent.logScore,
                    has_cue=torrent.hasCue,
                    scene=torrent.scene,
                    vanity_house=torrent.vanityHouse,
                    file_count=torrent.fileCount,
                    torrent_time=torrent.time,
                    size=torrent.size,
                    snatches=torrent.snatches,
                    seeders=torrent.seeders,
                    leechers=torrent.leechers,
                    is_freeleech=torrent.isFreeleech,
                    is_neutral_leech=torrent.isNeutralLeech,
                    is_freeload=torrent.isFreeload,
                    is_personal_freeleech=torrent.isPersonalFreeleech,
                    trumpable=torrent.trumpable,
                    can_use_token=torrent.canUseToken,
                )
                yield copy

    @classmethod
    def from_user_torrent(cls, torrent: RedUserTorrent, log: logging.Logger) -> "RedTorrent":
        log.debug("Creating RedTorrent from user torrent: {0}", torrent)
        return cls(
            preferred=True,
            artist_id=torrent.artistId,
            artist=torrent.artistName,
            group_id=torrent.groupId,
            group=torrent.name,
            torrent_id=torrent.torrentId,
        )


def red_torrent_matchable(torrent: RedTorrent) -> Optional[Matchable]:
    """Extract normalized fields from a Redacted torrent.

    Args:
        torrent: Torrent to extract fields from

    Returns:
        MatchableFields object with normalized fields
    """
    if not torrent.artist or not torrent.group:
        return None
    return Matchable(artist=torrent.artist, title=torrent.group, year=torrent.year)


def artist_torrent_group_matchable(
    group: RedArtistTorrentGroup, artist_name: Union[str, None]
) -> Union[Matchable, None]:
    """Extract normalized fields from a Redacted artist torrent group.

    Args:
        group: Artist torrent group to extract fields from
        artist_name: Artist name to use for the match fields

    Returns:
        MatchableFields object with normalized fields
    """
    if not group.groupName or not artist_name:
        return None
    return Matchable(artist=artist_name, title=group.groupName, year=group.groupYear)


def match_album(
    album: Album, results: Iterable[RedTorrent], log: logging.Logger
) -> tuple[Optional[RedTorrent], float]:
    """Check if an album exists in search results.

    The matching algorithm uses a weighted scoring system:
    - Artist name similarity: 50% weight
    - Album name similarity: 40% weight
    - Year similarity: 10% weight

    This weighting prioritizes exact artist matches while allowing for some flexibility
    in album names and years. The year similarity is particularly lenient, allowing
    matches within 1 year of difference.

    Args:
        album: Beets album to match
        results: Search results from Redacted API
        log: Logger instance for logging messages

    Returns:
        Tuple of (group, torrent) if found with sufficient similarity,
        None otherwise. The group contains the album information and the torrent
        contains the specific release information.
    """
    # Extract album fields for matching
    album_fields = extract_album_fields(album)

    # Find the best match among all groups
    best_match: Union[RedTorrent, None] = None
    best_match_score: float = 0.0
    weights = {"artist": 0.5, "title": 0.4, "year": 0.1}

    # Score all the groups, keeping track of the best match
    for torrent in results:
        group_fields = red_torrent_matchable(torrent)
        if not group_fields:
            log.debug(
                "Could not extract matching fields from torrent {:d}, skipping", torrent.torrent_id
            )
            continue

        log.debug(
            "Matching torrent {0} - {1} ({2:d}) against album {3} - {4} ({5:d})",
            torrent.artist,
            torrent.group,
            torrent.year or 0,
            album.albumartist,
            album.album,
            album.year or 0,
        )
        match_result = score_match(album_fields, group_fields, log, weights)

        if match_result.total_score > best_match_score:
            best_match = torrent
            best_match_score = match_result.total_score

    if not best_match:
        log.debug(
            "No match found in search results for {} - {} ({:d})",
            album.albumartist,
            album.album,
            album.year,
        )
        return None, 0.0

    log.debug(
        "Found match for {} - {} ({:d}): {} - {} (score: {:.2f})",
        album_fields.artist,
        album_fields.title,
        album_fields.year,
        best_match.artist,
        best_match.group,
        best_match_score,
    )
    return best_match, best_match_score


def match_artist_album(
    album: Album,
    artist_response: RedArtistResponse,
    preferred_torrents: list[RedTorrent],
    log: logging.Logger,
    min_score: float,
) -> tuple[Union[RedArtistTorrentGroup, None], Union[RedArtistTorrent, None]]:
    """Match an album against artist's torrent groups.

    Args:
        album: Beets album to match
        artist_response: Artist data from Redacted API
        log: Logger instance for logging messages
        min_score: Minimum similarity score to consider a match (0-1)

    Returns:
        Tuple of (matching group, matching torrent) if found with sufficient similarity,
        None otherwise.
    """
    # Extract album fields for matching
    album_fields = extract_album_fields(album)

    artist_data = artist_response.response
    torrent_groups = artist_data.torrentgroup

    if not torrent_groups:
        log.debug("Artist {:s} has no torrent groups", artist_data.name)
        return None, None

    # Find the best match among all artist's torrent groups
    best_group: Union[RedArtistTorrentGroup, None] = None
    best_torrent: Union[RedArtistTorrent, None] = None
    best_match_score: float = 0.0

    # Title and year weights are more important when artist is already known
    #
    # TODO: Make these weights configurable
    weights = {"artist": 0.2, "title": 0.7, "year": 0.1}

    pt_ids = set(torrent.torrent_id for torrent in preferred_torrents)

    # Score all the groups, keeping track of the best match
    for group in torrent_groups:
        if not group.torrent:
            log.debug("Artist group {:s} has no torrents, skipping", group.groupName)
            continue

        # If this group has the preferred torrent ID, use it as the best match
        preferred_torrent = next((t for t in group.torrent if t.id in pt_ids), None)
        if preferred_torrent:
            best_group = group
            best_torrent = preferred_torrent
            best_match_score = 1.0
            break

        group_fields = artist_torrent_group_matchable(group, artist_data.name)
        if not group_fields:
            log.debug(
                "Could not extract matching fields from artist group {0}, skipping", group.groupName
            )
            continue

        # Score match considering that we know we're matching against the correct artist
        match_result = score_match(album_fields, group_fields, log, weights)

        # Choose the best matching torrent amongst the group (largest size)
        #
        # TODO: We should consider other factors like format, media, and encoding
        match_best_torrent = max(group.torrent, key=lambda x: x.size or 0)
        if not match_best_torrent:
            log.debug("Artist group {:s} has no torrents, skipping", group.groupName)
            continue

        if match_result.total_score > best_match_score:
            best_match_score = match_result.total_score
            best_torrent = match_best_torrent
            best_group = group

    if not best_group or not best_torrent:
        log.debug(
            "No match with torrents found in artist {0}'s groups (checked {1:d} groups, "
            "best score: {2:.2f}). Artist response: id={3:d}, name={4}, groups={5}",
            artist_data.name,
            len(torrent_groups),
            best_match_score,
            artist_data.id,
            artist_data.name,
            [(g.groupId, g.groupName, g.groupYear) for g in torrent_groups if g.groupName],
        )
        return None, None

    if best_match_score < min_score:
        log.debug(
            "Best match for {0} in artist's groups was {1} (score: {2:.2f}, "
            "below threshold {3:.2f})",
            album_fields.title,
            best_group.groupName,
            best_match_score,
            min_score,
        )
        return None, None

    log.debug(
        "Best match for {0} from artist's groups: {1} (score: {2:.2f})",
        album_fields.title,
        best_group.groupName,
        best_match_score,
    )

    return best_group, best_torrent


def beets_fields_from_artist_torrent_groups(
    artist: RedArtistResponseResults,
    group: RedArtistTorrentGroup,
    torrent: RedArtistTorrent,
    log: logging.Logger,
) -> Union[BeetsRedFields, None]:
    """Extract fields from an artist group and torrent match.

    Args:
        artist: Artist result containing the match
        group: Group containing the match
        torrent: Matching torrent
        log: Logger instance for logging messages
    Returns:
        RedTorrentFields object with fields to update on the album, or None if validation fails
    """
    fields = None

    for field in dataclasses.fields(BeetsRedFields):
        from_meta = field.metadata.get("from")
        if not from_meta:
            continue

        source_cls = from_meta.get_source_cls()
        source_obj: Union[
            RedArtistResponseResults, RedArtistTorrentGroup, RedArtistTorrent, None
        ] = None
        if source_cls == RedArtistResponseResults:
            source_obj = artist
        elif source_cls == RedArtistTorrentGroup:
            source_obj = group
        elif source_cls == RedArtistTorrent:
            source_obj = torrent
        else:
            log.debug("Unsupported source class: {0}", source_cls)
            continue

        value = from_meta.get_value(source_obj)
        if not value:
            if field.metadata.get("required", False):
                log.debug("Field {0} is required but has no value, skipping match.", field.name)
                return None
            else:
                continue

        try:
            if fields is None:
                fields = BeetsRedFields()
            setattr(fields, field.name, value)
        except (ValueError, TypeError, ValidationError) as e:
            log.debug(
                "Error mapping field {0} from source ({1}) to Beets field ({2}).\n"
                "    Source class: {3}, value: {4}\n"
                "    Error: {5}",
                field.name,
                source_cls,
                field.name,
                source_cls,
                value,
                e,
            )
            return None

    return fields


def best_match_from_snatched(
    client: Client, album: Album, log: logging.Logger
) -> tuple[Optional[RedTorrent], float]:
    # Look up the user's snatched torrents. We will always add these in to the set of torrents
    # to match.
    log.debug("Retrieving user's snatched torrents")
    user_response = client.user(TorrentType.SNATCHED)
    if not (user_response and user_response.response and user_response.response.snatched):
        log.debug("No snatched torrents found")
        return None, 0.0

    snatched_torrents = [
        RedTorrent.from_user_torrent(torrent, log) for torrent in user_response.response.snatched
    ]

    # Is there a good match in the user's snatched torrents?
    return match_album(album, snatched_torrents, log)


def best_match_from_search(
    client: Client, album: Album, c_artist: str, c_album: str, log: logging.Logger
) -> tuple[Optional[RedTorrent], float]:
    log.debug("Searching for torrents matching {0} - {1}", c_artist, c_album)
    search_query = normalize_query(c_artist, c_album, log)
    if not search_query:
        log.debug("Could not construct search query for {0} - {1}", c_artist, c_album)
        return None, 0.0

    log.debug("Searching for torrents with query: {0}", search_query)
    search_response = client.search(search_query)

    if not (search_response and search_response.response and search_response.response.results):
        log.debug("No search results found")
        return None, 0.0

    results = [
        RedTorrent.from_search_result(group, log) for group in search_response.response.results
    ]

    return match_album(album, itertools.chain.from_iterable(results), log)


def search(
    album: Album, client: Client, log: logging.Logger, min_score: float
) -> Union[BeetsRedFields, None]:
    """Search for Redacted torrents matching an album using a two-step process.

    First searches for torrents using the browse API, then looks up artist details
    for more accurate matching.

    Args:
        album: Album to search for
        client: RedactedClient instance
        log: Logger instance for logging messages
        min_score: Minimum similarity score to consider a match (0-1)

    Returns:
        Dictionary of fields to update on the album if match found, None otherwise
    """
    # Find the best matching torrent, from the user's snatches or search, which we'll then use
    # to look up the artist and get the best match from the artist's discography.

    def matchers() -> Generator[Callable[[], tuple[Optional[RedTorrent], float]], None, None]:
        # First try to match from the user's snatched torrents
        yield functools.partial(best_match_from_snatched, client, album, log)

        # Then try to match from the search results, using variations of the artist and album names,
        # starting with the most likely.
        for c_artist, c_album in itertools.product(
            (
                album.albumartist,
                album.albumartist_credit,
                album.albumartist_sort,
                album.albumartists,
            ),
            (album.album, album.albumdisambig),
        ):
            yield functools.partial(best_match_from_search, client, album, c_artist, c_album, log)

    best_match = None
    best_match_score = 0.0
    best_matcher = None
    preferred_torrents = []
    for matcher in matchers():
        try:
            match, score = matcher()
        except (RedactedError, RateLimitException) as e:
            log.debug(
                "Error retrieving torrents for artist '{0}', album '{1}' "
                "with matcher function {2}: {3}",
                album.albumartist,
                album.album,
                matcher,
                e,
            )
            continue

        if match and score > best_match_score:
            best_match = match
            best_match_score = score
            best_matcher = matcher

        if match and match.preferred:
            preferred_torrents.append(match)

    if not best_match or best_match_score < min_score:
        log.debug(
            "No good search result for {0} - {1} ({2:d}) (min {3:.2f}, best was {4:.2f})",
            album.get("albumartist"),
            album.get("album"),
            album.get("year", 0),
            min_score,
            best_match_score,
        )
        return None
    else:
        log.debug(
            "Matched good search result for {0} - {1} ({2:d}) (min {3:.2f}, best was {4:.2f}) "
            "using matcher {5}",
            album.get("albumartist"),
            album.get("album"),
            album.get("year", 0),
            min_score,
            best_match_score,
            best_matcher,
        )

    # Extract artist ID for detailed lookup
    artist_id = best_match.artist_id
    if not artist_id:
        # No artist ID means we can't do the second step of the lookup
        # According to requirements, we should return None in this case
        log.debug(
            "No artist ID found in snatches or search results, best match was {0}", best_match
        )
        return None

    # Look up artist details for better matching
    try:
        log.debug("Looking up artist details for artist {0:d}", artist_id)
        artist_data = client.get_artist(artist_id)
    except (RedactedError, RateLimitException) as e:
        # Artist lookup failed, return None per requirements
        log.debug("Error looking up artist {0:d}: {1}", artist_id, e)
        return None

    # Find a match for the album in the artist's discography
    artist_group, artist_torrent = match_artist_album(
        album, artist_data, preferred_torrents, log, min_score
    )
    if artist_group and artist_torrent:
        # Extract album update fields from artist group (album) and torrent match
        return beets_fields_from_artist_torrent_groups(
            artist_data.response, artist_group, artist_torrent, log
        )

    # If there is no match among the artist's information, we consider this to be an error condition
    log.debug(
        "No match found in artist's discography for {0} - {1}", album.albumartist, album.album
    )
    return None
