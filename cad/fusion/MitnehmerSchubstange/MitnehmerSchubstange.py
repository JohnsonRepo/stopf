"""
Mitnehmer fuer die Schubstange (Gegenstueck zur Kurbel KurbelHuelsenschieber)
============================================================================

Erzeugt ein NEUES Fusion-Dokument mit dem 3D-druckbaren Mitnehmer:

  * Klemmnabe, die hinten auf das Messingrohr Oe5 aufgeschoben und mit einer
    M3-Schraube geklemmt wird - kein Kleben, jederzeit verschiebbar
  * zwei Schluesselflaechen, damit Schraubenkopf und Mutter plan aufliegen
  * dahinter ein Block mit QUERSCHLITZ fuer den Oe5-Bolzen der Kurbel

Wie es zusammenspielt
---------------------
Die Schubstange laeuft im Gleitlager koaxial zur Huelse und darf sich nur axial
bewegen. Das Kurbelende laeuft dagegen auf einem Kreis - es wandert also nicht
nur vor und zurueck, sondern auch quer. Dieser Querweg wird im Schlitz
aufgenommen: der Bolzen gleitet darin hin und her, waehrend die Schlitzflanken
die Schubkraft uebertragen.

Entscheidend ist, WO der Schlitz sitzt. Das Rohr endet in der Klemmnabe und
stoesst gegen die Blockvorderseite; der Schlitz liegt dahinter im vollen
Material und geht quer durch den Block hindurch. Damit greift die Schubkraft
mittig auf der Rohrachse an:

  Draufsicht (Blick von oben auf die Servoachse):

        Schubrichtung  <--->
     ____________       _______________
    |  Klemmnabe |     |     Block     |
    |   (Rohr)   |=====|   [=======]   |   <- Schlitz quer, Bolzen laeuft darin
    |____________|     |_______________|
                       ^ Rohr endet hier

  Vorderansicht (Blick entlang der Rohrachse):

           ___________
          |   |   |   |     Schlitz geht durch die ganze Blockhoehe,
          |   | O |   |     mittig zur Rohrachse -> die Kraft greift
          |___|___|___|     auf Achshoehe an, nichts kippt

Laege der Schlitz statt dessen ueber oder neben der Stange, wuerde die
Schubkraft ein Moment erzeugen und die Stange im Gleitlager verkanten. Bei nur
einem Lager merkt man das sofort als Schwergaengigkeit.

Ausfuehren: Utilities -> Scripts and Add-Ins -> Scripts -> MitnehmerSchubstange
Alle Masse in mm.

Bauteil-Koordinaten (nicht mit den Maschinenachsen verwechseln):
  Z = Rohrachse / Schubrichtung      X = quer (Schlitzlaenge)
  Y = parallel zur Servowelle (Bolzenachse, Schlitz geht in dieser Richtung durch)
"""

import math
import traceback

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Parameter (alles in mm)
# ---------------------------------------------------------------------------
DEFAULTS = [
    # --- Klemmnabe auf dem Messingrohr ---
    ('klemm_bohrung',      4.9, 'mm', 'Bohrung fuer Rohr OD 5 - die Klemmung zieht zu'),
    ('naben_d',           14.0, 'mm', 'Aussendurchmesser der Klemmnabe'),
    ('naben_laenge',      14.0, 'mm', 'Laenge der Klemmnabe = Klemmlaenge auf dem Rohr'),
    ('klemm_spalt',        1.0, 'mm', 'Breite des Klemmschlitzes'),
    ('schraube_d',         3.4, 'mm', 'Durchgang M3 fuer die Klemmschraube'),
    ('schraube_lage',      5.0, 'mm', 'Abstand der Klemmschraube von der Rohrachse'),
    ('flach_abstand',      5.5, 'mm', 'halber Abstand der beiden Schluesselflaechen'),

    # --- Block mit Querschlitz ---
    ('block_laenge',      13.0, 'mm', 'Laenge des Blocks in Schubrichtung'),
    ('block_breite',      30.0, 'mm', 'Breite quer = Richtung der Schlitzlaenge'),
    ('block_hoehe',       12.0, 'mm', 'Hoehe = Fuehrungslaenge fuer den Bolzen'),
    ('bolzen_d',           5.0, 'mm', 'Durchmesser des Kurbelbolzens'),
    ('schlitz_breite',     5.2, 'mm', 'Schlitzbreite = Bolzen + Spiel'),
    ('schlitz_laenge',    20.0, 'mm', 'nutzbare Schlitzlaenge quer'),

    # --- nur zur Kontrolle, geht nicht in die Geometrie ein ---
    ('kurbel_radius',     29.0, 'mm', 'Kurbelradius der Servokurbel - prueft die Schlitzlaenge'),
]

