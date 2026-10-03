"""
MusicBrainz + Partita artist image provider for the fetchartist plugin.

Flow: artist name -> MusicBrainz MBID -> Spotify URL (from url-rels) ->
Partita /resolve -> permanent art_ ID plus the artist image URL.
"""
import logging
import time

import requests

log = logging.getLogger("beets")

MUSICBRAINZ_API = "https://musicbrainz.org/ws/2/artist"
USER_AGENT = "beets-fetchartist/0.1 (beets fetchartist plugin)"


class PartitaResolver:
    BASE_URL = "https://api.partita.io/v1"

    def _search_musicbrainz(self, name):
        """Search MusicBrainz by name; return the top-scored MBID or None."""
        response = requests.get(
            MUSICBRAINZ_API,
            params={"query": "artist:%s" % name, "fmt": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()

        artists = response.json().get("artists") or []
        return artists[0]["id"] if artists else None

    def _get_spotify_url(self, mbid):
        """Return the artist's Spotify URL from MusicBrainz url-rels, or None."""
        response = requests.get(
            "%s/%s" % (MUSICBRAINZ_API, mbid),
            params={"inc": "url-rels", "fmt": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()

        relations = response.json().get("relations") or []
        for relation in relations:
            resource = relation.get("url", {}).get("resource") or ""
            # MusicBrainz labels Spotify links "free streaming" (or similar),
            # not "spotify", so match on the URL itself.
            if "spotify.com" in resource:
                return resource
        return None

    def get_artist_image(self, name):
        """
        Resolve an artist name to an image via MusicBrainz + Partita.

        Returns a tuple (image_url, partita_id); (None, None) on any failure.
        """
        try:
            mbid = self._search_musicbrainz(name)
            if not mbid:
                log.debug("partita: no MusicBrainz match for '{}'", name)
                return (None, None)

            time.sleep(1)  # MusicBrainz policy: max 1 request/second

            spotify_url = self._get_spotify_url(mbid)
            if not spotify_url:
                log.debug("partita: no Spotify relation for MBID {}", mbid)
                return (None, None)

            return self._resolve(spotify_url)
        except requests.RequestException as exc:
            log.debug("partita: request failed for '{}': {}", name, exc)
            return (None, None)

    def _resolve(self, spotify_url):
        """Resolve a Spotify artist URL via Partita; return (url, id)."""
        response = requests.get(
            "%s/resolve" % self.BASE_URL,
            params={"url": spotify_url},
            timeout=10,
        )
        if response.status_code == 429:
            log.warning("partita: rate limited (60 req/min); skipping")
            return (None, None)
        response.raise_for_status()

        data = response.json()
        artist = data.get("artist") or {}
        return (artist.get("imageUrl"), artist.get("id"))

    def lookup_artist(self, partita_id):
        """Get the artist image by permanent Partita ID. None on failure."""
        try:
            response = requests.get(
                "%s/artists/%s" % (self.BASE_URL, partita_id),
                timeout=10,
            )
            if response.status_code == 429:
                log.warning("partita: rate limited (60 req/min); skipping")
                return None
            if response.status_code == 404:
                return None
            response.raise_for_status()

            return response.json().get("imageUrl")
        except requests.RequestException as exc:
            log.debug("partita: lookup failed for {}: {}", partita_id, exc)
            return None
