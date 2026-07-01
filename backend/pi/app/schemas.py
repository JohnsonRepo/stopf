"""
schemas.py
Pydantic-Modelle, gespiegelt zur Nano-Firmware v0.3.0.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


# -------- Maschinen-Status (gespiegelt aus Nano `status`) --------

MachineState = Literal["idle", "homing", "stuffing", "step", "error"]


class MachineStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    connected: bool = True
    state: MachineState = "idle"
    step: int = 0
    error: Optional[str] = None
    press: bool = False
    push_front: bool = False
    push_rear: bool = False
    magazin: bool = False
    sol1: bool = False
    sol2: bool = False
    hopper: bool = False
    hopper_enabled: bool = False
    stepper_pos: int = 0


# -------- Parameter (gespiegelt aus Nano params.h) --------

class Params(BaseModel):
    """Alle Felder optional → für PATCH-artige Updates."""
    model_config = ConfigDict(extra="forbid")

    drum_steps_per_pos:    Optional[int] = Field(None, ge=1,   le=10000)
    home_drum_timeout_ms:  Optional[int] = Field(None, ge=100, le=60000)
    servo_home:            Optional[int] = Field(None, ge=0,   le=180)
    servo_load:            Optional[int] = Field(None, ge=0,   le=180)
    knock_on_ms:           Optional[int] = Field(None, ge=1,   le=1000)
    knock_off_ms:          Optional[int] = Field(None, ge=1,   le=2000)
    knock_cycles:          Optional[int] = Field(None, ge=1,   le=50)
    hopper_on_ms:          Optional[int] = Field(None, ge=100, le=60000)
    hopper_off_ms:         Optional[int] = Field(None, ge=100, le=60000)
    press_rev_ms:          Optional[int] = Field(None, ge=50,  le=10000)
    press_fwd_timeout_ms:  Optional[int] = Field(None, ge=100, le=10000)
    press_pwm:             Optional[int] = Field(None, ge=60,  le=255)
    pusher_fwd_timeout_ms: Optional[int] = Field(None, ge=100, le=10000)
    pusher_rev_timeout_ms: Optional[int] = Field(None, ge=100, le=10000)
    pusher_pwm:            Optional[int] = Field(None, ge=60,  le=255)
    sol1_dwell_ms:         Optional[int] = Field(None, ge=1,   le=1000)
    sol2_dwell_ms:         Optional[int] = Field(None, ge=1,   le=1000)
    step_delay_ms:         Optional[int] = Field(None, ge=0,   le=10000)


# Liste der gültigen Param-Namen (aus dem Modell extrahiert)
PARAM_KEYS = frozenset(Params.model_fields.keys())


# -------- Command-Responses --------

class CommandResponse(BaseModel):
    sent: str
    reply: str
    ok: bool
    parsed: dict | None = None


# -------- Manual-Requests --------

class StepperRequest(BaseModel):
    steps: int = Field(..., ge=-100000, le=100000)


class ServoRequest(BaseModel):
    angle: int = Field(..., ge=0, le=180)


class MotorRequest(BaseModel):
    direction: Literal["fwd", "rev", "stop"]


class SolenoidRequest(BaseModel):
    # Dauer-ON ist deaktiviert (Magnet-Schutz) — nur off/pulse.
    action: Literal["off", "pulse"]
    ms: Optional[int] = Field(None, ge=1, le=1000)


class HopperRequest(BaseModel):
    action: Literal["on", "off", "test"]
    ms: Optional[int] = Field(None, ge=1, le=4000)


class KnockRequest(BaseModel):
    cycles: Optional[int] = Field(None, ge=1, le=50)


class StepRequest(BaseModel):
    n: int = Field(..., ge=1, le=9)