# Servo-Schwenkbereich, identisch zum Kurbelskript.
SWEEP_GRAD = 104.0


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = 'Mitnehmer Schubstange'
        except Exception:
            pass  # rein kosmetisch, je nach Version schreibgeschuetzt

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        _anzeige_mm(design)
        root = design.rootComponent

        werte = _parameter_anlegen(design)
        warnungen = _pruefen(werte)
        _bauen(root, werte)

        app.activeViewport.fit()

        hub, quer, versatz = _kinematik(werte)
        hinweis = (
            'Mitnehmer erzeugt.\n\n'
            'Klemmnabe Oe{naben_d:.1f} x {naben_laenge:.1f} mm auf Rohr Oe5,\n'
            'Block {block_breite:.0f} x {block_laenge:.0f} x {block_hoehe:.0f} mm, '
            'Schlitz {schlitz_breite:.1f} x {schlitz_laenge:.0f} mm.\n\n'
            'Klemmung: M3 x 16 mit Mutter und Scheibe, die Schluesselflaechen sind\n'
            'dafuer da. Erst ausrichten, dann anziehen - gefuehlvoll, sonst reisst\n'
            'der Steg neben dem Schlitz.\n\n'
            'Einbau (gilt fuer Kurbelradius {kurbel_radius:.0f} mm, {sweep:.0f} Grad Servoweg):\n'
            '  Hub der Stange           {hub:.1f} mm\n'
            '  Querweg des Bolzens      {quer:.1f} mm\n'
            '  Servoachse quer versetzt {versatz:.1f} mm zur Stangenachse\n\n'
            'Der Querversatz ist wichtig: nur damit pendelt der Bolzen symmetrisch\n'
            'um die Stangenachse und die Schubkraft bleibt mittig.'
        ).format(hub=hub, quer=quer, versatz=versatz, sweep=SWEEP_GRAD, **werte)
        if warnungen:
            hinweis += '\n\nPruefen:\n- ' + '\n- '.join(warnungen)
        ui.messageBox(hinweis, 'Mitnehmer Schubstange')

    except Exception:
        if ui:
            ui.messageBox('Fehler:\n{}'.format(traceback.format_exc()),
                          'Mitnehmer Schubstange')


def _anzeige_mm(design):
    """Anzeige-Einheit auf mm stellen ('defaultLengthUnits' ist nur lesbar)."""
    try:
        manager = getattr(design, 'fusionUnitsManager', None) or design.unitsManager
        manager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
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
# Kinematik und Plausibilitaet
# ---------------------------------------------------------------------------
def _kinematik(w):
    """Hub, Querweg des Bolzens und noetiger Querversatz der Servoachse.

    Die Kurbel schwenkt symmetrisch um die Stellung senkrecht zur
    Schubrichtung. Dann gilt mit halbem Schwenkwinkel a:
      Hub     = 2 * r * sin(a)
      Querweg = r * (1 - cos(a))
      Versatz = r * (1 + cos(a)) / 2     <- Servoachse neben der Stangenachse
    Nur mit diesem Versatz pendelt der Bolzen symmetrisch um die Stangenachse.
    """
    r = w['kurbel_radius']
    a = math.radians(SWEEP_GRAD / 2.0)
    return (2.0 * r * math.sin(a),
            r * (1.0 - math.cos(a)),
            r * (1.0 + math.cos(a)) / 2.0)


