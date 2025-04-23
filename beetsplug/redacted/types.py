"""Type definitions for Redacted API responses.

Example responses can be found in the Redacted API documentation.

## Torrents

Torrents Search

URL: ajax.php?action=browse&searchstr=<Search Term>

Arguments:
searchstr - string to search for
page - page to display (default: 1)
taglist, tags_type, order_by, order_way, filter_cat, freetorrent, vanityhouse, scene,
haslog, releasetype, media, format, encoding, artistname, filelist, groupname,
recordlabel, cataloguenumber, year, remastertitle, remasteryear, remasterrecordlabel,
remastercataloguenumber - as in advanced search

Response format:

```json
    {
        "status": "success",
        "response": {
            "currentPage": 1,
            "pages": 3,
            "results": [
                {
                    "groupId": 410618,
                    "groupName": "Jungle Music / Toytown",
                    "artist": "Logistics",
                    "tags": [
                        "drum.and.bass",
                        "electronic"
                    ],
                    "bookmarked": false,
                    "vanityHouse": false,
                    "groupYear": 2009,
                    "releaseType": "Single",
                    "groupTime": 1339117820,
                    "maxSize": 237970,
                    "totalSnatched": 318,
                    "totalSeeders": 14,
                    "totalLeechers": 0,
                    "torrents": [
                        {
                            "torrentId": 959473,
                            "editionId": 1,
                            "artists": [
                                {
                                    "id": 1460,
                                    "name": "Logistics",
                                    "aliasid": 1460
                                }
                            ],
                            "remastered": false,
                            "remasterYear": 0,
                            "remasterCatalogueNumber": "",
                            "remasterTitle": "",
                            "media": "Vinyl",
                            "encoding": "24bit Lossless",
                            "format": "FLAC",
                            "hasLog": false,
                            "logScore": 79,
                            "hasCue": false,
                            "scene": false,
                            "vanityHouse": false,
                            "fileCount": 3,
                            "time": "2009-06-06 19:04:22",
                            "size": 243680994,
                            "snatches": 10,
                            "seeders": 3,
                            "leechers": 0,
                            "isFreeleech": false,
                            "isNeutralLeech": false,
                            "isFreeload": false,
                            "isPersonalFreeleech": false,
                            "trumpable": false,
                            "canUseToken": true
                        },
                        // ...
                    ]
                },
                // ...
            ]
        }
    }
```


## Requests

Request Search

URL: ajax.php?action=requests&search=<term>&page=<page>&tags=<tags>

Arguments:
search - search term
page - page to display (default: 1)
tags - tags to search by (comma separated)
tags_type - 0 for any, 1 for match all
show_filled - Include filled requests in results - true or false (default: false).
filter_cat[], releases[], bitrates[], formats[], media[] - as used on requests.php and
as defined in Mappings

If no arguments are specified then the most recent requests are shown.

Response format:

```json
    {
        "status": "success",
        "response": {
            "currentPage": 1,
            "pages": 1,
            "results": [
                {
                    "requestId": 185971,
                    "requestorId": 498,
                    "requestorName": "Satan",
                    "timeAdded": "2012-05-06 15:43:17",
                    "lastVote": "2012-06-10 20:36:46",
                    "voteCount": 3,
                    "bounty": 245366784,
                    "categoryId": 1,
                    "categoryName": "Music",
                    "artists": [
                        [
                            {
                                "id": "1460",
                                "name": "Logistics"
                            }
                        ],
                        [
                            {
                                "id": "25351",
                                "name": "Alice Smith"
                            },
                            {
                                "id": "44545",
                                "name": "Nightshade"
                            },
                            {
                                "id": "249446",
                                "name": "Sarah Callander"
                            }
                        ]
                    ],
                    "tags": {
                        "551": "japanese",
                        "1630": "video.game"
                    },
                    "title": "Fear Not",
                    "year": 2012,
                    "image": "http://whatimg.com/i/ralpc.jpg",
                    "description": "Thank you kindly.",
                    "catalogueNumber": "",
                    "releaseType": "",
                    "bitrateList": "1",
                    "formatList": "Lossless",
                    "mediaList": "FLAC",
                    "logCue": "CD",
                    "isFilled": false,
                    "fillerId": 0,
                    "fillerName": "",
                    "torrentId": 0,
                    "timeFilled": ""
                },
                // ...
            ]
        }
    }
```

"""

