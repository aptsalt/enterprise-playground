"""Tests for FastAPI endpoints."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_dependencies():
    """Mock all heavy dependencies before importing app."""
    with patch("playground.generator.PlaygroundGenerator") as mock_gen, \
         patch("playground.rag.RAGStore"), \
         patch("playground.metrics.MetricsCollector"), \
         patch("playground.observatory.MLObservatory"), \
         patch("playground.agent_tracer.AgentTracer"):

        gen_instance = MagicMock()
        gen_instance.list_generated.return_value = []
        gen_instance.cache.stats.return_value = {
            "entries": 0,
            "total_requests": 0,
            "cache_hits": 0,
            "hit_rate": "0%",
        }
        gen_instance.get_stats.return_value = {"playgrounds_count": 0, "cache_entries": 0}
        gen_instance.rag = MagicMock()
        gen_instance.rag.stats.return_value = {"total_chunks": 0, "collection": "workflows"}
        gen_instance.metrics = MagicMock()
        gen_instance.tracer = MagicMock()
        gen_instance.tracer.get_agent_stats.return_value = {
            "total_traces": 0,
            "avg_latency_ms": 0,
            "cache_hit_rate": "0%",
            "avg_confidence": 0,
            "last_24h_traces": 0,
        }
        gen_instance.tracer.get_recent_traces.return_value = []
        mock_gen.return_value = gen_instance
        yield gen_instance


@pytest.mark.asyncio
async def test_health_endpoint(mock_dependencies):
    from webapp.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "generator_model" in data
        assert "router_model" in data


@pytest.mark.asyncio
async def test_playgrounds_endpoint(mock_dependencies):
    from webapp.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/playgrounds")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_cache_clear_endpoint(mock_dependencies):
    from webapp.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/cache/clear")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"


@pytest.mark.asyncio
async def test_rag_stats_endpoint(mock_dependencies):
    from webapp.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/rag/stats")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_feedback_endpoint(mock_dependencies):
    from webapp.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/feedback",
            json={
                "playground_id": "pg-001",
                "rating": "up",
                "prompt": "test prompt",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "recorded"
