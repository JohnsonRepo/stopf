"""
Stopfmaschine - Pi Backend (FastAPI Starter v0.1)

Spricht mit dem Arduino Nano über USB-Serial und stellt eine
einfache HTTP-API bereit, mit der du jede Aktion vom Browser oder
der späteren App auslösen kannst.

Lauf-Anleitung:
    cd backend/pi
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Swagger-UI: http://<pi-ip>:8000/docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .nano_client import NanoClient


# --- Konfiguration ---
SERIAL_PORT = "/dev/ttyACM0"   # ggf. ttyUSB0 je nach Nano-Variante
SERIAL_BAUD = 115200

nano = NanoClient(port=SERIAL_PORT, baud=SERIAL_BAUD)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verbindung zum Nano beim Start aufbauen, beim Stop schließen."""
    await nano.connect()
    yield
    await nano.disconnect()


app = FastAPI(
    title="Stopfmaschine API",
    description="Steuerung der Zigarettenstopfmaschine über den Pi",
    version="0.1.0",
    lifespan=lifespan,
)


# ----- Schemas -----

class CommandResponse(BaseModel):
    sent: str
    reply: str


class StepperRequest(BaseModel):
    steps: int = Field(..., description="Schrittanzahl, negativ = rückwärts")


class ServoRequest(BaseModel):
    angle: int = Field(..., ge=0, le=180)


class MotorRequest(BaseModel):
    direction: str = Field(..., pattern="^(fwd|rev|stop)$")


# ----- Routes -----

@app.get("/", summary="Health check")
async def root():
    return {"status": "ok", "version": app.version}


@app.get("/ping", response_model=CommandResponse, summary="Test der Nano-Verbindung")
async def ping():
    reply = await nano.send("ping")
    return CommandResponse(sent="ping", reply=reply)


@app.get("/status", summary="Sensoren-Status auslesen")
async def status():
    reply = await nano.send("status")
    return {"raw": reply}


@app.post("/stepper", response_model=CommandResponse, summary="Schrittmotor bewegen")
async def stepper(req: StepperRequest):
    cmd = f"stepper {req.steps}"
    reply = await nano.send(cmd)
    return CommandResponse(sent=cmd, reply=reply)


@app.post("/servo", response_model=CommandResponse, summary="Servo auf Winkel fahren")
async def servo(req: ServoRequest):
    cmd = f"servo {req.angle}"
    reply = await nano.send(cmd)
    return CommandResponse(sent=cmd, reply=reply)


@app.post("/press", response_model=CommandResponse, summary="Presse-Motor")
async def press(req: MotorRequest):
    cmd = f"press {req.direction}"
    reply = await nano.send(cmd)
    return CommandResponse(sent=cmd, reply=reply)


@app.post("/pusher", response_model=CommandResponse, summary="Pusher-Motor")
async def pusher(req: MotorRequest):
    cmd = f"pusher {req.direction}"
    reply = await nano.send(cmd)
    return CommandResponse(sent=cmd, reply=reply)


@app.post("/stop", response_model=CommandResponse, summary="Notaus, alle Motoren stoppen")
async def stop():
    reply = await nano.send("stop")
    return CommandResponse(sent="stop", reply=reply)