def _pruefen(w):
    warnungen = []
    naben_r = w['naben_d'] / 2.0
    bohr_r = w['klemm_bohrung'] / 2.0
    _, quer, _ = _kinematik(w)

    noetig = quer + w['bolzen_d'] + 2.0
    if w['schlitz_laenge'] < noetig:
        warnungen.append(
            'Schlitz ist mit {:.1f} mm zu kurz - bei Kurbelradius {:.0f} mm wandert der '
            'Bolzen {:.1f} mm quer. Mindestens {:.1f} mm.'
            .format(w['schlitz_laenge'], w['kurbel_radius'], quer, noetig))
    if w['schlitz_breite'] < w['bolzen_d'] + 0.1:
        warnungen.append(
            'schlitz_breite kleiner als der Bolzen - der klemmt.')
    if w['schlitz_breite'] > w['bolzen_d'] + 0.6:
        warnungen.append(
            'schlitz_breite {:.1f} mm bei Bolzen Oe{:.1f} - viel Spiel, das gibt Schlag '
            'im Umkehrpunkt.'.format(w['schlitz_breite'], w['bolzen_d']))

    if w['block_breite'] - w['schlitz_laenge'] < 8.0:
        warnungen.append(
            'Nur {:.1f} mm Material an den Schlitzenden - block_breite auf mindestens '
            '{:.1f} mm.'.format((w['block_breite'] - w['schlitz_laenge']) / 2.0,
                                w['schlitz_laenge'] + 8.0))
    if w['block_laenge'] - w['schlitz_breite'] < 6.0:
        warnungen.append(
            'Schlitzflanken nur {:.1f} mm dick - block_laenge auf mindestens {:.1f} mm.'
            .format((w['block_laenge'] - w['schlitz_breite']) / 2.0,
                    w['schlitz_breite'] + 6.0))
    if w['block_hoehe'] < 2.0 * w['bolzen_d']:
        warnungen.append(
            'Fuehrungslaenge fuer den Bolzen nur {:.1f} mm - block_hoehe auf mindestens '
            '{:.1f} mm.'.format(w['block_hoehe'], 2.0 * w['bolzen_d']))

    if naben_r - bohr_r < 3.0:
        warnungen.append(
            'Nur {:.1f} mm Wand an der Klemmnabe - naben_d auf mindestens {:.1f} mm.'
            .format(naben_r - bohr_r, (bohr_r + 3.0) * 2.0))
    if w['naben_laenge'] < 2.0 * w['klemm_bohrung']:
        warnungen.append(
            'Klemmlaenge nur {:.1f} mm - der Mitnehmer sitzt wackelig, naben_laenge '
            'auf mindestens {:.1f} mm.'.format(w['naben_laenge'], 2.0 * w['klemm_bohrung']))
    if not (bohr_r + 1.0 < w['schraube_lage'] < naben_r - 1.5):
        warnungen.append(
            'schraube_lage muss zwischen {:.1f} und {:.1f} mm liegen.'
            .format(bohr_r + 1.0, naben_r - 1.5))
    if w['flach_abstand'] >= naben_r:
        warnungen.append('flach_abstand groesser als der Nabenradius - es entstehen keine Flaechen.')
    if w['flach_abstand'] < w['schraube_d'] / 2.0 + 1.5:
        warnungen.append('Schluesselflaechen zu dicht an der Achse - flach_abstand erhoehen.')

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


def _kreis(sketch, mittelpunkt, durchmesser_mm):
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(
        mittelpunkt, durchmesser_mm / 20.0)


def _rechteck(sketch, x1, y1, x2, y2):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(_pt(x1, y1), _pt(x2, y2))


def _pt_g(sketch, x_mm, y_mm, z_mm):
    """Globalen Punkt in Skizzenkoordinaten umrechnen.

    Spart das Raten, wie die lokalen Achsen einer Ebene zu den globalen liegen -
    genau daran scheitern Skripte auf der XZ-Ebene sonst gern.
    """
    return sketch.modelToSketchSpace(
        adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0))


def _rechteck_g(sketch, p1, p2):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)


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


def _schnitt_symmetrisch(root, sketch, ausdruck, operation):
    """Schneidet symmetrisch zu beiden Seiten der Skizzenebene, feste Laenge.

    Bewusst KEIN Through-All: das schlug in der Praxis von Offset-Ebenen aus
    mit "body not found to extrude through" fehl. Eine symmetrische Distanz
    mit reichlich Zugabe ist genauso wirksam und richtungsunabhaengig.
    """
    extrudes = root.features.extrudeFeatures
    eingabe = extrudes.createInput(_alle_profile(sketch), operation)
    eingabe.setSymmetricExtent(adsk.core.ValueInput.createByString(ausdruck), True)
    return extrudes.add(eingabe)


def _ebene_bei_z(root, ausdruck, name):
    eingabe = root.constructionPlanes.createInput()
    eingabe.setByOffset(root.xYConstructionPlane,
                        adsk.core.ValueInput.createByString(ausdruck))
    ebene = root.constructionPlanes.add(eingabe)
    _benennen(ebene, name)
    return ebene


