"""
stats.py
Zyklus-Tracking für die Fehlversuchs-Analyse.

Der CycleTracker wird vom StatusBroadcaster pro Status-Tick gefüttert und
leitet daraus Stopfzyklen ab: Zyklus-Wrap = sinkende Step-Nummer im Zustand
"stuffing" (die Firmware läuft 1→12 und springt zurück auf 1).

Näherung, keine exakte Zählung: Basis ist das 200-ms-(bzw. 1-Hz-)Polling des
Broadcasters. Ein Zyklus dauert ≥ 5 s, damit ist der Wrap zuverlässig sichtbar
— exakter wäre ein Zähler in der Firmware (bewusst vertagt, kein Reflash).
Die Aggregation (GET /stats) liegt in EventLog.stats().
"""
from __future__ import annotations

from .event_log import EventLog


class CycleTracker:
    def __init__(self, log: EventLog):
        self._log = log
        self._cycle_id: int | None = None
        self._in_cycle = False
        self._last_state = "idle"
        self._last_step = 0

    def tick(self, s) -> None:
        """s: MachineStatus vom Broadcaster-Polling."""
        state, step = s.state, s.step
        try:
            if state == "stuffing":
                if self._last_state != "stuffing":
                    self._begin()
                elif step < self._last_step:
                    # Wrap 12→1: Zigarette fertig, nächster Zyklus beginnt
                    self._end(ok=True)
                    self._begin()
            elif self._in_cycle:
                if state == "error":
                    self._end(ok=False, fail_code=s.error or "unknown",
                              fail_step=self._last_step)
                else:
                    # stuffing → idle: `stop` vom User oder Nano-Reset
                    self._end(ok=False, fail_code="aborted",
                              fail_step=self._last_step)
        finally:
            self._last_state = state
            self._last_step = step

    def _begin(self) -> None:
        self._cycle_id = self._log.cycle_start()
        self._in_cycle = True

    def _end(self, ok: bool, fail_code: str | None = None,
             fail_step: int | None = None) -> None:
        self._log.cycle_end(self._cycle_id, ok=ok,
                            fail_code=fail_code, fail_step=fail_step)
        self._cycle_id = None
        self._in_cycle = False
