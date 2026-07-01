# Serial-Protokoll Pi ↔ Nano

Textbasiertes Protokoll über USB-Serial, **115200 Baud, 8N1**.
Ein Befehl pro Zeile, mit `\n` (LF) terminiert. Antworten zeilenweise.

> **Implementiert in:** [`../firmware/nano/src/main.cpp`](../firmware/nano/src/main.cpp)
> **Konsumiert von:** [`../backend/pi/app/nano_client.py`](../backend/pi/app/nano_client.py)

---

## 1. Designprinzipien

| Regel | Begründung |
|---|---|
| **Ein Befehl pro Zeile**, terminiert mit `\n` | trivial zu parsen, in jedem Terminal-Tool testbar |
| **Antwort beginnt mit Schlüsselwort** (`ok`, `err`, `status`, `warn`, `pong`) | Pi kann auf Erfolg/Fehler matchen ohne JSON-Parser |
| **Befehle kleingeschrieben**, Antworten kleingeschrieben | konsistent, einfacher zu vergleichen |
| **Nano hat keine eigene Logik** — nur Befehlsausführung | jede Zustandsmaschine läuft auf dem Pi |
| **Watchdog**: 5 s ohne Befehl → alle Motoren AUS | Sicherheit bei Pi-Ausfall |
| **Synchron**: jeder Befehl bekommt genau eine Antwortzeile | (Ausnahmen: `status`, `warn …`) |

---

## 2. Befehlsübersicht

### Konnektivität

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `ping` | `pong` | Verbindungstest. Pi sollte das nach Connect zuerst senden. |
| `help` | mehrzeilige Hilfe | Liste aller Befehle (für manuelles Debuggen) |
| `status` | `status press=B push_front=B push_rear=B magazin=B magazin_raw=B sol1=B sol2=B hopper=B stepper_pos=N` | Sensor-Snapshot (`B` = `0`/`1`, `N` = signed long) |

### Schrittmotor (Trommelmagazin-Drehung)

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `stepper <N>` | `ok stepper <N>` | Bewegt Schrittmotor um N Steps. Negativ = rückwärts. |

Beispiele:

```
stepper 400      → 400 Steps vorwärts (Tabakdosis lt. Default)
stepper -200     → 200 Steps rückwärts
stepper 0        → no-op (aber Watchdog wird "gefüttert")
```

### DC-Motoren (Presse + Pusher)

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `press fwd` | `ok press fwd` | Presse vorwärts mit `PRESS_SPEED_DEFAULT` (PWM via ENA) |
| `press rev` | `ok press rev` | Presse rückwärts, ebenfalls drehzahlgeregelt (ENA-PWM) |
| `press stop` | `ok press stop` | Presse aus |
| `pusher fwd` | `ok pusher fwd` | Pusher vorwärts mit `PUSHER_SPEED_DEFAULT` (PWM via ENB) |
| `pusher rev` | `ok pusher rev` | Pusher rückwärts, ebenfalls drehzahlgeregelt (ENB-PWM) |
| `pusher stop` | `ok pusher stop` | Pusher aus |

> Mit dem großen L298N (ENA/ENB) ist die Drehzahl in **beide** Richtungen
> geregelt — anders als beim Mini-Modul, wo Rückwärts fix volle Drehzahl war.

### Servo (Hülsen-Schieber)

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `servo <0..180>` | `ok servo <angle>` | Fährt Servo auf Winkel (geclamped 0–180). |

Wichtige Positionen (siehe `config.h`):
- `servo 5` → Hülse fertig aufgeschoben (`SERVO_POS_HOME`)
- `servo 85` → Hülse aufnehmen (`SERVO_POS_LOAD`)

### Tabak-Dosierung (Tilt-Servo + 2 Solenoide via MOSFETs)

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `solenoid 1 pulse <ms>` | `ok sol1 pulse <ms>` | Hubmagnet #1 (Front-Knock) für ms an, dann aus (max 1000 ms) |
| `solenoid 1 off` | `ok sol1 off` | Hubmagnet #1 aus |
| `solenoid 1 on` | `err on_disabled sol1` | **Dauer-ON deaktiviert** (Magnet-Schutz, ab v0.3.1) |
| `solenoid 2 off\|pulse <ms>` | wie #1 | Hubmagnet #2 (Top-Druck) |
| `knock` | `ok knock start cycles=8` ... `ok knock done` | Komplette Knock-Sequenz mit Default-Cycles (8) |
| `knock <n>` | wie oben | mit `n` statt Default |

