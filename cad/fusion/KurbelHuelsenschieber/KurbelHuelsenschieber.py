"""
Kurbel fuer den Huelsen-Schieber (Ersatz fuer Pos. 49 aus Filling machine.STEP)
==============================================================================

Erzeugt ein NEUES Fusion-Dokument mit der 3D-druckbaren Servo-Kurbel:

  * Grundkoerper als Langloch (Nabe -> Rohrauge), Hebellaenge frei waehlbar
  * Tasche fuer ein EINARM-Servohorn in der Unterseite: runde Scheibe um die
    Welle + konischer Arm + runde Spitze
    -> Formschluss statt Presssitz, das Moment laeuft ueber die Werksverzahnung
  * Durchgangsbohrung fuer den erhabenen Kragen des Horns (gleichzeitig Zugang
    zur Zentralschraube)
  * 2 Bohrungen + Senkungen fuer M2-Blechschrauben durch zwei NICHT benachbarte
    Hornloecher (von oben eingedreht, sie schneiden ihr Gewinde im Horn)
  * Am Hebelende ein AUGE mit LIEGENDER Bohrung fuer ein Messingrohr
    (OD 5 / ID 3,8). Die Rohrachse steht quer zum Hebel und quer zur
    Servoachse, das Rohr geht durch das Auge hindurch und steht auf einer
    Seite ueber.

Warum das Ganze: die Original-Kurbel ist eine 3 mm dicke Platte mit Oe5-Bohrung
direkt auf der Servoverzahnung. Gedruckt bleiben davon ca. 2 mm Eingriffslaenge
auf einer faktisch glatten Bohrung uebrig - deshalb rutscht sie durch. Hier
uebernimmt das Originalhorn den Formschluss, der Druck sieht nur noch Scherung
an zwei M2-Schrauben.

So ist ein Einarm-Horn aufgebaut (Draufsicht, Wellenmitte links):

        horn_arm_b_wurzel        horn_arm_b_spitze
              |                        |
       .-----------.              .---------.
      /   (O)       \___________ /           \        <- horn_scheibe_d
      \   Scheibe    ___________              |          (runde Scheibe auf
       `-----------`              \          /            Armhoehe)
                                   `--------`
      |<------------ horn_arm_l ------------>|
      (Mitte Welle bis Armspitze)

Der erhabene Kragen (horn_kragen_d) sitzt mittig auf der Scheibe und ragt nach
OBEN, also von der Kurbel weg in die Durchgangsbohrung hinein.

Das Rohrauge in der Seitenansicht (Blick entlang des Hebels):

          .-''-.
        /        \        auge_d aussen, Bohrung rohr_bohrung
       |    (==)  |  <--  Rohrachse auf Hoehe rohr_hoehe ueber der Unterseite
        \        /        (Default = auge_d/2, damit das Auge unten buendig
          `-..-`           mit der Kurbelunterseite abschliesst)
       ------------  <-- Unterseite der Kurbel, Z = 0

Vor dem ersten Lauf: HORN NACHMESSEN
------------------------------------
Die Hornmasse (horn_*) schwanken je nach Hersteller deutlich. Mit dem
Messschieber am eigenen Horn pruefen und unten in DEFAULTS eintragen.

Masse aendern -> Werte in DEFAULTS anpassen und Skript neu laufen lassen. Die
Skizzen sind bewusst fest gezeichnet und tragen keine Bedingungen: ein
Skizzen-Solver, der eine nicht verankerte Kontur verdrehen kann, hat hier schon
einmal eine schiefe Tasche produziert. Parametrisch bleiben die Feature-Masse
(Dicke, Taschentiefe, Senkungstiefen) - die sind gegen so etwas immun.

Ausfuehren: Utilities -> Scripts and Add-Ins -> Scripts -> KurbelHuelsenschieber
Alle Masse in mm.
"""

import math
import traceback

