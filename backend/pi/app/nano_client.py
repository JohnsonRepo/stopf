"""
nano_client.py
Asynchroner Serial-Client für den Arduino Nano (Firmware v0.3.0).

Eigenschaften:
- Eine Befehlsausführung ist streng seriell (asyncio.Lock).
- Auto-Reconnect: ist der Port weg, versucht jeder send() einen
  einmaligen Reconnect, bevor er aufgibt.
- Strukturierte Helper für status/params/get/set.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import serial
import serial.tools.list_ports

from .status_parser import parse
from .schemas import MachineStatus

logger = logging.getLogger(__name__)


class NanoClient:
    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()

    # -------- Connection --------

    async def connect(self) -> bool:
        if await self._open(self.port):
            return True
        # Auto-Detect
        for p in serial.tools.list_ports.comports():
            desc = (p.description or "").lower()
            if any(s in p.device for s in ("ttyACM", "ttyUSB")) or "arduino" in desc or "ch340" in desc:
                if await self._open(p.device):
                    self.port = p.device
                    return True
        logger.error("No Arduino Nano found.")
        return False

    async def _open(self, port: str) -> bool:
        try:
            self._ser = serial.Serial(port, self.baud, timeout=self.timeout)
            logger.info(f"Connected to Nano on {port}")
        except (serial.SerialException, OSError):
            self._ser = None
            return False
        # Nano resettet beim Verbinden — kurz warten + Begrüßung leeren
        await asyncio.sleep(2.0)
        try:
            self._ser.reset_input_buffer()
        except (serial.SerialException, OSError):
            pass
        return True

    async def disconnect(self) -> None:
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            finally:
                logger.info("Serial connection closed")

    @property
    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # -------- Raw send --------

    async def send(self, command: str) -> str:
        """Sendet einen Befehl, liefert die erste Antwortzeile."""
        async with self._lock:
            if not self.is_connected:
                if not await self.connect():
                    return "err not_connected"

            loop = asyncio.get_event_loop()
            try:
                payload = (command.strip() + "\n").encode("utf-8")
                # Stale/unsolicited Zeilen verwerfen, damit die gelesene Antwort
                # garantiert zu DIESEM Befehl gehört. Ohne das kann ein einmal in
                # den Timeout gelaufener readline die Zuordnung Befehl↔Antwort um
                # eins verschieben (Desync mit dem 200-ms-Broadcaster) — dann
                # bekam z.B. `params` eine `status`-Zeile → leere Parameter.
                await loop.run_in_executor(None, self._ser.reset_input_buffer)
                await loop.run_in_executor(None, self._ser.write, payload)
                raw = await loop.run_in_executor(None, self._ser.readline)
                reply = raw.decode("utf-8", errors="replace").strip()
                logger.debug(f">> {command}  <<  {reply}")
                return reply or "err no_reply"
            except (serial.SerialException, OSError) as e:
                logger.warning(f"Serial error, dropping connection: {e}")
                try:
                    if self._ser:
                        self._ser.close()
                finally:
                    self._ser = None
                return f"err serial:{e}"

    # -------- Structured helpers --------

    async def get_status(self) -> MachineStatus:
        reply = await self.send("status")
        if reply.startswith("err"):
            return MachineStatus(connected=False, state="error", error=reply)
        parsed = parse(reply)
        if parsed.get("_kind") != "status":
            return MachineStatus(connected=True, state="error",
                                 error=f"bad_status:{reply}")
        # _kind aus dict werfen, MachineStatus akzeptiert den Rest
        parsed.pop("_kind", None)
        # error="" → None
        if parsed.get("error") in ("", None):
            parsed["error"] = None
        try:
            return MachineStatus(connected=True, **parsed)
        except Exception as e:
            logger.exception("status parse failed")
            return MachineStatus(connected=True, state="error", error=f"parse:{e}")

    async def get_params(self) -> dict[str, int]:
        reply = await self.send("params")
        parsed = parse(reply)
        if parsed.get("_kind") != "ok":
            return {}
        parsed.pop("_kind", None)
        parsed.pop("sub", None)
        return {k: int(v) for k, v in parsed.items() if isinstance(v, int)}

    async def set_param(self, key: str, value: int) -> tuple[bool, str]:
        reply = await self.send(f"set {key} {value}")
        parsed = parse(reply)
        if parsed.get("_kind") == "ok":
            return True, reply
        return False, reply
