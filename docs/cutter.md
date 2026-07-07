# Spitzen-Cutter (Servo-Guillotine)

Schneidet die **locker gestopfte Zigarettenspitze** nach dem Stopfen ab.
Prinzip wie in der Industrie: leicht überstopfen, dann die lockere Zone sauber
abtrennen — übrig bleibt eine feste, gleichmäßige Spitze.

> **Firmware:** Step 11 (`STEP_CUT`) + Manual-Befehl `cut`, ab v0.5.0
> **Pins:** Servo-Signal auf **A3** (`PIN_CUT_SERVO`, [`pins.h`](../firmware/nano/src/pins.h))
> **Params:** `cut_home` / `cut_cut` / `cut_dwell_ms` (EEPROM, live tunbar)

---

## 0. Vorab: Ursache tunen, bevor Mechanik gebaut wird

Lockere Spitzen entstehen, wenn der Tabakpfropfen das Hülsenende nicht erreicht
oder zurückfedert. Diese drei Stellschrauben sind kostenlos und reduzieren das
Problem oft deutlich (ersetzen den Cutter aber meist nicht ganz):

| Stellschraube | Wirkung |
|---|---|
| `set knock_cycles 12` (statt 8) | mehr Tabak pro Portion → längerer Pfropfen |
| `set press_pwm 230` / längeres Pressen | dichterer Pfropfen, weniger Rückfederung |
| Initiator **Push-Front (A1)** weiter nach vorn justieren | Pusher schiebt den Tabak näher ans Hülsenende |

Der Cutter bleibt der robuste Fix: Er macht das Ergebnis **unabhängig** von
Tabaksorte, Feuchtigkeit und Dosierstreuung.

---

## 1. Wie schneidet man Zigarettenspitzen sauber? (Grundlagen)

Vier Regeln entscheiden über die Schnittqualität:

1. **Scharfe, dünne Klinge — als Wechselteil.** Standard-Rasierklinge
   (Doppelklinge halbiert) oder ein Abbrechklingen-Segment (9 mm Cutter).
   Tabak enthält Silikate und stumpft Klingen erstaunlich schnell ab —
   die Klinge muss **ohne Demontage der Mechanik wechselbar** sein
   (Klemmhalter mit einer M3-Schraube).

2. **Stützung direkt neben der Schnittstelle.** Die Zigarette liegt in einer
   **engen Buchse (Bohrung 8,2–8,4 mm)**, die Klinge läuft durch einen
   **schmalen Querschlitz (1–1,5 mm)**. Das Papier wird so beidseitig ≤ 1 mm
   neben dem Schnitt gestützt. Ohne Stützung knickt die Hülse ein oder das
   Papier reißt, statt geschnitten zu werden — das ist der häufigste Fehler.

3. **Schnell und entschlossen schneiden, leicht ziehend.** Ein zügiger Hub
   quetscht nicht; langsames Drücken staucht die Hülse oval. Die Klinge
   **10–20° angestellt** montieren, dann trifft die Schneide schräg auf
   (ziehender Schnitt wie beim Brotmesser) — deutlich sauberer als ein
   90°-Hackschnitt.

4. **An der richtigen Stelle schneiden:** **3–6 mm vom Hülsenende**, also in
   der lockeren Zone. Die Position wird über die Lage der Stützbuchse
   eingestellt, nicht über den Servo — der Servo bestimmt nur oben/unten.

**Verworfene Alternativen** (für die Nachwelt):
- *Rotierender Schnitt* (Zigarre-Cutter-Prinzip): sauberster Schnitt, aber
  braucht Rotation von Klinge oder Zigarette → zu viel Mechanik.
- *Feststehende Klinge an der Trommel*: null Elektronik, aber Schnittqualität
  hängt komplett von Klingenposition/Trommelgeschwindigkeit ab, kaum tunbar.
- *Solenoid-Guillotine*: Heschen HS-0530B hat nur ~5 mm Hub — zu wenig für
  8 mm Zigarette + Anfahrweg.

---

## 2. Mechanik (Servo-Guillotine)

```
        SG90 (A3)
         ┌────┐
         │    │ Hebel ~15 mm
         └──┬─┘
            │        Klingenträger (PMMA GS 4 mm, läuft in Nut-Führung)
        ┌───▼────┐
        │ ▓▓▓▓▓▓ │  ← Rasierklinge, 10–20° angestellt, M3-Klemmung
        └───┬────┘
   ═════════╪═════════  Stützbuchse, Bohrung 8,2–8,4 mm,
     ○──────┼──────○    Querschlitz 1–1,5 mm für die Klinge
   ═════════╪═════════
            ▼
      Fallschacht → Auffangbehälter (Spitzen + Krümel)
```

- **Antrieb:** SG90 (~1,8 kg·cm Stall) über Hebelarm ~15 mm → ~10 N an der
  Klinge. Eine scharfe Rasierklinge braucht nur wenige Newton.
