"""
Servo-Gelenk nach Fraens-Original (Part-41 / Part-49 / Part-70)
===============================================================

Baut das Original-Gestaenge der Huelsen-Ladeeinheit aus Filling machine.STEP
als 3D-druckbare Teile nach - alle drei in EINEM neuen Dokument, nebeneinander
in Drucklage:

  * KURBEL   (Part-49): Hebel 24,0 mm, Kopf mit Oe3,2 fuer M3
  * KOPPEL   (Part-41): Knochenform, Lochabstand 10,0 mm, Oe3,4 / Oe2,2
  * GABELKOPF (Part-70): sitzt auf der Oe6-Schubstange; vorn ein Schlitz QUER
    DURCH das ganze Teil auf Hoehe der Stangenachse, darin schwenkt die Koppel
    um einen vertikalen Oe2-Stift

So funktioniert das Original (aus der STEP-Datei vermessen):

  Seitenansicht Gabelkopf:              Draufsicht Gelenkkette:

      ________________                    Servo--24--[M3]--10--[Stift Oe2]
     |   .------------|--- Rohr Oe6            \\           /
     |===| Schlitz 3mm|===                      Kurbel  Koppel --> Gabel auf
     |___`------------|---                                          der Stange
      ^ Stift Oe2 senkrecht

Der Schlitz ist seitlich OFFEN (geht in Querrichtung durch) - deshalb kann die
Koppel darin beliebig weit schwenken. Das braucht sie auch: nahe den Hubenden
steht sie bis zu 79 Grad zur Stangenachse.

Abweichungen vom Original (bewusst, wegen 3D-Druck):

  * Kurbel-Nabe: Tasche fuers Original-Servohorn + 2x M2 statt Oe5-Bohrung
    direkt auf der Verzahnung. Eine gedruckte Verzahnungs-Bohrung rutscht
    durch - der Ausloeser dieses ganzen Umbaus. Dicke 8 mm statt 3 mm.
  * Gabelkopf: untere Schlitzwange 4 mm statt 1,5 mm (bricht sonst),
    Rohr-Klemmung per M3-Madenschraube quer statt Loeten
  * Koppel: Augen Oe7 statt Oe6 (Wandstaerke an der Oe3,4-Bohrung)
  * Kurbelkopf Oe8 statt Oe6 (Wandstaerke an der Oe3,2-Bohrung)

Kinematik des Originals (r=24, Koppel=10, Achsversatz=24,8):
Das Gestaenge hat SPERRLAGEN bei Kurbelwinkel 38,1 und 141,9 Grad - der
Nutzhub (42 mm) liegt exakt dazwischen. In der Firmware unbedingt mit
mindestens 5 Grad Abstand zu beiden Grenzen fahren und den Servo in der
Endlage stromlos schalten, sonst arbeitet er die Nabe wieder aus.

Ausfuehren: Utilities -> Scripts and Add-Ins -> Scripts -> GelenkServoOriginal
Alle Masse in mm. Masse aendern -> DEFAULTS anpassen, Skript neu laufen lassen.
"""

