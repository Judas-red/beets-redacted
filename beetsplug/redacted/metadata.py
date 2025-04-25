"""Metadata plugin for Redacted.

Provides metadata matches for the autotagger from Redacted's API.
"""

import logging
from typing import Optional

from beets.library import Album, Item  # type: ignore[import-untyped]

from beetsplug.redacted import client
from beetsplug.redacted.utils.search_utils import normalize_query


def candidates(
    client: client.Client,
    log: logging.Logger,
    items: list[Item],
    artist: str,
    album: str,
    va_likely: bool,
    extra_tags: Optional[dict[str, str]] = None,
) -> list[Album]:
    """Return a list of Albums that are candidate matches for a release.

    Args:
        client: The Redacted client to use for searching
        items: The items to match
        artist: The artist to search for
        album: The album to search for
        va_likely: Whether this is likely a Various Artists album
        extra_tags: Additional tags to add to the album

    Returns:
        A list of Albums that are candidate matches
    """
    # Skip VA albums as they require special handling
    if va_likely:
        return []

    # Normalize the search query
    query = normalize_query(artist, album, log)
    if not query:
        return []

    try:
        # Search for the album on Redacted
        response = client.search(query)
        if not response or not response.response or not response.response.results:
            return []

        # Convert the search results to Beets Album objects
        albums = []
        for result in response.response.results:
            candidate = Album()
            candidate.albumartist = result.artist
            candidate.album = result.groupName
            candidate.year = result.groupYear
            albums.append(candidate)

        return albums

    except Exception as e:
        log.error(f"Error searching Redacted: {e}")
        return []
