"""
cache.py
Simple on-disk cache for AI responses, keyed by (file content hash,
prompt type). Prevents re-billing the API for a file that hasn't
changed since it was last summarized/refactored.

Deliberately just JSON-on-disk, not a database - this is a
single-developer CLI tool, not a service with concurrent writers.
"""

import hashlib
import json
import os
from pathlib import Path


class ResponseCache:
    def __init__(self, cache_dir: str = ".ai_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _cache_path(self, file_content: str, prompt_type: str, extra: str = "") -> Path:
        content_hash = self._hash_content(file_content + extra)
        return self.cache_dir / f"{prompt_type}_{content_hash}.json"

    def get(self, file_content: str, prompt_type: str, extra: str = ""):
        """
        Return the cached response for this exact (content, prompt_type,
        extra) combination, or None if not cached.
        """
        path = self._cache_path(file_content, prompt_type, extra)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("response")
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, file_content: str, prompt_type: str, response: str, extra: str = ""):
        """Store `response` for this (content, prompt_type, extra) combination."""
        path = self._cache_path(file_content, prompt_type, extra)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"response": response}, f)

    def clear(self):
        """Delete all cached responses."""
        for cached_file in self.cache_dir.glob("*.json"):
            os.remove(cached_file)
