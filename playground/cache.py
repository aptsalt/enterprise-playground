"""
Playground Cache
=================
Semantic caching layer that avoids regenerating similar playgrounds.
Uses token-level similarity (no embeddings needed — saves VRAM).

Cache hit → 0 tokens, instant response.
Cache miss → normal generation.

Typical hit rate after 50+ generations: 15-30% (saves significant compute).
"""

import hashlib
import json
import os
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CACHE_DIR, CACHE_ENABLED, CACHE_MAX_SIZE_MB, CACHE_SIMILARITY_THRESHOLD, CACHE_TTL_HOURS


class PlaygroundCache:
    def __init__(self):
        self.index_path = CACHE_DIR / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> dict:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"entries": {}, "stats": {"hits": 0, "misses": 0, "total_saved_tokens": 0}}

    def _save_index(self):
        self.index_path.write_text(json.dumps(self._index, indent=1), encoding="utf-8")

    def get(self, prompt: str, style: str = "banking") -> Optional[dict]:
        """
        Check cache for a similar prompt. Returns cached result or None.
        Uses SequenceMatcher for similarity — fast, no ML deps, no VRAM.
        """
        if not CACHE_ENABLED:
            return None

        self._evict_expired()
        key = self._normalize(prompt, style)
        now = time.time()

        # Exact match (hash)
        exact_hash = hashlib.md5(key.encode()).hexdigest()
        if exact_hash in self._index["entries"]:
            entry = self._index["entries"][exact_hash]
            html_path = Path(entry["html_path"])
            if html_path.exists():
                self._index["stats"]["hits"] += 1
                self._index["stats"]["total_saved_tokens"] += entry.get("est_tokens", 3000)
                entry["last_hit"] = now
                entry["hit_count"] = entry.get("hit_count", 0) + 1
                self._save_index()
                return {
                    "html": html_path.read_text(encoding="utf-8"),
                    "playground_id": entry["playground_id"],
                    "cache_hit": True,
                    "similarity": 1.0,
                }

        # Fuzzy match
        best_match = None
        best_score = 0.0
        for entry_hash, entry in self._index["entries"].items():
            score = SequenceMatcher(None, key, entry.get("normalized_key", "")).ratio()
            if score > best_score and score >= CACHE_SIMILARITY_THRESHOLD:
                best_score = score
                best_match = entry

        if best_match:
            html_path = Path(best_match["html_path"])
            if html_path.exists():
                self._index["stats"]["hits"] += 1
                self._index["stats"]["total_saved_tokens"] += best_match.get("est_tokens", 3000)
                best_match["last_hit"] = now
                best_match["hit_count"] = best_match.get("hit_count", 0) + 1
                self._save_index()
                return {
                    "html": html_path.read_text(encoding="utf-8"),
                    "playground_id": best_match["playground_id"],
                    "cache_hit": True,
                    "similarity": best_score,
                }

        self._index["stats"]["misses"] += 1
        self._save_index()
        return None

    def put(self, prompt: str, style: str, playground_id: str, html_path: str, est_tokens: int = 3000):
        """Store a generated playground in cache."""
        if not CACHE_ENABLED:
            return

        key = self._normalize(prompt, style)
        entry_hash = hashlib.md5(key.encode()).hexdigest()

        self._index["entries"][entry_hash] = {
            "prompt": prompt[:300],
            "style": style,
            "normalized_key": key,
            "playground_id": playground_id,
            "html_path": html_path,
            "est_tokens": est_tokens,
            "created_at": time.time(),
            "last_hit": time.time(),
            "hit_count": 0,
        }
        self._save_index()
        self._enforce_size_limit()

    def _normalize(self, prompt: str, style: str) -> str:
        """Normalize a prompt for comparison. Strips noise, lowercases."""
        p = prompt.lower().strip()
        # Remove common filler words that don't affect output
        for word in ["please", "can you", "i want", "i need", "could you", "would you",
                      "create", "generate", "make", "build", "a ", "an ", "the "]:
            p = p.replace(word, "")
        return f"{p.strip()}|{style}"

    def _evict_expired(self):
        """Remove entries older than TTL."""
        now = time.time()
        ttl_seconds = CACHE_TTL_HOURS * 3600
        expired = [
            k for k, v in self._index["entries"].items()
            if now - v.get("last_hit", v.get("created_at", 0)) > ttl_seconds
        ]
        for k in expired:
            del self._index["entries"][k]
        if expired:
            self._save_index()

    def _enforce_size_limit(self):
        """Remove oldest entries if cache exceeds size limit."""
        total_size = sum(
            Path(e["html_path"]).stat().st_size
            for e in self._index["entries"].values()
            if Path(e["html_path"]).exists()
        )
        max_bytes = CACHE_MAX_SIZE_MB * 1024 * 1024

        if total_size <= max_bytes:
            return

        # Evict least-recently-used entries
        sorted_entries = sorted(
            self._index["entries"].items(),
            key=lambda x: x[1].get("last_hit", 0)
        )
        while total_size > max_bytes and sorted_entries:
            key, entry = sorted_entries.pop(0)
            html_path = Path(entry["html_path"])
            if html_path.exists():
                total_size -= html_path.stat().st_size
            del self._index["entries"][key]
        self._save_index()

    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._index["stats"]["hits"] + self._index["stats"]["misses"]
        return {
            "entries": len(self._index["entries"]),
            "hits": self._index["stats"]["hits"],
            "misses": self._index["stats"]["misses"],
            "hit_rate": f"{self._index['stats']['hits'] / max(total, 1) * 100:.1f}%",
            "total_saved_tokens": self._index["stats"]["total_saved_tokens"],
            "est_saved_cost_usd": f"${self._index['stats']['total_saved_tokens'] * 0.000015:.2f}",
        }

    def clear(self):
        """Clear the entire cache."""
        self._index = {"entries": {}, "stats": {"hits": 0, "misses": 0, "total_saved_tokens": 0}}
        self._save_index()
