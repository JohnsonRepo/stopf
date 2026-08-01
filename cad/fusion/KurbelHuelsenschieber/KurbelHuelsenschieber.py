"""
Kurbel fuer den Huelsen-Schieber (Ersatz fuer Pos. 49 aus Filling machine.STEP)
==============================================================================

Erzeugt ein NEUES Fusion-Dokument mit der 3D-druckbaren Servo-Kurbel:

  * Grundkoerper als Langloch (Nabe -> Gelenkauge), parametrische Hebellaenge
  * Tasche fuer ein EINARM-Servohorn (SG90-Klasse) in der Unterseite
    -> Formschluss statt Presssitz, das Moment laeuft ueber die Werksverzahnung
  * Durchgangsbohrung fuer die Hornnabe (gleichzeitig Zugang zur Zentralschraube)
  * 2 Bohrungen + Senkungen fuer M2-Blechschrauben durch die beiden AEUSSEREN
    Hornloecher (von oben eingedreht, sie schneiden ihr Gewinde im Horn)
  * Gelenkbohrung mit Senkung fuer den Schraubenkopf an der Unterseite

Warum das Ganze: die Original-Kurbel ist eine 3 mm dicke Platte mit Oe5-Bohrung
direkt auf der Servoverzahnung. Gedruckt bleiben davon ca. 2 mm Eingriffslaenge
auf einer faktisch glatten Bohrung uebrig - deshalb rutscht sie durch. Hier
uebernimmt das Originalhorn den Formschluss, der Druck sieht nur noch Scherung
an zwei M2-Schrauben.

Vor dem ersten Lauf: HORN NACHMESSEN
------------------------------------
Die Hornmasse (horn_*) schwanken je nach Hersteller deutlich. Mit dem
Messschieber am eigenen Horn pruefen und unten in DEFAULTS anpassen (oder nach
dem Lauf direkt in den Fusion-Parametern aendern, Aenderungen -> Modell baut neu).

Ausfuehren: Utilities -> Scripts and Add-Ins -> Scripts -> KurbelHuelsenschieber
Alle Masse in mm.
"""

import math
import traceback

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Parameter (alles in mm / Grad). Werte hier oder spaeter in Fusion aendern.
# ---------------------------------------------------------------------------
DEFAULTS = [
    # (Name, Wert, Einheit, Kommentar)
    ('hebel_laenge',     24.0, 'mm',  'Achsabstand Servowelle -> Gelenkbolzen (Ist=24, Variante A=27)'),
    ('dicke',             8.0, 'mm',  'Plattendicke = Nabenhoehe (Original nur 3 mm - zu wenig)'),
    ('naben_d',          16.0, 'mm',  'Aussendurchmesser an der Nabe'),
    ('arm_breite',       10.0, 'mm',  'Breite des Hebelarms = Durchmesser am Gelenkauge'),

    ('horn_winkel',       0.0, 'deg', 'Winkel Hornarm gegen Hebelrichtung (0 = gleiche Richtung)'),
    ('horn_nabe_d',       7.0, 'mm',  'MESSEN: Aussendurchmesser der Hornnabe'),
    ('horn_arm_l',       16.0, 'mm',  'MESSEN: Laenge des Hornarms ab Wellenmitte'),
    ('horn_arm_b_innen',  6.5, 'mm',  'MESSEN: Armbreite an der Nabe'),
    ('horn_arm_b_aussen', 4.0, 'mm',  'MESSEN: Armbreite an der Spitze'),
    ('horn_arm_dicke',    1.5, 'mm',  'MESSEN: Dicke des Hornarms'),
    # Bewusst NICHT zwei benachbarte Hornloecher: bei ~2,5 mm Lochteilung wuerden
    # die Schraubenkoepfe (und ihre Senkungen) ineinanderlaufen. Deshalb das
    # zweite und das aeusserste Loch nehmen.
    ('horn_loch_1',       8.0, 'mm',  'MESSEN: Abstand 2. Hornloch ab Wellenmitte'),
    ('horn_loch_2',      13.0, 'mm',  'MESSEN: Abstand 4. (aeusserstes) Hornloch ab Wellenmitte'),

    ('spiel',            0.15, 'mm',  'Taschenspiel pro Seite (bei strammem Drucker 0,2)'),
    ('schraub_d',         2.1, 'mm',  'Durchgangsbohrung M2-Blechschraube'),
    ('kopf_d',            4.2, 'mm',  'Senkung Schraubenkopf M2'),
    ('kopf_t',            1.6, 'mm',  'Tiefe Senkung Schraubenkopf M2'),

    ('gelenk_bohrung',    3.2, 'mm',  'Gelenkbohrung (M3 = 3,2 / Kulisse M4 = 4,2)'),
    ('gelenk_senk_d',     6.4, 'mm',  'Senkung Schraubenkopf am Gelenk (Unterseite)'),
    ('gelenk_senk_t',     3.0, 'mm',  'Tiefe dieser Senkung'),
]

