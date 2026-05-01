# Verdrahtung & Schaltpläne

Alle Diagramme als Mermaid (rendern direkt auf GitHub) plus ASCII-Detailskizzen
für die kniffligen Stellen (Spannungsteiler, Servo-Entkopplung).

> **Quelle der Wahrheit für Pin-Nummern:** [`firmware/nano/src/pins.h`](../firmware/nano/src/pins.h)
> **Bauteilliste & Material:** [`../CLAUDE.md`](../CLAUDE.md)

---

## 1. Stromversorgung (Power Distribution)

```mermaid
flowchart LR
    PSU["12 V / 5 A<br/>Netzteil"] -->|+12 V| F1["F1<br/>5 A T<br/>5x20 mm Glas"]
    F1 -->|12 V| BUS12["12 V Bus<br/>+ 470 uF Elko"]
    BUS12 -->|12 V| L298N_VS["L298N V_S<br/>Motor-12 V"]
    BUS12 -->|12 V| A4988_VMOT["A4988 V_MOT<br/>100 uF Elko PFLICHT"]
    BUS12 -->|12 V| F3["F3<br/>500 mA F"]
    F3 -->|12 V braun| INIT["Initiatoren<br/>LJ8A3-2-Z/BX 3 Stueck"]
    BUS12 -->|12 V| F2["F2<br/>1 A T"]
    F2 -->|12 V| BUCK["Buck-Konverter<br/>LM2596 / Mini360<br/>auf 5,0 V justiert"]

    BUCK -->|5 V min. 3 A| BUS5["5 V Bus"]
    BUS5 -->|GPIO Pin 2/6| PI["Raspberry Pi<br/>Zero 2 W"]
    BUS5 -->|VCC + 470 uF| SERVO["SG90 Servo"]
    BUS5 -->|optional| NANO_5V["Arduino Nano<br/>via USB vom Pi"]

    PI -->|USB Daten + 5 V| NANO["Arduino Nano"]

    GND_BUS["GEMEINSAME GND<br/>Netzteil - Pi - Nano - Buck<br/>A4988 - L298N - Servo"]
    PSU -.->|GND| GND_BUS
    BUCK -.->|GND| GND_BUS
    NANO -.->|GND| GND_BUS
    PI -.->|GND| GND_BUS
    L298N_VS -.->|GND| GND_BUS
    A4988_VMOT -.->|GND| GND_BUS
    SERVO -.->|GND| GND_BUS
    INIT -.->|blau / GND| GND_BUS

    classDef warn fill:#ffe4b5,stroke:#d2691e,stroke-width:2px;
    classDef fuse fill:#ffe0e0,stroke:#cc0000,stroke-width:2px;
    class GND_BUS warn;
    class F1,F2,F3 fuse;
```

### Sicherungs-Konzept

```
                                                                   ┌─► L298N (Motoren)
                                                                   │
12 V Netzteil ─►【F1: 5 A T, 5×20 mm Glas】──► 12 V-Bus ────────────┼─► A4988 (Stepper)
                  in Halter mit Schraubklemmen,                    │
                  unmittelbar nach PSU-Ausgang                     │
                                                                   ├─►【F2: 1 A T】─► Buck → Pi/Servo
                                                                   │
                                                                   └─►【F3: 500 mA F】─► Initiatoren-12 V
```

| Sicherung | Wert | Charakteristik | Schutzobjekt | Begründung |
|---|---|---|---|---|
| **F1 Hauptsicherung** | 5 A T (träge) | 5×20 mm Glas | Verkabelung 12 V-Bus, gegen PSU-Ausfall der OCP | passt zum 5-A-Netzteil; *träge* wegen Motor-Anlaufstrom (NEMA + 2× DC + Buck-Cap-Ladung gleichzeitig kann kurz > 4 A ziehen) |
| **F2 Buck-Eingang** | 1 A T | 5×20 mm Glas | Pi + Servo + Logik | Pi+Servo zieht ≤ 700 mA; trennt Logikseite, falls Motor-Pfad einen Defekt hat |
| **F3 Initiator-Schiene** | 500 mA F (flink) | 5×20 mm Glas | Sensor-Verkabelung | 3 Sensoren ziehen je ~10 mA; flink, weil dahinter keine induktive Last hängt |

### Warum **Glas**, nicht keramisch?

