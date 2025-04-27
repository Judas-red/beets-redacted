"""Test utilities for the redacted plugin.

Example usage:

```python
from beetsplug.redacted.utils.test_utils import FakeLibrary

# Create a library with albums
lib = FakeLibrary([
    {
        "id": 1,
        "albumartist": "Test Artist 1",
        "album": "Test Album 1",
        "year": 2020,
    },
    {
        "id": 2,
        "albumartist": "Test Artist 2",
        "album": "Test Album 2",
        "year": 2021,
    }
])

# Get albums from the library
albums = lib.albums()
assert len(albums) == 2

# Get a specific album
filtered_albums = lib.albums(query="Test Artist 1")
assert len(filtered_albums) == 1
album = filtered_albums[0]

# Modify the album
album.year = 2022

# Save the changes
album.store()

# Verify the change was saved
updated_albums = lib.albums(query="Test Artist 1")
assert updated_albums[0].year == 2022

# Various ways to access album fields

# 1. Using attribute access (similar to Album.field in beets)
assert album.albumartist == "Test Artist 1"
assert album.year == 2022

# 2. Using dictionary-style access (similar to Album['field'] in beets)
assert album["albumartist"] == "Test Artist 1"
assert album["year"] == 2022

# 3. Using get() with default values (similar to Album.get(field, default) in beets)
# This is especially useful for optional fields that might not exist
assert album.get("genre", "Unknown") == "Unknown"  # Returns default if field doesn't exist
assert album.get("year", 1999) == 2022  # Returns actual value if field exists

# 4. Checking if a field exists
if "compilation" not in album:
    album.compilation = False

# 5. Adding new fields
album.genre = "Rock"
assert album.genre == "Rock"
```
"""

import copy
import logging
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional, Protocol, Union

import requests
from beets import library  # type: ignore[import-untyped]
from beets.library import Album  # type: ignore[import-untyped]

from beetsplug.redacted.client import Client
from beetsplug.redacted.exceptions import RedactedError
from beetsplug.redacted.http import HTTPClient
from beetsplug.redacted.types import (
    RedArtistResponse,
    RedArtistResponseResults,
    RedSearchResponse,
    RedSearchResults,
    RedUserResponse,
    RedUserResponseResults,
    TorrentType,
)

# Forward declaration for type checking
if TYPE_CHECKING:
    from typing import TypeVar

    T = TypeVar("T", bound="FakeAlbum")