# Taschentiefe bewusst 0,2 mm FLACHER als der Hornarm: die Kurbel liegt damit
# sicher auf dem Horn auf und schleift nie am Servogehaeuse.
TASCHE_EXPR = 'horn_arm_dicke - 0.2 mm'
# Hornnabe soll frei durchtreten, gleichzeitig Zugang zur Zentralschraube.
NABENBOHRUNG_EXPR = 'horn_nabe_d + 0.4 mm'


def run(context):
    ui = None
    fehler = []
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # --- Konvention: immer ein neues Dokument, nie ins aktive hineinbauen
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = 'Kurbel Huelsenschieber'
        except RuntimeError:
            pass  # rein kosmetisch

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.unitsManager.defaultLengthUnits = 'mm'
        root = design.rootComponent

        werte = _parameter_anlegen(design)
        warnungen = _pruefen(werte)
        _bauen(root, werte, fehler)

        app.activeViewport.fit()

        # Schraube soll den Hornarm gerade durchgreifen, aber nicht darueber hinaus
        schraubenlaenge = werte['dicke'] - werte['kopf_t'] + werte['horn_arm_dicke']
        hinweis = (
            'Kurbel erzeugt.\n\n'
            'Hebellaenge {hebel_laenge:.1f} mm, Dicke {dicke:.1f} mm, '
            'Nabe Oe{naben_d:.1f} mm.\n'
            'Passende Schrauben: 2x M2 x {schraube:.0f} mm (Blechschraube).\n\n'
            'Naechster Schritt: Hornmasse (horn_*) am eigenen Horn nachmessen und '
            'in den Parametern korrigieren.'
        ).format(schraube=schraubenlaenge, **werte)
        if warnungen:
            hinweis += '\n\nPruefen:\n- ' + '\n- '.join(warnungen)
        if fehler:
            hinweis += ('\n\nNicht gesetzte Skizzen-Bedingungen (Geometrie ist trotzdem '
                        'korrekt, nur nicht voll parametrisch):\n- ' + '\n- '.join(fehler))
        ui.messageBox(hinweis, 'Kurbel Huelsenschieber')

    except Exception:
        if ui:
            ui.messageBox('Fehler:\n{}'.format(traceback.format_exc()),
                          'Kurbel Huelsenschieber')


# ---------------------------------------------------------------------------
# Parameter
# ---------------------------------------------------------------------------
def _parameter_anlegen(design):
    """Legt die User-Parameter an und liefert die Zahlenwerte als dict zurueck."""
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
# Plausibilitaet - faengt die typischen Fehler nach dem Nachmessen ab
# ---------------------------------------------------------------------------
def _pruefen(w):
    warnungen = []

    abstand = abs(w['horn_loch_2'] - w['horn_loch_1'])
    if abstand < w['kopf_d'] + 0.5:
        warnungen.append(
            'Lochabstand {:.1f} mm ist zu klein fuer Senkungen Oe{:.1f} - die Koepfe '
            'laufen ineinander. Zwei weiter auseinanderliegende Hornloecher waehlen.'
            .format(abstand, w['kopf_d']))

    naben_r = w['naben_d'] / 2.0
    bohrung_r = (w['horn_nabe_d'] + 0.4) / 2.0
    if naben_r - bohrung_r < 3.0:
        warnungen.append(
            'Nur {:.1f} mm Wand um die Nabenbohrung - naben_d vergroessern (>= {:.1f} mm).'
            .format(naben_r - bohrung_r, (bohrung_r + 3.0) * 2.0))

    innen_r = w['horn_loch_1'] - w['kopf_d'] / 2.0
    if innen_r < bohrung_r + 1.0:
        warnungen.append(
            'Die innere Senkung schneidet fast in die Nabenbohrung - horn_loch_1 '
            'weiter aussen waehlen.')

    if w['horn_arm_l'] + w['horn_arm_b_aussen'] / 2.0 > w['hebel_laenge'] - w['gelenk_senk_d'] / 2.0:
        warnungen.append(
            'Hornarm reicht bis in die Gelenksenkung - hebel_laenge vergroessern oder '
            'kuerzeres Horn verwenden.')

    if w['horn_arm_b_innen'] / 2.0 + w['spiel'] > w['naben_d'] / 2.0:
        warnungen.append('Hornarm ist breiter als die Nabe - naben_d vergroessern.')

    if w['dicke'] <= w['gelenk_senk_t'] + 2.0:
        warnungen.append(
            'Zu wenig Restmaterial unter der Gelenksenkung - dicke erhoehen oder '
            'gelenk_senk_t verringern.')

    return warnungen


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _pt(x_mm, y_mm):
    """Skizzenpunkt aus mm - die API rechnet intern in cm."""
    return adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, 0.0)


