# CAD-Verzeichnis

Alle CAD-Quellen, Zeichnungen, 3D-Druck-Dateien und externe Referenzen für die Zigarettenstopfmaschine.

## Verzeichnisstruktur

```
cad/
├── README.md                     # diese Datei
├── source/                       # Master-DXFs (Fraens-Originale, ungesplittet, für Onshape-Import)
├── reference/                    # Externe Referenzen (Fraens-Vorlagen, Metallteile-Zeichnungen)
│   └── metal_parts/              # Einzel-DXFs + PDFs der Metallteile (Pos.63–87)
├── drawings/                     # Fertigungs-fertige Zeichnungen
│   └── acryl_parts/              # Laser-Cut-DXFs für Acryl-Strukturteile (4 mm)
├── stl/                          # STL-Dateien für 3D-Druck (PETG/PLA)
└── scad/                         # OpenSCAD-Quellen für eigene parametrische Anpassungen (leer)
```

**Hinweis:** Aktuell sind keine `.scad`-Dateien vorhanden. Der Ordner ist als Platzhalter angelegt
(via `.gitkeep`), für künftige eigene OpenSCAD-Konstruktionen (z. B. parametrische Halter,
Stopfrohr-Adapter, Magazin-Aufsätze).

**Hinweis Metallteile:** `reference/metal_parts/` ist als Referenz/Bestellunterlage gedacht — das ist,
was an die CNC-/Edelstahl-Werkstatt geht. Falls die Metallteile später als reguläre Eigenfertigung
gelten sollen, kann der Ordner zu `drawings/metal_parts/` verschoben werden.

## Materialien & Fertigungsverfahren

| Kürzel | Bedeutung |
|---|---|
| **PMMA GS 4 mm** | Acrylglas, gegossen, 4 mm Stärke (NICHT extrudiert) — Strukturteile |
| **Edelstahl V2A** | rostfreier Stahl, CNC- oder Laser-geschnitten — Tragteile, Wellen |
| **PETG / PLA** | 3D-Druck-Filament — Halter, Führungen, nicht-tragend |
| **Lasern** | DXF an Laser-Schnitt-Dienstleister (kunststoffplattenonline.de o. ä.) |
| **CNC** | Frästeil oder Edelstahl-Wasserstrahl/Laser |
| **3D-Druck** | Drucken in PETG (mechanische Teile) oder PLA (Prototyp) |

## Bauteilübersicht

| Name | Datei | Material | Fertigung | Status |
|---|---|---|---|---|
| **Acryl-Strukturteile (Master)** | [`source/Acryl cuttings_01.DXF`](source/Acryl%20cuttings_01.DXF) | PMMA GS 4 mm | Lasern | ✅ Master vorhanden |
| **Stopfmaschine Gesamt-Layout** | [`source/Stuffing machine_00.DXF`](source/Stuffing%20machine_00.DXF) | – | Referenz | ✅ |
| **Metallteile-Übersicht (Master)** | [`source/Metal parts.DXF`](source/Metal%20parts.DXF) | Edelstahl V2A / Stahl | CNC / Laser | ✅ Master vorhanden |
| **Grundplatte Pos.75** | [`source/Base plate Pos-75.DXF`](source/Base%20plate%20Pos-75.DXF) | PMMA GS 4 mm | Lasern | ✅ |
| Acryl-Teil Pos.95 | [`drawings/acryl_parts/acryl_teil1.dxf`](drawings/acryl_parts/acryl_teil1.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.96 | [`drawings/acryl_parts/acryl_teil2.dxf`](drawings/acryl_parts/acryl_teil2.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.97 | [`drawings/acryl_parts/acryl_teil3.dxf`](drawings/acryl_parts/acryl_teil3.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.98 | [`drawings/acryl_parts/acryl_teil4.dxf`](drawings/acryl_parts/acryl_teil4.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.99 | [`drawings/acryl_parts/acryl_teil5.dxf`](drawings/acryl_parts/acryl_teil5.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.100 | [`drawings/acryl_parts/acryl_teil6.dxf`](drawings/acryl_parts/acryl_teil6.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.101 | [`drawings/acryl_parts/acryl_teil7.dxf`](drawings/acryl_parts/acryl_teil7.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.102 | [`drawings/acryl_parts/acryl_teil8.dxf`](drawings/acryl_parts/acryl_teil8.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.103 | [`drawings/acryl_parts/acryl_teil9.dxf`](drawings/acryl_parts/acryl_teil9.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.104 | [`drawings/acryl_parts/acryl_teil10.dxf`](drawings/acryl_parts/acryl_teil10.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.105 | [`drawings/acryl_parts/acryl_teil11.dxf`](drawings/acryl_parts/acryl_teil11.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.106 | [`drawings/acryl_parts/acryl_teil12.dxf`](drawings/acryl_parts/acryl_teil12.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.107 | [`drawings/acryl_parts/acryl_teil13.dxf`](drawings/acryl_parts/acryl_teil13.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Teil Pos.108 | [`drawings/acryl_parts/acryl_teil14.dxf`](drawings/acryl_parts/acryl_teil14.dxf) | PMMA GS 4 mm | Lasern | 🔲 zu bestellen |
| Acryl-Sammelblatt 1 | [`drawings/acryl_parts/acryl1.dxf`](drawings/acryl_parts/acryl1.dxf) | PMMA GS 4 mm | Lasern | ✅ alternative Bestellvorlage |
| Acryl-Sammelblatt 2 | [`drawings/acryl_parts/acryl2.dxf`](drawings/acryl_parts/acryl2.dxf) | PMMA GS 4 mm | Lasern | ✅ alternative Bestellvorlage |
| Metallteile Pos.63–87 (split) | [`reference/metal_parts/`](reference/metal_parts/) | Edelstahl V2A / Stahl | CNC / Laser | 🔲 Werkstatt-Anfrage offen |
| 3D-Druck-Teile (alle) | [`stl/`](stl/) | PETG / PLA | 3D-Druck | 🔄 teilweise gedruckt |

### Status-Legende

- ✅ vorhanden / fertig / verfügbar
- 🔄 in Arbeit / teilweise erledigt
- 🔲 offen / noch zu erledigen
- ❌ verworfen / nicht relevant

## Workflow

1. **Onshape-Anpassungen** → eigene Änderungen parametrisch (Variables für Kernmaße, siehe `CLAUDE.md`).
2. **Export** → DXF in `source/` (Master) bzw. `drawings/acryl_parts/` (Fertigungsstand).
3. **Lasern** → DXF aus `drawings/acryl_parts/` an Dienstleister
   (kunststoffplattenonline.de, S-Polytec.de, Acrylglasplattenshop.de, Plattenzuschnitt24.de).
4. **3D-Druck** → STL aus `stl/` in den Slicer; Empfehlung PETG für mechanische Teile.
5. **Metallteile** → DXF + PDF aus `reference/metal_parts/` an die Edelstahl-Werkstatt.

## Reihenfolge der Eigen-Konstruktion (laut CLAUDE.md)

1. Stopfrohr-Halter + Pusher-Führung
2. Trommelmagazin
3. Tabakmagazin / Gehäuse