import adsk.core
import adsk.fusion


# ---------------------------------------------------------------------------
# Parameter (alles in mm / Grad)
# ---------------------------------------------------------------------------
DEFAULTS = [
    # --- Kurbel selbst ---
    ('hebel_laenge',      24.0, 'mm',  'Achsabstand Servowelle -> Rohrachse (Ist=24, Variante A=27)'),
    ('dicke',              8.0, 'mm',  'Plattendicke = Nabenhoehe (Original nur 3 mm - zu wenig)'),
    ('naben_d',           16.0, 'mm',  'Aussendurchmesser an der Nabe'),
    ('arm_breite',        10.0, 'mm',  'Breite des Hebelarms'),

    # --- Rohrauge am Hebelende (Messingrohr OD 5 / ID 3,8) ---
    ('auge_d',            12.0, 'mm',  'Aussendurchmesser des Rohrauges'),
    ('auge_hoehe',        12.0, 'mm',  'Hoehe des Auges ab Kurbelunterseite'),
    ('rohr_bohrung',       4.9, 'mm',  'Bohrung fuer Messingrohr OD 5 - Presssitz; 5,1 wenn geklebt'),
    ('rohr_hoehe',         6.0, 'mm',  'Hoehe der Rohrachse ueber der Unterseite (= auge_d/2)'),
    ('rohr_ueberstand',    8.0, 'mm',  'gewuenschter Ueberstand des Rohrs auf einer Seite'),

    # --- Horn: alle Werte am eigenen Horn nachmessen ---
    ('horn_winkel',        0.0, 'deg', 'Winkel Hornarm gegen Hebelrichtung (0 = gleiche Richtung)'),
    ('horn_scheibe_d',     7.2, 'mm',  'MESSEN: Oe der runden Scheibe am Horn (auf Armhoehe)'),
    ('horn_kragen_d',      6.0, 'mm',  'MESSEN: Oe des erhabenen Kragens ueber der Scheibe'),
    ('horn_arm_l',        15.5, 'mm',  'MESSEN: Wellenmitte -> Armspitze'),
    ('horn_arm_b_wurzel',  6.0, 'mm',  'MESSEN: Armbreite am Uebergang zur Scheibe'),
    ('horn_arm_b_spitze',  4.0, 'mm',  'MESSEN: Armbreite an der Spitze'),
    ('horn_arm_dicke',     1.5, 'mm',  'MESSEN: Dicke des Hornarms'),
    # Bewusst NICHT zwei benachbarte Hornloecher: bei ~2,5 mm Lochteilung wuerden
    # die Schraubenkoepfe (und ihre Senkungen) ineinanderlaufen.
    ('horn_loch_1',        7.0, 'mm',  'MESSEN: Abstand 2. Hornloch ab Wellenmitte'),
    ('horn_loch_2',       12.0, 'mm',  'MESSEN: Abstand 4. (aeusserstes) Hornloch ab Wellenmitte'),

    # --- Passungen und Verschraubung ---
    ('spiel',             0.15, 'mm',  'Taschenspiel pro Seite (bei strammem Drucker 0,2)'),
    ('schraub_d',          2.1, 'mm',  'Durchgangsbohrung M2-Blechschraube'),
    ('kopf_d',             4.2, 'mm',  'Senkung Schraubenkopf M2'),
    ('kopf_t',             1.6, 'mm',  'Tiefe Senkung Schraubenkopf M2'),
]

