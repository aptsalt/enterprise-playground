"""
Metrics Collector for Enterprise Playground
=============================================
Tracks per-generation metrics and aggregates for the dashboard.
Stores everything in SQLite alongside the existing cache DB.
"""

import json
import sqlite3
import subprocess
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import METRICS_DB, METRICS_ENABLED


class MetricsCollector:
    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        if METRICS_ENABLED:
            self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(str(METRICS_DB), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt TEXT,
                model TEXT,
                task_type TEXT,
                latency_ms REAL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cache_hit INTEGER DEFAULT 0,
                rag_chunks_used INTEGER DEFAULT 0,
                rag_enabled INTEGER DEFAULT 0,
                playground_id TEXT,
                style TEXT,
                html_size_bytes INTEGER DEFAULT 0
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS vram_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                used_mb INTEGER,
                total_mb INTEGER,
                temp_c INTEGER,
                utilization_pct INTEGER
            )
        """)
        # Indexes for dashboard query performance
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_gm_cache_hit ON generation_metrics(cache_hit)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_gm_timestamp ON generation_metrics(timestamp DESC)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_gm_rag ON generation_metrics(rag_chunks_used)")
        self._conn.commit()

    @property
    def enabled(self) -> bool:
        return METRICS_ENABLED and self._conn is not None

    def record_generation(
        self,
        prompt: str,
        model: str,
        task_type: str,
        latency_ms: float,
        cache_hit: bool = False,
        rag_chunks_used: int = 0,
        rag_enabled: bool = False,
        playground_id: str = "",
        style: str = "",
        html_size_bytes: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        if not self.enabled:
            return

        self._conn.execute("""
            INSERT INTO generation_metrics
            (timestamp, prompt, model, task_type, latency_ms, input_tokens, output_tokens,
             cache_hit, rag_chunks_used, rag_enabled, playground_id, style, html_size_bytes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            prompt[:500],
            model,
            task_type,
            latency_ms,
            input_tokens,
            output_tokens,
            1 if cache_hit else 0,
            rag_chunks_used,
            1 if rag_enabled else 0,
            playground_id,
            style,
            html_size_bytes,
        ))
        self._conn.commit()

    def record_vram_snapshot(self):
        """Capture current VRAM usage."""
        if not self.enabled:
            return

        try:
            result = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=memory.used,memory.total,temperature.gpu,utilization.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts = [p.strip() for p in result.stdout.strip().split(",")]
                if len(parts) >= 4:
                    self._conn.execute("""
                        INSERT INTO vram_snapshots (timestamp, used_mb, total_mb, temp_c, utilization_pct)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]),
                    ))
                    self._conn.commit()
        except Exception:
            pass

    def get_dashboard_stats(self) -> dict:
        """Return all stats the dashboard needs."""
        if not self.enabled:
            return {"enabled": False}

        cursor = self._conn.cursor()

        # Total generations
        cursor.execute("SELECT COUNT(*) FROM generation_metrics")
        total_generations = cursor.fetchone()[0]

        # Cache hit rate
        cursor.execute("SELECT COUNT(*) FROM generation_metrics WHERE cache_hit = 1")
        cache_hits = cursor.fetchone()[0]
        cache_hit_rate = f"{cache_hits / total_generations * 100:.1f}%" if total_generations > 0 else "0%"

        # Average latency (non-cache-hit only)
        cursor.execute("SELECT AVG(latency_ms) FROM generation_metrics WHERE cache_hit = 0")
        avg_latency = cursor.fetchone()[0] or 0

        # Total tokens
        cursor.execute("SELECT SUM(input_tokens), SUM(output_tokens) FROM generation_metrics")
        row = cursor.fetchone()
        total_input_tokens = row[0] or 0
        total_output_tokens = row[1] or 0

        # RAG usage
        cursor.execute("SELECT COUNT(*) FROM generation_metrics WHERE rag_chunks_used > 0")
        rag_generations = cursor.fetchone()[0]

        # Avg RAG chunks when RAG was used
        cursor.execute("SELECT AVG(rag_chunks_used) FROM generation_metrics WHERE rag_chunks_used > 0")
        avg_rag_chunks = cursor.fetchone()[0] or 0

        # Model breakdown
        cursor.execute("""
            SELECT model, COUNT(*), AVG(latency_ms)
            FROM generation_metrics
            GROUP BY model
        """)
        model_breakdown = {}
        for row in cursor.fetchall():
            model_breakdown[row[0]] = {
                "count": row[1],
                "avg_latency_ms": round(row[2] or 0, 1),
            }

        # Last 24h generation count
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM generation_metrics WHERE timestamp > ?", (cutoff,))
        last_24h = cursor.fetchone()[0]

        # Recent VRAM snapshot
        cursor.execute("SELECT * FROM vram_snapshots ORDER BY id DESC LIMIT 1")
        vram_row = cursor.fetchone()
        vram = None
        if vram_row:
            vram = {
                "used_mb": vram_row[2],
                "total_mb": vram_row[3],
                "temp_c": vram_row[4],
                "utilization_pct": vram_row[5],
                "recorded_at": vram_row[1],
            }

        # Recent generations (last 50)
        cursor.execute("""
            SELECT timestamp, prompt, model, task_type, latency_ms,
                   cache_hit, rag_chunks_used, playground_id, style
            FROM generation_metrics
            ORDER BY id DESC LIMIT 50
        """)
        recent = []
        for row in cursor.fetchall():
            recent.append({
                "timestamp": row[0],
                "prompt": row[1],
                "model": row[2],
                "task_type": row[3],
                "latency_ms": round(row[4] or 0, 1),
                "cache_hit": bool(row[5]),
                "rag_chunks_used": row[6],
                "playground_id": row[7],
                "style": row[8],
            })

        return {
            "enabled": True,
            "total_generations": total_generations,
            "cache_hits": cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "avg_latency_ms": round(avg_latency, 1),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "rag_generations": rag_generations,
            "avg_rag_chunks": round(avg_rag_chunks, 1),
            "model_breakdown": model_breakdown,
            "last_24h_generations": last_24h,
            "vram": vram,
            "recent": recent,
        }