def _dreh(x_mm, y_mm, winkel_grad):
    """Dreht einen Punkt um den Ursprung (fuer die Hornrichtung)."""
    a = math.radians(winkel_grad)
    return (x_mm * math.cos(a) - y_mm * math.sin(a),
            x_mm * math.sin(a) + y_mm * math.cos(a))


def _pt_gedreht(x_mm, y_mm, winkel_grad):
    x, y = _dreh(x_mm, y_mm, winkel_grad)
    return _pt(x, y)


def _versuch(fehler, beschreibung, funktion):
    """Bedingungen/Bemassungen sind Kuer, nicht Pflicht.

    Die Geometrie wird numerisch korrekt gezeichnet. Schlaegt eine Bedingung fehl
    (z. B. weil Fusion sie als ueberbestimmt ablehnt), laeuft das Skript weiter
    und meldet es am Ende - statt mittendrin abzubrechen.
    """
    try:
        return funktion()
    except Exception:
        fehler.append(beschreibung)
        return None


def _alle_profile(sketch):
    profile = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        profile.add(sketch.profiles.item(i))
    return profile


def _extrudieren(root, profil, ausdruck, operation):
    return root.features.extrudeFeatures.addSimple(
        profil, adsk.core.ValueInput.createByString(ausdruck), operation)