# Taschentiefe bewusst 0,2 mm FLACHER als der Hornarm: die Kurbel liegt damit
# sicher auf dem Horn auf und schleift nie am Servogehaeuse.
TASCHE_EXPR = 'horn_arm_dicke - 0.2 mm'
# Kragen soll frei durchtreten, gleichzeitig Zugang zur Zentralschraube.
KRAGEN_LUFT = 0.4
# Innendurchmesser des Rohrs - geht nicht in die Geometrie ein, nur in den Hinweis.
ROHR_ID = 3.8


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # --- Konvention: immer ein neues Dokument, nie ins aktive hineinbauen
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = 'Kurbel Huelsenschieber'
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

        # Schraube soll den Hornarm gerade durchgreifen, aber nicht darueber hinaus
        schraubenlaenge = werte['dicke'] - werte['kopf_t'] + werte['horn_arm_dicke']
        rohrlaenge = werte['auge_d'] + werte['rohr_ueberstand']
        hinweis = (
            'Kurbel erzeugt.\n\n'
            'Hebellaenge {hebel_laenge:.1f} mm, Dicke {dicke:.1f} mm, '
            'Nabe Oe{naben_d:.1f} mm.\n'
            'Rohrauge Oe{auge_d:.1f} x {auge_hoehe:.1f} mm, Bohrung '
            'Oe{rohr_bohrung:.1f} mm quer zum Hebel.\n\n'
            'Zuschnitt Messingrohr OD 5 / ID {rohr_id:.1f}: {rohrlaenge:.0f} mm '
            '({auge_d:.0f} mm Auge + {rohr_ueberstand:.0f} mm Ueberstand).\n'
            'Passende Schrauben fuers Horn: 2x M2 x {schraube:.0f} mm (Blechschraube).\n\n'
            'Hornmasse aendern: Werte in DEFAULTS im Skript anpassen und neu '
            'laufen lassen.'
        ).format(schraube=schraubenlaenge, rohrlaenge=rohrlaenge, rohr_id=ROHR_ID, **werte)
        if warnungen:
            hinweis += '\n\nPruefen:\n- ' + '\n- '.join(warnungen)
        ui.messageBox(hinweis, 'Kurbel Huelsenschieber')

    except Exception:
        if ui:
            ui.messageBox('Fehler:\n{}'.format(traceback.format_exc()),
                          'Kurbel Huelsenschieber')


def _anzeige_mm(design):
    """Anzeige-Einheit auf mm stellen.

    'defaultLengthUnits' ist nur lesbar - gesetzt wird ueber
    'distanceDisplayUnits' des FusionUnitsManager. Betrifft ohnehin nur die
    Anzeige: alle Masse im Skript tragen ihre Einheit selbst ('24 mm').
    """
    try:
        manager = getattr(design, 'fusionUnitsManager', None) or design.unitsManager
        manager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    except Exception:
        pass


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
def _im_koerper(x, y, w, rand):
    """Liegt der Punkt mit 'rand' Sicherheitsabstand noch im Grundkoerper?"""
    if math.hypot(x, y) <= w['naben_d'] / 2.0 - rand:
        return True
    if 0.0 <= x <= w['hebel_laenge'] and abs(y) <= w['arm_breite'] / 2.0 - rand:
        return True
    if math.hypot(x - w['hebel_laenge'], y) <= w['auge_d'] / 2.0 - rand:
        return True
    return False