- **U = 12 V DC**: der Lichtbogen erlischt ohnehin schnell, sobald der Sicherungsdraht durch ist. Keramik-HBC ist für 230 V AC und Kurzschluss-Ströme > 35 A relevant — bei dir nicht der Fall.
- **I_short** ist durch das Schaltnetzteil auf ~10–25 A begrenzt → weit unter dem Glas-Abschaltvermögen (typ. 35 A @ 250 V AC).
- **Keramik** lohnt sich erst bei: AC-Netzseite (vor dem 12-V-PSU), oder wenn du auf Bleibatterie / 4S LiPo umsteigst (Kurzschluss > 100 A möglich).

### Alternative: selbstrückstellende Polyfuses (PTC)

Wenn dir Sicherungswechsel zu lästig sind:

| Position | Bauteil | Trip-Strom | Hinweis |
|---|---|---|---|
| 12 V Hauptlinie | Bourns MF-R500 | 5 A | trippt langsamer (Sekunden), kühlt von selbst zurück |
| Buck-Eingang | Bourns MF-R110 | 1,1 A | gleiches Verhalten |

Nachteil: ungenauer als Schmelzsicherungen, langsamerer Trip — okay als "soft fuse" zusätzlich zu F1, **aber nicht als Ersatz für F1**, weil sie im Kurzschluss zu langsam sind.

### Wichtige Regeln

| Regel | Warum |
|---|---|
| **F1 unmittelbar nach PSU-Ausgang** (nicht erst nach 1 m Kabel) | Sicherung schützt das Kabel — wenn das Kabel vor der Sicherung schmort, hat sie nichts genützt |
| **Sicherungshalter mit Schraubklemmen**, kein Steckhalter | DIY-Vibrationen lockern Stecker; lose Sicherung = Lichtbogen |
| **Buck-Konverter VOR Anschluss auf exakt 5,0 V justieren** (Multimeter!) | werkseitig oft auf 1,2 V — würde Pi/Servo grillen |
| **A4988 V_MOT: 100 µF Elko zwingend** zwischen V_MOT und GND, < 5 cm vom IC | sonst zerstören Spannungsspitzen den Treiber |
| **L298N: 470 µF Elko** an 12 V-Eingang | DC-Motor-Anlaufstrom dämpfen |
| **Servo NICHT vom L298N-5 V-Ausgang** speisen | bricht unter Motorlast ein, Servo zappelt |
| **Servo VCC: 470 µF Elko direkt an VCC↔GND** | Servo-Anlaufstrom |
| **ALLE GNDs verbinden** (Sternpunkt am Netzteil) | sonst funktionieren Steuersignale unzuverlässig |
| **Pi NICHT über Micro-USB** speisen | Polyfuse begrenzt → Brownout. Statt: GPIO Pin 2 (5 V) + Pin 6 (GND) |
| **Bei AC-Netzseite Keramik-Sicherung verwenden** (im 12-V-Netzteil verbaut, sonst extern primärseitig) | für 230 V AC ist Keramik-HBC Pflicht (VDE/CE) — Glas würde Lichtbogen weiterführen |

---

## 2. Signalverdrahtung Arduino Nano

```mermaid
flowchart LR
    subgraph NANO [Arduino Nano]
        D2["D2 STEP"]
        D3["D3 DIR"]
        D4["D4 EN"]
        D5["D5 PRESS_IN1 PWM"]
        D6["D6 PUSHER_IN3 PWM"]
        D7["D7 PRESS_IN2"]
        D8["D8 PUSHER_IN4"]
        D11["D11 Servo PWM"]
        D12["D12 Start-Taster"]
        D13["D13 Status-LED"]
        A0["A0 Init Press"]
        A1["A1 Init PushFront"]
        A2["A2 Init PushRear"]
        A5["A5 Magazin-Sensor"]
    end

    D2 --> A4988["A4988<br/>STEP/DIR/EN<br/>zu NEMA 17"]
    D3 --> A4988
    D4 --> A4988

    D5 --> L298N_A["L298N Kanal A<br/>IN1 PWM + IN2 digital<br/>zu DC-Motor Presse"]
    D7 --> L298N_A

    D6 --> L298N_B["L298N Kanal B<br/>IN3 PWM + IN4 digital<br/>zu DC-Motor Pusher"]
    D8 --> L298N_B

    D11 --> SERVO["SG90 Servo<br/>Huelsen-Schieber"]

    BUTTON["Start-Taster<br/>mechanisch, momentary<br/>gegen GND"] --> D12

    DIV1["Spannungsteiler<br/>10 k + 7,5 k"] --> A0
    DIV2["Spannungsteiler<br/>10 k + 7,5 k"] --> A1
    DIV3["Spannungsteiler<br/>10 k + 7,5 k"] --> A2

    INIT_P["Initiator Press<br/>LJ8A3-2-Z/BX NPN"] -->|schwarz Signal 12 V| DIV1
    INIT_PF["Initiator Push-Front"] -->|schwarz| DIV2
    INIT_PR["Initiator Push-Rear"] -->|schwarz| DIV3

    OPTO["Gabellichtschranke<br/>Oniissy<br/>Magazin-Ref"] --> A5
```

