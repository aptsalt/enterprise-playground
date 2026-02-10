"""Shared test fixtures for backend tests."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_ollama():
    """Mock Ollama client to avoid real model calls in tests."""
    with patch("ollama.AsyncClient") as mock_cls:
        client = AsyncMock()
        mock_cls.return_value = client
        client.chat.return_value = {
            "message": {"content": "<div class='td-hero'>Test Banking Page</div>"},
            "eval_count": 150,
            "prompt_eval_count": 50,
        }
        yield client


@pytest.fixture
def sample_workflow() -> dict:
    """Minimal workflow fixture for testing."""
    return {
        "workflow_id": "test-wf-001",
        "name": "Test Banking Workflow",
        "category": "accounts",
        "steps": [
            {
                "page_url": "https://td.com/accounts",
                "page_title": "Accounts Overview",
                "actions": ["View balances", "Transfer funds"],
            }
        ],
        "tags": ["accounts", "banking"],
    }


@pytest.fixture
def sample_playground_html() -> str:
    """Sample generated playground HTML for testing."""
    return """<div class="td-nav">
<a href="#">Personal</a>
<a href="#">Business</a>
</div>
<div class="td-hero">
<h1>Welcome to TD Banking</h1>
<p>Manage your accounts with ease</p>
</div>
<div class="product-card">
<h3>Chequing Account</h3>
<p>No monthly fees with minimum balance</p>
</div>"""
