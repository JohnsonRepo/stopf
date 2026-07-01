"""
event_log.py
Leichtgewichtiger In-Memory-Ringpuffer für Ereignisse (Zustandswechsel,
Fehler, Nano-Verbindungsabbrüche, System-Aktionen).

Zweck: Fehler im Nachhinein nachvollziehen, ohne SSH/journalctl. Abrufbar per
GET /events, sichtbar in der App.

Grenzen: In-Memory → überlebt einen Backend-Neustart NICHT. Für dauerhafte
Historie zusätzlich journalctl (die wichtigen Events gehen auch dorthin).
Bewusst kein File-Log, damit es mit Overlay-FS (read-only SD) kompatibel bleibt.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import asdict, dataclass

logger = logging.getLogger("uvicorn.error")


@dataclass
class Event:
    ts: float      # Unix-Zeit (Sekunden)
    level: str     # "info" | "warn" | "error"
    message: str


class EventLog:
    def __init__(self, maxlen: int = 200):
        self._events: deque[Event] = deque(maxlen=maxlen)

    def add(self, level: str, message: str) -> None:
        self._events.append(Event(ts=time.time(), level=level, message=message))
        # Wichtige Events zusätzlich ins journald (überlebt Neustart).
        if level == "error":
            logger.error("EVENT %s", message)
        elif level == "warn":
            logger.warning("EVENT %s", message)
        else:
            logger.info("EVENT %s", message)

    def info(self, m: str) -> None:  self.add("info", m)
    def warn(self, m: str) -> None:  self.add("warn", m)
    def error(self, m: str) -> None: self.add("error", m)

    def list(self) -> list[dict]:
        """Neueste zuerst."""
        return [asdict(e) for e in reversed(self._events)]

    def clear(self) -> None:
        self._events.clear()


event_log = EventLog()