def _pruefen(w):
    warnungen = []
    kragen_r = (w['horn_kragen_d'] + KRAGEN_LUFT) / 2.0
    scheibe_r = w['horn_scheibe_d'] / 2.0 + w['spiel']
    naben_r = w['naben_d'] / 2.0
    rohr_r = w['rohr_bohrung'] / 2.0

    # --- Rohrauge ---
    if w['rohr_hoehe'] - rohr_r < 2.0:
        warnungen.append(
            'Nur {:.1f} mm Material unter der Rohrbohrung - rohr_hoehe erhoehen.'
            .format(w['rohr_hoehe'] - rohr_r))
    if w['auge_hoehe'] - w['rohr_hoehe'] - rohr_r < 2.0:
        warnungen.append(
            'Nur {:.1f} mm Material ueber der Rohrbohrung - auge_hoehe erhoehen.'
            .format(w['auge_hoehe'] - w['rohr_hoehe'] - rohr_r))
    if w['auge_d'] - w['rohr_bohrung'] < 4.0:
        warnungen.append(
            'Wand seitlich der Rohrbohrung zu duenn - auge_d auf mindestens '
            '{:.1f} mm vergroessern.'.format(w['rohr_bohrung'] + 4.0))
    if w['rohr_hoehe'] + rohr_r > w['auge_hoehe']:
        warnungen.append('Rohrbohrung liegt hoeher als das Auge - rohr_hoehe pruefen.')
    if w['rohr_ueberstand'] <= 0.0:
        warnungen.append('rohr_ueberstand ist 0 - das Rohr wuerde nicht ueberstehen.')

    # --- Nabe und Horn ---
    abstand = abs(w['horn_loch_2'] - w['horn_loch_1'])
    if abstand < w['kopf_d'] + 0.5:
        warnungen.append(
            'Lochabstand {:.1f} mm ist zu klein fuer Senkungen Oe{:.1f} - die Koepfe '
            'laufen ineinander. Zwei weiter auseinanderliegende Hornloecher waehlen.'
            .format(abstand, w['kopf_d']))

    if naben_r - kragen_r < 3.0:
        warnungen.append(
            'Nur {:.1f} mm Wand um die Kragenbohrung - naben_d auf mindestens '
            '{:.1f} mm vergroessern.'.format(naben_r - kragen_r, (kragen_r + 3.0) * 2.0))

    if scheibe_r > naben_r - 1.0:
        warnungen.append(
            'Die Hornscheibe (Oe{:.1f}) laesst kaum Rand an der Nabe (Oe{:.1f}) - '
            'naben_d vergroessern.'.format(w['horn_scheibe_d'], w['naben_d']))

    if w['horn_kragen_d'] > w['horn_scheibe_d']:
        warnungen.append(
            'horn_kragen_d ist groesser als horn_scheibe_d - vermutlich vertauscht. '
            'Scheibe = flacher Teil auf Armhoehe, Kragen = erhabener Ring darueber.')

    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        innen_r = w[schluessel] - w['kopf_d'] / 2.0
        if innen_r < kragen_r + 1.0:
            warnungen.append(
                'Senkung von {} liegt zu dicht an der Kragenbohrung - Loch weiter '
                'aussen waehlen.'.format(schluessel))
        if w[schluessel] > w['horn_arm_l'] - w['horn_arm_b_spitze'] / 2.0:
            warnungen.append(
                '{} liegt ausserhalb des Hornarms - Wert pruefen.'.format(schluessel))

    # Armspitze und beide Schraubenloecher muessen im Grundkoerper liegen -
    # bei schraegem horn_winkel laeuft der Arm sonst seitlich heraus.
    spitze = _dreh_xy(w['horn_arm_l'], 0.0, w['horn_winkel'])
    if not _im_koerper(spitze[0], spitze[1], w, w['horn_arm_b_spitze'] / 2.0 + w['spiel']):
        warnungen.append(
            'Die Armspitze liegt bei horn_winkel = {:.0f} Grad ausserhalb der Kurbel. '
            'Winkel verkleinern, arm_breite oder naben_d vergroessern.'
            .format(w['horn_winkel']))
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        loch = _dreh_xy(w[schluessel], 0.0, w['horn_winkel'])
        if not _im_koerper(loch[0], loch[1], w, w['kopf_d'] / 2.0 + 0.8):
            warnungen.append(
                'Senkung von {} liegt am oder ueber dem Rand der Kurbel - Winkel oder '
                'Breite anpassen.'.format(schluessel))

    if w['horn_arm_b_wurzel'] / 2.0 + w['spiel'] > naben_r:
        warnungen.append('Hornarm ist breiter als die Nabe - naben_d vergroessern.')

    if w['horn_arm_dicke'] <= 0.4:
        warnungen.append('horn_arm_dicke zu klein - die Tasche wuerde verschwinden.')

    return warnungen


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def _benennen(objekt, name):
    """Namen sind reine Kosmetik - nie das Skript daran scheitern lassen."""
    try:
        objekt.name = name
    except Exception:
        pass


