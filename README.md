# fetchartist

A plugin that fetches artist covers and places them in the artist directories.

Image sources, in order:

1. **Cache** — a previously resolved Partita permanent ID (`art_...`) is looked up directly.
2. **AudioDB** — artist image by name.
3. **Partita** — resolve via MusicBrainz: artist name → MBID → Spotify URL (from MusicBrainz url-rels) → Partita `/resolve`. The resulting permanent ID is stored in the cache.

The cache is a JSON file (`fetchartist-cache.json`) in beets' config directory.
Automatically fetching artist covers during import is not yet supported.

## Installation

The plugin requires `pylast` and `requests` which can be installed using `pip` on the host machine. MusicBrainz and Partita are accessed over plain HTTP (no extra dependencies).

```sh
sudo pip install pylast requests
```

Afterwards, beets has to be configured to use the plugin.

```sh
pluginpath:
  ~/fetchartist

plugins: fetchartist
```

## Configuration

The configuration is located in the fetchartist section.
Only the `filename` option exists at the moment, which will determine the filename of the images.
It will default to empty and use the artist names.

```sh
fetchartist:
  filename: "poster"
```

## Usage

This plugin should be the same as any other plugin for beets when using a recent version.

```sh
Usage: beet fetchartist [options]

Options:
-h, --help   show this help message and exit
-f, --force  force overwrite existing artist covers
```
