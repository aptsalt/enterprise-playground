"""Tests for the smart request router."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from playground.router import RequestRouter, TaskType


class TestKeywordRouting:
    """Test keyword-based routing (zero tokens, instant)."""

    def setup_method(self):
        self.router = RequestRouter.__new__(RequestRouter)
        self.router.model = "qwen2.5:3b"

    def test_generate_keywords(self):
        assert self.router._keyword_classify("create a banking dashboard") == TaskType.GENERATE
        assert self.router._keyword_classify("build me a login page") == TaskType.GENERATE
        assert self.router._keyword_classify("generate a mortgage calculator") == TaskType.GENERATE
        assert self.router._keyword_classify("make an account overview") == TaskType.GENERATE

    def test_explain_keywords(self):
        assert self.router._keyword_classify("explain how the nav works") == TaskType.EXPLAIN
        assert self.router._keyword_classify("what does this component do") == TaskType.EXPLAIN
        assert self.router._keyword_classify("how does the form validation work") == TaskType.EXPLAIN

    def test_modify_keywords(self):
        assert self.router._keyword_classify("change the header color") == TaskType.MODIFY
        assert self.router._keyword_classify("update the footer links") == TaskType.MODIFY
        assert self.router._keyword_classify("fix the broken button") == TaskType.MODIFY

    def test_summarize_keywords(self):
        assert self.router._keyword_classify("summarize this workflow") == TaskType.SUMMARIZE
        assert self.router._keyword_classify("give me an overview of accounts") == TaskType.SUMMARIZE

    def test_compare_keywords(self):
        assert self.router._keyword_classify("compare chequing and savings") == TaskType.COMPARE
        assert self.router._keyword_classify("difference between fixed and variable rates") == TaskType.COMPARE

    def test_ambiguous_falls_through(self):
        result = self.router._keyword_classify("hello there")
        assert result is None


class TestTaskTypeRouting:
    """Test that task types route to correct models."""

    def test_generate_uses_14b(self):
        assert TaskType.GENERATE.needs_code_model is True

    def test_explain_uses_3b(self):
        assert TaskType.EXPLAIN.needs_code_model is False

    def test_chat_uses_3b(self):
        assert TaskType.CHAT.needs_code_model is False

    def test_modify_uses_14b(self):
        assert TaskType.MODIFY.needs_code_model is True
