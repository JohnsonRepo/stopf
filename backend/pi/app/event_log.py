"""
event_log.py
Strukturiertes Ereignis-Protokoll (Fehlerspeicher).

Zwei Schichten:
- In-Memory-Ringpuffer (schnell, immer aktiv, wie bisher)
- optionale SQLite-Persistenz — überlebt Backend-Neustart und Stromausfall

Events sind strukturiert (code/source/step/details statt nur Freitext), damit
Fehlversuche filterbar (GET /events?level=&code=) und zählbar (GET /stats)
sind. Der Sensor-Snapshot im Fehlermoment landet in `details`.

Persistenz-Pfad: $STOPF_DB, Default backend/pi/data/stopf.db (liegt im
Repo-Ordner, ist gitignored, übersteht `git pull` vom Updater). Auf Overlay-FS
(read-only SD, siehe pi-setup.md) ist der Pfad nicht beschreibbar → das Log
läuft automatisch memory-only weiter wie vor v0.5.0. Wichtige Events gehen
unabhängig davon zusätzlich ins journald.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass

logger = logging.getLogger("uvicorn.error")

_PI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # backend/pi
DEFAULT_DB_PATH = os.path.join(_PI_DIR, "data", "stopf.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      REAL NOT NULL,
    level   TEXT NOT NULL,
    code    TEXT,
    message TEXT NOT NULL,
    source  TEXT NOT NULL DEFAULT 'backend',
    step    INTEGER,
    details TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts    ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_level ON events(level);

CREATE TABLE IF NOT EXISTS cycles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_ts REAL NOT NULL,
    ended_ts   REAL,
    ok         INTEGER,       -- 1=fertig, 0=fehlgeschlagen/abgebrochen, NULL=offen
    fail_code  TEXT,          -- z. B. press_fwd_timeout, 'aborted', 'backend_restart'
    fail_step  INTEGER
);
"""

# fail_codes, die kein Maschinenfehler sind (zählen nicht in die Erfolgsquote)
_ABORT_CODES = ("aborted", "backend_restart")


@dataclass
class Event:
    ts: float
    level: str                    # "info" | "warn" | "error"
    message: str
    code: str | None = None       # maschinenlesbar, z. B. "press_fwd_timeout"
    source: str = "backend"       # "nano" | "backend" | "user"
    step: int | None = None       # Stuff-Step im Fehlermoment
    details: dict | None = None   # z. B. Sensor-Snapshot