import math
import traceback

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Parameter (alles in mm / Grad)
# ---------------------------------------------------------------------------
DEFAULTS = [
    # --- Gelenkkette (Originalmasse aus der STEP-Datei) ---
    ('hebel_laenge',      24.0, 'mm',  'Kurbelradius Servowelle -> M3 (Original: 24,0)'),
    ('koppel_abstand',    10.0, 'mm',  'Lochabstand der Koppel (Original: 10,0)'),
    ('stange_bohrung',     6.1, 'mm',  'Bohrung fuer die Oe6-Schubstange im Gabelkopf'),
    ('stift_d',            2.0, 'mm',  'Querstift im Gabelkopf (Stahlstift/Nagel Oe2)'),

    # --- Kurbel ---
    ('dicke',              8.0, 'mm',  'Kurbeldicke = Nabenhoehe (Original 3 - gedruckt zu wenig)'),
    ('naben_d',           16.0, 'mm',  'Nabendurchmesser (Original 9 - zu klein fuer die Horntasche)'),
    ('kopf_d',             8.0, 'mm',  'Kurbelkopf aussen (Original 6)'),
    ('kopf_bohrung',       3.2, 'mm',  'Bohrung im Kurbelkopf fuer M3'),

    # --- Koppel ---
    ('koppel_dicke',       3.0, 'mm',  'Koppeldicke (Original 3) - bestimmt die Schlitzhoehe'),
    ('koppel_auge_d',      7.0, 'mm',  'Augendurchmesser der Koppel (Original 6)'),
    ('koppel_loch_kurbel', 3.4, 'mm',  'Koppelloch Kurbelseite - dreht frei auf M3'),
    ('koppel_loch_stift',  2.2, 'mm',  'Koppelloch Stiftseite (Original 2,2)'),

    # --- Gabelkopf ---
    ('gabel_laenge',      20.0, 'mm',  'Gesamtlaenge (Original 50 - unnoetig lang)'),
    ('gabel_breite',       9.0, 'mm',  'Breite quer (Original 6 - Wand um die Stiftbohrung)'),
    ('wange',              4.0, 'mm',  'Dicke der Schlitzwangen oben/unten (Original unten nur 1,5!)'),
    ('schlitz_spiel',      0.4, 'mm',  'Schlitzhoehe = koppel_dicke + dieses Spiel'),
    ('schlitz_tiefe',      8.0, 'mm',  'Schlitztiefe ab Vorderkante'),
    ('stift_abstand',      3.5, 'mm',  'Stiftachse hinter der Vorderkante (Original 3)'),
    ('stift_bohrung',      2.0, 'mm',  'Stiftbohrung in den Wangen - Presssitz, 2,1 wenn locker'),
    ('klemm_bohrung',      2.9, 'mm',  'Querbohrung fuer M3-Madenschraube (schneidet selbst)'),

    # --- Horn (identisch zum Skript KurbelHuelsenschieber - nachmessen!) ---
    ('horn_winkel',        0.0, 'deg', 'Winkel Hornarm gegen Hebelrichtung'),
    ('horn_scheibe_d',     7.2, 'mm',  'MESSEN: Oe der runden Scheibe am Horn'),
    ('horn_kragen_d',      6.0, 'mm',  'MESSEN: Oe des erhabenen Kragens'),
    ('horn_arm_l',        15.5, 'mm',  'MESSEN: Wellenmitte -> Armspitze'),
    ('horn_arm_b_wurzel',  6.0, 'mm',  'MESSEN: Armbreite an der Scheibe'),
    ('horn_arm_b_spitze',  4.0, 'mm',  'MESSEN: Armbreite an der Spitze'),
    ('horn_arm_dicke',     1.5, 'mm',  'MESSEN: Dicke des Hornarms'),
    ('horn_loch_1',        7.0, 'mm',  'MESSEN: Abstand 2. Hornloch ab Wellenmitte'),
    ('horn_loch_2',       12.0, 'mm',  'MESSEN: Abstand 4. Hornloch ab Wellenmitte'),

    # --- Passungen ---
    ('spiel',             0.35, 'mm',  'Taschenspiel pro Seite (0,15 + 0,2 Druck-Toleranz)'),
    ('schraub_d',          2.1, 'mm',  'Durchgang M2-Blechschraube (Horn)'),
    ('m2_kopf_d',          4.2, 'mm',  'Senkung M2-Kopf'),
    ('m2_kopf_t',          1.6, 'mm',  'Tiefe der M2-Senkung'),
]

TASCHE_EXPR = 'horn_arm_dicke - 0.2 mm'
KRAGEN_LUFT = 0.8
ACHSVERSATZ = 24.8          # quer, Servoachse -> Stangenachse (aus der STEP)
SPERRE_MIN, SPERRE_MAX = 38.1, 141.9   # Kurbelwinkel-Fenster des Originals
# Ablage der drei Teile auf der Druckplatte (Y-Offsets)
LAGE_KOPPEL_Y = 22.0
LAGE_GABEL_Y = -22.0


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = 'Gelenk Servo Original'
        except Exception:
            pass  # rein kosmetisch

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        _anzeige_mm(design)
        root = design.rootComponent

        werte = _parameter_anlegen(design)
        warnungen = _pruefen(werte)
        _bauen(root, werte)
        _material_zuweisen(app, design, root)

        app.activeViewport.fit()

        schlitz_h = werte['koppel_dicke'] + werte['schlitz_spiel']
        stange_z = werte['dicke'] + 0.2 + werte['koppel_dicke'] / 2.0
        stift_l = 2.0 * werte['wange'] + schlitz_h
        schraube = werte['dicke'] - werte['m2_kopf_t'] + werte['horn_arm_dicke']
        hinweis = (
            'Drei Teile erzeugt (Drucklage nebeneinander):\n'
            'Kurbel r={hebel_laenge:.1f} / Koppel {koppel_abstand:.1f} / Gabelkopf '
            'auf Oe6-Stange.\n\n'
            'Zuschnitte und Schrauben:\n'
            '  Querstift Oe{stift_d:.1f} x {stift_l:.0f} mm (Stahlstift oder Nagel)\n'
            '  1x M3 x 10 + Nyloc (Kurbel-Koppel, nur handfest - muss drehen)\n'
            '  1x M3 x 6 Madenschraube (Gabelkopf-Klemmung)\n'
            '  2x M2 x {schraube:.0f} mm Blechschraube (Horn)\n\n'
            'Einbau (Originalmasse aus der STEP):\n'
            '  Servoachse quer zur Stangenachse: {versatz:.1f} mm\n'
            '  Stangenachse ueber Horn-Oberseite: {stange_z:.1f} mm '
            '(= Kurbeldicke + Koppelmitte)\n\n'
            'ACHTUNG Kinematik des Originals: Sperrlagen bei {smin:.1f} und '
            '{smax:.1f} Grad Kurbelwinkel. Firmware-Endlagen mit mindestens 5 Grad '
            'Abstand setzen und den Servo in der Endlage stromlos schalten.'
        ).format(stift_l=stift_l, schraube=schraube, versatz=ACHSVERSATZ,
                 stange_z=stange_z, smin=SPERRE_MIN, smax=SPERRE_MAX, **werte)
        if warnungen:
            hinweis += '\n\nPruefen:\n- ' + '\n- '.join(warnungen)
        ui.messageBox(hinweis, 'Gelenk Servo Original')

    except Exception:
        if ui:
            ui.messageBox('Fehler:\n{}'.format(traceback.format_exc()),
                          'Gelenk Servo Original')


def _anzeige_mm(design):
    """'defaultLengthUnits' ist nur lesbar - Anzeige via distanceDisplayUnits."""
    try:
        manager = getattr(design, 'fusionUnitsManager', None) or design.unitsManager
        manager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    except Exception:
        pass


def _material_zuweisen(app, design, root):
    """PETG gibt es in der Fusion-Bibliothek nicht - ABS ist mechanisch am
    naechsten dran. Reine Stammdaten (Dichte/Masse), nie einen Lauf wert
    abzubrechen."""
    try:
        lib = app.materialLibraries.itemByName('Fusion 360 Material Library') \
            or app.materialLibraries.itemByName('Fusion Material Library')
        mat = lib.materials.itemByName('ABS Plastic')
        for i in range(root.bRepBodies.count):
            try:
                root.bRepBodies.item(i).material = mat
            except Exception:
                pass
    except Exception:
        pass


