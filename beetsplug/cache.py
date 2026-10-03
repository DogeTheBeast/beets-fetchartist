"""
Persistent mapping cache (artist name -> Partita permanent ID) for the
fetchartist plugin. Stored as JSON in beets' config directory.
"""
import json
import logging
import os
import tempfile
import time

from beets import config

log = logging.getLogger("beets")

CACHE_FILENAME = "fetchartist-cache.json"


class MappingCache:
    def __init__(self, path=None):
        self.path = path or os.path.join(config.config_dir(), CACHE_FILENAME)
        self._data = None

    def _load(self):
        if self._data is not None:
            return

        try:
            with open(self.path, "r") as handle:
                self._data = json.load(handle)
        except (IOError, OSError, ValueError):
            # missing or corrupt cache: start empty, never crash
            log.debug("fetchartist: cache could not be loaded from '{}'",
                      self.path)
            self._data = {}

    def get(self, name):
        """Return the cached Partita ID for an artist name, or None."""
        key = name.strip().lower()
        self._load()
        record = self._data.get(key) or {}
        return record.get("partita_id")

    def put(self, name, partita_id):
        """Store the Partita ID for an artist name (in memory)."""
        key = name.strip().lower()
        self._load()
        self._data[key] = {
            "partita_id": partita_id,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def save(self):
        """Write the cache to disk atomically. No-op if the dir is missing."""
        self._load()

        directory = os.path.dirname(self.path)
        if directory and not os.path.isdir(directory):
            log.debug("fetchartist: cache dir missing; not saving '{}'",
                      self.path)
            return

        fd, tmp_path = tempfile.mkstemp(dir=directory or ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(self._data, handle, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise