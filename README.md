# Zigarettenstopfmaschine

DIY vollautomatische Zigarettenstopfmaschine mit zweischichtiger Architektur:
**Raspberry Pi Zero 2 W** (Brain) + **Arduino Nano** (Echtzeitsteuerung).

## Repo-Struktur

```
stopfmaschine/
├── CLAUDE.md              # Projekt-Kontext für Claude Code
├── README.md              # Dieses File
├── .gitignore
│
├── firmware/
│   └── nano/              # Arduino Nano Firmware
│       ├── src/
│       │   ├── main.cpp           # Einstiegspunkt
│       │   ├── pins.h             # Pin-Belegung zentral
│       │   ├── config.h           # Konstanten (Speeds, Timeouts)
│       │   ├── commands.cpp/.h    # Serial-Befehlsparser
│       │   ├── motors.cpp/.h      # Motor-Steuerung
│       │   ├── sensors.cpp/.h     # Initiator-Auslesung
│       │   └── statemachine.cpp/.h # Stopfsequenz-Logik
│       └── platformio.ini
│
├── backend/
│   └── pi/                # Raspberry Pi Brain (Python/FastAPI)
│       ├── app/
│       │   ├── main.py            # FastAPI Entry
│       │   ├── nano_client.py     # Serial-Kommunikation
│       │   ├── api/               # REST-Endpunkte
│       │   ├── models/            # Pydantic-Models
│       │   └── db/                # SQLite-Stats
│       ├── requirements.txt
│       └── tests/
│
├── app/                   # Mobile App (Flutter primär)
│   └── ...
│
├── cad/                   # Onshape-Exports, STL, DXF
│   └── ...
│
└── docs/                  # Schaltpläne, Notizen, Referenzen
    ├── pinout.md
    ├── protocol.md
    ├── circuit-diagram.pdf
    └── fraens-reference.pdf
```

## Schnellstart

### Arduino Nano (PlatformIO empfohlen)

```bash
cd firmware/nano
pio run                    # Kompilieren
pio run -t upload          # Auf Nano flashen
pio device monitor         # Serial Monitor (115200 Baud)
```

### Raspberry Pi Backend

```bash
cd backend/pi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API-Docs anschließend unter `http://<pi-ip>:8000/docs`.

## Test-Reihenfolge

Siehe `CLAUDE.md` Abschnitt "Test-Reihenfolge". Wichtigster Hinweis:
**Buck-Konverter VOR Anschluss auf 5,0V justieren** und **A4988 Vref auf 0,7-1,0V einstellen**.

## Sicherheit

⚠️ Diese Maschine arbeitet mit 12V/5A und beweglichen Teilen.
Notaus-Knopf hardware-seitig einbauen (unterbricht 12V direkt).
Watchdog im Nano-Code stoppt alle Motoren bei Pi-Verbindungsverlust > 5s.

## Lizenz / Hinweis

Eigenbau für privaten Gebrauch. Verkauf der Maschine ist nach §30 TabStG verboten.
