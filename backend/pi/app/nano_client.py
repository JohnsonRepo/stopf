"""
nano_client.py
Asynchrone Serial-Kommunikation mit dem Arduino Nano.

Eine Befehlsausführung ist hier streng seriell: send() schickt
einen Befehl, wartet auf eine Antwortzeile und gibt sie zurück.
Damit bleibt das Protokoll einfach und deterministisch.
"""

import asyncio
import logging
from typing import Optional

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class NanoClient:
    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 115200, timeout: float = 2.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Öffnet die Serial-Verbindung. Auto-Detect, wenn der angegebene Port fehlt."""
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            logger.info(f"Connected to Nano on {self.port}")
        except serial.SerialException:
            # Versuche Auto-Detect
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if "Arduino" in (p.description or "") or "ttyACM" in p.device or "ttyUSB" in p.device:
                    try:
                        self._ser = serial.Serial(p.device, self.baud, timeout=self.timeout)
                        self.port = p.device
                        logger.info(f"Auto-detected Nano on {self.port}")
                        break
                    except serial.SerialException:
                        continue
            if self._ser is None:
                logger.error("No Arduino Nano found on any serial port.")
                return

        # Nano resettet beim Verbinden → kurz warten und Begrüßung leeren
        await asyncio.sleep(2.0)
        self._ser.reset_input_buffer()

    async def disconnect(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()
            logger.info("Serial connection closed")

    async def send(self, command: str) -> str:
        """Sendet einen Befehl und liefert die erste Antwortzeile zurück."""
        if self._ser is None or not self._ser.is_open:
            return "err not_connected"

        async with self._lock:
            loop = asyncio.get_event_loop()
            try:
                payload = (command.strip() + "\n").encode("utf-8")
                await loop.run_in_executor(None, self._ser.write, payload)
                # Antwortzeile lesen (blockierend, daher in Executor)
                raw = await loop.run_in_executor(None, self._ser.readline)
                reply = raw.decode("utf-8", errors="replace").strip()
                logger.debug(f">> {command}  <<  {reply}")
                return reply or "err no_reply"
            except serial.SerialException as e:
                logger.exception("Serial error")
                return f"err serial:{e}"