# ---------------------------------------------------------------------------
# Geometrie
# ---------------------------------------------------------------------------
def _bauen(root, w, fehler):
    NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    VEREINEN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    SCHNEIDEN = adsk.fusion.FeatureOperations.CutFeatureOperation
    HORIZONTAL = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation

    xy = root.xYConstructionPlane
    laenge = w['hebel_laenge']
    halbe_breite = w['arm_breite'] / 2.0
    # Durchgangsbohrungen etwas laenger als das Teil - sauberer Schnitt
    durch = 'dicke + 2 mm'

    # --- 1) Grundkoerper: Langloch von der Nabe zum Gelenkauge ---------------
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Grundkoerper'
    linien = sk.sketchCurves.sketchLines
    boegen = sk.sketchCurves.sketchArcs

    oben = linien.addByTwoPoints(_pt(0.0, halbe_breite), _pt(laenge, halbe_breite))
    unten = linien.addByTwoPoints(_pt(0.0, -halbe_breite), _pt(laenge, -halbe_breite))
    bogen_r = boegen.addByCenterStartSweep(_pt(laenge, 0.0),
                                           _pt(laenge, halbe_breite), -math.pi)
    bogen_l = boegen.addByCenterStartSweep(_pt(0.0, 0.0),
                                           _pt(0.0, -halbe_breite), -math.pi)

    gc = sk.geometricConstraints
    _versuch(fehler, 'Kontur: Eckpunkt rechts oben',
             lambda: gc.addCoincident(oben.endSketchPoint, bogen_r.startSketchPoint))
    _versuch(fehler, 'Kontur: Eckpunkt rechts unten',
             lambda: gc.addCoincident(bogen_r.endSketchPoint, unten.endSketchPoint))
    _versuch(fehler, 'Kontur: Eckpunkt links unten',
             lambda: gc.addCoincident(unten.startSketchPoint, bogen_l.startSketchPoint))
    _versuch(fehler, 'Kontur: Eckpunkt links oben',
             lambda: gc.addCoincident(bogen_l.endSketchPoint, oben.startSketchPoint))
    _versuch(fehler, 'Kontur: Nabenmitte auf Ursprung',
             lambda: gc.addCoincident(bogen_l.centerSketchPoint, sk.originPoint))
    for nr, (a, b) in enumerate(((oben, bogen_r), (bogen_r, unten),
                                 (unten, bogen_l), (bogen_l, oben)), start=1):
        _versuch(fehler, 'Kontur: Tangente {}'.format(nr),
                 lambda a=a, b=b: gc.addTangent(a, b))
    _versuch(fehler, 'Kontur: gleiche Radien',
             lambda: gc.addEqual(bogen_l, bogen_r))

    sd = sk.sketchDimensions
    _versuch(fehler, 'Kontur: Armbreite', lambda: _bemassung(
        sd.addRadialDimension(bogen_l, _pt(-halbe_breite, halbe_breite), True),
        'arm_breite / 2'))
    _versuch(fehler, 'Kontur: Hebellaenge', lambda: _bemassung(
        sd.addDistanceDimension(bogen_l.centerSketchPoint, bogen_r.centerSketchPoint,
                                HORIZONTAL, _pt(laenge / 2.0, -halbe_breite - 4.0), True),
        'hebel_laenge'))

    _extrudieren(root, _alle_profile(sk), 'dicke', NEU)

    # --- 2) Nabe aufdicken ---------------------------------------------------
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Nabe'
    kreis = sk.sketchCurves.sketchCircles.addByCenterRadius(_pt(0.0, 0.0),
                                                           w['naben_d'] / 20.0)
    _versuch(fehler, 'Nabe: Mitte auf Ursprung',
             lambda: sk.geometricConstraints.addCoincident(kreis.centerSketchPoint,
                                                           sk.originPoint))
    _versuch(fehler, 'Nabe: Durchmesser', lambda: _bemassung(
        sk.sketchDimensions.addDiameterDimension(kreis, _pt(w['naben_d'] / 2.0, 0.0), True),
        'naben_d'))
    _extrudieren(root, _alle_profile(sk), 'dicke', VEREINEN)

    # --- 3) Tasche fuer den Einarm-Hornarm (Unterseite) ----------------------
    # Leicht konisch, wie der Hornarm selbst: an der Nabe breit, zur Spitze schmal.
    a = w['horn_winkel']
    b_innen = w['horn_arm_b_innen'] / 2.0 + w['spiel']
    b_aussen = w['horn_arm_b_aussen'] / 2.0 + w['spiel']
    arm_l = w['horn_arm_l']

    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Hornaufnahme'
    linien = sk.sketchCurves.sketchLines
    linien.addByTwoPoints(_pt_gedreht(0.0, b_innen, a), _pt_gedreht(arm_l, b_aussen, a))
    spitze = sk.sketchCurves.sketchArcs.addByCenterStartSweep(
        _pt_gedreht(arm_l, 0.0, a), _pt_gedreht(arm_l, b_aussen, a), -math.pi)
    linien.addByTwoPoints(_pt_gedreht(arm_l, -b_aussen, a), _pt_gedreht(0.0, -b_innen, a))
    linien.addByTwoPoints(_pt_gedreht(0.0, -b_innen, a), _pt_gedreht(0.0, b_innen, a))
    _versuch(fehler, 'Hornaufnahme: Radius Spitze', lambda: _bemassung(
        sk.sketchDimensions.addRadialDimension(spitze, _pt_gedreht(arm_l + 6.0, 0.0, a), True),
        'horn_arm_b_aussen / 2 + spiel'))
    _extrudieren(root, _alle_profile(sk), TASCHE_EXPR, SCHNEIDEN)

    # --- 4) Durchgang fuer die Hornnabe / Zentralschraube --------------------
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Nabenbohrung'
    kreis = sk.sketchCurves.sketchCircles.addByCenterRadius(
        _pt(0.0, 0.0), (w['horn_nabe_d'] + 0.4) / 20.0)
    _versuch(fehler, 'Nabenbohrung: Mitte auf Ursprung',
             lambda: sk.geometricConstraints.addCoincident(kreis.centerSketchPoint,
                                                           sk.originPoint))
    _versuch(fehler, 'Nabenbohrung: Durchmesser', lambda: _bemassung(
        sk.sketchDimensions.addDiameterDimension(kreis, _pt(0.0, w['horn_nabe_d']), True),
        NABENBOHRUNG_EXPR))
    _extrudieren(root, _alle_profile(sk), durch, SCHNEIDEN)

    # --- 5) Zwei M2-Durchgangsbohrungen in den aeusseren Hornloechern --------
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Schraubenloecher M2'
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        k = sk.sketchCurves.sketchCircles.addByCenterRadius(
            _pt_gedreht(w[schluessel], 0.0, a), w['schraub_d'] / 20.0)
        _versuch(fehler, 'M2-Bohrung {}: Durchmesser'.format(schluessel), lambda k=k: _bemassung(
            sk.sketchDimensions.addDiameterDimension(k, _pt_gedreht(w[schluessel], 3.0, a), True),
            'schraub_d'))
    _extrudieren(root, _alle_profile(sk), durch, SCHNEIDEN)

    # --- 6) Senkungen fuer die M2-Koepfe (von der Oberseite) -----------------
    ebene_eingabe = root.constructionPlanes.createInput()
    ebene_eingabe.setByOffset(xy, adsk.core.ValueInput.createByString('dicke'))
    ebene_oben = root.constructionPlanes.add(ebene_eingabe)
    ebene_oben.name = 'Oberseite'

    sk = root.sketches.addWithoutEdges(ebene_oben)
    sk.name = 'Senkungen M2'
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        k = sk.sketchCurves.sketchCircles.addByCenterRadius(
            _pt_gedreht(w[schluessel], 0.0, a), w['kopf_d'] / 20.0)
        _versuch(fehler, 'Senkung {}: Durchmesser'.format(schluessel), lambda k=k: _bemassung(
            sk.sketchDimensions.addDiameterDimension(k, _pt_gedreht(w[schluessel], 4.0, a), True),
            'kopf_d'))
    # negative Distanz = nach unten ins Material
    _extrudieren(root, _alle_profile(sk), '-kopf_t', SCHNEIDEN)

    # --- 7) Gelenkbohrung ----------------------------------------------------
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Gelenkbohrung'
    kreis = sk.sketchCurves.sketchCircles.addByCenterRadius(
        _pt(laenge, 0.0), w['gelenk_bohrung'] / 20.0)
    _versuch(fehler, 'Gelenkbohrung: Durchmesser', lambda: _bemassung(
        sk.sketchDimensions.addDiameterDimension(kreis, _pt(laenge, 3.0), True),
        'gelenk_bohrung'))
    _versuch(fehler, 'Gelenkbohrung: Lage', lambda: _bemassung(
        sk.sketchDimensions.addDistanceDimension(sk.originPoint, kreis.centerSketchPoint,
                                                 HORIZONTAL, _pt(laenge / 2.0, 6.0), True),
        'hebel_laenge'))
    _extrudieren(root, _alle_profile(sk), durch, SCHNEIDEN)

    # --- 8) Senkung fuer den Gelenk-Schraubenkopf (Unterseite) ---------------
    # Haelt den Kopf weg vom Servogehaeuse und von der Montageplatte.
    sk = root.sketches.addWithoutEdges(xy)
    sk.name = 'Senkung Gelenk'
    kreis = sk.sketchCurves.sketchCircles.addByCenterRadius(
        _pt(laenge, 0.0), w['gelenk_senk_d'] / 20.0)
    _versuch(fehler, 'Senkung Gelenk: Durchmesser', lambda: _bemassung(
        sk.sketchDimensions.addDiameterDimension(kreis, _pt(laenge, 5.0), True),
        'gelenk_senk_d'))
    _extrudieren(root, _alle_profile(sk), 'gelenk_senk_t', SCHNEIDEN)


def _bemassung(dimension, ausdruck):
    """Bindet eine Skizzenbemassung an einen User-Parameter."""
    dimension.parameter.expression = ausdruck
    return dimension
