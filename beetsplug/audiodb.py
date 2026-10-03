"""
AudioDB artist image provider for the fetchartist plugin.
"""
import requests


class ArtistImages:
    BASE_URL = "https://www.theaudiodb.com/api/v1/json/123"

    def get_artist(self, name):
        response = requests.get(
            f"{self.BASE_URL}/search.php",
            params={"s": name},
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        artists = data.get("artists") or []

        return artists[0] if artists else None

    def get_artist_image(self, name):
        artist = self.get_artist(name)

        if not artist:
            return None

        return artist.get("strArtistThumb")