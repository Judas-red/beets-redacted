# Redacted Beets Plugin

A [Beets](https://beets.io/) plugin for matching albums to torrents on [Redacted](https://redacted.sh).

## Installation

1. Install the redacted plugin via Pip with `pip install beets-redacted`. If you installed Beets via PipX, then you can use `pipx inject beets beets-redacted`.
1. Create a Redacted API key. Go to your user's 'Settings' page, then to the 'Access Settings' section. Under 'API Keys', enter a name for your new API key (perhaps 'beets-redacted'), copy the key in the 'API Key' field for your Beets config, check only the 'Torrents' checkbox, and check the 'Confirm API Key' checkbox. Then, save your profile. The new API Key should then be present with the name you gave it.
1. Update your Beets configuration. Enable the `redacted` plugin, and configure the API Key you generated above:

```yaml
plugins:
  - redacted

redacted:
  api_key: <your new api key>
```

## Configuration

The configuration options are

- **api_key** (required): Your Redacted API key, with at least 'torrents' scope.
- **user_id** (default: empty): Your Redacted user id, used only for looking up your snatches to improve torrent matching. To find your Redacted user id, go to your profile and copy the "id" parameter from the URL bar. It will likely be a number between 1 and 100,000.
- **auto** (default: no): When enabled, search for matching torrents during import.
- **force** (default: no): When enabled, search for matching torrents even for albums that already have a match in the database.
- **pretend** (default: no): When enabled, show the changes that would be made to the database, but do not modify the database.
- **min_score** (experimental, default: 0.75): Minimum match score needed to consider a torrent to be a match to an album. Likely to be changed soon.

For example,

```yaml
redacted:
  api_key: ...
  user_id: ...
  auto: no
  force: no
  pretend: no
  min_score: 0.75
```

Some of these parameters can also be set on the command line, with `-f` / `--force`, `-p` / `--pretend`, and `-m 0.75` / `--min-score=0.75`.

## Usage

Match torrents for the entire library:

```shell
beet redacted
```

Match torrents for Radiohead albums:

```shell
beet redacted Radiohead
```

Match torrents for Radiohead albums, and overwrite the existing matches:

```shell
beet redacted -f Radiohead
```

List albums that don't have a matching torrent, which may be albums to upload:

```shell
beet ls -a red_torrentid::^$
```

(note: matching torrents is fuzzy and imperfect and has room for improvement. It's likely that there are torrents for albums without matches. Please do not automatically upload all unmatched albums without review - you are responsible for your own uploads)

List albums that are missing tracks (using the `missing` plugin) and have a matching torrent, which may be candidates for snatching to fill gaps in the library:

```shell
beet missing -a -c -f '$albumartist - $album: Missing $missing; Red: https://redacted.sh/torrents.php?id=$red_groupid&torrentid=$red_torrentid' ^red_torrentid::^$
```

## Roadmap

1. Improved album - torrent matching logic.
1. Configure preferred torrent encoding, e.g. 'Lossless' > '24bit Lossless' > 'V0 (VBR)' > '320'.
1. Command for snatching and exporting `.torrent` files.

Planned matching improvements:

- ~~Prioritize user's snatches~~
- If possible, re-use Beets' distance matching algorithm.
- Add fields other than artist name, album name, and year to the matching process. It should also include the album's media, distributor, multiple artists, remastering, format, encoding, if it's personal freeleech, and if it's bookmarked.

## Contributing

Comments and suggestions are welcome. Discussion may happen in [the Redacted forum thread](https://redacted.sh/forums.php?action=viewthread&threadid=72289). Pull requests will be eagerly considered.

### Development environment

The plugin uses [Poetry](https://python-poetry.org/) and [Poe the Poet](https://poethepoet.natn.io/) to manage the package, its dependencies, and to format, lint, and test the code. Please ensure you have both installed and are familiar with their usage.

While Beets supports Python 3.8+, this plugin requires 3.9+.

Set up the development environment:

```shell
# Install dependencies
poetry install

# Install Git pre-commit hooks
poetry run pre-commit install
```

Run Beets using the development plugin:

```shell
poetry run beet redacted
```

Sort imports, format, lint, run tests, and check types:

```shell
poetry run poe sort
poetry run poe format
poetry run poe lint
poetry run poe test
poetry run poe type
```

Sort, format, and run tests - useful for AI agents' self-iteration:

```shell
poetry run poe check
```

Sort imports, format, run tests, lint, and check types - enforced on merging pull requests:

```shell
poetry run poe checkall
```

### Development guidelines

To support AI-assisted development, strong type checking is required and it's imperative to maintain very high code coverage with effective unit tests.