def _pt(x_mm, y_mm):
    """Skizzenpunkt aus mm - die API rechnet intern in cm."""
    return adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, 0.0)


def _pt_auf_ebene(sketch, x_mm, y_mm, z_mm):
    """Globalen Punkt in die Skizzenebene umrechnen.

    Spart das Raten, wie die lokalen Achsen einer Ebene zu den globalen liegen -
    genau daran scheitern Skripte auf der XZ-Ebene sonst gern.
    """
    return sketch.modelToSketchSpace(
        adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0))


def _dreh_xy(x_mm, y_mm, winkel_grad):
    """Dreht einen Punkt um den Ursprung - fuer die Ausrichtung des Hornarms."""
    a = math.radians(winkel_grad)
    return (x_mm * math.cos(a) - y_mm * math.sin(a),
            x_mm * math.sin(a) + y_mm * math.cos(a))


def _pt_gedreht(x_mm, y_mm, winkel_grad):
    return _pt(*_dreh_xy(x_mm, y_mm, winkel_grad))


def _kreis(sketch, mittelpunkt, durchmesser_mm):
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(
        mittelpunkt, durchmesser_mm / 20.0)


def _polygon(sketch, punkte):
    """Geschlossener Linienzug aus einer Punktliste."""
    linien = sketch.sketchCurves.sketchLines
    for i in range(len(punkte)):
        linien.addByTwoPoints(punkte[i], punkte[(i + 1) % len(punkte)])


def _alle_profile(sketch):
    profile = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        profile.add(sketch.profiles.item(i))
    return profile


def _extrudieren(root, sketch, ausdruck, operation):
    """Extrudiert ALLE Profile einer Skizze.

    Die Konturen werden aus sich ueberlappenden Grundformen aufgebaut - Kreis,
    Vieleck, Kreis. Fusion zerlegt das in mehrere Teilprofile; werden alle
    zusammen extrudiert, ergibt das exakt die Vereinigungsflaeche. Das ist
    deutlich robuster als ein einzelner, zusammengehefteter Linienzug.
    """
    return root.features.extrudeFeatures.addSimple(
        _alle_profile(sketch),
        adsk.core.ValueInput.createByString(ausdruck),
        operation)


def _durchbruch(root, sketch, operation):
    """Schneidet durch alles, symmetrisch in beide Richtungen.

    Damit haengt das Ergebnis nicht davon ab, wohin die Normale der Skizzenebene
    zeigt - bei liegenden Bohrungen die haeufigste Fehlerquelle.
    """
    extrudes = root.features.extrudeFeatures
    eingabe = extrudes.createInput(_alle_profile(sketch), operation)
    eingabe.setAllExtent(adsk.fusion.ExtentDirections.SymmetricExtentDirection)
    return extrudes.add(eingabe)