Konstanten (in `config.h`):
- `KNOCK_PULSE_ON_MS = 80`, `KNOCK_PULSE_OFF_MS = 120`, `KNOCK_CYCLES_DEFAULT = 8`
- `SOLENOID_PULSE_MAX_MS = 1000` (max Einzelpuls — Heschen nicht für Dauer-ON)

> **Kein Tabak-Servo** — Knock-Sequenz pulst nur die zwei Solenoide synchron.
> Der einzige Servo im System ist der Hülsen-Schieber (D11).

### Hülsenmagazin-Motor (kleiner 5 V DC via MOSFET)

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `hopper on` | `ok hopper on` | Motor an (bis `off`, `stop` oder Watchdog) |
| `hopper off` | `ok hopper off` | Motor aus |
| `hopper run <ms>` | `ok hopper run <ms>` | Motor für ms an, dann aus (max 4000 ms wegen Watchdog) |

Konstante: `HOPPER_DEFAULT_MS = 1500` (Default wenn `run 0`).

### Sicherheit

| Befehl | Antwort | Beschreibung |
|---|---|---|
| `stop` | `ok stop` | Sofort-Stopp **aller** Aktoren (DC-Motoren, Stepper, Solenoide, Hopper). |

---

## 3. Antwort-Schemata

```
ok <verb> <args...>           # Erfolg, optional mit Echo der Argumente
err unknown_command:<text>    # Befehl nicht erkannt (Echo zur Diagnose)
err <reason>                  # Anderer Fehler (z. B. ERROR pusher_stuck — geplant)
warn watchdog_timeout motors_off
                              # Spontane Warnung vom Nano (KEIN Antwort-Satz)
status press=<0|1> push_front=<0|1> push_rear=<0|1> magazin=<0|1>
       magazin_raw=<0|1> sol1=<0|1> sol2=<0|1> hopper=<0|1> stepper_pos=<N>
                              # Antwort auf "status"
pong                          # Antwort auf "ping"
ready firmware=<version>      # Bei Boot, einmalig
```

> **Spontane `warn`-Zeilen** (z. B. Watchdog) können jederzeit auftauchen. Der Pi-
> Reader muss damit umgehen, dass nach einem Befehl ggf. mehr als eine Zeile kommt.

---

## 4. Sequenzbeispiel: eine Zigarette stopfen

Nano-Antworten **kursiv**.

```
Pi → ping
Pi ← pong

Pi → status
Pi ← status press=0 push_front=0 push_rear=1 stepper_pos=0

# 1) Tabak dosieren
Pi → stepper 400
Pi ← ok stepper 400
   (Pi wartet ~500 ms — Stepper läuft non-blocking auf dem Nano weiter)

# 2) Pressen, bis Initiator Press auslöst
Pi → press fwd
Pi ← ok press fwd
Pi → status                    (mehrfach gepollt im 50-ms-Takt)
Pi ← status press=1 push_front=0 push_rear=1 stepper_pos=400
Pi → press stop
Pi ← ok press stop

# 3) Hülse aufsetzen
Pi → servo 85
Pi ← ok servo 85
Pi → servo 5
Pi ← ok servo 5

# 4) Stopfen, bis Initiator PushFront auslöst
Pi → pusher fwd
Pi ← ok pusher fwd
Pi → status                    (Polling)
Pi ← status press=0 push_front=1 push_rear=0 stepper_pos=400
Pi → pusher stop
Pi ← ok pusher stop

# 5) Pusher zurück bis Initiator PushRear
Pi → pusher rev
Pi ← ok pusher rev
Pi → status                    (Polling)
Pi ← status press=0 push_front=0 push_rear=1 stepper_pos=400
Pi → pusher stop
Pi ← ok pusher stop
```

