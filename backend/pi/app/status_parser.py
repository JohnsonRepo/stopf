"""
status_parser.py
Zerlegt Nano-Antworten der Form "key=value key=value" in dict[str, Any].

Beispiele:
    "status state=idle step=0 error= press=1 push_front=0 ... stepper_pos=200"
        → {"_kind": "status", "state": "idle", "step": 0, "error": None,
           "press": True, "push_front": False, ..., "stepper_pos": 200}

    "ok params drum_steps_per_pos=200 servo_home=5 ..."
        → {"_kind": "params", "drum_steps_per_pos": 200, "servo_home": 5, ...}

    "ok knock_cycles=8"  (Antwort auf set/get)
        → {"_kind": "ok", "knock_cycles": 8}

    "err range:press_pwm"  → {"_kind": "err", "reason": "range", "detail": "press_pwm"}

Werte werden automatisch konvertiert:
    leer        → None
    "0"/"1"     (für bekannte Bool-Felder) → bool
    "123"       → int
    "abc"       → str (unverändert)
"""
from __future__ import annotations

from typing import Any

# Felder, die als bool interpretiert werden sollen (Sensoren + Aktor-Pins).
# Alles andere mit Zahl bleibt int.
_BOOL_FIELDS = {
    "press", "push_front", "push_rear", "magazin",
    "sol1", "sol2", "hopper", "hopper_enabled",
}


def _coerce(key: str, raw: str) -> Any:
    if raw == "":
        return None
    if key in _BOOL_FIELDS:
        return raw == "1"
    try:
        return int(raw)
    except ValueError:
        return raw


def parse(line: str) -> dict[str, Any]:
    """Parse eine Nano-Antwortzeile."""
    line = line.strip()
    if not line:
        return {"_kind": "empty"}

    # Erstes Wort = Marker (status / ok / err / warn / pong / ready)
    parts = line.split(" ", 1)
    head = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if head == "pong":
        return {"_kind": "pong"}

    if head == "err":
        # Format "err <reason>" oder "err <reason>:<detail>"
        reason = rest
        detail: str | None = None
        if ":" in rest:
            reason, detail = rest.split(":", 1)
        return {"_kind": "err", "reason": reason.strip(), "detail": detail}

    if head == "warn":
        return {"_kind": "warn", "message": rest}

    if head == "ready":
        # "ready firmware=0.3.0"
        result: dict[str, Any] = {"_kind": "ready"}
        result.update(_parse_kv(rest))
        return result

    if head == "status":
        result = {"_kind": "status"}
        result.update(_parse_kv(rest))
        return result

    if head == "ok":
        # "ok params <kvs>" oder "ok <key>=<val>" oder "ok stuffing"
        result = {"_kind": "ok"}
        sub_parts = rest.split(" ", 1)
        if not sub_parts or sub_parts == [""]:
            return result
        first = sub_parts[0]
        if "=" not in first and len(sub_parts) >= 1:
            # "ok params <kvs>" oder "ok knock 5" oder "ok stuffing"
            result["sub"] = first
            tail = sub_parts[1] if len(sub_parts) > 1 else ""
            if "=" in tail:
                result.update(_parse_kv(tail))
            elif tail:
                result["value"] = tail
        else:
            # "ok knock_cycles=5 ..."
            result.update(_parse_kv(rest))
        return result

    # Unbekannter Anfang → roh zurück
    return {"_kind": "raw", "line": line}


def _parse_kv(s: str) -> dict[str, Any]:
    """Spaltet 'a=1 b=2 c=' in {'a':1, 'b':2, 'c':None}."""
    out: dict[str, Any] = {}
    for token in s.split(" "):
        if "=" not in token:
            continue
        k, v = token.split("=", 1)
        if not k:
            continue
        out[k] = _coerce(k, v)
    return out