- **Führung:** Klingenträger aus 4 mm PMMA GS (wie Reststruktur) in einer
  Nut-Führung — die Klinge darf nur linear laufen, nicht kippen.
- **Hub:** ≥ 12 mm (8 mm Zigarette + Anfahrweg + Überhub). Über die
  Hebelgeometrie aus dem Servo-Winkelbereich (`cut_home`→`cut_cut`) ableiten.
- **Endlagen frei wählen:** `cut_cut` so einstellen, dass der Servo in der
  unteren Endlage **nicht gegen einen Anschlag drückt** (SG90 im Stall zieht
  >500 mA und stirbt thermisch). Die Klinge soll knapp unterhalb der
  Zigarette frei auslaufen.

### Einbauort + Sequenz-Position

Der Schnitt passiert als **Step 11**, direkt nach dem Auswurf-Rückstoß
(Steps 9/10) und **bevor** die Trommel weiterdreht (Step 1 des nächsten
Zyklus). Die fertige Zigarette liegt dann wieder in der Trommelnut, die
Spitze ragt über die Trommelkante — Trommelnut = hintere Stützung, die
Stützbuchse sitzt davor auf der überstehenden Spitze.

### Schnipsel-Management

- **Fallschacht direkt unter der Schnittstelle**, Auffangbehälter darunter.
- Abgeschnittene Spitzen + Krümel dürfen **nicht in die Gabellichtschranke
  (A5) rieseln** — Schacht seitlich geschlossen ausführen.
- Behälter regelmäßig leeren (Inhalt ist wiederverwendbarer Tabak + Papierring).

### Sicherheit

- Klinge nur **innerhalb des Gehäuses** exponiert; Klingenwechsel nur mit
  Werkzeug möglich (Abdeckung verschraubt, nicht geklipst).
- Firmware fährt die Klinge bei `stop` (Notaus), beim Homing und beim Boot
  immer in `cut_home` (eingefahren).
- Der Hardware-Notaus (12-V-Trennung, siehe TODO in CLAUDE.md) betrifft den
  Servo nicht (5 V) — die sichere Ruhelage der Klinge ist deshalb **oben**,
  gehalten durch die Selbsthemmung des SG90-Getriebes.

---

## 3. Elektrik

| Was | Wie |
|---|---|
| Signal | Nano **A3** → SG90 orange Litze |
| VCC | **Buck-5V-Bus** (NICHT L298N-5V!), eigener **470 µF Elko** direkt am Servo |
| GND | gemeinsamer GND-Stern (WAGO) |

Kein MOSFET, keine Flyback-Diode — Standard-Servoanschluss wie beim
Hülsen-Servo (D11). Der Buck muss beide Servos + Pi tragen (≥ 3 A: passt).
Servo.h auf dem ATmega328 bedient bis zu 12 Kanäle über Timer1 — der zweite
Servo kostet **keinen** weiteren Timer und keine PWM-Pins.

---

## 4. Firmware / API / Tuning

| Ebene | Was |
|---|---|
| Nano | Step 11 `STEP_CUT` in der Vollsequenz; Manual-Befehl `cut` (nur IDLE) |
| Params | `cut_home` (Default 10°), `cut_cut` (Default 110°), `cut_dwell_ms` (Default 150) |
| Pi-API | `POST /manual/cut`, Params via `PUT /params`, Status-Feld `cut` (Winkel) |

### Inbetriebnahme (nach dem Test-Reihenfolge-Schema in CLAUDE.md, als Punkt 13b)

1. Servo **vor dem Anbau** auf `cut_home` fahren (`servo`-Horn dann montieren):
   `cut` einmal ohne Klinge laufen lassen und Winkel beobachten.
2. `set cut_cut <winkel>` schrittweise erhöhen, bis die Klinge sicher durch
   eine **leere Hülse** schneidet, ohne am Ende anzustehen.
3. Mit gestopfter Zigarette testen; bei Quetschung: Klinge schärfer/steiler
   anstellen, `cut_dwell_ms` erhöhen bringt bei stumpfer Klinge nichts.
4. `step 11` einzeln testen, dann `stuff`-Vollsequenz.

### Stückliste

| Teil | Preis | Quelle |
|---|---|---|
| SG90 Servo | ~4 € | Amazon (wie Hülsen-Servo) |
| Rasierklingen (10er) / Abbrechklingen 9 mm | ~2–3 € | Drogerie / Baumarkt |
| M3-Schrauben + Muttern (Klemmhalter) | Restbestand | — |
| PMMA GS 4 mm (Träger, Führung, Buchse) | Verschnitt | vorhandene Zuschnitte |
| 470 µF Elko | Restbestand | Sortiment |

---

## Verwandte Dokumente

- [`pinout.md`](pinout.md) — A3-Belegung
- [`protocol.md`](protocol.md) — `cut`-Befehl, Step-Nummern
- [`wiring.md`](wiring.md) — 5V-Bus / Servo-Entkopplung
- [`../firmware/nano/src/main.cpp`](../firmware/nano/src/main.cpp) — `STEP_CUT` / `tickCut()`
