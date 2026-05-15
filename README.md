# Zigarettenstopfmaschine

DIY vollautomatische Zigarettenstopfmaschine mit zweischichtiger Architektur:
**Raspberry Pi Zero 2 W** (Brain) + **Arduino Nano** (Echtzeitsteuerung).

## Repo-Struktur

Legende: Dateien ohne Marker existieren; **(geplant)** = noch nicht angelegt.

```
stopfmaschine/
├── CLAUDE.md              # Projekt-Kontext für Claude Code
├── README.md              # Dieses File
├── .gitignore
│
├── firmware/
│   └── nano/              # Arduino Nano Firmware
│       ├── src/
│       │   ├── main.cpp           # Einstiegspunkt (Test-Firmware v0.1)
│       │   ├── pins.h             # Pin-Belegung zentral
│       │   └── config.h           # Konstanten (Speeds, Timeouts)
│       │   # (geplant) commands.*, motors.*, sensors.*, statemachine.*
│       └── platformio.ini
│
├── backend/
│   └── pi/                # Raspberry Pi Brain (Python/FastAPI)
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py            # FastAPI Entry + Endpoints
│       │   └── nano_client.py     # Serial-Kommunikation
│       │   # (geplant) api/, models/, db/
│       ├── requirements.txt
│       └── # (geplant) tests/
│
├── cad/                   # CAD-Quellen & Fertigungsdateien
│   ├── README.md          # CAD-Doku & Bauteilübersicht
│   ├── source/            # Master-DXFs (Fraens-Originale)
│   ├── drawings/
│   │   └── acryl_parts/   # Laser-Cut-DXFs (4 mm PMMA)
│   ├── reference/
│   │   └── metal_parts/   # Metallteile-Zeichnungen (DXF + PDF)
│   ├── stl/               # 3D-Druck-Dateien (PETG/PLA)
│   └── scad/              # OpenSCAD-Quellen (Platzhalter)
│
├── docs/                  # Schaltpläne & Referenzen
│   ├── wiring.md          # Schaltpläne (Mermaid + ASCII-Detail)
│   ├── pinout.md          # Pin-/Verdrahtungstabellen + Bestelllisten
│   └── protocol.md        # Serial-Protokoll Pi ↔ Nano
│
└── app/                   # Mobile App (Flutter primär) — (geplant)
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
