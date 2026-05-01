# Pinout & Verdrahtungstabelle

Vollständige Belegung aller Pins mit Kabelfarben und Zielbauteil.
Quelle der Pin-Nummern: [`firmware/nano/src/pins.h`](../firmware/nano/src/pins.h).

---

## Arduino Nano (final)

### Digitale Pins

| Pin | `pins.h`-Konstante | Funktion | Ziel | Kabelfarbe (Vorschlag) | Anmerkung |
|---|---|---|---|---|---|
| D2 | `PIN_STEPPER_STEP` | Step-Impuls | A4988 STEP | gelb | jeder steigende Flanke = 1 Step |
| D3 | `PIN_STEPPER_DIR` | Richtung | A4988 DIR | grün | HIGH/LOW = Drehrichtung |
| D4 | `PIN_STEPPER_EN` | Enable | A4988 EN | weiß | **LOW = Treiber aktiv** (invertiert!) |
| D5 | `PIN_PRESS_IN1` | Presse FWD (drehzahlgeregelt) | L298N IN1 | orange | **PWM** Timer0, sign-magnitude |
| D6 | `PIN_PUSHER_IN3` | Pusher FWD (drehzahlgeregelt) | L298N IN3 | violett | **PWM** Timer0, sign-magnitude |
| D7 | `PIN_PRESS_IN2` | Presse REV (volle Drehzahl) | L298N IN2 | rot | digital, nur HIGH/LOW |
| D8 | `PIN_PUSHER_IN4` | Pusher REV (volle Drehzahl) | L298N IN4 | blau | digital, nur HIGH/LOW |
| D9 | – frei – | (war ENA) | – | – | Reserve, Servo-Lib blockiert PWM |
| D10 | – frei – | (war ENB) | – | – | Reserve, Servo-Lib blockiert PWM |
| D11 | `PIN_SERVO` | Servo-Signal | SG90 (orange Litze) | orange | **PWM** (Servo-Library) |
| D12 | `PIN_BUTTON` | Start-Taster | mechanischer Drucktaster | grau | **active LOW** (Pull-up intern) |
| D13 | `PIN_STATUS_LED` | Status-LED | onboard LED | – | leuchtet während aktiver Befehl |

### Analoge Pins (nutzbar als digital, hier teils analog)

| Pin | `pins.h`-Konstante | Funktion | Ziel | Verdrahtung | Anmerkung |
|---|---|---|---|---|---|
| A0 | `PIN_INIT_PRESS` | Initiator Press | LJ8A3-2-Z/BX (schwarz) | über 10 k + 7,5 k Spannungsteiler | active LOW |
| A1 | `PIN_INIT_PUSH_FRONT` | Initiator Pusher vorne | LJ8A3-2-Z/BX (schwarz) | über 10 k + 7,5 k | active LOW |
| A2 | `PIN_INIT_PUSH_REAR` | Initiator Pusher hinten | LJ8A3-2-Z/BX (schwarz) | über 10 k + 7,5 k | active LOW |
| A3 | `PIN_RESERVE_A3` | Reserve | – | – | z. B. I²C SDA für Display |
| A4 | `PIN_RESERVE_A4` | Reserve | – | – | z. B. I²C SCL für Display |
| A5 | `PIN_MAGAZIN_SENSOR` | Magazin-Optosensor | Oniissy Gabellichtschranke | direkt 5 V-Logik | für später |

### Versorgungs-Pins

| Pin | Verbindung | Anmerkung |
|---|---|---|
| **VIN** | – nicht verwenden | Nano wird über USB vom Pi versorgt |
| **5V** | optional kleine Verbraucher (Start-Taster braucht NICHT, Buck-Out hat eigene 5 V) | max. 500 mA aus dem Nano-Regler |
| **3V3** | – nicht verwenden | für 3,3 V-Sensoren reserviert |
| **GND** (mehrfach) | **Sternpunkt am Netzteil** | 1× direkt zum Power-GND, 1× zum Pi |

---

## L298N Mini-Modul (Doppel-DC-Motortreiber, 1,5 A je Kanal)

> Das verwendete Mini-Modul hat **kein ENA/ENB**. Enable ist intern dauerhaft
> aktiviert. Drehzahl-Regelung läuft per PWM auf den IN-Pins
> ("sign-magnitude PWM").

