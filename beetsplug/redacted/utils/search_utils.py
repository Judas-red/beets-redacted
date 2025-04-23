import logging
import re
from typing import Union


def normalize_query(artist: Union[str, list[str]], album: str, log: logging.Logger) -> Union[str, None]:
    """Normalize a query string for searching.

    Args:
        query: The query string to normalize

    Returns:
        The normalized query string
    """
    if isinstance(artist, list):
        artist = " ".join(artist)

    # Remove featuring artists to improve search results
    artist = re.sub(
        r"\s+(and|ft\.?|feat\.?|featuring|\+|\&) .*", " ", artist, flags=re.IGNORECASE
    ).strip()

    # Remove common release format terms that can interfere with search
    album = re.sub(
        r"\b(Web|CD|EP|Single|Vinyl|LP|Box Set|Disc|Collection|Volume|"
        r"Years Of|Extended Version|Vol|Volume|Anniversary Edition|"
        r"Remaster|Remastered|)\b",
        "",
        album,
        flags=re.IGNORECASE,
    )

    query = f"{artist} {album}"

    # Remove text within parentheses, such as "(2015 Remaster)"
    query = re.sub(r"\(.*\)", " ", query, flags=re.IGNORECASE)
    query = re.sub(r"\[.*\]", " ", query, flags=re.IGNORECASE)

    # Remove non-alphanumeric characters
    query = re.sub(r"[^\w\d]", " ", query)

    # Normalize whitespace: replace multiple spaces with a single space and strip
    query = re.sub(r"\s+", " ", query).strip()

    log.debug("Search query: {0}", query)
    if not query:
        return None
    return query
