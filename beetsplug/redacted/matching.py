"""Module for matching albums against Redacted results."""

import logging
from difflib import SequenceMatcher
from typing import Union

from beets.library import Album  # type: ignore[import-untyped]
from pydantic.dataclasses import dataclass


@dataclass
class Matchable:
    """Common fields that can be used for matching."""

    # Required fields with defaults to avoid initialization issues
    artist: str = ""
    title: str = ""

    # Optional fields
    year: Union[int, None] = None
    media: Union[str, None] = None
    format: Union[str, None] = None


@dataclass
class MatchResult:
    """Result of a match scoring operation."""

    total_score: float
    field_scores: dict[str, float]


def string_similarity(a: str, b: str) -> float:
    """Calculate string similarity using SequenceMatcher.

    Args:
        a: First string
        b: Second string

    Returns:
        Similarity score between 0 and 1
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def year_similarity(year1: Union[int, None], year2: Union[int, None]) -> float:
    """Calculate year similarity.

    Args:
        year1: First year
        year2: Second year

    Returns:
        Similarity score between 0 and 1
    """
    if year1 is None or year2 is None:
        return 1.0  # If either year is missing, don't penalize the match

    if year1 == year2:
        return 1.0

    if abs(year1 - year2) <= 1:
        return 0.5  # If years are within 1 year, consider it a partial match

    return 0.0  # Different years are considered completely different


def extract_album_fields(album: Album) -> Matchable:
    """Extract normalized fields from a Beets album.

    Args:
        album: Beets album to extract fields from

    Returns:
        MatchableFields object with normalized fields
    """
    assert isinstance(album, Album)
    if "year" in album:
        year = album.get("year", None)
        if year == 0:
            year = None

    return Matchable(
        artist=album.get("albumartist"),
        title=album.get("album"),
        year=year,
        media=album.get("media", None) if "media" in album else None,
        format=album.get("format", None) if "format" in album else None,
    )


def score_match(
    item1: Matchable,
    item2: Matchable,
    log: logging.Logger,
    weights: Union[dict[str, float], None] = None,
) -> MatchResult:
    """Score the match between two items.

    Args:
        item1: First item fields
        item2: Second item fields
        log: Logger to log scoring details
        weights: Optional dictionary of field weights. Defaults to:
                 {"artist": 0.5, "title": 0.4, "year": 0.1}

    Returns:
        MatchResult containing total score and individual field scores
    """
    if weights is None:
        weights = {"artist": 0.5, "title": 0.4, "year": 0.1}

    scores: dict[str, float] = {}

    # Calculate required field similarities
    scores["artist"] = string_similarity(item1.artist, item2.artist)
    scores["title"] = string_similarity(item1.title, item2.title)

    # Calculate optional field similarities if both items have the field
    if item1.year is not None and item2.year is not None:
        scores["year"] = year_similarity(item1.year, item2.year)
    else:
        # Default to 1.0 if either doesn't have year (don't penalize)
        scores["year"] = 1.0

    # Calculate total score based on weights
    total_score = sum(scores.get(field, 0.0) * weight for field, weight in weights.items())

    # Normalize to ensure total score is between 0 and 1
    weight_sum = sum(weights.values())
    if weight_sum > 0:
        total_score /= weight_sum

    # Log scoring details
    field_details = "\n".join(f"\t{field}: {score:.2f}" for field, score in scores.items())
    log.debug(
        "Scoring {} - {} against {} - {}:\n" "{}\n" "\tTotal score: {:.2f}",
        item1.artist,
        item1.title,
        item2.artist,
        item2.title,
        field_details,
        total_score,
    )

    return MatchResult(total_score=total_score, field_scores=scores)