class FakeLibrary:
    """Fake library for testing.

    This implementation should be considered correct, and not changed in order to
    address failing tests.
    """

    _albums: dict[int, "FakeAlbum"]

    def __init__(self, albums_data: list[Union[dict[str, Any], "FakeAlbum"]]) -> None:
        """Initialize fake library.

        Args:
            albums_data: List of dictionaries containing album attributes or FakeAlbum instances
        """
        # Skip Library's __init__ to avoid database initialization
        self._albums: dict[int, FakeAlbum] = {}
        self._in_transaction = False

        # Create FakeAlbums from the provided data
        for item in albums_data:
            if isinstance(item, dict):
                # Create a new album from dictionary
                self._create_album(item)
            else:
                # Use existing FakeAlbum instance
                album = item
                album._library = self
                self._albums[album.id] = copy.deepcopy(album)

    def _create_album(self, data: dict[str, Any]) -> "FakeAlbum":
        """Create a new album and add it to the library.

        Args:
            data: Dictionary of album attributes

        Returns:
            The created album

        Raises:
            AssertionError: If required fields are missing
        """
        assert data.get("id") is not None
        assert data.get("albumartist") is not None
        assert data.get("album") is not None

        # Create a new FakeAlbum instance without calling __init__
        album = FakeAlbum.__new__(FakeAlbum)

        # Initialize essential Album attributes to make parent class methods work
        album._library = self
        album._model_unique = False
        album._model_loaded = True
        album._dirty = set()

        # Set up attributes that Album would normally use
        album._attrs = data.copy()
        album._model_values = album._attrs

        # Set up mock versions of _values_fixed and _values_flex
        # that will satisfy basic access patterns
        album._values_fixed = album._attrs
        album._values_flex = {}
        album._values_flex.update(data)

        # Store the album in the library
        self._albums[album.id] = album
        return album

    def albums(self, query: Union[str, None] = None) -> Sequence["FakeAlbum"]:
        """Get albums from the library.

        Args:
            query: Optional query to filter albums. If red_groupid::^$ is in the query,
                albums with red_groupid will be filtered out.

        Returns:
            Sequence of albums
        """
        albums = []
        for album in self._albums.values():
            # Skip albums with red_groupid if red_groupid::^$ is in query
            if (
                query
                and "red_groupid::^$" in query
                and "red_groupid" in album
                and album.red_groupid is not None
            ):
                continue
            albums.append(album)
        return albums

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Context manager for transactions."""
        self._in_transaction = True
        try:
            yield
        finally:
            self._in_transaction = False

    # Overriding methods that should not be called

    def items(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("items() is not implemented in FakeLibrary")

    def add(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("add() is not implemented in FakeLibrary")

    def add_album(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("add_album() is not implemented in FakeLibrary")

    def get_album(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("get_album() is not implemented in FakeLibrary")

    def get_item(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("get_item() is not implemented in FakeLibrary")

    def set_album(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("set_album() is not implemented in FakeLibrary")

    def remove_album(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeLibrary.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("remove_album() is not implemented in FakeLibrary")


class FakeAlbum(Album):
    """Fake implementation of beets Album for testing.

    This implementation should be considered correct, and not changed in order to
    address failing tests.

    The FakeAlbum class mimics the behavior of the real beets Album class by inheriting
    most of its functionality while avoiding database interactions.

    Examples:
        ```python
        # Get album by filtering library
        album = lib.albums(query="Test Artist")[0]

        # Access fields in multiple ways
        artist = album.albumartist
        title = album['album']
        year = album.get('year', 2000)  # Default if not present

        # Modify fields
        album.genre = "Rock"
        album['compilation'] = False

        # Iterate over all fields
        for field in album:
            print(f"{field}: {album[field]}")

        # Save changes to library
        album.store()
        ```
    """

    def __init__(self, **kwargs: Any) -> None:
        """Do not use this constructor.

        Raises:
            TypeError: Always. FakeAlbums should only be created via FakeLibrary.
        """
        raise TypeError(
            "Do not initialize FakeAlbum directly. Albums can only be created through FakeLibrary."
        )

    def store(self) -> None:
        """Save the album's metadata."""
        assert self._library is not None, "Album must be added to a library before it can be stored"
        assert self._library._in_transaction, "Album must be stored within a transaction"

        # Make sure our _model_values and _attrs stay in sync
        self._model_values = self._attrs

        # Update in the library's storage directly - no need for a transaction
        self._library._albums[self.id] = copy.deepcopy(self)

    def copy(self) -> "FakeAlbum":
        """Create a copy of this album."""
        # Create a new album by leveraging the FakeLibrary._create_album method
        # This ensures consistency with how albums are created initially
        assert self._library is not None, "Album must be added to a library before it can be copied"

        # Create a copy of the album's data with all attributes
        data = copy.deepcopy(self._attrs)

        # Use the library's _create_album method to create a properly initialized copy
        # This ensures all the necessary attributes are set correctly
        new_album: FakeAlbum = self._library._create_album(data)
        return new_album

    def _template_funcs(self) -> dict[str, Any]:
        """Return an empty dictionary of template functions.

        This overrides the parent class method to avoid accessing _db.
        """
        funcs: dict[str, Any] = library.DefaultTemplateFunctions(self).functions()
        return funcs

    # Override these methods to throw errors for operations we don't support

    def items(self) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("items() is not implemented in FakeAlbum")

    def remove(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("remove() is not implemented in FakeAlbum")

    def move_art(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("move_art() is not implemented in FakeAlbum")

    def move(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("move() is not implemented in FakeAlbum")

    def item_dir(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("item_dir() is not implemented in FakeAlbum")

    def art_destination(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("art_destination() is not implemented in FakeAlbum")

    def set_art(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("set_art() is not implemented in FakeAlbum")

    def try_sync(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("try_sync() is not implemented in FakeAlbum")

    def load(self, *args: Any, **kwargs: Any) -> None:
        """Not implemented in FakeAlbum."""
        raise NotImplementedError("load() is not implemented in FakeAlbum")


class LoggerInterface(Protocol):
    """Protocol defining the logger interface we need for testing."""

    def debug(self, msg: str, *args: Any) -> None:
        """Log a debug message."""
        ...

    def info(self, msg: str, *args: Any) -> None:
        """Log an info message."""
        ...

    def error(self, msg: str, *args: Any) -> None:
        """Log an error message."""
        ...


class FakeLogger(logging.Logger):
    """Fake logger for testing.

    As much as possible, a FakeLogger should not be used to verify behavior in
    testing. Behavior should rather be verified by checking material results from
    method calls. If a log message is the only way to verify an otherwise-invisible
    side effect of calling a method, please consider refactoring the code to make
    that effect visibile for testing.
    """

    def __init__(self) -> None:
        """Initialize fake logger."""
        super().__init__("fake")
        self.logger = logging.getLogger("FakeLogger")
        self.messages: list[tuple[str, tuple[Any]]] = []

    def debug(self, msg: str, *args: Any) -> None:  # type: ignore[override]
        """Log a debug message.

        Args:
            msg: Message to log
            args: Format arguments
        """
        self.logger.debug(msg.format(*args))
        self.messages.append((msg, args))

    def info(self, msg: str, *args: Any) -> None:  # type: ignore[override]
        """Log an info message.

        Args:
            msg: Message to log
            args: Format arguments
        """
        self.logger.info(msg.format(*args))
        self.messages.append((msg, args))

    def error(self, msg: str, *args: Any) -> None:  # type: ignore[override]
        """Log an error message.

        Args:
            msg: Message to log
            args: Format arguments
        """
        self.logger.error(msg.format(*args))
        self.messages.append((msg, args))

    def assert_message(self, msg: str, args: tuple[Any, ...]) -> None:
        """Assert that a message was logged.

        Args:
            msg: Message to check for. This can be a substring of the actual message.
            args: Format arguments
        """
        for message in self.messages:
            if msg in message[0] and args == message[1]:
                return
        raise AssertionError(f"Expected message containing '{msg}' not found in {self.messages}")


class FakeResponse(requests.Response):
    """Fake response object for testing."""

    def __init__(self, data: dict) -> None:
        """Initialize the fake response.

        Args:
            data: Response data
        """
        self._data = data
        self.status_code = 200

    def json(self, *args: Any, **kwargs: Any) -> dict:
        """Get the JSON response data.

        Returns:
            The JSON response data
        """
        return self._data

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the status code is not 2xx."""
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class FakeHTTPClient(HTTPClient):
    """Fake HTTP client for testing."""

    def __init__(self) -> None:
        """Initialize the fake client."""
        self.responses: dict[str, FakeResponse] = {}

    def _hash_request(self, params: dict[str, str], headers: dict[str, str]) -> str:
        """Create a unique hash for the request parameters and headers.

        Args:
            params: Query parameters
            headers: Request headers

        Returns:
            A string hash representing the request
        """
        # Sort the dictionaries to ensure consistent hashing
        param_items = sorted(params.items())
        header_items = sorted(headers.items())
        return f"params:{param_items}|headers:{header_items}"

    def add(
        self,
        params: dict[str, str],
        headers: dict[str, str],
        response: dict,
        status_code: int = 200,
    ) -> None:
        """Add a response for a specific request.

        Args:
            params: Query parameters that should trigger this response
            headers: Request headers that should trigger this response
            response: The response data to return
            status_code: The HTTP status code to return
        """
        request_hash = self._hash_request(params, headers)
        response_obj = FakeResponse(response)
        response_obj.status_code = status_code
        self.responses[request_hash] = response_obj

    def get(self, params: dict[str, str], headers: dict[str, str]) -> FakeResponse:
        """Get a response from the fake client.

        Args:
            params: Query parameters
            headers: Request headers

        Returns:
            The fake response

        Raises:
            Exception: If no response is configured for the request
        """
        request_hash = self._hash_request(params, headers)
        if request_hash not in self.responses:
            raise Exception(f"No response configured for request: {request_hash}")
        return self.responses[request_hash]


class FakeClient(Client):
    """Fake implementation of RedactedClient for testing."""

    def __init__(self) -> None:
        """Initialize the fake client."""
        self.search_responses: dict[str, RedSearchResponse] = {}
        self.artist_responses: dict[int, RedArtistResponse] = {}
        self.user_response: Optional[RedUserResponse] = None
        self.queries: list[str] = []
        self.error_queries: set[str] = set()
        self.rate_limit_queries: set[str] = set()
        self.artist_queries: list[int] = []
        self.error_artist_queries: set[int] = set()
        self.rate_limit_artist_queries: set[int] = set()

    def search(self, query: str) -> RedSearchResponse:
        """Fake implementation of browse method.

        Args:
            query: Query string

        Returns:
            Mock response from the configured responses

        Raises:
            RedactedError: If the query is in error_queries
            RedactedRateLimitError: If the query is in rate_limit_queries
        """
        self.queries.append(query)
        if query in self.error_queries:
            raise RedactedError(f"Error searching for {query}")
        if query in self.rate_limit_queries:
            # This will be caught by the caller and handled appropriately
            raise RedactedError("Rate limit exceeded")
        return self.search_responses.get(
            query, RedSearchResponse(status="success", response=RedSearchResults(results=[]))
        )

    def get_artist(self, artist_id: int) -> RedArtistResponse:
        """Fake implementation of get_artist method.

        Args:
            artist_id: Artist ID to look up

        Returns:
            Mock response from the configured responses

        Raises:
            RedactedError: If the artist_id is in error_artist_queries
            RedactedRateLimitError: If the artist_id is in rate_limit_artist_queries
        """
        self.artist_queries.append(artist_id)
        if artist_id in self.error_artist_queries:
            raise RedactedError(f"Error looking up artist {artist_id}")
        if artist_id in self.rate_limit_artist_queries:
            raise RedactedError("Rate limit exceeded")

        # If no specific response is configured, return a minimal valid response
        if artist_id not in self.artist_responses:
            return RedArtistResponse(
                status="success",
                response=RedArtistResponseResults(
                    id=artist_id,
                    name=f"Artist {artist_id}",
                    notificationsEnabled=False,
                    hasBookmarked=False,
                    torrentgroup=[],
                ),
            )

        return self.artist_responses[artist_id]

    def user(self, _: TorrentType, limit: int = 500, offset: int = 0) -> RedUserResponse:
        """Fake implementation of user torrents lookup (snatched, seeding, etc)."""
        if self.user_response:
            return self.user_response

        raise RedactedError("Fake user lookup failure")


class FakeCommandOpts:
    """Fake implementation of command arguments for testing."""

    def __init__(
        self,
        min_score: float = 0.75,
        query: Union[str, None] = None,
        pretend: bool = False,
        force: bool = False,
    ) -> None:
        """Initialize fake command arguments.

        Args:
            min_score: Minimum match score to consider
            query: Optional query to filter albums
            pretend: Whether to show changes without making them
            force: Whether to process all albums regardless of red_groupid
        """
        self.min_score = min_score
        self.query = query
        self.pretend = pretend
        self.force = force


class FakeConfigValue:
    """Fake configuration value for testing."""

    def __init__(self, value: Union[float, str]) -> None:
        """Initialize fake config value.

        Args:
            value: Configuration value
        """
        self._value = value

    def as_number(self) -> float:
        """Get the value as a number.

        Returns:
            Configuration value as a float
        """
        return float(self._value)

    def as_str(self) -> str:
        """Get the value as a string.

        Returns:
            Configuration value as a string
        """
        return str(self._value)


class FakeConfig:
    """Fake configuration for testing."""

    def __init__(self, min_score: float = 0.75, format: str = "{albumartist} - {album}") -> None:
        """Initialize fake config.

        Args:
            min_score: Minimum similarity score to consider a match
            format: Format string for displaying albums
        """
        self._min_score = min_score
        self._format = format

    def __getitem__(self, key: str) -> FakeConfigValue:
        """Get a configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value
        """
        if key == "min_score":
            return FakeConfigValue(self._min_score)
        elif key in ("format", "album_format"):
            return FakeConfigValue(self._format)
        raise KeyError(f"Unknown config key: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with a default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            return self[key]
        except KeyError:
            return default