| L298N-Pin | Verbindung | Anmerkung |
|---|---|---|
| V_S (12 V) | 12 V Netzteil + 470 µF Elko | Motor-Versorgung |
| GND | GND-Sternpunkt | |
| +5 V | – nicht abgreifen für Pi/Servo | wird vom Modul selbst nicht herausgeführt oder fällt unter Last ein |
| IN1 | Nano **D5 (PWM)** | Presse vorwärts (drehzahlgeregelt) |
| IN2 | Nano **D7 (digital)** | Presse rückwärts (volle Drehzahl) |
| IN3 | Nano **D6 (PWM)** | Pusher vorwärts (drehzahlgeregelt) |
| IN4 | Nano **D8 (digital)** | Pusher rückwärts (volle Drehzahl) |
| OUT1/OUT2 | DC-Motor Presse | Polarität egal, ggf. tauschen für Drehrichtung |
| OUT3/OUT4 | DC-Motor Pusher | dito |

### PWM-Logik ("sign-magnitude")

| Aktion | IN_a (PWM-Pin) | IN_b (digital) |
|---|---|---|
| Vorwärts mit Drehzahl x | `analogWrite(x)` | `LOW` |
| Rückwärts (volle Drehzahl) | `0` (LOW) | `HIGH` |
| Stop / Bremse | `0` (LOW) | `LOW` |

> Coast (Freilauf) ist mit dieser Beschaltung nicht möglich, weil Enable intern fix
> auf HIGH liegt. Stop = aktive Bremse durch Kurzschluss gegen GND.

---

## A4988 Schrittmotor-Treiber

| A4988-Pin | Verbindung | Anmerkung |
|---|---|---|
| V_MOT | 12 V + 100 µF Elko | **Pflicht!** Elko < 5 cm vom IC |
| GND (Motor) | GND-Sternpunkt | |
| V_DD | 5 V (vom Nano oder Buck) | Logik-Versorgung |
| GND (Logik) | GND-Sternpunkt | |
| STEP | Nano D2 | |
| DIR | Nano D3 | |
| EN | Nano D4 | LOW = aktiv |
| RESET | mit SLEEP brücken | beide HIGH = Treiber an |
| SLEEP | mit RESET brücken | |
| MS1/MS2/MS3 | offen lassen | Vollschritt; für Microstepping nach Bedarf |
| 1A / 1B | NEMA 17 Spule A | (meist schwarz/grün) |
| 2A / 2B | NEMA 17 Spule B | (meist rot/blau) |
| **Vref-Poti** | mit Multimeter messen | **0,7 ... 1,0 V** vor erstem Anlauf |

---

## NEMA 17 Schrittmotor

Standard-Belegung (variiert pro Hersteller — mit Multimeter durchklingeln!):

| Litzenfarbe (typisch) | Spule | Anschluss |
|---|---|---|
| schwarz | A | A4988 1A |
| grün | A | A4988 1B |
| rot | B | A4988 2A |
| blau | B | A4988 2B |

---

## SG90 Servo

| Litzenfarbe | Funktion | Anschluss |
|---|---|---|
| rot | VCC 5 V | Buck-Out + 470 µF Elko |
| braun / schwarz | GND | GND-Sternpunkt |
| orange / gelb | Signal (PWM) | Nano D11 |

---

## Initiatoren LJ8A3-2-Z/BX (3 Stück)

| Litzenfarbe | Funktion | Anschluss |
|---|---|---|
| braun | +12 V | 12 V Bus |
| blau | GND | GND-Sternpunkt |
| schwarz | Signal (NPN, 12 V active LOW) | Spannungsteiler 10 k + 7,5 k → A0 / A1 / A2 |

---

## Start-Taster (mechanisch, momentary)

Z. B. Tactile Push-Button (Mini), Panel-Mount-Taster mit 12 mm oder 16 mm Loch,
oder Pilzkopf-Taster (Pflicht-Schließer für Start, NICHT Notaus!).

| Taster-Pin | Anschluss | Anmerkung |
|---|---|---|
| Pin 1 (eines der zwei Kontakte) | Nano **D12** | Signal mit internem Pull-up |
| Pin 2 (der andere Kontakt) | **GND** | gemeinsame Masse |

Bei 4-Pin-Tactile-Buttons: zwei diagonale Pins nutzen (1+3 oder 2+4).
Die anderen beiden sind intern mit ihrem Diagonalpartner verbunden.