# ---------------------------------------------------------------------------
# Geometrie
# ---------------------------------------------------------------------------
def _bauen(root, w):
    NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    VEREINEN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    SCHNEIDEN = adsk.fusion.FeatureOperations.CutFeatureOperation

    xy = root.xYConstructionPlane
    xz = root.xZConstructionPlane
    laenge = w['hebel_laenge']
    halbe_breite = w['arm_breite'] / 2.0
    winkel = w['horn_winkel']
    durch = 'dicke + 2 mm'   # Durchgangsbohrungen etwas laenger als das Teil

    # --- 1) Grundplatte: Nabe + Arm ----------------------------------------
    # Zwei sich ueberlappende Grundformen statt einer getrimmten Kontur.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Grundkoerper')
    _kreis(sk, _pt(0.0, 0.0), w['naben_d'])
    _polygon(sk, [_pt(0.0, halbe_breite), _pt(laenge, halbe_breite),
                  _pt(laenge, -halbe_breite), _pt(0.0, -halbe_breite)])
    _extrudieren(root, sk, 'dicke', NEU)

    # --- 2) Rohrauge am Hebelende ------------------------------------------
    # Stehender Zylinder, hoeher als die Platte: er muss die liegende Bohrung
    # mit Wand oben und unten umschliessen.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Rohrauge')
    _kreis(sk, _pt(laenge, 0.0), w['auge_d'])
    _extrudieren(root, sk, 'auge_hoehe', VEREINEN)

    # --- 3) Liegende Bohrung fuers Messingrohr ------------------------------
    # Achse quer zum Hebel und quer zur Servoachse. Skizze auf der XZ-Ebene,
    # Schnitt symmetrisch durch alles.
    sk = root.sketches.addWithoutEdges(xz)
    _benennen(sk, 'Rohrbohrung')
    _kreis(sk, _pt_auf_ebene(sk, laenge, 0.0, w['rohr_hoehe']), w['rohr_bohrung'])
    _durchbruch(root, sk, SCHNEIDEN)

    # --- 4) Tasche fuer das Einarm-Horn (Unterseite) ------------------------
    # Runde Scheibe um die Welle + konischer Arm + runde Spitze.
    b_wurzel = w['horn_arm_b_wurzel'] / 2.0 + w['spiel']
    b_spitze = w['horn_arm_b_spitze'] / 2.0 + w['spiel']
    arm_l = w['horn_arm_l']

    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Hornaufnahme')
    _kreis(sk, _pt(0.0, 0.0), w['horn_scheibe_d'] + 2.0 * w['spiel'])
    _kreis(sk, _pt_gedreht(arm_l, 0.0, winkel), w['horn_arm_b_spitze'] + 2.0 * w['spiel'])
    _polygon(sk, [_pt_gedreht(0.0, b_wurzel, winkel),
                  _pt_gedreht(arm_l, b_spitze, winkel),
                  _pt_gedreht(arm_l, -b_spitze, winkel),
                  _pt_gedreht(0.0, -b_wurzel, winkel)])
    _extrudieren(root, sk, TASCHE_EXPR, SCHNEIDEN)

    # --- 5) Durchgang fuer den erhabenen Kragen / Zentralschraube -----------
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Kragenbohrung')
    _kreis(sk, _pt(0.0, 0.0), w['horn_kragen_d'] + KRAGEN_LUFT)
    _extrudieren(root, sk, durch, SCHNEIDEN)

    # --- 6) Zwei M2-Durchgangsbohrungen in den Hornloechern -----------------
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Schraubenloecher M2')
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        _kreis(sk, _pt_gedreht(w[schluessel], 0.0, winkel), w['schraub_d'])
    _extrudieren(root, sk, durch, SCHNEIDEN)

    # --- 7) Senkungen fuer die M2-Koepfe (von der Oberseite) ----------------
    # Ebene auf Hoehe des Senkungsgrundes legen und nach OBEN herausschneiden -
    # so kommt das Skript ohne negative Extrusionsmasse aus.
    ebene_eingabe = root.constructionPlanes.createInput()
    ebene_eingabe.setByOffset(xy, adsk.core.ValueInput.createByString('dicke - kopf_t'))
    ebene_oben = root.constructionPlanes.add(ebene_eingabe)
    _benennen(ebene_oben, 'Senkungsgrund M2')

    sk = root.sketches.addWithoutEdges(ebene_oben)
    _benennen(sk, 'Senkungen M2')
    for schluessel in ('horn_loch_1', 'horn_loch_2'):
        _kreis(sk, _pt_gedreht(w[schluessel], 0.0, winkel), w['kopf_d'])
    _extrudieren(root, sk, 'kopf_t + 1 mm', SCHNEIDEN)