---

## 3. Initiator-Spannungsteiler (KRITISCH)

NPN-Initiatoren geben das Signal als **12 V Pull-up** aus → würde 5 V-Eingang
des Nano sofort zerstören. Spannungsteiler-Verhältnis:

```
U_out = U_in · R2 / (R1 + R2)
      = 12 V · 7,5 kΩ / (10 kΩ + 7,5 kΩ)
      = 12 V · 7,5 / 17,5
      ≈ 5,14 V       ← noch innerhalb 5 V-Toleranz des Nano (max 5,5 V)
```

### ASCII-Schaltbild pro Sensor (3× identisch für Press / PushFront / PushRear)

```
  Initiator LJ8A3-2-Z/BX (NPN, 12 V)
  ┌──────────────────────┐
  │  braun  ──────────── │ ◄──── +12 V Versorgung
  │  blau   ──────────── │ ◄──── GND (gemeinsame Masse!)
  │  schwarz ─── Signal  │
  └──────────────┬───────┘
                 │
                 ●  Sensor inaktiv → ~12 V
                 │  Sensor aktiv (Metall vor Sensor) → 0 V (zieht auf GND)
                 │
                ┌┴┐
                │ │  R1 = 10 kΩ  (1/4 W reicht)
                │ │
                └┬┘
                 │
                 ●──────► A0 / A1 / A2 am Nano
                 │
                ┌┴┐
                │ │  R2 = 7,5 kΩ
                │ │
                └┬┘
                 │
                ─┴─  GND
```

> **Logik im Code:** `INIT_TRIGGERED_LEVEL = LOW`
> ([`firmware/nano/src/config.h`](../firmware/nano/src/config.h))
> Sensor "sieht" Metall → Output zieht auf GND → Spannungsteiler liefert 0 V → `digitalRead == LOW`.

### Für ESP32 (Übergangslösung, 3,3 V-Logik)

```
R1 = 10 kΩ, R2 = 3,9 kΩ
U_out = 12 V · 3,9 / 13,9 ≈ 3,37 V    ← innerhalb 3,3 V-Toleranz (max 3,6 V)
```

---

## 4. A4988 Schrittmotor-Treiber (NEMA 17)

```
                  ┌───────────────────────┐
       12 V ────► │ V_MOT          1B │───┐
                  │              ↓   1A │   ├─► NEMA 17 Spule A
                  │            ╔═════╗  │   │
                  │            ║  IC ║  │   ├─► NEMA 17 Spule B
                  │            ╚═════╝  │   │
                  │                2A │───┘
                  │                2B │
       Nano D2 ─► │ STEP                │
       Nano D3 ─► │ DIR                 │
       Nano D4 ─► │ EN  (LOW = aktiv)   │
                  │ MS1/MS2/MS3 ► offen │  ← Vollschritt; ggf. überbrücken für 1/8 oder 1/16
                  │ RESET ─┐            │
                  │ SLEEP ─┤  verbinden │  ← per Kabelbrücke beide HIGH
                  │        └─ V_DD 5 V  │
                  │ V_DD ───────────── │ ◄── 5 V Logik
                  │ GND ─────────────── │ ◄── GND
                  │ V_MOT GND ───────── │ ◄── GND (Sternpunkt!)
                  └───────────────────────┘
                         │
                       ║ ║  100 µF Elko
                       ║ ║  zwischen V_MOT + GND
                       ─ ─  PFLICHT, < 5 cm vom IC
                        │
                       GND
```

### Vref einstellen (vor erstem Anlauf!)

