"""Module for searching and matching albums against Redacted torrents."""

import dataclasses
import itertools
import logging
from typing import Union

from beets.library import Album  # type: ignore[import-untyped]
from pydantic import ValidationError
from ratelimit import RateLimitException  # type: ignore[import-untyped]

from beetsplug.redacted.client import RedactedClient
from beetsplug.redacted.exceptions import RedactedError
from beetsplug.redacted.matching import Matchable, extract_album_fields, score_match
from beetsplug.redacted.types import (
    BeetsRedFields,
    RedArtistResponse,
    RedArtistResponseResults,
    RedArtistTorrent,
    RedArtistTorrentGroup,
    RedSearchResponse,
    RedSearchResult,
)
from beetsplug.redacted.utils.search_utils import normalize_query


def torrent_group_matchable(group: RedSearchResult) -> Union[Matchable, None]:
    """Extract normalized fields from a Redacted torrent group.

    Args:
        group: Group to extract fields from

    Returns:
        MatchableFields object with normalized fields
    """
    if not group.artist or not group.groupName:
        return None
    return Matchable(artist=group.artist, title=group.groupName, year=group.groupYear)


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
    album: Album, results: RedSearchResponse, log: logging.Logger, min_score: float
) -> tuple[Union[RedSearchResult, None], float]:
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
        min_score: Minimum similarity score to consider a match (0-1)

    Returns:
        Tuple of (group, torrent) if found with sufficient similarity,
        None otherwise. The group contains the album information and the torrent
        contains the specific release information.
    """
    # Extract album fields for matching
    album_fields = extract_album_fields(album)

    # Get all groups from the response
    response = results.response
    groups = response.results
    if not groups:
        log.debug("No groups found in search results")
        return None, 0.0

    # Find the best match among all groups
    best_match: Union[RedSearchResult, None] = None
    best_match_score: float = 0.0
    weights = {"artist": 0.5, "title": 0.4, "year": 0.1}

    # Score all the groups, keeping track of the best match
    for group in groups:
        if not group.torrents:
            log.debug("Group {:d} has no torrents, skipping", group.groupId)
            continue

        group_fields = torrent_group_matchable(group)
        if not group_fields:
            log.debug("Could not extract matching fields from group {:d}, skipping", group.groupId)
            continue

        match_result = score_match(album_fields, group_fields, log, weights)

        if match_result.total_score > best_match_score:
            best_match = group
            best_match_score = match_result.total_score

    if not best_match:
        log.debug(
            "No match found in search results for {} - {} ({:d})",
            album.albumartist,
            album.album,
            album.year,
        )
        return None, 0.0

    if best_match_score < min_score:
        log.debug(
            "Best match for {} - {} ({:d}) was {} - {} (score: {:.2f}, below threshold {:.2f})",
            album.albumartist,
            album.album,
            album.year,
            best_match.artist,
            best_match.groupName,
            best_match_score,
            min_score,
        )
        return None, 0.0

    log.debug(
        "Found match for {} - {} ({:d}): {} - {} (score: {:.2f})",
        album_fields.artist,
        album_fields.title,
        album_fields.year,
        best_match.artist,
        best_match.groupName,
        best_match_score,
    )
    return best_match, best_match_score


def match_artist_album(
    album: Album, artist_response: RedArtistResponse, log: logging.Logger, min_score: float
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
    weights = {"artist": 0.2, "title": 0.7, "year": 0.1}

    # Score all the groups, keeping track of the best match
    for group in torrent_groups:
        if not group.torrent:
            log.debug("Artist group {:s} has no torrents, skipping", group.groupName)
            continue

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


def get_artist_id_from_red_group(group: RedSearchResult, log: logging.Logger) -> Union[int, None]:
    """Extract artist ID from a torrent.

    Args:
        group: Group containing the torrent
        log: Logger instance for logging messages

    Returns:
        Artist ID if found, None otherwise
    """
    if not group.torrents:
        log.debug("Group {0:d} has no torrents, cannot determine artist id.", group.groupId)
        return None

    try:
        torrent = group.torrents[0]
        if not torrent.artists:
            log.debug(
                "Torrent {0:d} has no artists, cannot determine artist id.", torrent.torrentId
            )
            return None

        return torrent.artists[0].id
    except (IndexError, AttributeError) as e:
        log.debug("Error extracting artist ID from group {0:d}: {1}", group.groupId, e)
        return None


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


def search(
    album: Album, client: RedactedClient, log: logging.Logger, min_score: float
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
    # Step 1: Find the best initial match using the browse API
    best_search_match = None
    best_match_score = 0.0
    for artist_c, album_c in itertools.product(
        (album.albumartist, album.albumartist_credit, album.albumartist_sort, album.albumartists),
        (album.album, album.albumdisambig),
    ):
        search_query = normalize_query(artist_c, album_c, log)
        if not search_query:
            log.debug(
                "Could not construct search query for {0} - {1}", album.albumartist, album.album
            )
            continue

        try:
            log.debug("Searching for torrents with query: {0}", search_query)
            results = client.browse(search_query)
        except (RedactedError, RateLimitException) as e:
            log.debug(
                "Error searching for torrents for {0} - {1}: {2}", album.albumartist, album.album, e
            )
            continue

        search_match, match_score = match_album(album, results, log, min_score)
        if search_match and match_score > best_match_score:
            best_match_score = match_score
            best_search_match = search_match
            break

    if not best_search_match:
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
            "Matched good search result for {0} - {1} ({2:d}) (min {3:.2f}, best was {4:.2f})",
            album.get("albumartist"),
            album.get("album"),
            album.get("year", 0),
            min_score,
            best_match_score,
        )

    # Extract artist ID for detailed lookup
    artist_id = get_artist_id_from_red_group(best_search_match, log)
    if not artist_id:
        # No artist ID means we can't do the second step of the lookup
        # According to requirements, we should return None in this case
        log.debug(
            "No artist ID found in search result torrent group {0:d}", best_search_match.groupId
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
    artist_group, artist_torrent = match_artist_album(album, artist_data, log, min_score)
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
