"""
Main client class for interacting with Redacted.
"""

import logging
from typing import Any, Optional

from pydantic import ValidationError

from .exceptions import RedactedError
from .http import HTTPClient
from .types import (
    Action,
    RedArtistResponse,
    RedSearchResponse,
    RedUserResponse,
    RedUserResponseResults,
    TorrentType,
)


class Client:
    """Client for interacting with the Redacted private tracker."""

    def __init__(
        self,
        http_client: HTTPClient,
        log: logging.Logger,
        api_key: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: API key for authentication.
            http_client: HTTP client implementation.
            log: Logger instance for logging messages.
            user_id: User ID for the user to get torrents for. If None, then the #user method will
                always return an empty list.
        """
        self.log = log
        self.log.debug("Initializing RedactedClient")

        self.http_client = http_client
        self.api_key = api_key
        self.user_id = user_id

    def _make_api_request(self, action: Action, params: dict[str, str]) -> dict[str, Any]:
        """Make an API request to Redacted.

        Args:
            action: The API action to perform.
            **params: Additional parameters for the request.

        Returns:
            The API response data.

        Raises:
            RedactedError: If the request fails.
            RedactedRateLimitError: If rate limited by the Redacted API.
        """
        api_params: dict[str, str] = {"action": action.value, **params}
        headers: dict[str, str] = {"Authorization": self.api_key}

        response = self.http_client.get(params=api_params, headers=headers)
        try:
            data: dict[str, Any] = response.json()
        except ValueError as e:
            self.log.debug(
                "Invalid JSON response from API: {0}\n\t{1}", str(e), str(response.content)
            )
            raise RedactedError("Invalid JSON response from API") from e

        if data.get("status") != "success":
            raise RedactedError(f"API error: {data.get('error', 'Unknown error')}")

        return data

    def search(self, query: str) -> RedSearchResponse:
        """Search for torrents on Redacted.

        URL: ajax.php?action=browse&searchstr=<Search Term>

        Arguments:
        searchstr - string to search for
        page - page to display (default: 1)
        taglist, tags_type, order_by, order_way, filter_cat, freetorrent, vanityhouse, scene,
        haslog, releasetype, media, format, encoding, artistname, filelist, groupname, recordlabel,
        cataloguenumber, year, remastertitle, remasteryear, remasterrecordlabel,
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

        Args:
            query: Search query string. Can be a general search term, an artist name,
                  or in the format "Artist - Album" for specific album searches.

        Returns:
            Search results.

        Raises:
            RedactedError: If the response is not in the expected format or indicates failure.
        """
        response = self._make_api_request(Action.BROWSE, {"searchstr": query})
        try:
            return RedSearchResponse(**response)
        except ValidationError as e:
            import json

            self.log.debug(
                "Couldn't parse RedactedSearchResponse from:\n%s", json.dumps(response, indent=2)
            )
            raise RedactedError(f"Invalid response format: {e}") from e

    def get_artist(self, artist_id: int) -> RedArtistResponse:
        """Get detailed information about an artist by ID.

        URL: ajax.php?action=artist&id=<Artist Id>

        Arguments:
        id - artist's id
        artistname - Artist's Name
        artistreleases - if set, only include groups where the artist is the main artist.

        Response format:

        ```json
        {
            "status": "success",
            "response": {
                "id": 1460,
                "name": "Logistics",
                "notificationsEnabled": false,
                "hasBookmarked": true,
                "image": "http://img120.imageshack.us/img120/3206/logiop1.jpg",
                "body": "",
                "vanityHouse": false,
                "tags": [
                    {
                        "name": "breaks",
                        "count": 3
                    },
                    // ...
                ],
                "similarArtists": [],
                "statistics": {
                    "numGroups": 125,
                    "numTorrents": 443,
                    "numSeeders": 3047,
                    "numLeechers": 95,
                    "numSnatches": 28033
                },
                "torrentgroup": [
                    {
                        "groupId": 72189681,
                        "groupName": "Fear Not",
                        "groupYear": 2012,
                        "groupRecordLabel": "Hospital Records",
                        "groupCatalogueNumber": "NHS209CD",
                        "tags": [
                            "breaks",
                            "drum.and.bass",
                            "electronic",
                            "dubstep"
                        ],
                        "releaseType": 1,
                        "groupVanityHouse": false,
                        "hasBookmarked": false,
                        "torrent": [
                            {
                                "id": 29991962,
                                "groupId": 72189681,
                                "media": "CD",
                                "format": "FLAC",
                                "encoding": "Lossless",
                                "remasterYear": 0,
                                "remastered": false,
                                "remasterTitle": "",
                                "remasterRecordLabel": "",
                                "scene": true,
                                "hasLog": false,
                                "hasCue": false,
                                "logScore": 0,
                                "fileCount": 19,
                                "freeTorrent": false,
                                "isNeutralleech": false,
                                "isFreeload": false,
                                "size": 527749302,
                                "leechers": 0,
                                "seeders": 20,
                                "snatched": 55,
                                "time": "2012-04-14 15:57:00",
                                "hasFile": 29991962
                            },
                            // ...
                        ]
                    },
                    // ...
                ],
                "requests": [
                    {
                        "requestId": 172667,
                        "categoryId": 1,
                        "title": "We Are One (Nu:logic Remix)/timelapse",
                        "year": 2012,
                        "timeAdded": "2012-02-07 03:44:39",
                        "votes": 3,
                        "bounty": 217055232
                    },
                    // ...
                ]
            }
        }
        ```

        Args:
            artist_id: The artist ID to look up.

        Returns:
            Detailed artist information including releases and statistics.

        Raises:
            RedactedError: If the response is not in the expected format or indicates failure.
        """
        response = self._make_api_request(Action.ARTIST, {"id": str(artist_id)})

        if response["status"] == "failure":
            raise RedactedError(f"API error: {response.get('error', 'Unknown error')}")

        try:
            return RedArtistResponse(**response)
        except ValidationError as e:
            import json

            self.log.debug(
                "Couldn't parse RedactedArtistResponse from:\n%s", json.dumps(response, indent=2)
            )
            raise RedactedError(f"Invalid response format: {e}") from e

    def user(self, type: TorrentType, limit: int = 500, offset: int = 0) -> RedUserResponse:
        """Get user torrents by type.

        Calls Redacted's 'user_torrents' API endpoint.

        URL: ajax.php?action=user_torrents&id=<User ID>
                     &type=<Torrent Type>
                     &limit=<Results Limit>
                     &offset=<Torrents Offset>

        Arguments:
        id - request id
        type - type of torrents to display options are: seeding leeching uploaded snatched
        limit - number of results to display (default: 500)
        offset - number of results to offset by (default: 0)

        Response format:

        ```json
        {
            "status": "success",
            "response": {
                "seeding": [
                    {
                        "groupId": "4",
                        "name": "If You Have Ghost",
                        "torrentId": "4",
                        "artistName": "Ghost B.C.",
                        "artistId": "4"
                    },
                    {
                        "groupId": "3",
                        "name": "Absolute Dissent",
                        "torrentId": "3",
                        "artistName": "Killing Joke",
                        "artistId": "3"
                    }
                ]
            }
        }
        ```

        Args:
            type: The type of torrents to get.
            limit: The number of torrents to get.
            offset: The offset to start from.
        """
        if not self.user_id:
            return RedUserResponse(
                status="success",
                response=RedUserResponseResults(seeding=[], leeching=[], uploaded=[], snatched=[]),
            )

        response = self._make_api_request(
            Action.USER_TORRENTS,
            {
                "id": str(self.user_id),
                "type": type.value,
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        try:
            return RedUserResponse(**response)
        except ValidationError as e:
            self.log.debug("Couldn't parse RedactedUserResponse from:\n%s", response)
            raise RedactedError(f"Invalid response format: {e}") from e