def _parameter_anlegen(design):
    params = design.userParameters
    werte = {}
    for name, wert, einheit, kommentar in DEFAULTS:
        ausdruck = '{} {}'.format(wert, einheit)
        vorhanden = params.itemByName(name)
        if vorhanden:
            vorhanden.expression = ausdruck
        else:
            params.add(name,
                       adsk.core.ValueInput.createByString(ausdruck),
                       einheit,
                       kommentar)
        werte[name] = wert
    return werte


# ---------------------------------------------------------------------------
# Plausibilitaet
# ---------------------------------------------------------------------------
def _pruefen(w):
    warnungen = []
    schlitz_h = w['koppel_dicke'] + w['schlitz_spiel']

    # Kinematik: Koppel muss den Gabelstift im ganzen Fenster erreichen
    grenze = (ACHSVERSATZ - w['koppel_abstand']) / w['hebel_laenge']
    if grenze >= 1.0:
        warnungen.append(
            'Kurbel {:.1f} + Koppel {:.1f} erreichen den Achsversatz {:.1f} nicht - '
            'Gestaenge unmoeglich.'.format(w['hebel_laenge'], w['koppel_abstand'], ACHSVERSATZ))
    elif grenze > 0.95:
        warnungen.append(
            'Gestaenge nur knapp montierbar - hebel_laenge oder koppel_abstand '
            'vergroessern.')

    # Kurbel
    if w['kopf_d'] - w['kopf_bohrung'] < 3.0:
        warnungen.append('Wand am Kurbelkopf unter 1,5 mm - kopf_d vergroessern.')
    kragen_r = (w['horn_kragen_d'] + KRAGEN_LUFT) / 2.0
    if w['naben_d'] / 2.0 - kragen_r < 3.0:
        warnungen.append('Wand um die Kragenbohrung unter 3 mm - naben_d vergroessern.')
    if w['horn_arm_l'] + w['horn_arm_b_spitze'] / 2.0 > w['hebel_laenge'] - w['kopf_d'] / 2.0:
        warnungen.append('Hornarm reicht bis in den Kurbelkopf - kuerzeres Horn oder '
                         'hebel_laenge pruefen.')
    if abs(w['horn_loch_2'] - w['horn_loch_1']) < w['m2_kopf_d'] + 0.5:
        warnungen.append('Hornloecher zu dicht beieinander fuer die M2-Senkungen.')

    # Koppel
    for loch in ('koppel_loch_kurbel', 'koppel_loch_stift'):
        if w['koppel_auge_d'] - w[loch] < 2.5:
            warnungen.append(
                'Koppelauge um {} hat unter 1,25 mm Wand - koppel_auge_d vergroessern.'
                .format(loch))
    if w['koppel_abstand'] < w['koppel_auge_d']:
        warnungen.append('Koppelaugen ueberlappen - koppel_abstand zu klein.')

    # Gabelkopf
    hoehe = 2.0 * w['wange'] + schlitz_h
    if w['wange'] < 3.0:
        warnungen.append('Schlitzwangen unter 3 mm - brechen gedruckt (Original-Metall '
                         'hatte 1,5, das traegt PETG nicht).')
    if hoehe < w['stange_bohrung'] + 2.0:
        warnungen.append(
            'Gabelkopf nur {:.1f} mm hoch bei Stangenbohrung Oe{:.1f} - wange erhoehen.'
            .format(hoehe, w['stange_bohrung']))
    if w['gabel_breite'] - w['stift_bohrung'] < 4.0:
        warnungen.append('Wand neben der Stiftbohrung unter 2 mm - gabel_breite '
                         'vergroessern.')
    if w['schlitz_tiefe'] - w['stift_abstand'] < w['koppel_auge_d'] / 2.0 + 0.5:
        warnungen.append(
            'Koppelauge stoesst an den Schlitzgrund - schlitz_tiefe auf mindestens '
            '{:.1f} mm.'.format(w['stift_abstand'] + w['koppel_auge_d'] / 2.0 + 0.5))
    if w['gabel_laenge'] - w['schlitz_tiefe'] < 8.0:
        warnungen.append('Unter 8 mm Klemmlaenge auf der Stange - gabel_laenge '
                         'vergroessern.')
    if w['stift_bohrung'] > w['stift_d'] + 0.15:
        warnungen.append('Stiftbohrung deutlich groesser als der Stift - der wandert '
                         'raus. Presssitz waehlen oder Stift verkleben.')

    return warnungen


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _benennen(objekt, name):
    try:
        objekt.name = name
    except Exception:
        pass


