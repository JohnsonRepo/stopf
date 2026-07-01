"""
Stopfmaschine - Pi Backend (FastAPI v0.3.0)

Spiegelt die Nano-Firmware v0.3.0 als REST + WebSocket. iOS-App spricht nur
mit dem Pi, nicht direkt mit dem Nano.

Endpoints:
    GET  /                          health
    GET  /status                    parsed MachineStatus
    GET  /params                    alle EEPROM-Parameter
    PUT  /params                    batch-update (nur gesetzte Felder)
    PUT  /params/{key}              einzelner Wert
    POST /sequence/home             Referenzfahrt
    POST /sequence/stuff            Vollsequenz
    POST /sequence/step             {"n": 1..9}
    POST /sequence/stop             Notaus
    POST /manual/stepper            {"steps": N}
    POST /manual/press              {"direction":"fwd|rev|stop"}
    POST /manual/pusher             {"direction":"fwd|rev|stop"}
    POST /manual/servo              {"angle": 0..180}
    POST /manual/solenoid/{1|2}     {"action":"off|pulse","ms":?}  (Dauer-ON deaktiviert)
    POST /manual/hopper             {"action":"on|off|test","ms":?}
    POST /manual/knock              {"cycles": ?}
    POST /system/shutdown           Pi sicher herunterfahren (stop + poweroff)
    POST /system/reboot             Pi neu starten (stop + reboot)
    POST /system/update             git pull + Abhängigkeiten + Dienst-Neustart
    POST /system/flash-nano         Nano-Firmware (firmware.hex) via avrdude flashen
    WS   /ws/status                 5 Hz Push (200 ms)

Start:
    cd backend/pi
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import asyncio
import logging
import os
import socket
import subprocess
import time
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Path, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .broadcaster import StatusBroadcaster
from .nano_client import NanoClient
from .schemas import (
    CommandResponse,
    HopperRequest,
    KnockRequest,
    MachineStatus,
    MotorRequest,
    Params,
    ServoRequest,
    SolenoidRequest,
    StepRequest,
    StepperRequest,
)
from .status_parser import parse

logger = logging.getLogger("uvicorn.error")

SERIAL_PORT = os.environ.get("STOPF_SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUD = int(os.environ.get("STOPF_SERIAL_BAUD", "115200"))

nano = NanoClient(port=SERIAL_PORT, baud=SERIAL_BAUD)
broadcaster = StatusBroadcaster(nano, interval_ms=200)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await nano.connect()
    await broadcaster.start()
    try:
        yield
    finally:
        await broadcaster.stop()
        await nano.disconnect()


app = FastAPI(
    title="Stopfmaschine API",
    description="Steuerung der Zigarettenstopfmaschine — gespiegelt zu Nano-Firmware v0.3.0",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS für iOS-Sim, lokale Tools, ggf. zukünftige PWA. Lokales Netz only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Helpers --------

async def _send_cmd(cmd: str) -> CommandResponse:
    reply = await nano.send(cmd)
    parsed = parse(reply)
    ok = parsed.get("_kind") in ("ok", "status", "pong", "ready")
    return CommandResponse(sent=cmd, reply=reply, ok=ok, parsed=parsed)


# -------- Internet-Erreichbarkeit (für App-Update-Gating) --------

_internet_cache = {"ok": False, "ts": 0.0}
_INTERNET_TTL = 20.0   # Sekunden — Ergebnis kurz cachen, Probe ist teuer


def _probe_internet() -> bool:
    """Blockierend: TCP zu github.com:443 (genau das, was git pull braucht)."""
    try:
        with socket.create_connection(("github.com", 443), timeout=2):
            return True
    except OSError:
        return False


async def _internet_ok() -> bool:
    now = time.time()
    if now - _internet_cache["ts"] < _INTERNET_TTL:
        return _internet_cache["ok"]
    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, _probe_internet)   # Event-Loop nicht blocken
    _internet_cache["ok"] = ok
    _internet_cache["ts"] = now
    return ok


# -------- Health + Status --------

@app.get("/", summary="Health check")
async def root():
    return {
        "service": "stopfmaschine",
        "version": app.version,
        "nano_connected": nano.is_connected,
        "nano_port": nano.port,
        "internet": await _internet_ok(),
    }


@app.get("/status", response_model=MachineStatus, summary="Parsed Maschinenstatus")
async def status():
    return await nano.get_status()


# -------- Parameter --------

@app.get("/params", summary="Alle EEPROM-Parameter")
async def get_params():
    return await nano.get_params()


@app.put("/params", response_model=CommandResponse, summary="Mehrere Parameter setzen (Batch)")
async def put_params(params: Params):
    payload = params.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(400, "no fields to update")
    results = []
    last_reply = ""
    all_ok = True
    for k, v in payload.items():
        ok, reply = await nano.set_param(k, v)
        results.append({"key": k, "value": v, "ok": ok, "reply": reply})
        last_reply = reply
        if not ok:
            all_ok = False
    return CommandResponse(
        sent=f"batch ({len(payload)} keys)",
        reply=last_reply,
        ok=all_ok,
        parsed={"results": results},
    )


@app.put("/params/{key}", response_model=CommandResponse, summary="Einzelnen Parameter setzen")
async def put_param(key: str, value: int):
    ok, reply = await nano.set_param(key, value)
    return CommandResponse(sent=f"set {key} {value}", reply=reply, ok=ok, parsed=parse(reply))


# -------- Sequence --------

@app.post("/sequence/home", response_model=CommandResponse)
async def seq_home():
    return await _send_cmd("home")


@app.post("/sequence/stuff", response_model=CommandResponse)
async def seq_stuff():
    return await _send_cmd("stuff")


@app.post("/sequence/step", response_model=CommandResponse)
async def seq_step(req: StepRequest):
    return await _send_cmd(f"step {req.n}")


@app.post("/sequence/stop", response_model=CommandResponse, summary="Notaus")
async def seq_stop():
    return await _send_cmd("stop")


# -------- Manual --------

@app.post("/manual/stepper", response_model=CommandResponse)
async def m_stepper(req: StepperRequest):
    return await _send_cmd(f"stepper {req.steps}")


@app.post("/manual/press", response_model=CommandResponse)
async def m_press(req: MotorRequest):
    return await _send_cmd(f"press {req.direction}")


@app.post("/manual/pusher", response_model=CommandResponse)
async def m_pusher(req: MotorRequest):
    return await _send_cmd(f"pusher {req.direction}")


@app.post("/manual/servo", response_model=CommandResponse)
async def m_servo(req: ServoRequest):
    return await _send_cmd(f"servo {req.angle}")


@app.post("/manual/solenoid/{which}", response_model=CommandResponse)
async def m_solenoid(req: SolenoidRequest, which: int = Path(..., ge=1, le=2)):
    if req.action == "pulse":
        if req.ms is None:
            raise HTTPException(400, "pulse requires ms")
        return await _send_cmd(f"solenoid {which} pulse {req.ms}")
    return await _send_cmd(f"solenoid {which} {req.action}")


@app.post("/manual/hopper", response_model=CommandResponse)
async def m_hopper(req: HopperRequest):
    if req.action == "test":
        if req.ms is None:
            raise HTTPException(400, "test requires ms")
        return await _send_cmd(f"hopper test {req.ms}")
    return await _send_cmd(f"hopper {req.action}")


@app.post("/manual/knock", response_model=CommandResponse)
async def m_knock(req: KnockRequest):
    if req.cycles is None:
        return await _send_cmd("knock")
    return await _send_cmd(f"knock {req.cycles}")


# -------- System (Power) --------

def _power_action(action: str) -> None:
    """Läuft als BackgroundTask, NACHDEM die HTTP-Antwort raus ist.
    Kurze Verzögerung, damit App/WS die Antwort sicher erhalten."""
    time.sleep(1.0)
    try:
        # -n = non-interaktiv: scheitert sofort statt auf ein Passwort zu warten.
        subprocess.run(["sudo", "-n", action], check=True)
    except Exception:  # noqa: BLE001
        logger.exception("Power-Aktion '%s' fehlgeschlagen", action)


async def _power(action: str, background_tasks: BackgroundTasks) -> CommandResponse:
    # Maschine zuerst sicher stoppen — der Nano läuft sonst nach dem Pi-Aus weiter.
    stop_reply = await nano.send("stop")
    background_tasks.add_task(_power_action, action)
    return CommandResponse(
        sent=action,
        reply=f"machine stopped ({stop_reply}); {action} in 1s",
        ok=True,
        parsed={"_kind": "system", "action": action},
    )


@app.post("/system/shutdown", response_model=CommandResponse, summary="Pi herunterfahren")
async def system_shutdown(background_tasks: BackgroundTasks):
    return await _power("poweroff", background_tasks)


@app.post("/system/reboot", response_model=CommandResponse, summary="Pi neu starten")
async def system_reboot(background_tasks: BackgroundTasks):
    return await _power("reboot", background_tasks)


# -------- System (Update) --------

_PI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # backend/pi
_REPO_ROOT = os.path.dirname(os.path.dirname(_PI_DIR))                  # Repo-Wurzel
_UPDATE_SH = os.path.join(_PI_DIR, "scripts", "update.sh")


def _run_update() -> None:
    """BackgroundTask: git pull + pip + Dienst-Neustart via update.sh.
    Der Neustart killt am Ende auch diesen Prozess — git pull/pip sind bis
    dahin fertig, und systemd führt den Restart-Job selbst zu Ende."""
    time.sleep(1.0)
    try:
        subprocess.run(["bash", _UPDATE_SH], check=False)
    except Exception:  # noqa: BLE001
        logger.exception("Update fehlgeschlagen")


_NANO_HEX = os.path.join(_REPO_ROOT, "firmware", "nano", "firmware.hex")


@app.post("/system/flash-nano", response_model=CommandResponse, summary="Nano-Firmware flashen")
async def system_flash_nano():
    # Flasht den ins Repo eingecheckten Hex. Läuft im separaten Dienst
    # stopf-flash (eigene cgroup) → avrdude überlebt den Backend-Stop.
    if not os.path.isfile(_NANO_HEX):
        raise HTTPException(400, "kein firmware.hex im Repo — erst bauen/committen + git pull")
    try:
        subprocess.run(
            ["sudo", "-n", "systemctl", "start", "--no-block", "stopf-flash.service"],
            check=True,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Flash-Dienst-Start fehlgeschlagen: {e}")
    return CommandResponse(
        sent="flash-nano",
        reply="Flashen gestartet — Backend pausiert ~20-40 s, dann wieder verbunden",
        ok=True,
        parsed={"_kind": "system", "action": "flash-nano"},
    )


@app.post("/system/update", response_model=CommandResponse, summary="Backend aktualisieren (git pull + Neustart)")
async def system_update(background_tasks: BackgroundTasks):
    # Nur bei Git-Deployment möglich (update.sh macht git pull).
    if not os.path.isdir(os.path.join(_REPO_ROOT, ".git")):
        raise HTTPException(400, "kein Git-Deployment — Update nur bei 'git clone' möglich")
    # Braucht Internet — im AP-Modus schlägt git pull fehl (dann bleibt alter Stand).
    if not await _internet_ok():
        raise HTTPException(400, "keine Internetverbindung — Update nur im Client-Modus")
    background_tasks.add_task(_run_update)
    return CommandResponse(
        sent="update",
        reply="Update gestartet — git pull + Neustart, in ~30-60 s wieder verbunden",
        ok=True,
        parsed={"_kind": "system", "action": "update"},
    )


# -------- WebSocket --------

@app.websocket("/ws/status")
async def ws_status(ws: WebSocket):
    await broadcaster.attach(ws)
    try:
        # Keep alive — wir empfangen nichts vom Client, broadcaster pusht.
        while True:
            # Optional: Client kann "ping" schicken, wir antworten "pong"
            msg = await ws.receive_text()
            if msg.strip().lower() == "ping":
                await ws.send_json({"_kind": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.detach(ws)
