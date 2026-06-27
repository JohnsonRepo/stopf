# MOSFET-Treiber — 3. DC-Motor & Solenoide

Leitfaden zur Frage: *„Passen MOSFETs an den Arduino, und wie stelle ich für
einen aufgeräumteren Aufbau auf ein MOSFET-Board um?"*

> **Quelle der Wahrheit für Pin-Nummern:** [`../firmware/nano/src/pins.h`](../firmware/nano/src/pins.h)
> **Verwandt:** [`wiring.md`](wiring.md) · [`pinout.md`](pinout.md)

---

## 1. Ausgangslage (was sich geändert hat)

| Last | Vorher | Jetzt |
|---|---|---|
| Presse + Pusher (DC, reversierend) | L298N #1 (Standard) | L298N #1 (Standard) — unverändert |
| 2× Heschen HS-0530B Solenoid | L298N-**Mini** | **L298N #2 (Standard)** — Mini hat die Halteströme nicht überlebt |
| **3. DC-Motor (unidirektional, NEU)** | – | **braucht eigenen Treiber** |
| Vibrationsmotor | geplant | **entfällt** |

Daraus folgen zwei Aufgaben: (a) einen Treiber für den neuen 3. Motor finden,
(b) optional den Aufbau „ordentlicher" machen, indem die EIN/AUS-Lasten von den
sperrigen L298N auf ein kompaktes MOSFET-Board wandern.

---

## 2. Passt ein MOSFET an den Arduino?

**Ja — aber mit zwei Bedingungen:**