```
Vref-Poti am A4988 mit Multimeter messen (zwischen Poti-Mittenkontakt und GND)
Ziel: Vref = 0,7 ... 1,0 V

Strom pro Spule = Vref / (8 · R_sense)
NEMA 17 (1,5 A nominal): Vref ≈ 0,8 V → I ≈ 1,0 A
```

> **Sicherheits-Reihenfolge:** Erst Vref justieren, dann V_MOT 12 V einschalten,
> dann erst Logik 5 V. Sonst stirbt der Treiber.

---

## 5. L298N Mini-Modul (1,5 A je Kanal, ohne ENA/ENB)

> Verwendetes Modul: kompakte 6-Pin-Variante (V_S, GND, IN1–IN4) ohne ENA/ENB.
> Enable ist intern auf HIGH festverdrahtet. Drehzahl-Regelung läuft daher per
> PWM direkt auf den aktiven IN-Pin ("sign-magnitude PWM").

```
              ┌──────────────────────────────────┐
   12 V ────► │ +12 V                  Out 1 │──► DC-Motor Presse +
              │                        Out 2 │──► DC-Motor Presse −
              │                        Out 3 │──► DC-Motor Pusher +
              │                        Out 4 │──► DC-Motor Pusher −
              │                                  │
   D5 ──────► │ IN1   (PWM, Presse FWD)          │
   D7 ──────► │ IN2   (digital, Presse REV)      │
   D6 ──────► │ IN3   (PWM, Pusher FWD)          │
   D8 ──────► │ IN4   (digital, Pusher REV)      │
              │                                  │
              │ GND ──────────────────────────── │ ◄── GND Sternpunkt
              └──────────────────────────────────┘
                       │
                     ║ ║  470 µF Elko
                     ║ ║  an +12 V Eingang
                     ─ ─
                      │
                     GND
```

### Wahrheitstabelle (sign-magnitude PWM)

| IN_a (PWM-Pin) | IN_b (digital) | Verhalten |
|---|---|---|
| `analogWrite(x)` mit x > 0 | LOW | Motor vorwärts mit Drehzahl x/255 |
| 0 (LOW) | HIGH | Motor rückwärts mit voller Drehzahl |
| 0 (LOW) | LOW | Motor gebremst (kurzgeschlossen gegen GND) |
| HIGH (255) | HIGH | beide Brücken HIGH → Bremse gegen V_S |

> **Coast (Freilauf) gibt es nicht** mit dieser Beschaltung — der Enable-Eingang
> liegt intern fest auf HIGH. Stop = aktive Bremse.

> **D9 und D10 sind frei** (waren bei der Standard-L298N-Variante ENA/ENB).
> Können später für I²C-Display, zusätzliche Endschalter o. ä. genutzt werden,
> aber **PWM** ist auf D9/D10 nicht möglich, solange `Servo.h` läuft (Servo
> blockiert Timer1, der die PWM auf D9/D10 erzeugt).

---

## 6. Servo-Entkopplung

```
                              ╔═══════════════╗
   Buck 5 V ──────●──────────╣ VCC (rot)     ║
                  │           ║               ║
                ║ ║           ║   SG90 Servo  ║
                ║ ║ 470 µF    ║  (Hülsenschieber)║
                ─ ─           ║               ║
                  │           ║               ║
   GND ───────────●──────────╣ GND (braun)   ║
                              ║               ║
   Nano D11 ─────────────────╣ Signal (orange)║
                              ╚═══════════════╝
```

> Der **Elko direkt am Servo** (nicht erst am Buck) ist entscheidend — die kurze
> Stromspitze beim Servo-Anlauf bricht sonst die 5 V-Schiene ein und der Pi
> bootet neu.

---

## 7. Start-Taster (mechanisch, momentary)

```
                                    +5 V (intern)
                                       │
                                      ┌┴┐
                                      │ │  ~30 kΩ
                                      │ │  (interner
                                      │ │  Pull-up im
                                      │ │  ATmega328)
                                      └┬┘
                                       │
   Nano D12 ◄──────────────────────────●──────────● Taster Pin 1
                                                  │
                                                 ─┤   Drucktaster
                                                  │   (Schließer,
                                                 ─┤    momentary)
                                                  │
   Nano GND ──────────────────────────────────── ● Taster Pin 2
```

**Logik:**
- **Ungedrückt:** Pin-Eingang über internen Pull-up auf HIGH gezogen (~5 V).
- **Gedrückt:** Taster schließt → Eingang direkt an GND → LOW.
- `digitalRead(PIN_BUTTON) == LOW` → Taster ist gedrückt.