def _pt(x_mm, y_mm):
    """Skizzenpunkt aus mm - die API rechnet intern in cm."""
    return adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, 0.0)


def _dreh_xy(x_mm, y_mm, winkel_grad):
    a = math.radians(winkel_grad)
    return (x_mm * math.cos(a) - y_mm * math.sin(a),
            x_mm * math.sin(a) + y_mm * math.cos(a))


def _pt_gedreht(x_mm, y_mm, winkel_grad):
    return _pt(*_dreh_xy(x_mm, y_mm, winkel_grad))


def _kreis(sketch, mittelpunkt, durchmesser_mm):
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(
        mittelpunkt, durchmesser_mm / 20.0)


def _polygon(sketch, punkte):
    linien = sketch.sketchCurves.sketchLines
    for i in range(len(punkte)):
        linien.addByTwoPoints(punkte[i], punkte[(i + 1) % len(punkte)])


def _rechteck(sketch, x1, y1, x2, y2):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(_pt(x1, y1), _pt(x2, y2))


def _rechteck_g(sketch, p1, p2):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)


def _pt_g(sketch, x_mm, y_mm, z_mm):
    """Globaler Punkt -> Skizzenkoordinaten (fuer Skizzen auf Offset-Ebenen)."""
    return sketch.modelToSketchSpace(
        adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0))


def _alle_profile(sketch):
    profile = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        profile.add(sketch.profiles.item(i))
    return profile


def _extrudieren(root, sketch, ausdruck, operation):
    """Extrudiert ALLE Profile einer Skizze (Vereinigung ueberlappender Formen)."""
    return root.features.extrudeFeatures.addSimple(
        _alle_profile(sketch),
        adsk.core.ValueInput.createByString(ausdruck),
        operation)


def _ebene(root, ausdruck, name):
    eingabe = root.constructionPlanes.createInput()
    eingabe.setByOffset(root.xYConstructionPlane,
                        adsk.core.ValueInput.createByString(ausdruck))
    ebene = root.constructionPlanes.add(eingabe)
    _benennen(ebene, name)
    return ebene


# ---------------------------------------------------------------------------
# Geometrie - drei Koerper nebeneinander in Drucklage
# ---------------------------------------------------------------------------
def _bauen(root, w):
    NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    VEREINEN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    SCHNEIDEN = adsk.fusion.FeatureOperations.CutFeatureOperation

    xy = root.xYConstructionPlane
    _kurbel(root, w, NEU, SCHNEIDEN, xy)
    _koppel(root, w, NEU, SCHNEIDEN, xy)
    _gabelkopf(root, w, NEU, VEREINEN, SCHNEIDEN, xy)