1. **Logic-Level-Typ.** Der Nano gibt am Pin nur **5 V** aus, der ESP32 sogar nur
   **3,3 V**. Ein klassischer MOSFET (z. B. **IRF520**, auch auf vielen blauen
   „MOSFET-Modulen") braucht ~10 V am Gate, um voll durchzusteuern → bei 5 V ist
   er nur halb offen, wird heiß, verheizt Spannung. **Logic-Level-FET nehmen**
   (das „L" im Namen): **IRLZ44N, IRL540N, IRLB8721, AOD4184**.
2. **Ein MOSFET schaltet nur in EINE Richtung** (Low-Side-Schalter, EIN/AUS bzw.
   PWM). Er kann **die Drehrichtung nicht umkehren** — dafür braucht es eine
   H-Brücke. Heißt:

| Last | Richtung? | MOSFET geeignet? |
|---|---|---|
| 2× Hubmagnet (Solenoid) | nur EIN/AUS | ✅ ideal |
| **3. DC-Motor** | **nur eine Richtung** | ✅ **ideal** (PWM aufs Gate = Drehzahl) |
| Presse / Pusher | reversierend | ❌ → H-Brücke (L298N o. ä.) |

### Logic-Level-MOSFETs im Vergleich

| Typ | V_GS(th) | R_DS(on) @ 5 V | Strom | Hinweis |
|---|---|---|---|---|
| **IRLZ44N** ← Default | 1–2 V | ~22 mΩ | 47 A | Klassiker, billig, TO-220 |
| IRL540N | 1–2 V | ~44 mΩ | 28 A | gut verfügbar |
| IRLB8721 | 1–2,5 V | ~8 mΩ | 62 A | sehr niederohmig |
| AOD4184 | 1–2 V | ~5 mΩ | 50 A | meist auf 4-Kanal-Modulen verbaut |
| ❌ IRF520 | **4 V** | nicht spezifiziert @ 5 V | – | **kein Logic-Level — meiden** |

---

## 3. Gate-Beschaltung (Pflicht, sonst läuft's unsauber)

```
   Arduino-Pin ──[ R_gate 150–220 Ω ]──●── Gate
                                        │
                                       ┌┴┐ R_pulldown
                                       │ │ 10 kΩ
                                       └┬┘
                                        │
   Last(+) ── 12 V                     GND
   Last(−) ── Drain
   Source  ── GND (gemeinsamer Sternpunkt!)

        +12 V ──────────●──────────── Last(+)
                        │
                       ─┴─  Flyback-Diode 1N5819
                        ▲   Kathode an +12 V
                       ─┬─  Anode an Drain/Last(−)
                        │
        Drain ──────────●──────────── Last(−)
```

| Bauteil | Wert | Warum |
|---|---|---|
| **R_gate** (Reihe) | 150–220 Ω | begrenzt Gate-Einschaltstrom, schont den µC-Pin |
| **R_pulldown** (Gate→GND) | 10 kΩ | hält die Last **AUS** während Boot/Reset des µC — sonst zuckt Magnet/Motor beim Einschalten |
| **Flyback-Diode** | 1N5819 (Schottky) oder 1N4007 | fängt die Induktionsspitze beim Abschalten ab — **Pflicht** bei Spule *und* Motor |
| **gemeinsames GND** | Source an Sternpunkt | ohne gemeinsame Masse schaltet das Gate nicht zuverlässig |

> Fertige 1-/4-Kanal-MOSFET-Boards haben R_gate + R_pulldown (+ Status-LED) meist
> schon bestückt. **Flyback-Dioden fehlen dort oft** → bei Spule/Motor selbst
> nachrüsten (1N5819 direkt an der Last).

---

## 4. Der 3. DC-Motor → einzelner MOSFET

Unidirektional = **keine H-Brücke nötig**. Ein einzelner Logic-Level-MOSFET als
Low-Side-Schalter ist die einfachste und sauberste Lösung. PWM aufs Gate →
Drehzahl gratis.

```
   12 V ──────────●──────────── Motor(+)
                  │
                 ─┴─ 1N5819 (Flyback)
                  ▲
                 ─┬─
                  │
   Motor(−) ──────●──── Drain ┐
                             [Q]  IRLZ44N
   µC-PWM ─[220Ω]─●─ Gate ────┘
                  │
                 [10k]
                  │
   GND ───────────●──── Source ──── GND-Sternpunkt
```

Anlaufstrom des Motors beachten: IRLZ44N (47 A) hat massig Reserve, bleibt kalt.
Bei > ~5 A Dauerstrom kleines Kühlblech, sonst nicht nötig.

---

## 5. Solenoide → MOSFET löst genau das Halteström-Problem

Dass das L298N-Mini an den Solenoid-Strömen gestorben ist, ist **thermisch** —
und genau dagegen ist ein MOSFET immun:

| Treiber | Drop @ 0,5 A | Verlustwärme/Kanal | Folge |
|---|---|---|---|
| L298N-Mini | ~2,5 V | **~1,25 W** | kocht → ausgefallen |
| L298N Standard | ~2,5 V | ~1,25 W | überlebt dank Kühlkörper, aber heiß + nur ~9,5 V am Magnet |
| **IRLZ44N** | ~11 mV | **~5 mW** | bleibt eiskalt, volle 12 V am Magnet |

### ⚠️ Nicht nur der Treiber — auch die Spule

Die **Heschen HS-0530B** sind **intermittent duty** (kurze Pulse, nicht Dauer-ON,
siehe [`pinout.md`](pinout.md)). Dauerhaltung kocht irgendwann die **Spule**
selbst, egal wie kühl der Treiber bleibt.

**Lösung, die ein MOSFET geschenkt mitbringt — Pick-and-Hold:**
voller Strom zum Anziehen (~50–100 ms), dann per **PWM auf ~30–50 % runter** zum
Halten. Spart Wärme in Spule *und* Treiber. Genau das kann ein MOSFET nativ, ein
L298N/ULN nicht sauber. (Deshalb hier **kein** ULN2803: bei 0,5 A Dauerhalten
thermisch grenzwertig.)

> Der bestehende Knock-Zyklus (`KNOCK_CYCLES=8`, `SOL_PULSE_MS=50`,
> `SOL_PAUSE_MS=100` in [`config.h`](../firmware/nano/src/config.h)) ist schon
> gepulst → unkritisch. Pick-and-Hold lohnt nur, falls ein Magnet länger halten
> soll.

---

## 6. Saubere Topologie: ein 4-Kanal-MOSFET-Board

Statt zweitem L298N + Einzel-FETs: **ein** Logic-Level-4-Kanal-Board
(IRLZ44N- oder AOD4184-basiert, „4-channel high-power MOSFET trigger switch",
~5–8 €) für alle EIN/AUS-/Eine-Richtung-Lasten:

```
   ┌──────────────── 4-Kanal-MOSFET-Board ────────────────┐
   │  Logik 3,3–5 V kompatibel · Schraubklemmen · LED/Kanal │
   ├───────────┬───────────┬───────────┬───────────────────┤
   │  Kanal 1  │  Kanal 2  │  Kanal 3  │  Kanal 4          │
   │ Solenoid#1│ Solenoid#2│ 3. Motor  │ Reserve           │
   │ Front-Knock  Top-Druck   (PWM)                         │
   └───────────┴───────────┴───────────┴───────────────────┘
        ▲           ▲           ▲
     PIN_SOL_FRONT PIN_SOL_TOP  (neuer Motor-Pin)
```

**Vorteile:**
- Das Standard-L298N #2 wird **komplett frei** (Reserve oder Rückbau).
- Alle EIN/AUS-Lasten auf **einem** kompakten Board statt zwei sperrigen L298N.
- Pin-Namen im Code bleiben: `PIN_SOL_FRONT`/`PIN_SOL_TOP` gehen direkt aufs Gate.
- Volle 12 V an den Magneten (keine ~2,5 V L298N-Verluste mehr).

⚠️ **Flyback-Diode (1N5819) pro induktiver Last selbst nachrüsten** — diese
Boards haben sie meist nicht.

---

## 7. Der echte Engpass: Pins

### Arduino Nano — kein freier PWM-Pin

Der Nano ist in [`pins.h`](../firmware/nano/src/pins.h) **voll** belegt. Für PWM
gibt es auf dem ATmega328 nur **D3, D5, D6, D9, D10, D11** — und die sind alle weg:

| PWM-Pin | belegt mit |
|---|---|
| D3 | A4988 DIR |
| D5 | L298N ENA (Presse) |
| D6 | L298N ENB (Pusher) |
| D9 | L298N IN3 (Pusher) |
| D10 | L298N IN4 (Pusher) |
| D11 | Servo Hülsen-Schieber |

→ **Drehzahl-Regelung (PWM) für den 3. Motor ist am Nano nicht möglich**, ohne
einer bestehenden Funktion das PWM zu nehmen. **Nur EIN/AUS** ginge über den
einzigen verbleibbaren Digital-Pin **A5** — der ist aktuell der Magazin-Sensor
(noch nicht implementiert), müsste also weichen. (A6/A7 sind input-only und
können kein Gate treiben.)

### ESP-WROOM-32 — die saubere Heimat

Der ESP32 hat reichlich freie GPIOs und macht PWM per LEDC auf fast jedem Pin.
Hier passt der 3. Motor **plus** die ohnehin noch fehlenden Solenoide/Tabak-Servo
problemlos rein. Vorschlag (siehe auch [`pinout.md`](pinout.md)):

| Funktion | ESP32 GPIO | Anmerkung |
|---|---|---|
| Tabak-Servo | GPIO 18 | LEDC, fehlte bisher im ESP32-Map |
| Solenoid #1 (Front-Knock) → MOSFET K1 | GPIO 17 | EIN/AUS bzw. Pick-and-Hold-PWM |
| Solenoid #2 (Top-Druck) → MOSFET K2 | GPIO 16 | dito |
| **3. Motor → MOSFET K3** | **GPIO 23** | **LEDC-PWM (Drehzahl)** |
| MOSFET K4 | – | Reserve |

> Sichere Output-Pins, keine Strapping-Pins (0/2/5/12/15) und keine
> Flash-Pins (6–11). Beim ESP32 Gate-Vorwiderstand wie gehabt; Logic-Level-FET
> ist hier wegen 3,3 V **doppelt** wichtig.

### Empfehlung

- **Jetzt (ESP32-Übergang):** 3. Motor + Solenoide aufs 4-Kanal-MOSFET-Board,
  Gates an die obigen GPIOs. PWM-Drehzahl inklusive.
- **Final (Nano):** wenn der 3. Motor nur EIN/AUS sein darf → A5 umwidmen
  (Magazin-Sensor verschiebt sich auf ESP32/Portexpander). Soll er
  drehzahlgeregelt sein → führt am ESP32 oder einem I²C-PWM-Treiber (PCA9685)
  kaum vorbei, weil der Nano keinen PWM-Pin mehr frei hat.

---

## 8. Bauteilliste

| Bauteil | Wert/Typ | Anzahl | Quelle ca. |
|---|---|---|---|
| 4-Kanal-MOSFET-Board (Logic-Level) | IRLZ44N / AOD4184 | 1× | Amazon ~5–8 € |
| *oder* Einzel-MOSFET | IRLZ44N (TO-220) | 1–3× | Reichelt ~0,50 €/St. |
| Gate-Vorwiderstand | 150–220 Ω, 1/4 W | je Kanal | – |
| Gate-Pulldown | 10 kΩ, 1/4 W | je Kanal | – |
| Flyback-Diode | 1N5819 (1 A, 40 V) | je induktive Last | ~5 ct/St. |
| (optional) Bulk-Elko 12 V | 470 µF / ≥ 25 V | 1× | – |

> Einzel-MOSFET nur nötig, wenn du **nicht** das fertige Board nimmst — dann
> R_gate + R_pulldown selbst setzen. Das Board hat beides drauf.
