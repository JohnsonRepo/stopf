# Fusion-Skripte

Parametrische Konstruktionsskripte für Autodesk Fusion. Jedes Skript liegt in einem eigenen
Ordner mit gleichnamiger `.py`- und `.manifest`-Datei — so erwartet es Fusion.

## Installation

Ordner (nicht nur die `.py`) in das Fusion-Skriptverzeichnis kopieren:

| OS | Pfad |
|---|---|
| macOS | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/` |
| Windows | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\` |

Dann in Fusion: **Utilities → Scripts and Add-Ins → Scripts** → Skript auswählen → **Run**.

Alternativ im selben Dialog über **+ → Script from device** direkt auf den Ordner zeigen.

Jedes Skript legt ein **neues Dokument** an — das gerade offene Design bleibt unangetastet.

## Skripte

### KurbelHuelsenschieber

Ersatz für die Servo-Kurbel **Pos. 49** der Hülsen-Ladeeinheit (`cad/source/Stuffing machine_00.DXF`
bzw. die Fraens-STEP). Das Original ist eine 3 mm dicke Platte, die direkt mit einer Ø5-Bohrung auf
der Servoverzahnung sitzt. Gedruckt bleiben davon rund 2 mm Eingriffslänge auf einer faktisch
glatten Bohrung — deshalb rutscht die Nabe durch.

Dieses Teil legt stattdessen ein **Original-Einarm-Servohorn** formschlüssig in eine Tasche ein und
verschraubt es mit 2× M2. Das Moment läuft über die Werksverzahnung, der Druck sieht nur noch
Scherung an den Schrauben.

**Erzeugte Geometrie**

- Langloch-Grundkörper von der Nabe zum Gelenkauge, Hebellänge frei wählbar (Default 24 mm =
  Ist-Maß, für Kinematik-Variante A auf 27 mm setzen)
- 8 mm Plattendicke statt 3 mm — die Nabenhöhe ist der größte Hebel gegen Durchrutschen
- Tasche für das Horn in der Unterseite: **runde Scheibe um die Welle + konischer Arm + runde
  Spitze**, 0,2 mm flacher als der Arm (die Kurbel liegt damit auf dem Horn auf und schleift
  nie am Servogehäuse)
- Durchgang für den erhabenen Kragen, gleichzeitig Zugang zur Zentralschraube
- 2× Ø2,1 Durchgang + Senkung für M2-Blechschrauben durch zwei **nicht benachbarte** Hornlöcher
- Gelenkbohrung Ø3,2 (M3) mit Senkung Ø6,4 × 3 an der Unterseite für den Schraubenkopf

**Vor dem ersten Druck**

Die `horn_*`-Werte sind Richtwerte für ein SG90-Einarmhorn und schwanken je nach Hersteller.
Das eigene Horn mit dem Messschieber prüfen und die Werte in `DEFAULTS` im Skript eintragen:
Scheibendurchmesser (flacher Teil auf Armhöhe), Kragendurchmesser (erhabener Ring darüber),
Armlänge ab Wellenmitte, Armbreite an der Wurzel und an der Spitze, Armdicke und die zwei
Lochabstände.

Beim Lauf prüft das Skript die Maße gegeneinander und meldet Kollisionen: Senkungen zu dicht
beieinander oder zu nah an der Kragenbohrung, zu dünne Wand an der Nabe, Armspitze oder
Schraubenlöcher außerhalb der Kurbel (passiert schnell, sobald `horn_winkel` deutlich von 0
abweicht), Arm bis in die Gelenksenkung, Scheibe und Kragen vertauscht.

**Maße ändern → Skript neu laufen lassen.** Die Skizzen sind bewusst fest gezeichnet und tragen
keine Bedingungen: eine nicht am Ursprung verankerte Kontur darf der Skizzen-Solver verdrehen,
und genau das hat schon einmal eine schiefe Hornaufnahme erzeugt. Parametrisch bleiben die
Feature-Maße (Dicke, Taschentiefe, Senkungstiefen) — die sind gegen so etwas immun.

**Druckempfehlung**

PETG oder ASA (kein PLA — kriecht unter Dauerlast), liegend drucken, damit die Schichtebene die
Bewegungsebene ist, 4–5 Perimeter, Infill ≥ 50 %, Nabenbereich möglichst massiv.

**Montage**

1. Horn auf die Servowelle stecken, Servo-Endlage grob einstellen, Horn wieder abziehen.
2. Kurbel auf das Horn setzen, 2× M2 × 8 von oben eindrehen — sie schneiden ihr Gewinde in die
   vorhandenen Hornlöcher.
3. Einheit auf die Welle stecken, mit der originalen Zentralschraube sichern.
4. Gelenkschraube M3 × 16 von unten durch die Kurbel, Distanzhülse Ø6 als Lauffläche für die
   Koppel, Nyloc-Mutter oben — die Koppel muss frei drehen.