# ruff: noqa: N815

import dataclasses
from enum import StrEnum
from typing import Generic, Literal, TypeVar, Union

from pydantic.dataclasses import dataclass


class RedAction(StrEnum):
    """Valid actions for the Redacted API."""

    BROWSE = "browse"
    REQUESTS = "requests"
    ARTIST = "artist"


@dataclass
class RedArtist:
    """Type for artist information in a torrent."""

    id: int
    name: str
    aliasid: int


@dataclass
class RedSearchTorrent:
    """Type for a single torrent in a group.

    Version of RedTorrent that is returned from the 'browse' search API. Used for determining the
    best artist id to use for a Beets album. No fields from this should be stored in the Beets
    database.
    """

    torrentId: int
    editionId: Union[int, None] = None
    artists: Union[list[RedArtist], None] = None
    remastered: Union[bool, None] = None
    remasterYear: Union[int, None] = None
    remasterCatalogueNumber: Union[str, None] = None
    remasterTitle: Union[str, None] = None
    media: Union[str, None] = None
    encoding: Union[str, None] = None
    format: Union[str, None] = None
    hasLog: Union[bool, None] = None
    logScore: Union[int, None] = None
    hasCue: Union[bool, None] = None
    scene: Union[bool, None] = None
    vanityHouse: Union[bool, None] = None
    fileCount: Union[int, None] = None
    time: Union[str, None] = None
    size: Union[int, None] = None
    snatches: Union[int, None] = None
    seeders: Union[int, None] = None
    leechers: Union[int, None] = None
    isFreeleech: Union[bool, None] = None
    isNeutralLeech: Union[bool, None] = None
    isFreeload: Union[bool, None] = None
    isPersonalFreeleech: Union[bool, None] = None
    trumpable: Union[bool, None] = None
    canUseToken: Union[bool, None] = None


@dataclass
class RedSearchResult:
    """Type for a group result in the search response.

    Version of RedTorrentGroup that is returned from the 'browse' search API. Used for determining
    the best artist id to use for a Beets album. No fields from this should be stored in the Beets
    database.
    """

    groupId: Union[int, None] = None
    torrents: Union[list[RedSearchTorrent], None] = None
    groupName: Union[str, None] = None
    artist: Union[str, None] = None
    tags: Union[list[str], None] = None
    bookmarked: Union[bool, None] = None
    vanityHouse: Union[bool, None] = None
    groupYear: Union[int, None] = None
    releaseType: Union[str, None] = None
    groupTime: Union[int, None] = None
    maxSize: Union[int, None] = None
    totalSnatched: Union[int, None] = None
    totalSeeders: Union[int, None] = None
    totalLeechers: Union[int, None] = None


@dataclass
class RedSuccessResponse:
    """Base type for successful API responses."""

    status: Literal["success"]


@dataclass
class RedFailureResponse:
    """Base type for failed API responses."""

    status: Literal["failure"]
    error: str


@dataclass
class RedSearchResults:
    """Type for search results from Redacted API."""

    results: list[RedSearchResult]


@dataclass
class RedSearchResponse(RedSuccessResponse):
    """Type for the search response from Redacted API."""

    response: RedSearchResults


@dataclass
class RedArtistTag:
    """Type for a tag in an artist result."""

    name: str
    count: int


@dataclass
class RedArtistStatistics:
    """Type for the statistics section of an artist response."""

    numGroups: int
    numTorrents: int
    numSeeders: int
    numLeechers: int
    numSnatches: int


