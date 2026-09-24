# Hülsen-Schieber: Servo + Zahnstange

Der Hülsen-Schieber schiebt die leere Hülse aus der Trommel aufs Stopfrohr
(Schritt 2) und fährt den Stift danach wieder ganz zurück (Schritt 3), damit
die Trommel frei drehen kann.

**Bisher:** SG90 mit gedrucktem Hebel (Part-49) und kurzer Koppel (Part-41).
Das machte Probleme: Der Hebel rutschte auf der Servo-Verzahnung, die schräge
Koppel verkantete den Schlitten, an den Hubenden kam zu wenig Kraft an, und es
gab keine Rückmeldung, ob der Stift wirklich zurück ist.

**Jetzt:** Ritzel am Servo-Horn → Zahnstange am Schlitten → Stift. Ein
Endschalter meldet die hintere Endlage (Home) und verriegelt die Trommel.

```
                 MG90S (Metallgetriebe)
                        |
                  ( Ritzel z=24 )          Stift
   [KW12] ◄──  ==[ Zahnstange M1 ]==  ─────────────►  [Hülse in Trommel] ══► Stopfrohr
   Home-          Schlitten auf Linearführung (MGN7 oder 2× Ø4-Welle)
   Schalter
```

Warum das besser ist:

- **Rein linear:** keine schräge Koppel, also keine Querkraft auf den Schlitten.
- **Konstante Kraft** über den ganzen Hub, auch an den Enden.
- **Kein Rutschen:** Das Ritzel wird ans Original-Horn **geschraubt** und
  nicht auf die Verzahnung gepresst.
- **Sanft:** Die Firmware fährt den Winkel als Rampe (`servo_speed`), statt
  dass der Servo mit Vollgas gegen die Hülse schlägt.
- **Rückmeldung:** Der Endschalter zeigt, ob der Stift zurück ist. Nur dann
  dreht die Trommel.

---

## 1. Auslegung

**Hub** = Teilkreisradius × Schwenkwinkel (im Bogenmaß) = `d/2 · Δθ · π/180`

Modul 1 wie die vorhandene Pusher-Zahnstange (Part-10: 39 Zähne auf 120 mm,
Teilung 3,14 mm) und das Pusher-Ritzel (Part-31: z = 10). Für den
Hülsen-Schieber braucht das Ritzel mehr Zähne, sonst reicht der Hub nicht:

| Ritzel (Modul 1) | Teilkreis | Hub bei 100° | 120° | 140° | 160° | Blockierkraft MG90S* |
|---|---|---|---|---|---|---|
| z = 20 | Ø 20 mm | 17,5 mm | 20,9 mm | 24,4 mm | 27,9 mm | ~18 N |
| **z = 24** | **Ø 24 mm** | **20,9 mm** | **25,1 mm** | **29,3 mm** | **33,5 mm** | **~15 N** |
| z = 30 | Ø 30 mm | 26,2 mm | 31,4 mm | 36,7 mm | 41,9 mm | ~12 N |

\* MG90S ≈ 1,8 kg·cm bei 5 V. Dauerhaft nutzbar ist etwa ein Drittel davon.
Das reicht, um die Hülse aufs Rohr zu schieben.

**Empfehlung: z = 24** und höchstens 160° vom Servo-Bereich nutzen, also
mindestens 10° Abstand zu 0° und 180° (interner Anschlag).

Weitere Maße:

- **Zahnstange:** Zahnlänge ≥ Hub + 10 mm, gesamt etwa Hub + 20 mm. Bei 30 mm
  Hub also ~50 mm. Nimm Part-10 als Vorlage und kürze sie.
- **Zahnbreite** 6–8 mm, PETG.
- **Achsabstand** Ritzel ↔ Zahnstange: Teilkreisradius (12 mm) bis zur
  Wälzlinie der Zahnstange, plus 0,1–0,15 mm Spiel für den Druck.
- **Keine harten Anschläge im Hub:** Der Schlitten muss hinter Home und vor
  Laden noch 2–3 mm frei laufen können. Die Endlagen sind Servo-Winkel in der
  Software. Ein Anschlag innerhalb des Hubs lässt den Servo blockieren.
- **Endschalter** so setzen, dass er ~1 mm vor der Home-Endlage schaltet. Den
  Rest nimmt der Überhub des Rollenhebels auf.
- **Stift:** Ø 5–6 mm, vorne leicht angesenkt, damit er mittig auf dem Filter
  sitzt.

### Ritzel ans Servo

1. Servo per App auf **90°** fahren und den Schlitten von Hand in
   **Hubmitte** stellen.
2. Erst dann das Ritzel mit Horn aufstecken. So liegt der Hub mittig im
   Servo-Bereich.
3. Ritzel mit **2–4 Schrauben** am runden Original-Horn befestigen (die
   Schrauben aus der Servo-Tüte), dazu die Horn-Mittelschraube.
4. **Nie** ein gedrucktes Teil direkt auf die Servo-Verzahnung pressen.
   Genau das rutscht.

---

## 2. Teile