---

## 5. Watchdog-Verhalten

```
T=0      letzter Befehl empfangen → lastCommandMs = 0
T=4,9 s  noch nichts geschehen → alles weiter
T=5,0 s  WATCHDOG_TIMEOUT_MS überschritten
         → allMotorsOff()  (inkl. Solenoide + Hopper-Motor!)
         Nano → Pi: warn watchdog_timeout motors_off
T=5,1 s  Pi sendet: ping
         Nano → Pi: pong
         (Watchdog wieder aktiv, nächste 5 s bewacht)
```

> Der Pi sollte mindestens alle **2 s** ein `ping` oder `status` senden, um den
> Watchdog zu füttern, auch wenn gerade keine aktive Sequenz läuft.

---

## 6. Geplante Erweiterungen (noch nicht implementiert)

Folgende Befehle stehen in [`../CLAUDE.md`](../CLAUDE.md) und sind **geplant**:

| Befehl | Zweck | Status |
|---|---|---|
| `home` | Referenzfahrt Trommel via Magazin-Lichtschranke | 🔲 |
| `stuff [<n>]` | komplette Stopfsequenz (1 oder n Zigaretten) | 🔲 wenn `statemachine.cpp/.h` existiert |
| `set_press_time <ms>` | Presszeit zur Laufzeit setzen | 🔲 |
| `set_push_speed <pwm>` | Pusher-Geschwindigkeit setzen | 🔲 |
| `set_knock_cycles <n>` | Anzahl Knock-Wiederholungen pro Dose ändern | 🔲 |
| `abort` | sequenz sauber abbrechen, alle Aktoren in safe state | 🔲 (entspricht aktuell `stop`) |

Implementierte Tabak/Hopper-Befehle (`solenoid 1|2`, `knock`, `hopper`)
siehe Sektion 2 oben — Bestandteil von Firmware v0.2.

Bis diese existieren, baut der Pi die Sequenz aus den **bestehenden** Befehlen
(`stepper`, `press fwd/stop`, `servo`, `pusher fwd/rev/stop`) zusammen.

---

## 7. Manuelles Testen

### Mit `pio device monitor` (Arduino IDE / PlatformIO)

```bash
cd firmware/nano
pio device monitor      # öffnet Serial Monitor mit 115200 Baud
> ping
< pong
> help
< === Stopfmaschine Test-Firmware ===
< ...
> stepper 200
< ok stepper 200
```

### Mit `screen` oder `minicom` (Linux/macOS)

```bash
screen /dev/ttyACM0 115200       # ggf. /dev/ttyUSB0
# Beenden: Ctrl-A, dann k, dann y
```

### Aus Python testen

```python
import serial
nano = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
nano.write(b"ping\n")
print(nano.readline())   # b'pong\n'
```

---

## 8. Fehlerbehandlung im Pi

Empfohlene Pattern für [`nano_client.py`](../backend/pi/app/nano_client.py):

```python
async def send(self, cmd: str, timeout: float = 1.0) -> str:
    self._serial.write((cmd + "\n").encode())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = (await self._readline()).decode().strip()
        if not line:
            continue
        if line.startswith("warn "):
            log.warning("nano: %s", line)        # nicht als Antwort werten
            continue
        return line                              # erste echte Antwort
    raise TimeoutError(f"no reply for {cmd!r}")
```

Empfehlungen:

- **`warn`-Zeilen ignorieren** (oder ans Logging weiterleiten), nicht als Antwort werten.
- Bei `err unknown_command:…` ist der Befehl falsch geschrieben — programmatischer Fehler, nicht recoverable.
- Bei Timeout: erst `ping` versuchen, dann ggf. Serial neu öffnen.

---

## Verwandte Dokumente

- [`wiring.md`](wiring.md) — Schaltpläne
- [`pinout.md`](pinout.md) — Pin-Belegung
- [`../firmware/nano/src/main.cpp`](../firmware/nano/src/main.cpp) — Befehlsparser
- [`../backend/pi/app/nano_client.py`](../backend/pi/app/nano_client.py) — Pi-seitiger Serial-Client
