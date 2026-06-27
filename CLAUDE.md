# Zigarettenstopfmaschine · Vollautomatisch

## Projektübersicht

Vollautomatische DIY Zigarettenstopfmaschine, basierend auf dem Fraens-Engineering-Projekt, mit eigenen Anpassungen. Aktueller Stand: Mechanik teilweise montiert, Elektronik wird gerade aufgebaut.

**Referenzprojekt:** Fraens Engineering Cigarette Stuffing Machine (https://fraensengineering.com), Video: https://youtu.be/scCJcUZJsKU

**Gesetzliche Lage:** §30 TabStG verbietet in Deutschland den Verkauf solcher Maschinen, Eigenbau und private Nutzung sind aber legal.

---

## Architektur

Zweischicht-Architektur mit klarer Trennung von Echtzeit-Steuerung und höherer Logik:

```
┌─────────────────────┐         USB        ┌──────────────────┐
│ Raspberry Pi Zero 2 │ ◄────────────────► │  Arduino Nano    │
│ (Brain)             │   Serial + 5V      │ (Maschinencontr.)│
│ FastAPI / BLE       │                    │ Echtzeit         │
└──────────┬──────────┘                    └────────┬─────────┘
           │                                        │
           │ HTTP / BLE                             │ GPIO
           ▼                                        ▼
   ┌───────────────┐                   ┌──────────────────────┐
   │ Mobile App    │                   │ Motoren / Sensoren    │
   │ Flutter/Swift │                   │ A4988, L298N, Servo   │
   └───────────────┘                   └──────────────────────┘
```

**Pi Zero 2 W:** HTTP-API (FastAPI), Konfiguration, Logging, BLE/WLAN, Stats. Versorgt über GPIO Pin 2 (5V) und Pin 6 (GND) vom Buck-Konverter.

**Arduino Nano:** Echtzeitsteuerung aller Motoren/Sensoren, Watchdog (sicherer Zustand bei 5s ohne Pi-Befehl). Versorgung und Datenkommunikation laufen beide über das eine USB-Kabel zum Pi.

**Aktuelle Übergangslösung (bis Buck-Konverter da ist):** ESP-WROOM-32 als Single-Board-Steuerung. Pin-Belegung siehe `docs/esp32-pinout.md`.

---

## Mechanik

### Stopfrohr (Slip-On Tube)
- **Material:** Edelstahl V2A
- **Maße:** 7mm OD, 0,5mm Wandstärke → 6mm ID
- **Oberfläche:** glatt (KEIN Widerhaken-Design wie bei Handmaschinen)
- **Gegendruck:** über separaten einstellbaren Klemmring/Federmechanismus am Hülsenausgang
- **Vordere Kante** entgratet und leicht verrundet, damit Hülsen nicht reißen

### Pusher
- **Material:** Messing-Rundwelle 5,5mm (0,25mm Spiel pro Seite zu 6mm ID)
- **Länge:** ~120-150mm gesamt (70mm Hub + Führung + Anbindung)
- **Vorderes Ende:** 2-3 Längskerben (~1mm tief, 5mm lang) als Mitnahmezähne
- **Hinteres Ende:** Querloch oder Klemmverbindung zum Antrieb

### Linearantrieb für Pusher
- **T8 Leitspindel 150mm**, 2mm Pitch
- **T8 Messingmutter** in 3D-gedrucktem Führungsstück
- **Flexible Wellenkupplung** 5×8mm (NICHT starr — verzeiht Fluchtungsfehler)
- **KFL08 Flanschlager** als Gegenlager
- **Selbsthemmend** — Pusher bleibt bei Motorstillstand auch unter Druck stehen
- Bei 200-Step NEMA17 → 0,01mm Auflösung pro Step

### Tabak-Dosierung (Tilt-Schwenkwand + 2 Hubmagnete)
**Mechanismus der vollautomatischen Fraens-Maschine** (anders als die teil-automatische
Variante mit Förderschnecke — die wäre falsch hier). Drei Aktoren arbeiten gemeinsam in
der „Knocking"-Phase:

- **Servo-Schwenkwand** im Acryl-Trog — Mini-Servo (Tabak-Servo) schwenkt eine Wand vor/zurück
  → mischt und führt den Tabak in Richtung Auslass
- **Hubmagnet #1 (Front-Knock)** — schlägt seitlich gegen den Trog → bricht Brücken im Vorrat
- **Hubmagnet #2 (Top-Druck)** — schlägt von oben → drückt Tabak in Stopfrohr-Position
- **Zyklus:** ~8× Knocking-Wiederholungen, Servo + beide Magnete pulsieren parallel
  → eine Tabak-Portion ist dosiert

**Bauteile:**
- 1× Mini-Servo (SG90 / Tower Pro Tiny-S Klasse), 5 V, ~10 g
- 2× **Heschen HS-0530B** Push/Pull-Solenoid: 12 V DC, ~5 mm Hub, ~3–5 N Zugkraft,
  ~0,5 A pro Solenoid, Bauform ~14×30 mm, Duty cycle intermittent (für kurze Pulse, nicht Dauer)
- 1× L298N **Mini-Modul** als 2-Kanal-Solenoid-Treiber — das alte ausgetauschte Modul
  ist hier perfekt: fehlende ENA/ENB sind für Solenoide kein Nachteil, sondern ideal
  (Always-Enabled-Betrieb passt zur EIN/AUS-Steuerung)
- 2× Flyback-Diode 1N5819 oder 1N4007 (zusätzlich zur L298N-internen — optional aber sicher)

### Hülsen-Standard (King Size)
- 84mm × 8mm OD, ~7,5mm ID

### Strukturmaterial
- **PMMA GS (gegossen, NICHT extrudiert)** — bohrfähiger, mechanisch stabiler
- **4mm Stärke** (laut Fraens-DXF)

---

## Elektronik

### Mikrocontroller
- **Final:** Arduino Nano (Echtzeit) + Raspberry Pi Zero 2 W (Brain)
- **Übergang:** ESP-WROOM-32 (3,3V Logik, beachten bei Spannungsteilern!)

### Motortreiber
- **A4988** (Schrittmotor): 100µF Elko zwischen VMOT und GND PFLICHT, sonst stirbt der Treiber. Vref auf 0,7-1,0V einstellen vor erstem Anlauf.
- **L298N Standard-Modul** (großes Board mit Kühlkörper, Schraubklemmen, ENA/ENB): 470µF Elko an 12V-Eingang. ENA/ENB für PWM-Drehzahlsteuerung in beide Richtungen. **Verwendung: Presse + Pusher (DC-Getriebemotoren).**
- **MOSFETs (3× IRLZ44N o. ä. Logic-Level)**: **Verwendung: 2 Tabak-Solenoide + 1 Hülsenmagazin-Motor**. Pro Kanal: Nano-Pin → 100 Ω → Gate, Source an GND, Drain an Last, Last-andere-Seite an +12 V bzw. +5 V, Flyback-Diode parallel (1N5819 für Solenoide, 1N4148 reicht für 40-mA-Motor). Spannungsabfall < 20 mV, keine Wärme. Ersetzt den ursprünglich geplanten L298N-Mini, der bei Solenoid-Halteströmen überhitzen würde.

### Motoren / Aktoren
- 1× NEMA 17 Schrittmotor (**Trommelmagazin-Drehung**, Belt 1:1 zur Drum)
- 2× DC-Getriebemotor 12V (Presse + Pusher) — via L298N Standard-Modul mit ENA/ENB
- 1× SG90 Servo (Hülsen-Schieber, D11)
- 1× SG90/Tiny-S Servo (Tabak-Tilt-Schwenkwand, A3)
- 2× **Heschen HS-0530B** Hubmagnet 12 V (Tabak-Front-Knock + Tabak-Top-Druck)
  via **MOSFETs** (IRLZ44N) — kein L298N-Mini, weil Halteströme (~1 A/Solenoid)
  und Spannungsabfall (~2,5 V) ihn überhitzen würden
- 1× **5 V Vibrationsmotor** (Hülsenmagazin, ~40 mA) via MOSFET + 1N4148-Flyback

### Sensoren
- **3× induktive Initiatoren** (LJ8A3-2-Z/BX **oder LJ12A3-4-Z/BX**, NPN, 12V): Press-Position, Push-Front, Push-Rear
  - LJ8 (M8, 2 mm Schaltabstand) und LJ12 (M12, 4 mm) sind elektrisch identisch — Code/Spannungsteiler gleich. LJ12 nur größere Bohrung + Target ≥ 12×12 mm
  - Verkabelung: braun=12V, blau=GND, schwarz=Signal
  - **WICHTIG: Spannungsteiler nötig!** Initiator gibt 12V Signal aus.
    - Für **Arduino Nano (5V Logik):** 10kΩ + 7,5kΩ Spannungsteiler
    - Für **ESP32 (3,3V Logik):** 10kΩ + 3,9kΩ Spannungsteiler
- **1× Optosensor** (Oniissy Gabellichtschranke) für Trommelmagazin-Referenz (sauberer Bereich)
- **Mikroschalter (KW12) als Backup-Endschalter** für staubige Bereiche (optional)

### Steuerung (rein remote)
- Manueller Drucktaster entfällt — komplette Steuerung erfolgt **remote** über den
  Raspberry Pi (HTTP-API, später BLE). Der Nano kennt keinen lokalen Start-Trigger.

### Stromversorgung
- **12V Netzteil min. 5A** als Hauptversorgung
- **Buck-Konverter LM2596 / Mini360** 12V→5V für Pi und Servo (≥3A)
- **Pi-Versorgung über GPIO Pin 2/6**, NICHT über USB-Power-Eingang (Polyfuse umgehen)
- **Servo direkt vom Buck-Konverter** (NICHT vom L298N-5V-Ausgang — instabil unter Motorlast)
- **470µF Elko direkt am Servo** zwischen VCC und GND

### Pin-Belegung Arduino Nano
**Timer-Hinweis:** ENA/ENB MÜSSEN auf D5/D6 (Timer0-PWM) — `Servo.h` belegt
Timer1 und deaktiviert PWM auf D9/D10. IN1–IN4 sind reine digitale
Richtungspins, daher auf D7–D10 unkritisch.
```
D2  → A4988 STEP
D3  → A4988 DIR
D4  → A4988 EN
D5  → L298N ENA (PWM Timer0, Presse Drehzahl)
D6  → L298N ENB (PWM Timer0, Pusher Drehzahl)
D7  → L298N IN1 (Presse Richtung A, digital)
D8  → L298N IN2 (Presse Richtung B, digital)
D9  → L298N IN3 (Pusher Richtung A, digital)
D10 → L298N IN4 (Pusher Richtung B, digital)
D11 → Servo Signal Hülsen-Schieber (PWM)
D12 → MOSFET-Gate → Hülsenmagazin-Motor (5 V, ~40 mA)
D13 → MOSFET-Gate → Hubmagnet #2 (Top-Druck, Heschen HS-0530B)
A0  → Initiator Press (über Spannungsteiler)
A1  → Initiator Push-Front (über Spannungsteiler)
A2  → Initiator Push-Rear (über Spannungsteiler)
A3  → Servo Signal Tabak-Tilt-Schwenkwand (Servo-Lib auf Analog-Pin)
A4  → MOSFET-Gate → Hubmagnet #1 (Front-Knock, Heschen HS-0530B)
A5  → Magazin-Lichtschranke (Gabellichtschranke, direkt 5 V)

# Manueller Start-Taster: ENTFÄLLT (Steuerung remote über Pi)
# Onboard-Status-LED: ENTFÄLLT (D13 jetzt MOSFET-Gate für Solenoid #2)
```

### Pin-Belegung ESP-WROOM-32 (Übergangslösung)
**Hinweis:** Beim ESP32 ist die ENA/ENB-Platzierung **frei** — der ESP32 nutzt
das LEDC-Peripherie für PWM und Servo (kein Timer1-Konflikt wie beim Nano).
Daher andere Zuordnung als beim Nano, das ist beabsichtigt und unkritisch.
```
GPIO 25 → A4988 STEP        GPIO 14 → L298N IN1
GPIO 26 → A4988 DIR         GPIO 12 → L298N IN2
GPIO 27 → A4988 EN          GPIO 13 → L298N IN3
GPIO 19 → Servo             GPIO 32 → L298N IN4
GPIO 21 → Start-Taster      GPIO 33 → L298N ENA
GPIO 34 → Initiator Press   GPIO 4  → L298N ENB
GPIO 35 → Initiator PushFr
GPIO 36 → Initiator PushRe
GPIO 39 → Magazin-Sensor

⚠️ GPIO 0, 2, 5, 12, 15 sind Boot-Strapping-Pins — vorsichtig nutzen
⚠️ GPIO 34/35/36/39 sind Input-only ohne interne Pull-Ups
```

---

## Stopfsequenz (Programm-Logik)

1. **Referenzfahrt** — Trommel per Schlitzsensor auf Startposition
2. **Tabak dosieren („Knocking")** — ~8× wiederholt: Tabak-Servo schwenkt Tilt-Wand, Hubmagnet #1 schlägt seitlich gegen Trog (bricht Brücken), Hubmagnet #2 drückt von oben → Tabak rieselt in Stopfrohr-Position
3. **Pressen** — Presse-Motor verdichtet Tabak; Initiator Press signalisiert Endposition
4. **Hülse aufsetzen** — Servo schiebt Hülse aufs Stopfrohr
5. **Stopfen** — Pusher-Motor schiebt Tabak in Hülse; Initiator Push-Front = Endposition
6. **Pusher zurück** — bis Initiator Push-Rear auslöst
7. **Trommel weiterdrehen** — fertige Zigarette fällt aus, neue Hülse vorrutschen
8. **Repeat ab Schritt 2**

### Servo-Positionen (aus Fraens-Code)
- Hülsen-Servo: 5° (vorne) / 85° (hinten)
- Tabak-Servo: 80° (vorne) / 140° (hinten)

---

## Software-Architektur

### Arduino Nano (Echtzeit)
- **Sprache:** C++ (PlatformIO Standard, Arduino IDE als Alternative)
- **Aufgabe:** Stupide, robuste Befehlsausführung. KEINE eigene Logik, keine UI.
- **Watchdog:** Wenn 5s kein Befehl vom Pi → alle Motoren AUS, sicherer Zustand
- **Bibliotheken:** AccelStepper, Servo, ggf. PID
- **Code-Portabilität:** `config.h` setzt `SERIAL_BAUD` und `FIRMWARE_VERSION` via `#ifndef`-Fallback → kompiliert in PlatformIO (Build-Flags aus `platformio.ini`) UND in Arduino IDE (Fallback-Werte aus config.h)
- **CH340-Clone-Nano:** brauchen oft den alten Bootloader (57600 Baud). In `platformio.ini` ist `upload_speed = 57600` gesetzt. Arduino IDE: „Werkzeuge → Prozessor → ATmega328P (Old Bootloader)" wählen. Bei „stk500_getsync: not in sync"-Fehler: manueller Reset-Trick (Reset-Taste genau bei „Uploading" drücken)

### Raspberry Pi Zero 2 W (Brain)
- **OS:** Raspberry Pi OS Lite (headless)
- **Sprache:** Python mit FastAPI (REST + automatische Swagger-Docs)
- **Pakete:**
  - `fastapi`, `uvicorn` — HTTP-Server
  - `pyserial` — Kommunikation mit Nano
  - `bleak` oder `dbus-bluez` — BLE-Service für App
  - `sqlite3` — Stats und Konfig
- **Endpunkte (Beispiel):**
  - `POST /stuff` — eine Zigarette stopfen
  - `GET /status` — Maschinenstatus, Zähler
  - `GET /config` / `PUT /config` — Konfiguration lesen/schreiben
  - `GET /logs` — letzte Events

### Mobile App
- **Plattform:** Flutter primär (Code-Sharing mit iOS), Swift falls iOS-only
- **Kommunikation:**
  - Phase 1: HTTP über WLAN (einfacher zu debuggen)
  - Phase 2: BLE-Direktverbindung (funktioniert ohne WLAN)
- **Features (geplant):** Live-Status, Zigarettenzähler, Stopf-Härte einstellen, Fehlerprotokoll, Service-Modus

### Befehlsprotokoll Pi ↔ Nano
Textbasiert über Serial (115200 Baud), ein Befehl pro Zeile, mit `\n` terminiert:

```
Pi → Nano:
  STUFF                  # Stopfsequenz starten
  STATUS                 # Statusabfrage
  STOP                   # Sofort-Stopp
  HOME                   # Referenzfahrt
  SET_PRESS_TIME 800     # Presszeit setzen (ms)
  SET_PUSH_SPEED 200     # Pusher-Drehzahl (PWM 0-255)
  TEST_MOTOR press       # Einzeltest (press/push/feed/servo)

Nano → Pi:
  READY
  BUSY
  DONE
  ERROR <reason>         # z.B. "ERROR pusher_stuck"
  STATUS pos=front,cnt=42,err=0
```

---

## Aktueller Aufbau-Stand

✅ Mechanik teilweise montiert
✅ Elektronik-Komponenten bestellt und angekommen
✅ Beide DC-Getriebemotoren verbaut (Presse, Pusher)
✅ NEMA 17 Schrittmotor verbaut
✅ Servo SG90 für Hülsenschieber verbaut
🔲 Buck-Konverter bestellt, noch nicht da → ESP32 als Übergang
🔲 Tabak-Magazin & Hülsen-Magazin folgen nach Tests
🔲 Pi und Nano warten auf Buck-Konverter

---

## Test-Reihenfolge (KRITISCH)

1. **Buck-Konverter justieren** — auf exakt 5,0V einstellen mit Multimeter
2. **A4988 Vref einstellen** — auf 0,7-1,0V (sonst Motor heiß oder schwach)
3. **Pi flashen, SSH, WLAN** — headless setup
4. **Nano per USB an Pi** — `ls /dev/ttyACM*` prüfen
5. **Echo-Test** — Pi → Nano "PING", erwartet "PONG"
6. **NEMA 17** isoliert testen (A4988 + Spindel + Pusher)
7. **DC-Motor 1 Presse** mit L298N
8. **DC-Motor 2 Pusher** mit L298N
9. **Servo** zum Schluss
10. **Initiatoren** mit Spannungsteilern
11. **Magazin-Lichtschranke** (Trommel-Index)
12. **Tabak-Servo + 2× Solenoide** (MOSFET-Tests via `knock`-Befehl)
13. **Hülsenmagazin-Motor** (MOSFET, on/off via `hopper`-Befehl)
14. **Vollintegration:** Stopfsequenz schrittweise (Pi-orchestriert)

---

## Wichtige Konstruktions-Erkenntnisse

- **Pusher darf sich nicht drehen, nur linear bewegen** → Linearführung mit zwei Schienen
- **Tabak muss VOR dem Stopfen auf < Hülsen-ID gepresst werden** (Kniehebel oder Spindel)
- **Tabak-Dosierung in der Vollautomatik = Tilt + Schlag**, nicht Förderschnecke! Förderschnecke war Fraens' teil-automatische Variante; die Vollautomatik nutzt Servo-Schwenkwand + 2 Hubmagnete. Vorteil: Tabak wird nicht zerkleinert
- **Zwei Hubmagnete statt einem** — einer bricht Brücken im Vorrat (Front-Knock), der andere drückt Tabak in Position (Top-Druck). Ein Solenoid allein reicht oft nicht für sauberen Tabak-Fluss
- **Glattes Stopfrohr für Vollautomatik** (keine Widerhaken — die sind nur für Hand-Stopfer)
- **Slip-on Tube Außendurchmesser ~7,3mm ideal** für 7,5mm Hülsen-ID; bei 7mm OD: Schrumpfschlauch oder 3D-Druck-Trichter ergänzen
- **Alle GNDs müssen verbunden sein!** Pi, Nano, A4988, L298N, Buck, Netzteil, Servo — sonst funktionieren Steuersignale nicht zuverlässig
- **Pi Zero 2 W hat nur EINE LED** (grün, ACT) — keine rote PWR-LED wie die großen Pis. Aktivität der grünen LED bei Einschalten ohne SD-Karte ist normal (kein Defekt)
- **Initiator-Target idealerweise aus Stahl**, nicht Edelstahl V2A — V2A reduziert den Schaltabstand auf 70–85 % des Nominalwerts
- **Sensor-LED ist die beste Diagnose** bei Initiator-Problemen — leuchtet unabhängig von Spannungsteiler/Nano, isoliert das Sensor-Problem vom Schaltungsproblem
- **WAGO 221 Hebelklemmen** (oder vergleichbar) für GND-Stern und +12V-Bus — Steckbrett ist NICHT geeignet für Power-Verteilung (Federkontakte zu hochohmig + nicht vibrationsfest)

---

## Bezugsquellen (Deutschland)

### Acrylglas-Zuschnitt nach DXF
- **Kunststoffplattenonline.de** (DXF-Upload, Online-Preis, ±0,05mm Laser-Genauigkeit) — Hauptanbieter
- **S-Polytec.de** (akzeptiert auch STEP/IGES aus Onshape)
- **Acrylglasplattenshop.de** (mit Onshape-Tutorial)
- **Plattenzuschnitt24.de** (per Mail, persönliche Betreuung)

### Elektronik
- Amazon: A4988, L298N, Buck-Konverter, NEMA 17, Servo SG90, ESP32, Arduino Nano, Pi Zero 2 W
- Initiatoren: "LJ8A3-2-Z/BX" auf Amazon (~5€/Stück)
- Hubmagnete: **Heschen HS-0530B** (12V, ~5mm Hub, ~4N, ~0,5A) — Amazon, ~8–12€/Stück, im 2er-Pack
- MOSFETs (Treiber für Solenoide + Hülsenmagazin-Motor): **3× IRLZ44N** (Logic-Level, Reichelt ~0,30€/Stück) oder 2N7000/BS170 für kleinere Lasten
- Flyback-Dioden: **2× 1N5819** (Solenoide), **1× 1N4148** (Hülsenmotor-40mA) — Standard, im Sortiment dabei
- Gate-Widerstände: 2× 100 Ω (Solenoide), 1× 1 kΩ (Hopper-Motor)
- Hülsenmagazin-Motor: 5 V Mini-DC- oder Vibrationsmotor, ~40 mA

### Mechanik
- T8 Leitspindel + Mutter: Amazon Set ~6€
- Wellenkupplung 5×8mm (FLEXIBEL!): ~3€
- KFL08 Flanschlager: ~3€
- Edelstahlrohr 7mm OD: Modellbau-Shops oder eBay

---

## CAD / Konstruktion

- **Onshape** für eigene Anpassungen (parametrisch, Variables nutzen für Kernmaße)
- **Reihenfolge:** Stopfrohr-Halter + Pusher-Führung → Trommelmagazin → Tabakmagazin/Gehäuse
- **Fraens DXF-Datei** wurde in 14 Einzelteile aufgeteilt (Pos.95–Pos.108)
- **Werkstoff in DXF:** "Acrylglas" (war ursprünglich PETG, wurde ersetzt für Laser-Cutter-Bestellung)

---

## Coding-Konventionen

### Allgemein
- **Sprachpräferenz für Mobile Apps:** Swift (iOS), Kotlin Multiplatform, Flutter, React Native, .NET MAUI
- Code-Kommentare auf Deutsch oder Englisch — konsistent pro Datei
- Sicherheits-First: Maschine darf in keinem Fehlerzustand unkontrolliert weiterlaufen

### Arduino Nano
- Header-Dateien für Konstanten (Pins, Geschwindigkeiten, Timeouts)
- Zustandsautomat (state machine) für die Stopfsequenz
- Nicht-blockierende Programmierung — kein `delay()` in der Hauptschleife
- AccelStepper für sanfte Beschleunigung des NEMA 17

### Python (Pi)
- FastAPI mit Type Hints
- async/await für Serial-Kommunikation
- Pydantic-Models für API-Schemas
- Logging mit `logging`-Modul, nicht `print`

### Mobile App (Flutter bevorzugt)
- Riverpod oder Bloc für State Management
- Repository-Pattern für API/BLE-Zugriff
- Theme-fähig (Dark/Light)

---

## Bekannte Risiken / TODO

- [ ] Buck-Konverter justieren bevor anschließen (Multimeter!)
- [ ] A4988 Vref vor erstem Test einstellen
- [ ] Watchdog im Nano-Code: Maschine bei Pi-Verbindungsverlust stoppen
- [ ] Endabschalter überall — nicht nur Initiatoren, auch Software-Limits
- [ ] Tabak-Staub-Filter für Optosensoren (sonst Fehlsignale)
- [ ] Notaus-Knopf hardware-seitig (unterbricht 12V direkt, nicht nur via Software)
- [ ] Geräuschdämmung — DC-Motoren und Schrittmotor sind laut