class EventLog:
    def __init__(self, maxlen: int = 200, db_path: str | None = None):
        self._events: deque[Event] = deque(maxlen=maxlen)
        self._db: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        # RAM-Zähler: Fallback für stats() wenn keine DB beschreibbar ist
        self._ram_cycles = {"started": 0, "completed": 0, "failed": 0, "aborted": 0}
        path = db_path if db_path is not None else os.environ.get("STOPF_DB", DEFAULT_DB_PATH)
        if path:
            self._open_db(path)

    # -------- Persistenz --------

    def _open_db(self, path: str) -> None:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            db = sqlite3.connect(path, check_same_thread=False)
            db.executescript(_SCHEMA)
            db.execute("PRAGMA journal_mode=WAL")
            # Zyklen, die beim letzten Lauf offen blieben (Absturz/Stromaus),
            # sauber schließen — sonst zählt started ewig gegen completed.
            db.execute(
                "UPDATE cycles SET ended_ts=?, ok=0, fail_code='backend_restart' WHERE ok IS NULL",
                (time.time(),),
            )
            db.commit()
            self._db = db
            logger.info("EventLog: SQLite-Persistenz aktiv (%s)", path)
        except (OSError, sqlite3.Error) as e:
            self._db = None
            logger.warning(
                "EventLog: Persistenz nicht möglich (%s) — weiter memory-only "
                "(normal bei Overlay-FS). Grund: %s", path, e,
            )

    @property
    def persisted(self) -> bool:
        return self._db is not None

    # -------- Schreiben --------

    def add(self, level: str, message: str, *, code: str | None = None,
            source: str = "backend", step: int | None = None,
            details: dict | None = None) -> None:
        ev = Event(ts=time.time(), level=level, message=message,
                   code=code, source=source, step=step, details=details)
        self._events.append(ev)
        if self._db:
            try:
                with self._lock:
                    self._db.execute(
                        "INSERT INTO events (ts, level, code, message, source, step, details) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (ev.ts, ev.level, ev.code, ev.message, ev.source, ev.step,
                         json.dumps(ev.details, ensure_ascii=False)
                         if ev.details is not None else None),
                    )
                    self._db.commit()
            except sqlite3.Error:
                logger.exception("EventLog: DB-Insert fehlgeschlagen")
        # Wichtige Events zusätzlich ins journald (überlebt Neustart auch ohne DB).
        if level == "error":
            logger.error("EVENT %s", message)
        elif level == "warn":
            logger.warning("EVENT %s", message)
        else:
            logger.info("EVENT %s", message)

    def info(self, m: str, **kw) -> None:  self.add("info", m, **kw)
    def warn(self, m: str, **kw) -> None:  self.add("warn", m, **kw)
    def error(self, m: str, **kw) -> None: self.add("error", m, **kw)

    # -------- Lesen --------

    def list(self, level: str | None = None, code: str | None = None,
             limit: int = 200, since: float | None = None) -> list[dict]:
        """Neueste zuerst, optional gefiltert. Mit DB auch über den Ringpuffer hinaus."""
        if self._db:
            conds, args = [], []
            if level is not None:
                conds.append("level = ?");  args.append(level)
            if code is not None:
                conds.append("code = ?");   args.append(code)
            if since is not None:
                conds.append("ts >= ?");    args.append(since)
            where = ("WHERE " + " AND ".join(conds)) if conds else ""
            try:
                with self._lock:
                    rows = self._db.execute(
                        f"SELECT ts, level, code, message, source, step, details "
                        f"FROM events {where} ORDER BY ts DESC, id DESC LIMIT ?",
                        (*args, limit),
                    ).fetchall()
                return [
                    {"ts": r[0], "level": r[1], "code": r[2], "message": r[3],
                     "source": r[4], "step": r[5],
                     "details": json.loads(r[6]) if r[6] else None}
                    for r in rows
                ]
            except sqlite3.Error:
                logger.exception("EventLog: DB-Query fehlgeschlagen — RAM-Fallback")
        out = [
            asdict(e) for e in reversed(self._events)
            if (level is None or e.level == level)
            and (code is None or e.code == code)
            and (since is None or e.ts >= since)
        ]
        return out[:limit]

    def clear(self) -> None:
        self._events.clear()
        self._ram_cycles = {"started": 0, "completed": 0, "failed": 0, "aborted": 0}
        if self._db:
            try:
                with self._lock:
                    self._db.execute("DELETE FROM events")
                    self._db.execute("DELETE FROM cycles")
                    self._db.commit()
            except sqlite3.Error:
                logger.exception("EventLog: DB-Clear fehlgeschlagen")

    # -------- Zyklen (gefüttert vom CycleTracker in stats.py) --------

    def cycle_start(self) -> int | None:
        """Neuer Stopfzyklus. Rückgabe: DB-Zeilen-ID (None ohne DB)."""
        self._ram_cycles["started"] += 1
        if self._db:
            try:
                with self._lock:
                    cur = self._db.execute(
                        "INSERT INTO cycles (started_ts) VALUES (?)", (time.time(),))
                    self._db.commit()
                    return cur.lastrowid
            except sqlite3.Error:
                logger.exception("EventLog: cycle_start fehlgeschlagen")
        return None

    def cycle_end(self, cycle_id: int | None, ok: bool,
                  fail_code: str | None = None, fail_step: int | None = None) -> None:
        if ok:
            self._ram_cycles["completed"] += 1
        elif fail_code in _ABORT_CODES:
            self._ram_cycles["aborted"] += 1
        else:
            self._ram_cycles["failed"] += 1
        if self._db and cycle_id is not None:
            try:
                with self._lock:
                    self._db.execute(
                        "UPDATE cycles SET ended_ts=?, ok=?, fail_code=?, fail_step=? WHERE id=?",
                        (time.time(), 1 if ok else 0, fail_code, fail_step, cycle_id),
                    )
                    self._db.commit()
            except sqlite3.Error:
                logger.exception("EventLog: cycle_end fehlgeschlagen")

    # -------- Statistik --------

    def stats(self) -> dict:
        """Aggregation für GET /stats — aus DB (gesamte Historie) oder RAM."""
        if self._db:
            try:
                with self._lock:
                    cyc = self._db.execute(
                        "SELECT COUNT(*),"
                        " SUM(CASE WHEN ok=1 THEN 1 ELSE 0 END),"
                        " SUM(CASE WHEN ok=0 AND (fail_code IS NULL OR fail_code NOT IN (?,?)) THEN 1 ELSE 0 END),"
                        " SUM(CASE WHEN ok=0 AND fail_code IN (?,?) THEN 1 ELSE 0 END)"
                        " FROM cycles", (*_ABORT_CODES, *_ABORT_CODES),
                    ).fetchone()
                    by_code = dict(self._db.execute(
                        "SELECT code, COUNT(*) FROM events "
                        "WHERE level='error' AND code IS NOT NULL GROUP BY code").fetchall())
                    by_step = {str(k): v for k, v in self._db.execute(
                        "SELECT step, COUNT(*) FROM events "
                        "WHERE level='error' AND step IS NOT NULL GROUP BY step").fetchall()}
                    span = self._db.execute("SELECT MIN(ts), MAX(ts) FROM events").fetchone()
                started, completed, failed, aborted = (cyc[0] or 0, cyc[1] or 0,
                                                       cyc[2] or 0, cyc[3] or 0)
                first_ts, last_ts = span
            except sqlite3.Error:
                logger.exception("EventLog: stats-Query fehlgeschlagen — RAM-Fallback")
                return self._ram_stats()
        else:
            return self._ram_stats()
        return self._build_stats(started, completed, failed, aborted,
                                 by_code, by_step, first_ts, last_ts)

    def _ram_stats(self) -> dict:
        by_code: dict[str, int] = {}
        by_step: dict[str, int] = {}
        for e in self._events:
            if e.level != "error":
                continue
            if e.code:
                by_code[e.code] = by_code.get(e.code, 0) + 1
            if e.step is not None:
                by_step[str(e.step)] = by_step.get(str(e.step), 0) + 1
        c = self._ram_cycles
        first_ts = self._events[0].ts if self._events else None
        last_ts = self._events[-1].ts if self._events else None
        return self._build_stats(c["started"], c["completed"], c["failed"],
                                 c["aborted"], by_code, by_step, first_ts, last_ts)

    def _build_stats(self, started, completed, failed, aborted,
                     by_code, by_step, first_ts, last_ts) -> dict:
        ended = completed + failed   # Abbrüche zählen nicht in die Quote
        return {
            "persisted": self.persisted,
            "cycles": {
                "started": started,
                "completed": completed,
                "failed": failed,
                "aborted": aborted,
                "success_rate": round(completed / ended, 4) if ended > 0 else None,
            },
            "errors_by_code": by_code,
            "errors_by_step": by_step,
            "first_event_ts": first_ts,
            "last_event_ts": last_ts,
        }


event_log = EventLog()
