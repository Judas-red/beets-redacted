#!/usr/bin/env python3
"""Command implementation for the redacted plugin."""

import logging
import sys
import time
from optparse import OptionParser, Values
from typing import Any

import enlighten  # type: ignore[import-untyped]
from beets import ui  # type: ignore[import-untyped]
from beets.library import Library  # type: ignore[import-untyped]

from beetsplug.redacted.client import Client
from beetsplug.redacted.search import search


def command_func(
    _: "RedactedCommand",
    lib: Library,
    opts: Values,
    args: list[str],
    client: Client,
    log: logging.Logger,
) -> dict[str, int]:
    """Execute the redacted command.

    Args:
        lib: Beets library instance
        opts: Command line options
        args: Command line arguments

    Returns:
        Dictionary with counts of modified and unmodified albums
    """
    # Get the Beets database query from args
    query = " ".join(args) if args else ""

    # Filter query to only include albums without red_groupid if force=False
    if not opts.force:
        query = f"{query} red_groupid::^$"

    # Get the albums to process from the Beets database
    query = query.strip()
    albums = lib.albums(ui.decargs(query))

    n_modified = 0
    n_total = len(albums)

    # Set up progress bars with a shared manager. Disable progress bars in tests,
    # as they fail during pytest on Windows. The output terminal in Windows under
    # pytest cause issues, and the progress bars are not needed for testing.
    with enlighten.get_manager(enabled="pytest" not in sys.modules) as manager:
        # Process each album, searching for both torrents and requests
        with manager.counter(
            total=n_total, desc="Processing albums", unit="albums", color="white"
        ) as c_unmodified:
            c_modified = c_unmodified.add_subcounter("blue")

            for album in albums:
                # Search for matching torrents
                red_fields = search(album, client, log, opts.min_score)
                if red_fields is None:
                    # No match found, so we skip this album
                    c_unmodified.update()
                    continue

                with lib.transaction():
                    old = album.copy()

                    # Apply fields from torrent and request matches
                    modified = False
                    for key, value in red_fields.__dict__.items():
                        if album.get(key) != value:
                            album[key] = value
                            modified = True

                    if not modified:
                        c_unmodified.update()
                        continue

                    ui.show_model_changes(album, old)

                    if opts.pretend:
                        c_unmodified.update()
                    else:
                        c_modified.update()
                        n_modified += 1
                        album.red_mtime = time.time()
                        album.store()
    return {"modified": n_modified, "unmodified": n_total - n_modified, "total": n_total}


class RedactedCommand(ui.Subcommand):
    """Command for searching and updating Redacted information for library albums."""

    def __init__(self, config: Any, log: logging.Logger, client: Client) -> None:
        """Initialize the command.

        Args:
            config: Configuration object from beets
            log: Logger instance for logging messages
            client: RedactedClient instance
        """
        self.config = config
        self.log = log
        self.client = client

        # Create the command parser
        parser = OptionParser(usage="beet redacted [options] [QUERY...]")
        parser.add_option(
            "--min-score",
            dest="min_score",
            type="float",
            default=config["min_score"].as_number(),
            help="Minimum match score to consider (0-1, default: 0.75)",
        )
        parser.add_option(
            "-p",
            "--pretend",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_option(
            "-f",
            "--force",
            action="store_true",
            help="Search all albums even if they already have a red_groupid",
        )

        # Initialize the parent class
        super().__init__(
            name="redacted",
            parser=parser,
            help="Search Redacted and update library albums with matching information",
        )

        # Bind the logger and client to the command function
        self.func = lambda lib, opts, args: command_func(
            self, lib, opts, args, self.client, self.log
        )