@dataclass
class RedArtistTorrent:
    """Type for a torrent in an artist's torrent group.

    Version of RedArtistTorrent that is returned from the 'artist' endpoint.

    Note: This is similar to RedactedTorrentResult but with a different structure
    as it comes from the artist endpoint. Key differences:
    - Uses 'id' instead of 'torrentId'
    - Different field availability and naming conventions
    """

    id: Union[int, None] = None
    groupId: Union[int, None] = None
    media: Union[str, None] = None  # Media, e.g. "Vinyl", "CD", "Web"
    format: Union[str, None] = None  # Format, e.g. "FLAC", "MP3"
    encoding: Union[str, None] = None  # Encoding, e.g. "24bit Lossless", "VBR", "CBR"
    remasterYear: Union[int, None] = None  # Remaster year. 0 indicates no remaster or no value.
    remastered: Union[bool, None] = None
    remasterTitle: Union[str, None] = None
    remasterRecordLabel: Union[str, None] = None
    scene: Union[bool, None] = None
    hasLog: Union[bool, None] = None
    hasCue: Union[bool, None] = None
    logScore: Union[int, None] = None
    fileCount: Union[int, None] = None  # Number of files in the torrent. May include non-audio files.
    freeTorrent: Union[bool, None] = None
    isNeutralleech: Union[bool, None] = None
    isFreeload: Union[bool, None] = None
    size: Union[int, None] = None  # Size of the torrent in bytes.
    leechers: Union[int, None] = None
    seeders: Union[int, None] = None
    snatched: Union[int, None] = None
    time: Union[str, None] = None  # Time string, e.g. "2009-06-06 19:04:22"
    hasFile: Union[int, None] = None  # Unclear what this is.


@dataclass
class RedArtistTorrentGroup:
    """Type for a torrent group in an artist result.

    Version of the torrent group that is returned from the 'artist' endpoint.

    Note: This is similar to RedactedGroupResult but with a different structure
    as it comes from the artist endpoint. Key differences:
    - Has 'torrent' (singular) instead of 'torrents'
    - Uses different field naming conventions
    - The artist is implied by the parent artist response
    """

    groupId: Union[int, None] = None
    groupName: Union[str, None] = None
    groupYear: Union[int, None] = None
    groupRecordLabel: Union[str, None] = None
    groupCatalogueNumber: Union[str, None] = None
    tags: Union[list[str], None] = None
    releaseType: Union[int, None] = None
    groupVanityHouse: Union[bool, None] = None
    hasBookmarked: Union[bool, None] = None
    torrent: Union[list[RedArtistTorrent], None] = None


@dataclass
class RedArtistRequest:
    """Type for a request in an artist result."""

    requestId: Union[int, None] = None
    categoryId: Union[int, None] = None
    title: Union[str, None] = None
    year: Union[int, None] = None
    timeAdded: Union[str, None] = None
    votes: Union[int, None] = None
    bounty: Union[int, None] = None


@dataclass
class RedArtistResponseResults:
    """Type for the artist response data."""

    id: Union[int, None] = None
    name: Union[str, None] = None
    notificationsEnabled: Union[bool, None] = None
    hasBookmarked: Union[bool, None] = None
    image: Union[str, None] = None
    body: Union[str, None] = None
    vanityHouse: Union[bool, None] = None
    tags: Union[list[RedArtistTag], None] = None
    similarArtists: Union[list[dict], None] = None
    statistics: Union[RedArtistStatistics, None] = None
    torrentgroup: Union[list[RedArtistTorrentGroup], None] = None
    requests: Union[list[RedArtistRequest], None] = None


@dataclass
class RedArtistResponse(RedSuccessResponse):
    """Type for the artist response from Redacted API."""

    response: RedArtistResponseResults


RedactedAPIResponse = Union[RedSearchResponse, RedArtistResponse, RedFailureResponse]

# Field metadata for the Beets database

# Create type variables for the source object type and the field value type
SourceT = TypeVar("SourceT")
ValueT = TypeVar("ValueT")


