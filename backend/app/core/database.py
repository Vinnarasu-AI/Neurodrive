"""
Database module using SQLite and aiosqlite for persistent logging of:
- EOG double-blink detection events
- Relay actuation commands and states
- Calibration records
- System alerts and status changes
"""

import aiosqlite
import logging
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger("neurodrive.db")


class Database:
    def __init__(self, db_path: str = "neurodrive.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    details TEXT,
                    success INTEGER NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS calibrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    baseline_mean REAL NOT NULL,
                    baseline_std REAL NOT NULL,
                    peak_threshold REAL NOT NULL,
                    notes TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS relay_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    command TEXT NOT NULL,
                    state TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    latency_ms REAL,
                    success INTEGER NOT NULL,
                    error_message TEXT
                )
                """
            )
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def log_event(
        self,
        event_type: str,
        source: str,
        details: str = "",
        success: bool = True,
    ) -> int:
        now = time.time()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO event_logs (timestamp, event_type, source, details, success)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, event_type, source, details, 1 if success else 0),
            )
            await db.commit()
            return cursor.lastrowid

    async def log_relay_action(
        self,
        command: str,
        state: str,
        trigger: str,
        latency_ms: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> int:
        now = time.time()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO relay_actions (timestamp, command, state, trigger, latency_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (now, command, state, trigger, latency_ms, 1 if success else 0, error_message or ""),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, timestamp, event_type, source, details, success
                FROM event_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_recent_relay_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, timestamp, command, state, trigger, latency_ms, success, error_message
                FROM relay_actions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


db = Database()