| Teil | Hinweis | ca. Preis |
|---|---|---|
| MG90S Servo | Metallgetriebe, gleiche Bauform wie SG90 → passt in die vorhandene Halterung | 4–6 € |
| Ritzel Modul 1, z = 24 | gedruckt (PETG), ans Original-Rundhorn geschraubt | – |
| Zahnstange Modul 1, ~50 mm | gedruckt nach Vorlage Part-10 | – |
| Linearführung | MGN7-Schiene 100 mm + Wagen (am saubersten) oder 2× Silberstahl Ø4 h6 + gedruckter Schlitten | 10–15 € / ~3 € |
| KW12-Mikroschalter mit Rolle | Schließer (NO) — steht schon als Backup-Endschalter in der Teileliste | < 1 € |
| optional: 10 kΩ + 100 nF | Pull-up und Entstörung bei Kabel > 30 cm | Cent-Beträge |

---

## 3. Verdrahtung Endschalter (A3)

```
   KW12 COM ──────────────── GND (Sternpunkt)
   KW12 NO  ──────────────── Nano A3   (interner Pull-up aktiv)

   optional bei langem Kabel / Motorleitungen daneben:
   Nano A3 ──[10 kΩ]── +5 V
   Nano A3 ──||100 nF── GND
```

- **Schließer (NO) verwenden:** Gedrückt (Schieber in Home) = LOW.
- Das ist fail-safe: Bei Kabelbruch liest der Nano HIGH, also „nicht Home“,
  und die Trommel bleibt gesperrt.
- **Alternative Hall-Sensor A3144:** VCC 5 V, GND, OUT an A3 (Open Collector,
  10 kΩ Pull-up empfohlen), Magnet am Schlitten. Gleiche Logik, keine
  Code-Änderung. Staubunempfindlich.

---

## 4. Firmware-Verhalten (ab v0.5.0)

| Situation | Verhalten |
|---|---|
| Schritt 2 „Hülse aufschieben“ | Rampe auf `servo_load` mit `servo_speed` °/s, danach 150 ms Nachlauf. Ist der Schalter dann **noch gedrückt**, kommt Fehler `sleeve_stuck` (Servo dreht, aber der Schieber bewegt sich nicht). |
| Schritt 3 „Home“ | Rampe auf `servo_home`, danach Warten auf den Schalter (max. 1 s). Sonst kommt `sleeve_home_timeout`. |
| Trommel drehen | Schritt 1, Referenzfahrt und manueller `stepper`-Befehl laufen nur mit gedrücktem Schalter. Sonst kommt `sleeve_not_home`. |
| Referenzfahrt | Schieber → Pusher zurück → Presse zurück → **zuletzt** Trommel (Schritte 101–104). |
| `stop` / Fehler / Watchdog | Rampe stoppt, Servo wird stromlos (kein Blockierstrom). |
| Boot | Servo geht direkt auf `servo_home`, ohne das Zucken auf 90°. |
| `sleeve_switch = 0` | Keine Schalter-Prüfung. Schritte 2/3 laufen rein zeitgesteuert, wie bis v0.4. |

**EEPROM:** Beim ersten Boot mit v0.5.0 werden alle bisherigen Parameter
übernommen. Nur die zwei neuen bekommen Defaults: `servo_speed` = 150,
`sleeve_switch` = 1.

> **Solange der Schalter noch nicht verbaut ist:** In der App unter Parameter →
> Servo den Schalter „Endschalter prüfen (A3)“ **ausschalten**. Sonst bricht
> die Referenzfahrt mit `sleeve_home_timeout` ab, und die Trommel bleibt
> gesperrt.

---

## 5. Kalibrieren (App → Handbetrieb)

1. **Parameter → Servo:** `Geschwindigkeit` auf 150 °/s lassen. Für die
   Kalibrierung „Endschalter prüfen“ vorerst **aus**.
2. **Handbetrieb → Servo:** Mit dem Slider langsam Richtung Home fahren, bis
   der Sensor „Endschalter Hülsen-Schieber“ **AUSGELÖST** zeigt. Dann noch
   1–2° weiter. Diesen Winkel als **Position Home** (`servo_home`) speichern.
3. Eine Hülse in die Trommel legen und Richtung Laden fahren, bis die Hülse
   **ganz** auf dem Stopfrohr sitzt. Diesen Winkel als **Position Laden**
   (`servo_load`) speichern.
4. „Endschalter prüfen“ **einschalten** und speichern.
5. Testen: Einzelschritt 2 und 3, dann „Home“, dann eine Stopfsequenz.
6. Knickt die Hülse oder springt sie ab, `Geschwindigkeit` auf 80–100 °/s
   senken. Läuft alles sauber, sind auch 200–250 °/s möglich.

---

## 6. Fehlercodes

| Code | Bedeutung | Prüfen |
|---|---|---|
| `sleeve_not_home` | Trommel soll drehen, der Schalter ist aber nicht gedrückt | Steht der Stift wirklich hinten? Ist `servo_home` weit genug hinten? Schalter-Position, Kabel (NO an GND) |
| `sleeve_home_timeout` | Nach der Home-Fahrt hat der Schalter nicht innerhalb 1 s ausgelöst | Klemmt der Schlitten? Ist `servo_home` zu weit vorne? Ohne Schalter: `sleeve_switch` = 0 |
| `sleeve_stuck` | Nach der Laden-Fahrt ist der Schalter noch gedrückt | Rutscht das Ritzel am Horn? Greift die Zahnstange? Klemmt der Schlitten? Hängt der Schalter? |
| `err servo_angle:<x>` | `servo`-Befehl ohne gültige Zahl | nur Ziffern 0–180 senden |