class RedBeetsFieldMapping(Generic[SourceT, ValueT]):
    """Defines a mapping from Redacted API fields to Beets database fields."""

    def __init__(self, cls: type[SourceT], source_attr: str, value_type: type[ValueT]):
        """Initialize a field mapping.

        Args:
            source_attr: The attribute name in the source class
        """
        self.source_cls = cls
        self.source_attr = source_attr
        self.value_type = value_type

    def get_source_cls(self) -> type[SourceT]:
        """Get the source class from the type parameters at runtime."""
        return self.source_cls

    def get_source_type(self) -> type[ValueT]:
        """Get the value type from the type parameters at runtime."""
        return self.value_type

    def get_value(self, obj: SourceT) -> Union[ValueT, None]:
        """Get the value of the source attribute from the object."""
        if not isinstance(obj, self.get_source_cls()):
            raise TypeError(f"Expected {self.get_source_cls().__name__}, got {type(obj).__name__}")
        if not hasattr(obj, self.source_attr):
            raise ValueError(f"Source attribute {self.source_attr} not found in {obj}")
        value = getattr(obj, self.source_attr)
        if value is None:
            return None
        if isinstance(value, self.get_source_type()):
            return value
        raise ValueError(
            f"Expected value of type {self.get_source_type().__name__}, "
            f"got {type(value).__name__}: {value}"
        )


RBF = RedBeetsFieldMapping
AR = RedArtistResponseResults
GR = RedArtistTorrentGroup
TR = RedArtistTorrent


@dataclass
class BeetsRedFields:
    """Fields to update on a Beets album relating to Redacted torrents."""

    # The last time the redacted fields were modified, in seconds since the epoch
    red_mtime: Union[float, None] = dataclasses.field(default=None)

    # ID fields
    red_artistid: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[AR, int](AR, "id", int), "required": True}
    )
    red_groupid: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, int](GR, "groupId", int), "required": True}
    )
    red_torrentid: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "id", int), "required": True}
    )

    # Artist fields, from RedArtistResponse
    red_artist: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[AR, str](AR, "name", str)}
    )
    red_image: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[AR, str](AR, "image", str)}
    )

    # Group fields, from RedArtistTorrentGroup
    red_groupname: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, str](GR, "groupName", str)}
    )
    red_groupyear: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, int](GR, "groupYear", int)}
    )
    red_grouprecordlabel: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, str](GR, "groupRecordLabel", str)}
    )
    red_groupcataloguenumber: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, str](GR, "groupCatalogueNumber", str)}
    )
    red_groupreleasetype: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[GR, int](GR, "releaseType", int)}
    )

    # Torrent fields, from RedArtistTorrent
    red_media: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "media", str)}
    )
    red_format: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "format", str)}
    )
    red_encoding: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "encoding", str)}
    )
    red_remastered: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "remastered", bool)}
    )
    red_remasteryear: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "remasterYear", int)}
    )
    red_remastertitle: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "remasterTitle", str)}
    )
    red_remasterrecordlabel: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "remasterRecordLabel", str)}
    )
    red_scene: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "scene", bool)}
    )
    red_haslog: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "hasLog", bool)}
    )
    red_logscore: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "logScore", int)}
    )
    red_hascue: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "hasCue", bool)}
    )
    red_filecount: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "fileCount", int)}
    )
    red_freetorrent: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "freeTorrent", bool)}
    )
    red_isneutralleech: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "isNeutralleech", bool)}
    )
    red_isfreeload: Union[bool, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, bool](TR, "isFreeload", bool)}
    )
    red_size: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "size", int)}
    )
    red_leechers: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "leechers", int)}
    )
    red_seeders: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "seeders", int)}
    )
    red_snatched: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "snatched", int)}
    )
    red_time: Union[str, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, str](TR, "time", str)}
    )
    red_hasfile: Union[int, None] = dataclasses.field(
        default=None, metadata={"from": RBF[TR, int](TR, "hasFile", int)}
    )
