"""
broadcaster.py
Pollt den Nano-Status in einem Background-Task und schickt das JSON
an alle verbundenen WebSocket-Clients.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Set

from fastapi import WebSocket

from .event_log import event_log
from .nano_client import NanoClient
from .stats import CycleTracker

logger = logging.getLogger(__name__)


class StatusBroadcaster:
    def __init__(self, nano: NanoClient, interval_ms: int = 200):
        self._nano = nano
        self._interval = interval_ms / 1000.0
        self._clients: Set[WebSocket] = set()
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._last = None   # vorheriger MachineStatus für Übergangs-Erkennung
        self.tracker = CycleTracker(event_log)   # Stopfzyklen für GET /stats

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except asyncio.TimeoutError:
                self._task.cancel()
        self._task = None

    async def attach(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def detach(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def _run(self) -> None:
        # Wenn keine Clients verbunden sind, langsamer pollen (1 Hz) — sonst
        # belasten wir die Serial-Leitung sinnlos.
        idle_interval = max(self._interval, 1.0)
        while not self._stop.is_set():
            interval = self._interval if self._clients else idle_interval
            try:
                status = await self._nano.get_status()
                self._note_transitions(status)
                self.tracker.tick(status)
                payload = status.model_dump()
                if self._clients:
                    dead = []
                    for ws in list(self._clients):
                        try:
                            await ws.send_json(payload)
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        self._clients.discard(ws)
            except Exception:
                logger.exception("broadcaster tick failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    def _note_transitions(self, s) -> None:
        """Erkennt relevante Übergänge und schreibt sie ins Ereignis-Protokoll."""
        last = self._last
        self._last = s
        if last is None:
            return
        # Nano-Verbindung
        if s.connected != last.connected:
            if s.connected:
                event_log.info("Nano wieder verbunden",
                               code="nano_reconnected", source="nano")
            else:
                event_log.warn("Nano-Verbindung verloren",
                               code="nano_disconnected", source="nano")
        # Zustandswechsel (inkl. Fehler + möglicher Reset)
        if s.state != last.state:
            if s.state == "error":
                # Sensor-Snapshot im Fehlermoment mitloggen — beantwortet
                # "Sensor klemmt vs. Motor dreht nicht" ohne Nachstellen.
                # Ab Firmware v0.6.0 liefert der Nano den Snapshot selbst
                # (err_*-Felder, eingefroren in setError) — exakter als das
                # 200-ms-Polling. Fallback: aktueller Poll-Status.
                if s.err_step is not None:
                    step = s.err_step
                    details = {
                        "press": s.err_press,
                        "push_front": s.err_pf,
                        "push_rear": s.err_pr,
                        "magazin": s.err_mag,
                        "t_ms": s.err_t,
                        "cut": s.cut,
                        "stepper_pos": s.stepper_pos,
                        "prev_state": last.state,
                        "snapshot": "firmware",
                    }
                else:
                    step = last.step
                    details = {
                        "press": s.press,
                        "push_front": s.push_front,
                        "push_rear": s.push_rear,
                        "magazin": s.magazin,
                        "cut": s.cut,
                        "stepper_pos": s.stepper_pos,
                        "prev_state": last.state,
                        "snapshot": "poll",
                    }
                event_log.error(
                    f"Fehler: {s.error or '?'} (bei Schritt {step})",
                    code=s.error or "unknown",
                    source="nano",
                    step=step,
                    details=details,
                )
            elif last.state in ("stuffing", "homing", "step") and s.state == "idle":
                # Sequenz endete/abgebrochen — bei laufender Sequenz oft ein Nano-Reset
                event_log.warn(
                    f"Ablauf beendet/abgebrochen (war {last.state}, Schritt {last.step})",
                    code="sequence_aborted", source="nano", step=last.step,
                )
            else:
                event_log.info(f"Zustand: {last.state} → {s.state}",
                               code="state_change", source="nano")