> **Logik:** Pin-Modus `INPUT_PULLUP`. Ungedrückt = HIGH (intern hochgezogen),
> gedrückt = LOW (Taster zieht gegen GND). Das `status`-Feld `button=1` bedeutet
> "Taster wird gerade gedrückt". Kein externer Pull-up und kein Vorwiderstand
> nötig — interne 20–50 kΩ vom ATmega328 reichen.

---

## Raspberry Pi Zero 2 W (Brain)

| Pi-Pin | Funktion | Anschluss |
|---|---|---|
| Pin 2 (5 V) | Versorgung **rein** | Buck-Out 5 V (≥ 3 A) |
| Pin 6 (GND) | GND | GND-Sternpunkt |
| – | USB-A oder Micro-USB-OTG | → Arduino Nano (Daten + 5 V Versorgung des Nano) |
| Pin 8 (TX) / Pin 10 (RX) | optional: UART zum Nano | falls USB nicht genutzt — mit Pegelwandler! |

> **Pi NICHT über Micro-USB-Power speisen** (Polyfuse begrenzt → Brownout unter Last).
> 5 V immer über GPIO Pin 2 einspeisen, Buck vorher auf 5,0 V justieren.

---

## ESP-WROOM-32 (Übergangslösung, parallel dokumentiert)

> Solange der Buck-Konverter noch nicht da ist, kann ein ESP32 als Single-Board-
> Controller alle Funktionen übernehmen. Pin-Mapping ist bewusst anders, weil
> manche ESP32-Pins Boot-Strapping-Pins oder input-only sind.

| Funktion | ESP32 GPIO | Anmerkung |
|---|---|---|
| A4988 STEP | GPIO 25 | |
| A4988 DIR | GPIO 26 | |
| A4988 EN | GPIO 27 | |
| L298N IN1 | GPIO 14 | |
| L298N IN2 | GPIO 12 | ⚠️ Boot-Strapping |
| L298N IN3 | GPIO 13 | |
| L298N IN4 | GPIO 32 | |
| L298N ENA | GPIO 33 | PWM |
| L298N ENB | GPIO 4 | PWM |
| Servo | GPIO 19 | PWM (LEDC-Kanal) |
| Start-Taster | GPIO 21 | INPUT_PULLUP, active LOW |
| Initiator Press | GPIO 34 | ⚠️ input-only, kein Pull-Up |
| Initiator PushFront | GPIO 35 | ⚠️ input-only |
| Initiator PushRear | GPIO 36 | ⚠️ input-only |
| Magazin-Sensor | GPIO 39 | ⚠️ input-only |

⚠️ **Spannungsteiler für ESP32:** 10 kΩ + **3,9 kΩ** (nicht 7,5 kΩ wie beim Nano).
   U_out = 12 V · 3,9/13,9 ≈ 3,37 V — innerhalb 3,3 V-Toleranz.

⚠️ **Boot-Strapping-Pins** (GPIO 0, 2, 5, 12, 15) nur mit Bedacht nutzen — falsche
   Pegel beim Reset verhindern den Boot.

---

## Elektrolytkondensatoren (Bestellliste)

Zentrale Pufferkondensatoren — alle 105 °C, radial THT.

| Position | Kapazität | Spannung | Typ | Anzahl | Begründung |
|---|---|---|---|---|---|
| **A4988 V_MOT** | ≥ 100 µF (220 µF besser) | **≥ 25 V** | **Low ESR** Pflicht | 1× | Schaltet 500 kHz, Standard-Elkos zu lahm |
| **L298N V_S** | ≥ 470 µF (1000 µF besser) | **≥ 25 V** | Standard reicht | 1× | DC-Motor-Anlaufstrom puffern |
| **Servo VCC** | ≥ 470 µF (bis 2200 µF) | ≥ 10 V (16 V/25 V auch ok) | Standard | 1× | Servo-Anlaufstrom 0,5–1 A |
| **Buck-Ausgang Bulk** (optional) | 470–1000 µF | ≥ 10 V | Standard | 1× | nur falls Pi und Servo räumlich weit auseinander |

> ⚠️ **Niemals 16 V-Elkos im 12 V-Pfad!** Headroom 33 % ist zu knapp gegen
> Spannungsspikes von Motoren — Elko explodiert, Treiber stirbt mit. Mindestens
> 25 V im 12 V-Pfad. Im 5 V-Pfad sind 10 V/16 V/25 V alle okay (alle ≥ 2× U_op).

### Konkret zum Bestellen