def _kurbel(root, w, NEU, SCHNEIDEN, xy):
    """Wie das Original: Nabe -> konischer Arm -> runder Kopf mit M3-Loch.
    Nabe traegt die Horntasche statt der Verzahnungs-Bohrung."""
    laenge = w['hebel_laenge']
    winkel = w['horn_winkel']
    durch = 'dicke + 2 mm'

    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Kurbel Grundkoerper')
    _kreis(sk, _pt(0.0, 0.0), w['naben_d'])
    _kreis(sk, _pt(laenge, 0.0), w['kopf_d'])
    # konischer Arm: an der Nabe breit, am Kopf schmal (wie das Original)
    _polygon(sk, [_pt(0.0, w['naben_d'] / 2.0), _pt(laenge, w['kopf_d'] / 2.0),
                  _pt(laenge, -w['kopf_d'] / 2.0), _pt(0.0, -w['naben_d'] / 2.0)])
    _extrudieren(root, sk, 'dicke', NEU)

    # Horntasche (Unterseite): Scheibe + konischer Arm + runde Spitze
    b_wurzel = w['horn_arm_b_wurzel'] / 2.0 + w['spiel']
    b_spitze = w['horn_arm_b_spitze'] / 2.0 + w['spiel']
    arm_l = w['horn_arm_l']
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Kurbel Horntasche')
    _kreis(sk, _pt(0.0, 0.0), w['horn_scheibe_d'] + 2.0 * w['spiel'])
    _kreis(sk, _pt_gedreht(arm_l, 0.0, winkel), w['horn_arm_b_spitze'] + 2.0 * w['spiel'])
    _polygon(sk, [_pt_gedreht(0.0, b_wurzel, winkel),
                  _pt_gedreht(arm_l, b_spitze, winkel),
                  _pt_gedreht(arm_l, -b_spitze, winkel),
                  _pt_gedreht(0.0, -b_wurzel, winkel)])
    _extrudieren(root, sk, TASCHE_EXPR, SCHNEIDEN)

    # Kragendurchgang + M2-Bohrungen + M3-Loch im Kopf
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Kurbel Bohrungen')
    _kreis(sk, _pt(0.0, 0.0), w['horn_kragen_d'] + KRAGEN_LUFT)
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        _kreis(sk, _pt_gedreht(w[schluessel], 0.0, winkel), w['schraub_d'])
    _kreis(sk, _pt(laenge, 0.0), w['kopf_bohrung'])
    _extrudieren(root, sk, durch, SCHNEIDEN)

    # M2-Senkungen von oben
    ebene_senk = _ebene(root, 'dicke - m2_kopf_t', 'Senkungsgrund M2')
    sk = root.sketches.addWithoutEdges(ebene_senk)
    _benennen(sk, 'Kurbel Senkungen M2')
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        _kreis(sk, _pt_gedreht(w[schluessel], 0.0, winkel), w['m2_kopf_d'])
    _extrudieren(root, sk, 'm2_kopf_t + 1 mm', SCHNEIDEN)


def _koppel(root, w, NEU, SCHNEIDEN, xy):
    """Knochenform wie Part-41: zwei Augen, tangentiale Flanken."""
    y0 = LAGE_KOPPEL_Y
    d = w['koppel_abstand']
    r = w['koppel_auge_d'] / 2.0

    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Koppel Grundkoerper')
    _kreis(sk, _pt(0.0, y0), w['koppel_auge_d'])
    _kreis(sk, _pt(d, y0), w['koppel_auge_d'])
    _rechteck(sk, 0.0, y0 - r, d, y0 + r)
    _extrudieren(root, sk, 'koppel_dicke', NEU)

    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Koppel Bohrungen')
    _kreis(sk, _pt(0.0, y0), w['koppel_loch_kurbel'])
    _kreis(sk, _pt(d, y0), w['koppel_loch_stift'])
    _extrudieren(root, sk, 'koppel_dicke + 2 mm', SCHNEIDEN)


