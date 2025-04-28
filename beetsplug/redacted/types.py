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
from enum import Enum
from typing import Generic, Literal, Optional, TypeVar, Union

from pydantic.dataclasses import dataclass


class Action(Enum):
    """Valid actions for the Redacted API."""

    BROWSE = "browse"
    REQUESTS = "requests"
    ARTIST = "artist"
    USER_TORRENTS = "user_torrents"


class TorrentType(Enum):
    """Valid types for user torrents."""

    SEEDING = "seeding"
    LEECHING = "leeching"
    UPLOADED = "uploaded"
    SNATCHED = "snatched"


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
    editionId: Optional[int] = None
    artists: Optional[list[RedArtist]] = None
    remastered: Optional[bool] = None
    remasterYear: Optional[int] = None
    remasterCatalogueNumber: Optional[str] = None
    remasterTitle: Optional[str] = None
    media: Optional[str] = None
    encoding: Optional[str] = None
    format: Optional[str] = None
    hasLog: Optional[bool] = None
    logScore: Optional[int] = None
    hasCue: Optional[bool] = None
    scene: Optional[bool] = None
    vanityHouse: Optional[bool] = None
    fileCount: Optional[int] = None
    time: Optional[str] = None
    size: Optional[int] = None
    snatches: Optional[int] = None
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    isFreeleech: Optional[bool] = None
    isNeutralLeech: Optional[bool] = None
    isFreeload: Optional[bool] = None
    isPersonalFreeleech: Optional[bool] = None
    trumpable: Optional[bool] = None
    canUseToken: Optional[bool] = None


@dataclass
class RedSearchResult:
    """Type for a group result in the search response.

    Version of RedTorrentGroup that is returned from the 'browse' search API. Used for determining
    the best artist id to use for a Beets album. No fields from this should be stored in the Beets
    database.
    """

    groupId: Optional[int] = None
    torrents: Optional[list[RedSearchTorrent]] = None
    groupName: Optional[str] = None
    artist: Optional[str] = None
    tags: Optional[list[str]] = None
    bookmarked: Optional[bool] = None
    vanityHouse: Optional[bool] = None
    groupYear: Optional[int] = None
    releaseType: Optional[str] = None
    groupTime: Optional[int] = None
    maxSize: Optional[int] = None
    totalSnatched: Optional[int] = None
    totalSeeders: Optional[int] = None
    totalLeechers: Optional[int] = None


@dataclass
class RedSuccessResponse:
    """Base type for successful API responses."""

    status: Literal["success"]


@dataclass
class RedFailureResponse:
    """Base type for failed API responses."""

    status: Literal["failure"]
    error: Optional[str] = None


@dataclass
class RedSearchResults:
    """Type for search results from Redacted API."""

    results: Optional[list[RedSearchResult]] = None


@dataclass
class RedSearchResponse(RedSuccessResponse):
    """Type for the search response from Redacted API."""

    response: Optional[RedSearchResults] = None


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

    id: Optional[int] = None
    groupId: Optional[int] = None
    media: Optional[str] = None  # Media, e.g. "Vinyl", "CD", "Web"
    format: Optional[str] = None  # Format, e.g. "FLAC", "MP3"
    encoding: Optional[str] = None  # Encoding, e.g. "24bit Lossless", "VBR", "CBR"
    remasterYear: Optional[int] = None  # Remaster year. 0 indicates no remaster or no value.
    remastered: Optional[bool] = None
    remasterTitle: Optional[str] = None
    remasterRecordLabel: Optional[str] = None
    scene: Optional[bool] = None
    hasLog: Optional[bool] = None
    hasCue: Optional[bool] = None
    logScore: Optional[int] = None
    fileCount: Optional[int] = None  # Number of files in the torrent. May include non-audio files.
    freeTorrent: Optional[bool] = None
    isNeutralleech: Optional[bool] = None
    isFreeload: Optional[bool] = None
    size: Optional[int] = None  # Size of the torrent in bytes.
    leechers: Optional[int] = None
    seeders: Optional[int] = None
    snatched: Optional[int] = None
    time: Optional[str] = None  # Time string, e.g. "2009-06-06 19:04:22"
    hasFile: Optional[int] = None  # Unclear what this is.


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

    groupId: Optional[int] = None
    groupName: Optional[str] = None
    groupYear: Optional[int] = None
    groupRecordLabel: Optional[str] = None
    groupCatalogueNumber: Optional[str] = None
    tags: Optional[list[str]] = None
    releaseType: Optional[int] = None
    groupVanityHouse: Optional[bool] = None
    hasBookmarked: Optional[bool] = None
    torrent: Optional[list[RedArtistTorrent]] = None


@dataclass
class RedArtistRequest:
    """Type for a request in an artist result."""

    requestId: Optional[int] = None
    categoryId: Optional[int] = None
    title: Optional[str] = None
    year: Optional[int] = None
    timeAdded: Optional[str] = None
    votes: Optional[int] = None
    bounty: Optional[int] = None


@dataclass
class RedArtistResponseResults:
    """Type for the artist response data."""

    id: Optional[int] = None
    name: Optional[str] = None
    notificationsEnabled: Optional[bool] = None
    hasBookmarked: Optional[bool] = None
    image: Optional[str] = None
    body: Optional[str] = None
    vanityHouse: Optional[bool] = None
    tags: Optional[list[RedArtistTag]] = None
    similarArtists: Optional[list[dict]] = None
    statistics: Optional[RedArtistStatistics] = None
    torrentgroup: Optional[list[RedArtistTorrentGroup]] = None
    requests: Optional[list[RedArtistRequest]] = None


@dataclass
class RedArtistResponse(RedSuccessResponse):
    """Type for the artist response from Redacted API."""

    response: RedArtistResponseResults


@dataclass
class RedUserTorrent:
    """Type for a user torrent."""

    groupId: Optional[int] = None
    name: Optional[str] = None
    torrentId: Optional[int] = None
    artistName: Optional[str] = None
    artistId: Optional[int] = None


@dataclass
class RedUserResponseResults:
    seeding: Optional[list[RedUserTorrent]] = None
    leeching: Optional[list[RedUserTorrent]] = None
    uploaded: Optional[list[RedUserTorrent]] = None
    snatched: Optional[list[RedUserTorrent]] = None


@dataclass
class RedUserResponse(RedSuccessResponse):
    """Type for the user response from Redacted API."""

    response: Optional[RedUserResponseResults] = None


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