| Bauteil | Quelle | Preis |
|---|---|---|
| Panasonic FC 100 µF/35 V (low ESR) | Reichelt: "FC 100/35" | ~0,40 € |
| Panasonic FC 470 µF/35 V (low ESR) | Reichelt: "FC 470/35" | ~0,80 € |
| Standard 470 µF/25 V/105 °C | Reichelt: "RAD 470/25" | ~0,30 € |
| Standard 1000 µF/35 V/105 °C | Reichelt: "RAD 1000/35" | ~0,80 € |

### Optionale Schutzbauteile

| Bauteil | Wert | Anzahl | Position |
|---|---|---|---|
| Schottky-Flyback-Diode | 1N5819 (1 A, 40 V) | 8× | je 4 pro DC-Motor an L298N-Ausgängen |

---

## Spannungsteiler für Initiatoren (Bestellliste)

Pro Sensor-Eingang (3× für Press / PushFront / PushRear):

| Bauteil | Wert | Anzahl | Bauform | Anmerkung |
|---|---|---|---|---|
| R1 | 10 kΩ, 5 %, 1/4 W | 3× (+ Reserve) | THT 0207 | Standard-Kohleschicht |
| R2 (Nano) | 7,5 kΩ, 5 %, 1/4 W | 3× | THT 0207 | für 5 V-Logik |
| R2 (ESP32) | 3,9 kΩ, 5 %, 1/4 W | 3× | THT 0207 | für 3,3 V-Logik |
| C (Filter) | 47 nF Keramik | 3× | X7R, 50 V | parallel zu R2, EMV-Filter |

Optionale Pull-up-Bestückung **falls** der Sensor im Leerlauf < 10 V auf Schwarz zeigt:

| Bauteil | Wert | Anzahl | Anmerkung |
|---|---|---|---|
| R_pullup | 4,7 kΩ, 1/4 W | 3× | von "schwarz" nach +12 V, **nur wenn nötig** |

> Vor dem Anschluss am Nano: Test-Checkliste in [`wiring.md` § 3](wiring.md#3-initiator-spannungsteiler-kritisch) durchgehen.

---

## Sicherungen (Bestellliste)

Alle 5×20 mm Glas-Schmelzsicherungen, in Schraubklemmen-Halter
(z. B. Stelvio Kontek PTF/30 oder beliebiger Würth/Schurter-Halter).

| Position | Wert | Charakteristik | Schützt | Halter-Typ |
|---|---|---|---|---|
| **F1** Hauptsicherung 12 V | 5 A | T (träge) | gesamten 12 V-Bus, Verkabelung | Schraubklemme, Panel-mount |
| **F2** Buck-Eingang | 1 A | T (träge) | Pi + Servo + Nano-Logik | Schraubklemme, inline |
| **F3** Initiator-Schiene | 500 mA | F (flink) | Sensor-Verkabelung | Schraubklemme, inline |

> **Glas, nicht Keramik:** bei 12 V DC reicht Glas (Lichtbogen erlischt von selbst).
> Keramische HBC-Sicherungen sind erst bei 230 V AC-Netzseite oder bei Bleibatterie/LiPo-
> Versorgung mit > 100 A Kurzschlussstrom Pflicht. Details in [`wiring.md` § 1](wiring.md#1-stromversorgung-power-distribution).

> **Reserve mitbestellen:** je Wert mind. 5 Stück, sind günstig (~0,30 €/Stück).

---

## GND-Sternpunkt (★ kritisch ★)

Alle GNDs an **einem Punkt** zusammenführen, am besten direkt an der GND-Klemme
des 12 V-Netzteils. Sterntopologie verhindert Masseschleifen und Spannungs-
abfall-Probleme bei pulsenden Lasten (Schrittmotor, DC-Motor).

```
                  Netzteil GND (Sternpunkt)
                         │
     ┌──────┬──────┬─────┼──────┬───────┬───────┐
     │      │      │     │      │       │       │
   Pi GND  Nano  Buck  L298N  A4988  Servo   Initiatoren
                  GND   GND    GND    GND      (alle 3, blau)
```

---

## Verwandte Dokumente

- [`wiring.md`](wiring.md) — Schaltpläne und Spannungsteiler-Details
- [`protocol.md`](protocol.md) — Serial-Befehle Pi ↔ Nano
- [`../firmware/nano/src/pins.h`](../firmware/nano/src/pins.h) — Pin-Defines im Code
- [`../firmware/nano/src/config.h`](../firmware/nano/src/config.h) — Konstanten (Speeds, Timeouts)
