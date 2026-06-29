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

from .nano_client import NanoClient

logger = logging.getLogger(__name__)


class StatusBroadcaster:
    def __init__(self, nano: NanoClient, interval_ms: int = 200):
        self._nano = nano
        self._interval = interval_ms / 1000.0
        self._clients: Set[WebSocket] = set()
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

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
