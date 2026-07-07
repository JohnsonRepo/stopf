"""
stats.py
Zyklus-Tracking für die Fehlversuchs-Analyse.

Der CycleTracker wird vom StatusBroadcaster pro Status-Tick gefüttert und
leitet daraus Stopfzyklen ab.

Zwei Quellen, je nach Firmware:
- ab v0.6.0 meldet der Nano `cnt` (fertige Zyklen seit Boot) — exakt, kein
  Polling-Verlust möglich; wir zählen die Delta-Schritte.
- ältere Firmware (cnt=None): Fallback auf den Wrap-Heuristik — sinkende
  Step-Nummer im Zustand "stuffing" (Firmware läuft 1→12 und springt auf 1).

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
        self._last_cnt: int | None = None

    def tick(self, s) -> None:
        """s: MachineStatus vom Broadcaster-Polling."""
        state, step = s.state, s.step
        cnt = s.cnt   # None bei Firmware < v0.6.0
        try:
            if state == "stuffing":
                if self._last_state != "stuffing":
                    self._begin()
                elif cnt is not None and self._last_cnt is not None and cnt != self._last_cnt:
                    # Exakter Firmware-Zähler: jede Delta-Einheit = 1 fertige
                    # Zigarette (fängt auch mehrere Wraps zwischen zwei Polls
                    # und den uint16-Überlauf via Modulo ab).
                    done = (cnt - self._last_cnt) % 65536
                    for _ in range(done):
                        self._end(ok=True)
                        self._begin()
                elif cnt is None and step < self._last_step:
                    # Fallback alte Firmware — Wrap 12→1 am sinkenden Step
                    self._end(ok=True)
                    self._begin()
            elif self._in_cycle:
                if state == "error":
                    fail_step = s.err_step if s.err_step is not None else self._last_step
                    self._end(ok=False, fail_code=s.error or "unknown",
                              fail_step=fail_step)
                else:
                    # stuffing → idle: `stop` vom User oder Nano-Reset
                    self._end(ok=False, fail_code="aborted",
                              fail_step=self._last_step)
        finally:
            self._last_state = state
            self._last_step = step
            self._last_cnt = cnt

    def _begin(self) -> None:
        self._cycle_id = self._log.cycle_start()
        self._in_cycle = True

    def _end(self, ok: bool, fail_code: str | None = None,
             fail_step: int | None = None) -> None:
        self._log.cycle_end(self._cycle_id, ok=ok,
                            fail_code=fail_code, fail_step=fail_step)
        self._cycle_id = None
        self._in_cycle = False