# ---------------------------------------------------------------------------
# Geometrie
# ---------------------------------------------------------------------------
def _bauen(root, w):
    NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    VEREINEN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    SCHNEIDEN = adsk.fusion.FeatureOperations.CutFeatureOperation

    xy = root.xYConstructionPlane
    xz = root.xZConstructionPlane
    naben_r = w['naben_d'] / 2.0
    nl = w['naben_laenge']
    bl = w['block_laenge']
    weit = max(w['naben_d'], w['block_breite'], w['block_hoehe']) + 10.0

    # --- 1) Klemmnabe (Achse = Z = Rohrachse) -------------------------------
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Klemmnabe')
    _kreis(sk, _pt(0.0, 0.0), w['naben_d'])
    _extrudieren(root, sk, 'naben_laenge', NEU)

    # --- 2) Schluesselflaechen fuer Schraubenkopf und Mutter ----------------
    # Zwei Halbraeume wegschneiden - erzeugt plane Auflagen auf der Nabe.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Schluesselflaechen')
    _rechteck(sk, -weit, w['flach_abstand'], weit, weit)
    _rechteck(sk, -weit, -w['flach_abstand'], weit, -weit)
    _extrudieren(root, sk, 'naben_laenge', SCHNEIDEN)

    # --- 3) Block mit dem Querschlitz --------------------------------------
    # Sitzt HINTER dem Rohrende, damit der Schlitz im vollen Material liegt.
    ebene_block = _ebene_bei_z(root, 'naben_laenge', 'Blockanfang')
    sk = root.sketches.addWithoutEdges(ebene_block)
    _benennen(sk, 'Block')
    _rechteck(sk, -w['block_breite'] / 2.0, -w['block_hoehe'] / 2.0,
              w['block_breite'] / 2.0, w['block_hoehe'] / 2.0)
    _extrudieren(root, sk, 'block_laenge', VEREINEN)

    # --- 4) Rohrbohrung - blind, endet an der Blockvorderseite --------------
    # Das Rohr stoesst gegen den Block, der Schlitz dahinter bleibt voll.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Rohrbohrung')
    _kreis(sk, _pt(0.0, 0.0), w['klemm_bohrung'])
    _extrudieren(root, sk, 'naben_laenge', SCHNEIDEN)

    # --- 5) Klemmschlitz ----------------------------------------------------
    # Von der Bohrung radial nach aussen, teilt die Nabe in zwei Haelften.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Klemmschlitz')
    _rechteck(sk, 0.0, -w['klemm_spalt'] / 2.0, naben_r + 2.0, w['klemm_spalt'] / 2.0)
    _extrudieren(root, sk, 'naben_laenge', SCHNEIDEN)

    # --- 6) Bohrung fuer die Klemmschraube ----------------------------------
    # Achse quer durch die Nabe (global Y), kreuzt den Klemmschlitz.
    sk = root.sketches.addWithoutEdges(xz)
    _benennen(sk, 'Klemmschraube')
    _kreis(sk, _pt_g(sk, w['schraube_lage'], 0.0, nl / 2.0), w['schraube_d'])
    _schnitt_symmetrisch(root, sk, 'naben_d + 4 mm', SCHNEIDEN)

    # --- 7) Querschlitz fuer den Kurbelbolzen -------------------------------
    # Langloch quer zur Schubrichtung, geht durch die ganze Blockhoehe.
    # Aufgebaut aus zwei Kreisen und einem Rechteck - alle Profile zusammen
    # ergeben das Langloch, ohne getrimmte Kontur.
    mitte = nl + bl / 2.0
    halb = (w['schlitz_laenge'] - w['schlitz_breite']) / 2.0
    hb = w['schlitz_breite'] / 2.0
    sk = root.sketches.addWithoutEdges(xz)
    _benennen(sk, 'Querschlitz')
    _kreis(sk, _pt_g(sk, -halb, 0.0, mitte), w['schlitz_breite'])
    _kreis(sk, _pt_g(sk, halb, 0.0, mitte), w['schlitz_breite'])
    _rechteck_g(sk, _pt_g(sk, -halb, 0.0, mitte - hb), _pt_g(sk, halb, 0.0, mitte + hb))
    _schnitt_symmetrisch(root, sk, 'block_hoehe + 4 mm', SCHNEIDEN)