**Vorteile gegenüber TTP223:**
- robust gegen Tabakstaub und EMI von DC-Motoren
- kein zusätzliches Modul / keine Versorgungsleitung
- nur zwei Kabel (Signal + GND) statt drei

**Geeignete Bauarten:**
- Mini-Tactile-Tactile-Button auf Steckbrett (für Tests)
- Panel-Mount-Drucktaster 12 mm oder 16 mm (mit Verschraubung am Gehäuse)
- Pilzkopf-Taster mit Schließer-Kontakt (NICHT als Notaus verwenden — der hat
  einen Öffner und unterbricht 12 V hardwareseitig)

**Software-Entprellung:** Mechanische Taster prellen ~1–10 ms beim Schließen.
Konstante `BUTTON_DEBOUNCE_MS = 50` in [`config.h`](../firmware/nano/src/config.h)
ist als Vorgabe für künftiges Edge-Detection im Pi reserviert. Bei reinem
Status-Polling (alle 50 ms) ist Prellen meist unkritisch — die nächste Abfrage
sieht schon den stabilen Zustand.

---

## 8. Notaus + Sicherungen (Hardware-seitig, geplant)

```mermaid
flowchart LR
    PSU["12 V Netzteil"] --> F1["F1<br/>5 A T<br/>Hauptsicherung"]
    F1 --> SW["Pilzkopf<br/>NOTAUS<br/>Oeffner-Kontakt"]
    SW -->|12 V Motor-Schiene| LOAD["L298N + A4988<br/>+ Initiatoren ueber F3"]

    F1 -.->|12 V Logik-Schiene<br/>wird NICHT unterbrochen| F2["F2<br/>1 A T"]
    F2 --> BUCK["Buck-Konverter<br/>5 V Pi/Servo/Nano"]
    BUCK --> NANO["Nano detektiert<br/>via Watchdog-Timeout<br/>oder dedizierten GPIO"]

    classDef warn fill:#ffcccc,stroke:#cc0000,stroke-width:2px;
    classDef fuse fill:#ffe0e0,stroke:#cc0000,stroke-width:2px;
    class SW warn;
    class F1,F2 fuse;
```

### Reihenfolge der Schutzelemente

```
PSU ──► [F1 Hauptsicherung] ──┬──► [NOTAUS-Schalter] ──► Motor-12V (L298N, A4988, F3→Initiatoren)
                              │
                              └──► [F2] ──► Buck → 5V (Pi, Servo, Nano-Logik)
```

| Element | Schützt gegen | Was passiert beim Auslösen |
|---|---|---|
| **F1** | Kurzschluss / Defekt irgendwo im 12 V-Bus | Maschine **komplett** stromlos (auch Pi) |
| **NOTAUS** | bewusst durch Bediener | nur Motorseite stromlos; Pi/Nano laufen weiter, melden Notaus-Zustand |
| **F2** | Kurzschluss im Buck oder Pi/Servo/Nano | Logikseite aus, Motorseite läuft theoretisch weiter — aber Watchdog im Nano triggert nach 5 s "alle Motoren aus", weil der Pi nicht mehr antwortet |
| **F3** | Verdrahtungsfehler an Initiatoren (z. B. 12 V auf Signal-Eingang) | Sensoren tot, Stopfsequenz pausiert; Motoren bleiben an, müssen vom Pi kontrolliert gestoppt werden |

> Wichtig: Notaus unterbricht **nur die 12 V-Motorschiene**, nicht die 5 V-Logik.
> So bleibt der Pi an, kann den Notaus-Zustand loggen und die App informieren.
> Der Nano merkt am Wegfall der INIT-Signale (12 V weg) bzw. am Watchdog (5 s
> kein Pi-Befehl wird ohnehin ausgewertet).
>
> **F1 sitzt VOR dem Notaus**, damit auch bei verschweißtem Notaus-Kontakt
> (Worst Case) noch ein Schutz greift.

---

## Verwandte Dokumente

- [`pinout.md`](pinout.md) — vollständige Pin-zu-Bauteil-Tabelle
- [`protocol.md`](protocol.md) — Serial-Befehle Pi ↔ Nano
- [`../CLAUDE.md`](../CLAUDE.md) — Projektkontext & Materialliste
- [`../firmware/nano/src/pins.h`](../firmware/nano/src/pins.h) — Pin-Defines im Code
