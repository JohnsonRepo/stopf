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
  * Am Hebelende ein AUGE mit STEHENDER Bohrung Oe4,9 fuer einen Oe5-Bolzen -
    ein abgelaengtes Stueck des gleichen Messingrohrs tut es. Der Bolzen steht
    parallel zur Servowelle und laeuft im Querschlitz des Mitnehmers, der auf
    der Schubstange sitzt.

Warum stehend: die Schubstange laeuft im Gleitlager koaxial zur Huelse und darf
sich nur axial bewegen. Die Kurbel kann sie also nicht halten, sondern muss sie
antreiben - und ein Kurbelende bewegt sich auf einem Kreis. Der Ausgleich quer
zur Schubrichtung passiert im Schlitz des Mitnehmers. Damit das spannungsfrei
laeuft, muss die Gelenkachse parallel zur Servowelle stehen; eine liegende
Achse wuerde das Gestaenge verspannen.

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

Das Bolzenauge in der Seitenansicht (Blick quer zum Hebel):

            | |
          .-| |-.        auge_d aussen, Bohrung bolzen_bohrung
          | | | |   <--  stehende Bohrung, durchgehend: der Bolzen laesst sich
       ---' | | `---          nach oben ODER nach unten durchstecken
       -----| |-----   <-- Unterseite der Kurbel, Z = 0
            | |        <-- Ueberstand zum Mitnehmer hin

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
    ('hebel_laenge',      29.0, 'mm',  'Kurbelradius: Servowelle -> Bolzenachse. Hub = 2*r*sin(52): '
                                       '27 -> 42,6 / 29 -> 45,7 / 31 -> 48,9 mm'),
    ('dicke',              8.0, 'mm',  'Plattendicke = Nabenhoehe (Original nur 3 mm - zu wenig)'),
    ('naben_d',           16.0, 'mm',  'Aussendurchmesser an der Nabe'),
    ('arm_breite',        10.0, 'mm',  'Breite des Hebelarms'),

    # --- Bolzenauge am Hebelende (Oe5-Bolzen, z. B. Stueck Messingrohr) ---
    ('auge_d',            12.0, 'mm',  'Aussendurchmesser des Bolzenauges'),
    ('auge_hoehe',        12.0, 'mm',  'Hoehe des Auges ab Kurbelunterseite = Fuehrungslaenge'),
    ('bolzen_bohrung',     4.9, 'mm',  'Bohrung fuer Oe5-Bolzen - Presssitz; 5,1 wenn geklebt'),
    ('bolzen_ueberstand', 12.0, 'mm',  'Ueberstand zum Mitnehmer: 12 = 10 mm Eingriff im Schlitz bei 2 mm Luft ueberm Auge'),

    # --- Horn: alle Werte am eigenen Horn nachmessen ---
    ('horn_winkel',        0.0, 'deg', 'Winkel Hornarm gegen Hebelrichtung (0 = gleiche Richtung)'),
    ('horn_scheibe_d',     7.4, 'mm',  'GEMESSEN am eigenen Horn: Oe der runden Scheibe'),
    ('horn_kragen_d',      6.2, 'mm',  'GEMESSEN: Oe des erhabenen Kragens ueber der Scheibe'),
    ('horn_arm_l',        15.6, 'mm',  'GEMESSEN: Wellenmitte -> Armspitze'),
    ('horn_arm_b_wurzel',  7.0, 'mm',  'GEMESSEN: Armbreite am Uebergang zur Scheibe'),
    ('horn_arm_b_spitze',  5.0, 'mm',  'GEMESSEN: Armbreite an der Spitze'),
    ('horn_arm_dicke',     1.6, 'mm',  'GEMESSEN: Dicke des Hornarms'),
    # Bewusst NICHT zwei benachbarte Hornloecher: bei ~2,5 mm Lochteilung wuerden
    # die Schraubenkoepfe (und ihre Senkungen) ineinanderlaufen.
    ('horn_loch_1',        9.0, 'mm',  'GEMESSEN: Abstand 2. Hornloch ab Wellenmitte'),
    ('horn_loch_2',       13.0, 'mm',  'GEMESSEN: Abstand 4. (aeusserstes) Hornloch ab Wellenmitte'),

    # --- Passungen und Verschraubung ---
    ('spiel',             0.35, 'mm',  'Taschenspiel pro Seite (0,15 + 0,2 Druck-Toleranz)'),
    ('schraub_d',          2.1, 'mm',  'Durchgangsbohrung M2-Blechschraube'),
    ('kopf_d',             4.2, 'mm',  'Senkung Schraubenkopf M2'),
    ('kopf_t',             1.6, 'mm',  'Tiefe Senkung Schraubenkopf M2'),
]

