"""
Agent Tracer — Runtime Pipeline Observability
===============================================
Records step-by-step traces of the agent pipeline:
  Route → Cache → RAG → Compress → Generate → Store → Metrics

Each trace captures:
- Per-step latency and metadata
- Routing decisions with confidence scores
- Token usage and savings
- RAG retrieval details
- Cache hit/miss reasoning

Stored in SQLite alongside existing metrics DB.
"""

import json
import sqlite3
import time
import uuid
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CACHE_DIR, METRICS_ENABLED


AGENT_DB = CACHE_DIR / "agent_traces.db"


class AgentTracer:
    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        if METRICS_ENABLED:
            self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(str(AGENT_DB), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                prompt TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                total_latency_ms REAL DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                final_model TEXT,
                task_type TEXT,
                cache_hit INTEGER DEFAULT 0,
                rag_chunks INTEGER DEFAULT 0,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                tokens_saved INTEGER DEFAULT 0,
                playground_id TEXT,
                router_method TEXT,
                router_confidence REAL DEFAULT 0
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trace_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                step_order INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                latency_ms REAL DEFAULT 0,
                status TEXT DEFAULT 'ok',
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trace_steps_trace_id
            ON trace_steps(trace_id)
        """)
        self._conn.commit()

    @property
    def enabled(self) -> bool:
        return METRICS_ENABLED and self._conn is not None

    def start_trace(self, prompt: str) -> str:
        """Begin a new agent trace. Returns trace_id."""
        if not self.enabled:
            return ""
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        self._conn.execute(
            "INSERT INTO traces (id, prompt, started_at) VALUES (?, ?, ?)",
            (trace_id, prompt[:500], datetime.now().isoformat()),
        )
        self._conn.commit()
        return trace_id

    def add_step(
        self,
        trace_id: str,
        step_name: str,
        step_order: int,
        latency_ms: float,
        status: str = "ok",
        **metadata,
    ):
        """Record a completed pipeline step."""
        if not self.enabled or not trace_id:
            return
        now = datetime.now().isoformat()
        self._conn.execute(
            """INSERT INTO trace_steps
               (trace_id, step_name, step_order, started_at, ended_at, latency_ms, status, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace_id, step_name, step_order, now, now,
                round(latency_ms, 2), status,
                json.dumps(metadata, default=str),
            ),
        )
        self._conn.commit()

    def end_trace(
        self,
        trace_id: str,
        total_latency_ms: float,
        total_steps: int,
        final_model: str = "",
        task_type: str = "",
        cache_hit: bool = False,
        rag_chunks: int = 0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_saved: int = 0,
        playground_id: str = "",
        router_method: str = "",
        router_confidence: float = 0,
    ):
        """Finalize a trace with summary data."""
        if not self.enabled or not trace_id:
            return
        self._conn.execute(
            """UPDATE traces SET
               ended_at=?, total_latency_ms=?, total_steps=?,
               final_model=?, task_type=?, cache_hit=?,
               rag_chunks=?, tokens_input=?, tokens_output=?,
               tokens_saved=?, playground_id=?,
               router_method=?, router_confidence=?
               WHERE id=?""",
            (
                datetime.now().isoformat(),
                round(total_latency_ms, 1), total_steps,
                final_model, task_type, 1 if cache_hit else 0,
                rag_chunks, tokens_input, tokens_output,
                tokens_saved, playground_id,
                router_method, round(router_confidence, 3),
                trace_id,
            ),
        )
        self._conn.commit()

    def get_trace(self, trace_id: str) -> Optional[dict]:
        """Retrieve a single trace with all its steps."""
        if not self.enabled:
            return None
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM traces WHERE id=?", (trace_id,))
        row = cursor.fetchone()
        if not row:
            return None
        trace = self._trace_row_to_dict(row)
        cursor.execute(
            "SELECT * FROM trace_steps WHERE trace_id=? ORDER BY step_order",
            (trace_id,),
        )
        trace["steps"] = [self._step_row_to_dict(r) for r in cursor.fetchall()]
        return trace

    def get_recent_traces(self, limit: int = 30) -> list[dict]:
        """Get recent traces with their steps."""
        if not self.enabled:
            return []
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM traces ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        traces = []
        for row in cursor.fetchall():
            trace = self._trace_row_to_dict(row)
            cursor2 = self._conn.cursor()
            cursor2.execute(
                "SELECT * FROM trace_steps WHERE trace_id=? ORDER BY step_order",
                (trace["id"],),
            )
            trace["steps"] = [self._step_row_to_dict(r) for r in cursor2.fetchall()]
            traces.append(trace)
        return traces

    def get_agent_stats(self) -> dict:
        """Aggregate agent statistics for the dashboard."""
        if not self.enabled:
            return {"enabled": False}

        cursor = self._conn.cursor()

        # Total traces
        cursor.execute("SELECT COUNT(*) FROM traces WHERE ended_at IS NOT NULL")
        total_traces = cursor.fetchone()[0]

        if total_traces == 0:
            return {
                "enabled": True,
                "total_traces": 0,
                "avg_latency_ms": 0,
                "avg_steps": 0,
                "cache_hit_rate": "0%",
                "routing_breakdown": {},
                "model_distribution": {},
                "token_economy": {"total_input": 0, "total_output": 0, "total_saved": 0},
                "router_methods": {},
                "avg_confidence": 0,
                "last_24h_traces": 0,
                "step_avg_latencies": {},
            }

        # Avg latency
        cursor.execute("SELECT AVG(total_latency_ms) FROM traces WHERE ended_at IS NOT NULL")
        avg_latency = cursor.fetchone()[0] or 0

        # Avg steps
        cursor.execute("SELECT AVG(total_steps) FROM traces WHERE ended_at IS NOT NULL")
        avg_steps = cursor.fetchone()[0] or 0

        # Cache hit rate
        cursor.execute("SELECT COUNT(*) FROM traces WHERE cache_hit=1")
        cache_hits = cursor.fetchone()[0]
        cache_hit_rate = f"{cache_hits / total_traces * 100:.1f}%" if total_traces > 0 else "0%"

        # Task type breakdown (routing decisions)
        cursor.execute("""
            SELECT task_type, COUNT(*) FROM traces
            WHERE ended_at IS NOT NULL
            GROUP BY task_type
        """)
        routing_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

        # Model distribution
        cursor.execute("""
            SELECT final_model, COUNT(*) FROM traces
            WHERE ended_at IS NOT NULL AND final_model != ''
            GROUP BY final_model
        """)
        model_distribution = {row[0]: row[1] for row in cursor.fetchall()}

        # Token economy
        cursor.execute("""
            SELECT SUM(tokens_input), SUM(tokens_output), SUM(tokens_saved)
            FROM traces WHERE ended_at IS NOT NULL
        """)
        tok_row = cursor.fetchone()
        token_economy = {
            "total_input": tok_row[0] or 0,
            "total_output": tok_row[1] or 0,
            "total_saved": tok_row[2] or 0,
        }

        # Router method breakdown
        cursor.execute("""
            SELECT router_method, COUNT(*) FROM traces
            WHERE ended_at IS NOT NULL AND router_method != ''
            GROUP BY router_method
        """)
        router_methods = {row[0]: row[1] for row in cursor.fetchall()}

        # Avg confidence
        cursor.execute("SELECT AVG(router_confidence) FROM traces WHERE router_confidence > 0")
        avg_confidence = cursor.fetchone()[0] or 0

        # Last 24h
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM traces WHERE started_at > ?", (cutoff,))
        last_24h = cursor.fetchone()[0]

        # Per-step average latencies
        cursor.execute("""
            SELECT step_name, AVG(latency_ms), COUNT(*)
            FROM trace_steps
            GROUP BY step_name
            ORDER BY AVG(latency_ms) DESC
        """)
        step_avg_latencies = {
            row[0]: {"avg_ms": round(row[1] or 0, 1), "count": row[2]}
            for row in cursor.fetchall()
        }

        return {
            "enabled": True,
            "total_traces": total_traces,
            "avg_latency_ms": round(avg_latency, 1),
            "avg_steps": round(avg_steps, 1),
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": cache_hits,
            "routing_breakdown": routing_breakdown,
            "model_distribution": model_distribution,
            "token_economy": token_economy,
            "router_methods": router_methods,
            "avg_confidence": round(avg_confidence, 3),
            "last_24h_traces": last_24h,
            "step_avg_latencies": step_avg_latencies,
        }

    def _trace_row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "prompt": row[1],
            "started_at": row[2],
            "ended_at": row[3],
            "total_latency_ms": row[4],
            "total_steps": row[5],
            "final_model": row[6],
            "task_type": row[7],
            "cache_hit": bool(row[8]),
            "rag_chunks": row[9],
            "tokens_input": row[10],
            "tokens_output": row[11],
            "tokens_saved": row[12],
            "playground_id": row[13],
            "router_method": row[14],
            "router_confidence": row[15],
        }

    def _step_row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "trace_id": row[1],
            "step_name": row[2],
            "step_order": row[3],
            "started_at": row[4],
            "ended_at": row[5],
            "latency_ms": row[6],
            "status": row[7],
            "metadata": json.loads(row[8]) if row[8] else {},
        }
