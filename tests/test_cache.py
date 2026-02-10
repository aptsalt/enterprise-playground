"""Tests for the semantic response cache."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from playground.cache import ResponseCache


class TestResponseCache:
    """Test semantic caching behavior."""

    def setup_method(self):
        self.cache = ResponseCache.__new__(ResponseCache)
        self.cache._entries = {}
        self.cache._access_order = []
        self.cache.cache_dir = Path("/tmp/test_cache")
        self.cache.similarity_threshold = 0.85
        self.cache.max_size_mb = 500
        self.cache._total_requests = 0
        self.cache._cache_hits = 0
        self.cache._tokens_saved = 0

    def test_exact_match(self):
        key = "create a banking dashboard"
        self.cache._entries[key] = {
            "prompt": key,
            "html": "<div>test</div>",
            "playground_id": "pg-001",
            "created": time.time(),
            "tokens": 100,
        }
        result = self.cache.lookup(key)
        assert result is not None
        assert result["playground_id"] == "pg-001"

    def test_cache_miss(self):
        result = self.cache.lookup("nonexistent prompt")
        assert result is None

    def test_stats_tracking(self):
        self.cache._total_requests = 100
        self.cache._cache_hits = 35
        stats = self.cache.stats()
        assert stats["total_requests"] == 100
        assert stats["cache_hits"] == 35
        assert stats["hit_rate"] == "35.0%"

    def test_clear(self):
        self.cache._entries["test"] = {"html": "x"}
        self.cache.clear()
        assert len(self.cache._entries) == 0
        assert self.cache._cache_hits == 0

    def test_similar_prompt_match(self):
        key = "create a banking dashboard for personal accounts"
        self.cache._entries[key] = {
            "prompt": key,
            "html": "<div>banking</div>",
            "playground_id": "pg-002",
            "created": time.time(),
            "tokens": 150,
        }
        similar = "create a banking dashboard for personal account"
        result = self.cache.lookup(similar)
        assert result is not None

    def test_dissimilar_prompt_no_match(self):
        key = "create a banking dashboard"
        self.cache._entries[key] = {
            "prompt": key,
            "html": "<div>x</div>",
            "playground_id": "pg-003",
            "created": time.time(),
            "tokens": 100,
        }
        dissimilar = "explain mortgage amortization schedule"
        result = self.cache.lookup(dissimilar)
        assert result is None