# Taschentiefe bewusst 0,2 mm FLACHER als der Hornarm: die Kurbel liegt damit
# sicher auf dem Horn auf und schleift nie am Servogehaeuse.
TASCHE_EXPR = 'horn_arm_dicke - 0.2 mm'
# Kragen soll frei durchtreten (0,4 pro Seite - gedruckte Innenkonturen
# schrumpfen), gleichzeitig Zugang zur Zentralschraube.
KRAGEN_LUFT = 0.8
# Servo-Schwenkbereich, aus dem Hub und Schlitzlaenge folgen (SG90 schafft das gut).
SWEEP_GRAD = 104.0


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
        bolzenlaenge = werte['auge_hoehe'] + werte['bolzen_ueberstand']
        hub, quer = _hub_und_querweg(werte)
        schlitz = quer + werte['bolzen_bohrung'] + 2.0
        hinweis = (
            'Kurbel erzeugt.\n\n'
            'Kurbelradius {hebel_laenge:.1f} mm, Dicke {dicke:.1f} mm, '
            'Nabe Oe{naben_d:.1f} mm.\n'
            'Bolzenauge Oe{auge_d:.1f} x {auge_hoehe:.1f} mm, stehende Bohrung '
            'Oe{bolzen_bohrung:.1f} mm.\n\n'
            'Bolzen Oe5 ablaengen auf {bolzenlaenge:.0f} mm '
            '({auge_hoehe:.0f} mm Auge + {bolzen_ueberstand:.0f} mm Ueberstand).\n'
            'Schrauben fuers Horn: 2x M2 x {schraube:.0f} mm (Blechschraube).\n\n'
            'Daraus folgt fuer den Mitnehmer auf der Schubstange:\n'
            '  Hub {hub:.1f} mm bei {sweep:.0f} Grad Servoweg\n'
            '  Bolzen wandert {quer:.1f} mm quer -> Schlitz mindestens '
            '{schlitz:.0f} mm lang, Breite {bolzen_bohrung:.1f} mm + 0,2\n'
            '  Schlitz quer zur Schubrichtung, Mitte auf Hoehe der Stangenachse\n\n'
            'Hornmasse aendern: Werte in DEFAULTS im Skript anpassen und neu '
            'laufen lassen.'
        ).format(schraube=schraubenlaenge, bolzenlaenge=bolzenlaenge, hub=hub,
                 quer=quer, schlitz=schlitz, sweep=SWEEP_GRAD, **werte)
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


def _hub_und_querweg(w):
    """Hub der Schubstange und Querweg des Bolzens im Schlitz.

    Kurbel schwenkt symmetrisch um die Stellung senkrecht zur Schubrichtung.
    Hub  = 2 * r * sin(halber Schwenkwinkel)
    Quer = r * (1 - cos(halber Schwenkwinkel))
    """
    r = w['hebel_laenge']
    halb = math.radians(SWEEP_GRAD / 2.0)
    return 2.0 * r * math.sin(halb), r * (1.0 - math.cos(halb))


def _pruefen(w):
    warnungen = []
    kragen_r = (w['horn_kragen_d'] + KRAGEN_LUFT) / 2.0
    scheibe_r = w['horn_scheibe_d'] / 2.0 + w['spiel']
    naben_r = w['naben_d'] / 2.0

    # --- Bolzenauge ---
    if w['auge_d'] - w['bolzen_bohrung'] < 4.0:
        warnungen.append(
            'Wand um die Bolzenbohrung zu duenn - auge_d auf mindestens '
            '{:.1f} mm vergroessern.'.format(w['bolzen_bohrung'] + 4.0))
    if w['auge_hoehe'] < 2.0 * w['bolzen_bohrung']:
        warnungen.append(
            'Fuehrungslaenge nur {:.1f} mm bei Oe{:.1f} - der Bolzen kippt. '
            'auge_hoehe auf mindestens {:.1f} mm erhoehen.'
            .format(w['auge_hoehe'], w['bolzen_bohrung'], 2.0 * w['bolzen_bohrung']))
    if w['auge_hoehe'] < w['dicke']:
        warnungen.append('auge_hoehe ist kleiner als dicke - das Auge verschwindet in der Platte.')
    if w['bolzen_ueberstand'] <= 0.0:
        warnungen.append('bolzen_ueberstand ist 0 - der Bolzen wuerde nicht ueberstehen.')

    # --- Nabe und Horn ---
    abstand = abs(w['horn_loch_2'] - w['horn_loch_1'])
    if abstand < w['kopf_d'] - 0.5:
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


# ---------------------------------------------------------------------------
# Geometrie
# ---------------------------------------------------------------------------
def _bauen(root, w):
    NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    VEREINEN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    SCHNEIDEN = adsk.fusion.FeatureOperations.CutFeatureOperation

    xy = root.xYConstructionPlane
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

    # --- 2) Bolzenauge am Hebelende ----------------------------------------
    # Stehender Zylinder, hoeher als die Platte: er gibt dem Bolzen
    # Fuehrungslaenge, damit er unter Last nicht kippt.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Bolzenauge')
    _kreis(sk, _pt(laenge, 0.0), w['auge_d'])
    _extrudieren(root, sk, 'auge_hoehe', VEREINEN)

    # --- 3) Stehende Bohrung fuer den Oe5-Bolzen ----------------------------
    # Achse parallel zur Servowelle. Durchgehend, damit der Bolzen wahlweise
    # nach oben oder nach unten durchgesteckt werden kann.
    sk = root.sketches.addWithoutEdges(xy)
    _benennen(sk, 'Bolzenbohrung')
    _kreis(sk, _pt(laenge, 0.0), w['bolzen_bohrung'])
    _extrudieren(root, sk, 'auge_hoehe + 2 mm', SCHNEIDEN)

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