def _gabelkopf(root, w, NEU, VEREINEN, SCHNEIDEN, xy):
    """Wie Part-70, aber mit symmetrischen 4-mm-Wangen: Block auf der Stange,
    vorn ein Schlitz quer durch das ganze Teil, vertikale Stiftbohrung.

    Drucklage = Einbaulage: die Wangen liegen als Schichten UEBEREINANDER
    (Bauhoehe = 2*wange + Schlitz), der Schlitz ist ein innenliegender
    horizontaler Spalt (3,4 mm Bridging - unkritisch) und die Stiftbohrung
    steht senkrecht. Vorher lag das Teil auf der Seite - dann verlief der
    Stift-Schnitt komplett durch den leeren Schlitz und am fertigen Koerper
    fehlte die Bohrung, die die Koppel anbindet.
    """
    y0 = LAGE_GABEL_Y
    schlitz_h = w['koppel_dicke'] + w['schlitz_spiel']
    hoehe = 2.0 * w['wange'] + schlitz_h        # Bauhoehe (Z)
    gl = w['gabel_laenge']
    hoehe_expr = '2 * wange + koppel_dicke + schlitz_spiel'

    # Grundkoerper: Grundriss gl x gabel_breite, hochgezogen auf hoehe
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Gabel Grundkoerper')
    _rechteck(sk, 0.0, y0 - w['gabel_breite'] / 2.0, gl, y0 + w['gabel_breite'] / 2.0)
    _extrudieren(root, sk, hoehe_expr, NEU)

    # Schlitz: horizontaler Spalt zwischen den Wangen, vorn und seitlich offen.
    # Ab der Ebene z = wange um die Schlitzhoehe nach oben geschnitten.
    ebene_schlitz = _ebene(root, 'wange', 'Gabel Schlitzboden')
    sk = root.sketches.addWithoutEdges(ebene_schlitz)
    _benennen(sk, 'Gabel Schlitz')
    _rechteck_g(sk,
                _pt_g(sk, -1.0, y0 - w['gabel_breite'] / 2.0 - 1.0, w['wange']),
                _pt_g(sk, w['schlitz_tiefe'], y0 + w['gabel_breite'] / 2.0 + 1.0,
                      w['wange']))
    _extrudieren(root, sk, 'koppel_dicke + schlitz_spiel', SCHNEIDEN)

    # Stangenbohrung: blind vom Heck bis zum Schlitzgrund, auf halber Hoehe
    _stangenbohrung(root, w, y0, hoehe / 2.0, SCHNEIDEN)

    # Stiftbohrung (verbindet die Koppel!) und Klemmbohrung: beide stehen
    # jetzt senkrecht und werden von der XY-Ebene aus durchgeschnitten.
    # Der Stift durchdringt untere Wange -> Schlitz (Koppelauge) -> obere Wange.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Gabel Stift + Klemme')
    _kreis(sk, _pt(w['stift_abstand'], y0), w['stift_bohrung'])
    # M3-Madenschraube: hinter dem Schlitz, kreuzt die Stangenbohrung
    klemm_x = (w['schlitz_tiefe'] + gl) / 2.0
    _kreis(sk, _pt(klemm_x, y0), w['klemm_bohrung'])
    _extrudieren(root, sk, hoehe_expr + ' + 2 mm', SCHNEIDEN)


def _stangenbohrung(root, w, y0, mitte_z, SCHNEIDEN):
    """Bohrung laengs der Stange, blind: Schlitzgrund -> Heck.

    Im Original lief die Bohrung durch das ganze Teil und fraeste dabei eine
    Rinne in beide Schlitzwangen (Oe6 Bohrung > 3 mm Schlitz). In Metall egal,
    gedruckt kostet es Wangendicke und Stift-Eingriff. Blind ab dem
    Schlitzgrund bleibt die volle Wange stehen - die Stange endet dort sowieso.

    Die Stangenachse liegt in X, also steht die YZ-Ebene senkrecht dazu;
    eine um schlitz_tiefe verschobene Kopie davon ist die Startebene.
    """
    eingabe = root.constructionPlanes.createInput()
    eingabe.setByOffset(root.yZConstructionPlane,
                        adsk.core.ValueInput.createByString('schlitz_tiefe'))
    ebene = root.constructionPlanes.add(eingabe)
    _benennen(ebene, 'Gabel Schlitzgrund')

    sk = root.sketches.addWithoutEdges(ebene)
    _benennen(sk, 'Gabel Stangenbohrung')
    _kreis(sk, _pt_g(sk, w['schlitz_tiefe'], y0, mitte_z), w['stange_bohrung'])
    _extrudieren(root, sk, 'gabel_laenge - schlitz_tiefe + 1 mm', SCHNEIDEN)
