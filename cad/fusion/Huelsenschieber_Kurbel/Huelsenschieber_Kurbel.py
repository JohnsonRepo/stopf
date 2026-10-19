# Huelsenschieber_Kurbel.py — Kurbeltrieb für den SG90-Hülsenschieber
#
# Erzeugt eine Baugruppe (bewegliche Teile -> Komponenten + Gelenke):
#   Grundplatte     Servorahmen + 2 Stangenhalter + Befestigungs-Langlöcher
#   Kurbelscheibe   sitzt auf dem Doppelarm-Horn des SG90, Kurbelradius = Hub / 2
#   Pleuel          M3-Gelenke an beiden Enden
#   Schlitten       läuft auf 2 × Ø4-Stangen, oben 2 × M3-Einschmelzmutter für den Mitnehmer
#   Fuehrungsstangen, SG90_Referenz   nur zur Kontrolle, werden nicht gedruckt
#
# Lage: Servowelle bei x = y = 0, Schub in +X (Richtung Stopfrohr), Z nach oben,
# Z = 0 = Unterkante Grundplatte. Gebaut in HOME-Stellung (äußerer Totpunkt).
#
# Alle Maße stehen im Block MASSE. Nach dem Testdruck lassen sich die Bohrungs-
# Passungen live im Parameter-Dialog ändern (stange_d, spiel_*, gelenk_loch_d,
# kopf_d, insert_d). Alles andere: Wert im Block ändern und Skript neu ausführen.
#
# Daneben gehört die gleichnamige .manifest-Datei.

import adsk.core, adsk.fusion, traceback, math

SKRIPT_NAME = 'Huelsenschieber_Kurbel'   # = Dateiname des Skripts
REVISION = 1                             # bei jeder Änderung hochzählen

# ============================== MASSE (mm) ==================================
# [?] = Datenblatt-/Erfahrungswert, am eigenen Teil mit dem Messschieber prüfen.

# --- Kinematik ---
HUB = 30.0                  # Schlittenweg LOAD -> HOME (Kurbelradius = HUB / 2)
PLEUEL_L = 55.0             # Lochabstand Pleuel (>= 3 × Kurbelradius)

# --- Passungen (werden als User-Parameter angelegt) ---
SPIEL_PRESS = 0.05          # diametral: Stangen in den Haltern
SPIEL_GLEIT = 0.2           # diametral: Schlitten auf den Stangen
SPIEL_LOCKER = 0.4          # diametral: Servotasche, Schraubenköpfe

# --- Gelenke (M3, Schraube von unten, Kopf versenkt) ---
GELENK_LOCH_D = 2.8         # gedruckt; mit 3,0-mm-Bohrer aufreiben
KOPF_D = 5.5                # M3 DIN 912 Kopf-Ø
KOPF_T = 3.0                # M3 DIN 912 Kopfhöhe
GELENK_AUFBAU = 2.9         # Mutter (2,4) + U-Scheibe (0,5) zwischen Teil und Pleuel
STOPPMUTTER_T = 4.0         # M3 DIN 985

# --- Pleuel ---
PLEUEL_B = 8.0
PLEUEL_T = 4.0

# --- Kurbelscheibe ---
SCHEIBE_D = 42.0
SCHEIBE_T = 6.0
UNTER_KOPF = 1.0            # Material unter dem Kopf der Hornschraube

# --- SG90-Doppelarm-Horn [?] ---
HORN_L = 35.0               # Länge Spitze bis Spitze
HORN_NABE_D = 7.5           # Breite an der Nabe
HORN_SPITZE_D = 4.5         # Breite an den Spitzen
HORN_T = 2.0                # Dicke der Arme
HORN_OBEN_UEBER_FLANSCH = 7.5   # Oberkante Servolasche -> Oberseite Horn
HORN_SPIEL = 0.1            # radial, Horntasche
HORNSCHRAUBE_D = 2.4        # Durchgang Hornschraube
HORNSCHRAUBE_KOPF_D = 4.5   # Kopf-Ø Hornschraube

# --- SG90 [?] ---
SERVO_L = 22.8              # Gehäuselänge
SERVO_B = 12.2              # Gehäusebreite
SERVO_FLANSCH_H = 15.9      # Gehäuseboden -> Unterseite Laschen
SERVO_FLANSCH_T = 2.5       # Laschendicke
SERVO_GEHAEUSE_H = 22.7     # Gehäuseboden -> Gehäuseoberkante (nur Referenz)
SERVO_LASCHEN_L = 32.2      # Länge über die Laschen
SERVO_LOCH_ABSTAND = 27.6   # Abstand Laschenlöcher
SERVO_WELLE_ENDE = 5.9      # Wellenmitte -> nahes Gehäuseende
SERVO_WELLE_D = 4.8
SERVO_LUFT_UNTEN = 1.5      # Servo hängt an den Laschen, Boden bleibt frei
KABEL_B = 6.0

# --- Führung ---
STANGE_D = 4.0
STANGEN_ABSTAND = 18.0
SCHLITTEN_L = 30.0
SCHLITTEN_H = 12.0
SCHLITTEN_WAND = 3.0        # Wand neben den Stangenbohrungen
STANGE_UEBER_SCHLITTEN_UNTEN = 5.0   # Bohrungsmitte über Schlittenunterkante
ZAPFEN_HINTEN = 6.0         # Schlittengelenk ab Schlittenhinterkante
INSERT_D = 4.0              # Einpressbohrung M3-Einschmelzmutter
INSERT_T = 6.7
INSERT_X = 16.0             # erste Einschmelzmutter ab Schlittenhinterkante
INSERT_ABSTAND = 9.0
BLOCK_T = 8.0               # Dicke Stangenhalter in X
BLOCK_WAND = 4.0            # Wand seitlich um die Stange
BLOCK_WAND_OBEN = 3.0
LUFT = 2.0                  # Mindestabstand bewegte Teile

# --- Grundplatte ---
BASIS_T = 5.0
BREITE = 42.0
RAHMEN_WAND = 3.0
RAND = 3.0
LANGLOCH_L = 10.0           # Befestigungs-Langlöcher (Verstellung in X)
DURCHGANG_M3 = 3.4
# ============================================================================

# --- Materialien (Standardblock, in jedem Skript identisch) ------------------
# Eigene Materialien: Name -> (Basis in Bibliothek, Basis-Dichte, Ziel-Dichte) in g/cm³
EIGENE_MATERIALIEN = {
    'PLA':  ('ABS Plastic', 1.06, 1.24),
    'PETG': ('ABS Plastic', 1.06, 1.27),
}

def material_zuweisen(app, design, ziel, name):
    """Setzt das physikalische Material auf `ziel` (BRepBody oder Component)."""
    mat = design.materials.itemByName(name)
    if not mat and name in EIGENE_MATERIALIEN:
        basis_name, d_basis, d_ziel = EIGENE_MATERIALIEN[name]
        basis = _bibliotheksmaterial(app, basis_name)
        if basis:
            mat = design.materials.addByCopy(basis, name)
            prop = adsk.core.FloatProperty.cast(
                mat.materialProperties.itemByName('Density'))
            prop.value *= d_ziel / d_basis      # relativ skalieren, einheitenfrei
    if not mat:
        gefunden = _bibliotheksmaterial(app, name)
        mat = design.materials.addByCopy(gefunden, name) if gefunden else None
    if mat:
        ziel.material = mat
    return mat        # None = nicht gefunden -> Fusion-Default bleibt, kein Abbruch

def _bibliotheksmaterial(app, name):
    """Alle Materialbibliotheken durchsuchen: erst exakter Name, dann Teilstring."""
    libs = app.materialLibraries
    for k in range(libs.count):
        m = libs.item(k).materials.itemByName(name)
        if m:
            return m
    nl = name.lower()
    for k in range(libs.count):
        mats = libs.item(k).materials
        for i in range(mats.count):
            if nl in mats.item(i).name.lower():
                return mats.item(i)
    return None
# -----------------------------------------------------------------------------

# --- Validierung (Standardblock, in jedem Skript identisch) -------------------
def validierungs_bericht(app, design, ui, hinweise=None):
    """Meldet am Skriptende alle Körper mit Masse und Abmessungen per
    messageBox. Scheitert nie – Validierung darf das Skript nicht abbrechen."""
    try:
        zeilen = ['{} (Rev. {})'.format(SKRIPT_NAME, REVISION), '']
        comps = design.allComponents
        for k in range(comps.count):
            comp = comps.item(k)
            for i in range(comp.bRepBodies.count):
                b = comp.bRepBodies.item(i)
                bb = b.boundingBox
                gr = ((bb.maxPoint.x - bb.minPoint.x) * 10,
                      (bb.maxPoint.y - bb.minPoint.y) * 10,
                      (bb.maxPoint.z - bb.minPoint.z) * 10)
                praefix = '' if comps.count == 1 else comp.name + ' > '
                status = '' if b.isLightBulbOn else '  [ausgeblendet]'
                zeilen.append('{}{}: {:.1f} g, {:.0f} x {:.0f} x {:.0f} mm{}'.format(
                    praefix, b.name, b.physicalProperties.mass * 1000,
                    gr[0], gr[1], gr[2], status))
        if hinweise:
            zeilen += [''] + list(hinweise)
        ui.messageBox('\n'.join(zeilen), 'Validierung')
    except:
        pass
# -----------------------------------------------------------------------------

NEU = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def P(x, y, z=0.0):
    """Punkt aus mm-Koordinaten (die API rechnet intern in cm)."""
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)

def vs(ausdruck):
    return adsk.core.ValueInput.createByString(ausdruck)

def vmm(wert_mm):
    return adsk.core.ValueInput.createByReal(wert_mm / 10.0)


def geometrie():
    """Alle abgeleiteten Lagen (mm). Hängen an den MASSE-Konstanten,
    nicht live an den User-Parametern."""
    g = {}
    r = HUB / 2.0
    g['r'] = r
    g['x_home'] = r + PLEUEL_L           # Schlittengelenk im äußeren Totpunkt
    g['x_load'] = PLEUEL_L - r           # Schlittengelenk im inneren Totpunkt

    # Höhen: Servo hängt an den Laschen auf dem Rahmen
    g['z_rahmen'] = SERVO_LUFT_UNTEN + SERVO_FLANSCH_H
    g['z_horn_oben'] = g['z_rahmen'] + SERVO_FLANSCH_T + HORN_OBEN_UEBER_FLANSCH
    g['taschen_t'] = HORN_T - 0.3        # Scheibe bleibt 0,3 über der Hornunterseite
    g['z_sch_u'] = g['z_horn_oben'] - g['taschen_t']
    g['z_sch_o'] = g['z_sch_u'] + SCHEIBE_T
    g['z_schl_o'] = g['z_sch_o']         # gleiche Höhe -> Pleuel liegt waagrecht
    g['z_schl_u'] = g['z_schl_o'] - SCHLITTEN_H
    g['z_stange'] = g['z_schl_u'] + STANGE_UEBER_SCHLITTEN_UNTEN
    g['z_block_o'] = g['z_stange'] + STANGE_D / 2.0 + BLOCK_WAND_OBEN
    g['z_pl_u'] = g['z_sch_o'] + GELENK_AUFBAU
    g['z_servo_o'] = SERVO_LUFT_UNTEN + SERVO_GEHAEUSE_H
    g['senk_horn_t'] = SCHEIBE_T - g['taschen_t'] - UNTER_KOPF
    # Gelenkschrauben: unter dem Kopf bleibt in Scheibe und Schlitten gleich viel
    # Material -> an beiden Gelenken dieselbe Schraubenlänge
    g['rest_unter_kopf'] = SCHEIBE_T - (KOPF_T + 0.3)
    g['senk_schl_t'] = SCHLITTEN_H - g['rest_unter_kopf']
    g['schraube_min'] = (g['rest_unter_kopf'] + GELENK_AUFBAU + PLEUEL_T
                         + 0.5 + STOPPMUTTER_T)
    g['schraube'] = next((l for l in (12, 16, 20, 25, 30, 35)
                          if l >= g['schraube_min'] + 1.0), 40)

    # Servo: Welle bei x = 0, nahes Gehäuseende in +X
    g['cx'] = SERVO_WELLE_ENDE - SERVO_L / 2.0
    g['tasche_l'] = SERVO_L + SPIEL_LOCKER
    g['tasche_b'] = SERVO_B + SPIEL_LOCKER
    g['rahmen_hl'] = SERVO_LASCHEN_L / 2.0 + 1.5
    g['rahmen_hb'] = g['tasche_b'] / 2.0 + RAHMEN_WAND

    # Schlitten in HOME-Stellung
    g['x_s0'] = g['x_home'] - ZAPFEN_HINTEN
    g['x_s1'] = g['x_s0'] + SCHLITTEN_L
    g['schl_hb'] = STANGEN_ABSTAND / 2.0 + STANGE_D / 2.0 + SCHLITTEN_WAND
    g['inserts'] = [(g['x_s0'] + INSERT_X, 0.0),
                    (g['x_s0'] + INSERT_X + INSERT_ABSTAND, 0.0)]

    # Stangenhalter: hinten vor dem Schlitten in LOAD, vorne hinter ihm in HOME
    g['x_bh1'] = g['x_load'] - ZAPFEN_HINTEN - LUFT
    g['x_bh0'] = g['x_bh1'] - BLOCK_T
    g['x_bv0'] = g['x_s1'] + LUFT
    g['x_bv1'] = g['x_bv0'] + BLOCK_T
    g['block_hb'] = STANGEN_ABSTAND / 2.0 + STANGE_D / 2.0 + BLOCK_WAND
    g['stangen_l'] = g['x_bv1'] - g['x_bh0']

    # Grundplatte und Befestigung (eine Quelle für Langlöcher und Bohrlehre)
    g['x_basis0'] = g['cx'] - g['rahmen_hl'] - RAND
    g['x_basis1'] = g['x_bv1'] + RAND
    yb = BREITE / 2.0 - 5.0
    xh = g['cx'] - 6.5
    xv = (g['x_bh1'] + g['x_bv0']) / 2.0
    g['befestigung'] = [(xh, -yb), (xh, yb), (xv, -yb), (xv, yb)]

    w = []
    if g['x_bh0'] < SCHEIBE_D / 2.0 + LUFT:
        w.append('WARNUNG: hinterer Stangenhalter zu nah an der Kurbelscheibe – PLEUEL_L vergrößern')
    if g['z_pl_u'] - g['z_block_o'] < 1.0:
        w.append('WARNUNG: Pleuel streift die Stangenhalter')
    if g['z_schl_o'] - g['z_block_o'] < 1.5:
        w.append('WARNUNG: kaum Freigang für den Mitnehmer über dem vorderen Stangenhalter')
    if g['senk_horn_t'] < 1.0:
        w.append('WARNUNG: Kurbelscheibe zu dünn für die Senkung der Hornschraube')
    if g['z_sch_u'] - g['z_servo_o'] < 0.5:
        w.append('WARNUNG: Kurbelscheibe streift evtl. das Servogehäuse')
    if PLEUEL_L < 3.0 * r:
        w.append('WARNUNG: Pleuel kürzer als 3 × Kurbelradius – hohe Querkraft')
    g['warnungen'] = w
    return g


def parameter_anlegen(design):
    up = design.userParameters
    up.add('spiel_press', vs('{} mm'.format(SPIEL_PRESS)), 'mm',
           'Presspassung, diametral (Stangen in den Haltern)')
    up.add('spiel_gleit', vs('{} mm'.format(SPIEL_GLEIT)), 'mm',
           'Gleitpassung, diametral (Schlitten auf den Stangen)')
    up.add('spiel_locker', vs('{} mm'.format(SPIEL_LOCKER)), 'mm',
           'Montagespiel, diametral (Schraubenköpfe)')
    up.add('stange_d', vs('{} mm'.format(STANGE_D)), 'mm', 'Ø Führungsstangen (gemessen)')
    up.add('gelenk_loch_d', vs('{} mm'.format(GELENK_LOCH_D)), 'mm',
           'Gelenklöcher gedruckt, auf 3,0 aufreiben')
    up.add('kopf_d', vs('{} mm'.format(KOPF_D)), 'mm', 'Kopf-Ø M3 DIN 912')
    up.add('insert_d', vs('{} mm'.format(INSERT_D)), 'mm', 'Einpressbohrung M3-Einschmelzmutter')


def komponente(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name          # NICHT occ.name (abgeleitet, ':1')
    return occ

def skizze(comp, name, ebene=None):
    sk = comp.sketches.add(ebene if ebene is not None else comp.xYConstructionPlane)
    sk.name = name
    return sk

def alle_profile(sk):
    coll = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        coll.add(sk.profiles.item(i))
    return coll

def rechteck(sk, x0, y0, x1, y1):
    return sk.sketchCurves.sketchLines.addTwoPointRectangle(P(x0, y0), P(x1, y1))

def stadion(sk, x0, x1, y, b):
    """Langloch entlang X: Bogenmittelpunkte bei x0 und x1, Breite b (mm)."""
    r = b / 2.0
    linien = sk.sketchCurves.sketchLines
    boegen = sk.sketchCurves.sketchArcs
    linien.addByTwoPoints(P(x0, y - r), P(x1, y - r))
    linien.addByTwoPoints(P(x1, y + r), P(x0, y + r))
    boegen.addByCenterStartSweep(P(x1, y), P(x1, y - r), math.pi)
    boegen.addByCenterStartSweep(P(x0, y), P(x0, y + r), math.pi)

def kreis(sk, p, d, ausdruck=None):
    """Kreis um Skizzenpunkt p (Point3D in cm), Ø d in mm. Mit `ausdruck`
    hängt der Durchmesser live am User-Parameter (Mittelpunkt fixiert)."""
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(p, d / 20.0)
    if ausdruck:
        c.centerSketchPoint.isFixed = True
        dim = sk.sketchDimensions.addDiameterDimension(
            c, adsk.core.Point3D.create(p.x + d / 20.0 + 0.3, p.y + d / 20.0 + 0.3, 0))
        dim.parameter.expression = ausdruck
    return c

def horn_umriss(sk, spiel):
    """SG90-Doppelarm-Horn entlang ±Y: Nabe + 2 Spitzen + Tangenten-Trapeze.
    Die überlappenden Profile werden immer gemeinsam verwendet."""
    rn = HORN_NABE_D / 2.0 + spiel
    rs = HORN_SPITZE_D / 2.0 + spiel
    d = HORN_L / 2.0 - HORN_SPITZE_D / 2.0
    phi = math.asin((rn - rs) / d)          # Winkel der äußeren Tangente
    kreise = sk.sketchCurves.sketchCircles
    linien = sk.sketchCurves.sketchLines
    kreise.addByCenterRadius(P(0, 0), rn / 10.0)
    for s in (1.0, -1.0):
        kreise.addByCenterRadius(P(0, s * d), rs / 10.0)
        ax, ay = rn * math.cos(phi), s * rn * math.sin(phi)
        bx, by = rs * math.cos(phi), s * (d + rs * math.sin(phi))
        ecken = [P(-ax, ay), P(ax, ay), P(bx, by), P(-bx, by)]
        for i in range(4):
            linien.addByTwoPoints(ecken[i], ecken[(i + 1) % 4])

def extrude_z(comp, sk, z0, h, op, koerper=None):
    """Alle Profile einer XY-Skizze von Höhe z0 aus um h in +Z extrudieren (mm)."""
    feats = comp.features.extrudeFeatures
    ext_in = feats.createInput(alle_profile(sk), op)
    if z0 != 0:
        ext_in.startExtent = adsk.fusion.OffsetStartDefinition.create(vmm(z0))
    ext_in.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(vmm(h)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    if koerper is not None:
        ext_in.participantBodies = [koerper]
    return feats.add(ext_in)

def extrude_sym(comp, sk, laenge, op, koerper=None):
    """Alle Profile symmetrisch zur Skizzenebene extrudieren (Gesamtlänge in mm).
    Richtungsunabhängig – für Durchgangsschnitte und die Stangen."""
    feats = comp.features.extrudeFeatures
    ext_in = feats.createInput(alle_profile(sk), op)
    ext_in.setSymmetricExtent(vmm(laenge), True)
    if koerper is not None:
        ext_in.participantBodies = [koerper]
    return feats.add(ext_in)

def cut_durch(comp, sk, koerper):
    return extrude_sym(comp, sk, 400.0, CUT, koerper)

def bohrlehre(comp, punkte, z, name):
    """Dünne, ausgeblendete Lehrenplatte mit dem Bohrbild `punkte` (mm, XY)."""
    sk = skizze(comp, 'Skizze_Bohrlehre_' + name)
    for x, y in punkte:
        kreis(sk, P(x, y), DURCHGANG_M3)
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    rand = 8.0
    rechteck(sk, min(xs) - rand, min(ys) - rand, max(xs) + rand, max(ys) + rand)
    prof = max((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: p.areaProperties().area)   # Platte inkl. Löcher
    feats = comp.features.extrudeFeatures
    ext_in = feats.createInput(prof, NEU)
    ext_in.startExtent = adsk.fusion.OffsetStartDefinition.create(vmm(z))
    ext_in.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(vmm(3.0)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    lehre = feats.add(ext_in).bodies.item(0)
    lehre.name = 'Bohrlehre_' + name
    lehre.isLightBulbOn = False          # Konvention: standardmäßig ausgeblendet
    return lehre


# --- Gelenke ------------------------------------------------------------------
def zylinder(body, punkt_mm, achse, radius_mm):
    """Zylinderfläche von body mit Achse durch punkt_mm, parallel zu achse."""
    p = P(*punkt_mm)
    a = adsk.core.Vector3D.create(*achse)
    for i in range(body.faces.count):
        f = body.faces.item(i)
        if f.geometry.surfaceType != adsk.core.SurfaceTypes.CylinderSurfaceType:
            continue
        cyl = adsk.core.Cylinder.cast(f.geometry)
        ax = cyl.axis.copy()
        ax.normalize()
        if abs(abs(ax.dotProduct(a)) - 1.0) > 1e-6:
            continue
        if cyl.origin.vectorTo(p).crossProduct(ax).length > 1e-3:
            continue
        if abs(cyl.radius - radius_mm / 10.0) > 1e-3:
            continue
        return f
    return None

def gelenk(root, occ1, occ2, flaeche, art, name, hinweise):
    """As-Built-Gelenk an der Zylinderachse von `flaeche` (gehört zu occ1).
    Fehler werden gemeldet, brechen das Skript aber nicht ab."""
    try:
        if flaeche is None:
            hinweise.append('Gelenk {}: Zylinderfläche nicht gefunden'.format(name))
            return None
        proxy = flaeche.createForAssemblyContext(occ1)
        geo = None
        for kp in (adsk.fusion.JointKeyPointTypes.MiddleKeyPoint,
                   adsk.fusion.JointKeyPointTypes.CenterKeyPoint,
                   adsk.fusion.JointKeyPointTypes.StartKeyPoint):
            try:
                geo = adsk.fusion.JointGeometry.createByNonPlanarFace(proxy, kp)
                break
            except:
                geo = None
        if geo is None:
            hinweise.append('Gelenk {}: keine Gelenkgeometrie'.format(name))
            return None
        ab_in = root.asBuiltJoints.createInput(occ1, occ2, geo)
        z = adsk.fusion.JointDirections.ZAxisJointDirection   # = Zylinderachse
        if art == 'dreh':
            ab_in.setAsRevoluteJointMotion(z)
        elif art == 'schieb':
            ab_in.setAsSliderJointMotion(z)
        else:
            ab_in.setAsCylindricalJointMotion(z)
        j = root.asBuiltJoints.add(ab_in)
        j.name = name
        return j
    except:
        hinweise.append('Gelenk {} nicht angelegt: {}'.format(
            name, traceback.format_exc().strip().splitlines()[-1]))
        return None
# -----------------------------------------------------------------------------


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # 1) Neues Dokument — nie ins aktive Dokument bauen
        doc = app.documents.add(
            adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            doc.name = '{}_r{}'.format(SKRIPT_NAME, REVISION)   # rein kosmetisch
        except RuntimeError:
            pass

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        parameter_anlegen(design)
        g = geometrie()
        hinweise = []
        r = g['r']

        # ---------------- Grundplatte ----------------
        occ_basis = komponente(root, 'Grundplatte')
        cb = occ_basis.component

        sk = skizze(cb, 'Platte')
        rechteck(sk, g['x_basis0'], -BREITE / 2.0, g['x_basis1'], BREITE / 2.0)
        basis = extrude_z(cb, sk, 0, BASIS_T, NEU).bodies.item(0)
        basis.name = 'Grundplatte'

        # Servorahmen (1 mm in die Platte überlappend -> saubere Vereinigung)
        sk = skizze(cb, 'Servorahmen')
        rechteck(sk, g['cx'] - g['rahmen_hl'], -g['rahmen_hb'],
                 g['cx'] + g['rahmen_hl'], g['rahmen_hb'])
        extrude_z(cb, sk, BASIS_T - 1.0, g['z_rahmen'] - BASIS_T + 1.0, JOIN, basis)

        # Stangenhalter hinten + vorne
        sk = skizze(cb, 'Stangenhalter')
        for x0, x1 in ((g['x_bh0'], g['x_bh1']), (g['x_bv0'], g['x_bv1'])):
            rechteck(sk, x0, -g['block_hb'], x1, g['block_hb'])
        extrude_z(cb, sk, BASIS_T - 1.0, g['z_block_o'] - BASIS_T + 1.0, JOIN, basis)

        # Servotasche, durchgehend (Servo hängt an den Laschen)
        sk = skizze(cb, 'Servotasche')
        rechteck(sk, g['cx'] - g['tasche_l'] / 2.0, -g['tasche_b'] / 2.0,
                 g['cx'] + g['tasche_l'] / 2.0, g['tasche_b'] / 2.0)
        cut_durch(cb, sk, basis)

        # Kabelschlitze an beiden Enden (hinten bis zur Plattenkante)
        sk = skizze(cb, 'Kabelschlitze')
        rechteck(sk, g['x_basis0'] - 1.0, -KABEL_B / 2.0,
                 g['cx'] - g['tasche_l'] / 2.0 + 0.5, KABEL_B / 2.0)
        rechteck(sk, g['cx'] + g['tasche_l'] / 2.0 - 0.5, -KABEL_B / 2.0,
                 g['cx'] + g['rahmen_hl'] + 1.0, KABEL_B / 2.0)
        extrude_z(cb, sk, SERVO_LUFT_UNTEN, BASIS_T + 6.0 - SERVO_LUFT_UNTEN, CUT, basis)

        # Vorbohrungen Laschenschrauben, als kurze Schlitze in X (Lochabstand [?])
        sk = skizze(cb, 'Laschenloecher')
        for s in (-1.0, 1.0):
            x = g['cx'] + s * SERVO_LOCH_ABSTAND / 2.0
            rechteck(sk, x - 1.2, -0.75, x + 1.2, 0.75)
        extrude_z(cb, sk, g['z_rahmen'] - 6.0, 7.0, CUT, basis)

        # Stangenbohrungen in beiden Haltern (live: stange_d + spiel_press)
        sk = skizze(cb, 'Stangenbohrungen_Halter', cb.yZConstructionPlane)
        for s in (-1.0, 1.0):
            kreis(sk, sk.modelToSketchSpace(P(0, s * STANGEN_ABSTAND / 2.0, g['z_stange'])),
                  STANGE_D + SPIEL_PRESS, 'stange_d + spiel_press')
        cut_durch(cb, sk, basis)

        # Befestigungs-Langlöcher (Verstellung in X)
        sk = skizze(cb, 'Befestigung')
        versatz = (LANGLOCH_L - DURCHGANG_M3) / 2.0
        for x, y in g['befestigung']:
            stadion(sk, x - versatz, x + versatz, y, DURCHGANG_M3)
        cut_durch(cb, sk, basis)

        bohrlehre(cb, g['befestigung'], g['z_pl_u'] + 25.0, 'Grundplatte')

        # ---------------- Kurbelscheibe ----------------
        occ_kurbel = komponente(root, 'Kurbelscheibe')
        ck = occ_kurbel.component

        sk = skizze(ck, 'Scheibe')
        kreis(sk, P(0, 0), SCHEIBE_D)
        scheibe = extrude_z(ck, sk, g['z_sch_u'], SCHEIBE_T, NEU).bodies.item(0)
        scheibe.name = 'Kurbelscheibe'

        # Horntasche von unten, quer zum Kurbelzapfen (Horn entlang ±Y)
        sk = skizze(ck, 'Horntasche')
        horn_umriss(sk, HORN_SPIEL)
        extrude_z(ck, sk, g['z_sch_u'], g['taschen_t'], CUT, scheibe)

        # Hornschraube: Durchgang + Senkung von oben
        sk = skizze(ck, 'Hornschraube')
        kreis(sk, P(0, 0), HORNSCHRAUBE_D)
        cut_durch(ck, sk, scheibe)
        sk = skizze(ck, 'Hornschraube_Senkung')
        kreis(sk, P(0, 0), HORNSCHRAUBE_KOPF_D + SPIEL_LOCKER)
        extrude_z(ck, sk, g['z_sch_o'] - g['senk_horn_t'], g['senk_horn_t'] + 1.0,
                  CUT, scheibe)

        # Kurbelzapfen bei r: Loch + Kopfsenkung von unten
        sk = skizze(ck, 'Kurbelzapfen')
        kreis(sk, P(r, 0), GELENK_LOCH_D, 'gelenk_loch_d')
        cut_durch(ck, sk, scheibe)
        sk = skizze(ck, 'Kurbelzapfen_Kopf')
        kreis(sk, P(r, 0), KOPF_D + SPIEL_LOCKER, 'kopf_d + spiel_locker')
        extrude_z(ck, sk, g['z_sch_u'] - 1.0, SCHEIBE_T - g['rest_unter_kopf'] + 1.0,
                  CUT, scheibe)

        # ---------------- Pleuel ----------------
        occ_pleuel = komponente(root, 'Pleuel')
        cp = occ_pleuel.component

        sk = skizze(cp, 'Pleuel')
        stadion(sk, r, g['x_home'], 0.0, PLEUEL_B)
        pleuel = extrude_z(cp, sk, g['z_pl_u'], PLEUEL_T, NEU).bodies.item(0)
        pleuel.name = 'Pleuel'

        sk = skizze(cp, 'Gelenkloecher')
        for x in (r, g['x_home']):
            kreis(sk, P(x, 0), GELENK_LOCH_D, 'gelenk_loch_d')
        cut_durch(cp, sk, pleuel)

        # ---------------- Schlitten ----------------
        occ_schlitten = komponente(root, 'Schlitten')
        cs = occ_schlitten.component

        sk = skizze(cs, 'Schlitten')
        rechteck(sk, g['x_s0'], -g['schl_hb'], g['x_s1'], g['schl_hb'])
        schlitten = extrude_z(cs, sk, g['z_schl_u'], SCHLITTEN_H, NEU).bodies.item(0)
        schlitten.name = 'Schlitten'

        sk = skizze(cs, 'Stangenbohrungen_Schlitten', cs.yZConstructionPlane)
        for s in (-1.0, 1.0):
            kreis(sk, sk.modelToSketchSpace(P(0, s * STANGEN_ABSTAND / 2.0, g['z_stange'])),
                  STANGE_D + SPIEL_GLEIT, 'stange_d + spiel_gleit')
        cut_durch(cs, sk, schlitten)

        sk = skizze(cs, 'Schlittengelenk')
        kreis(sk, P(g['x_home'], 0), GELENK_LOCH_D, 'gelenk_loch_d')
        cut_durch(cs, sk, schlitten)
        sk = skizze(cs, 'Schlittengelenk_Kopf')
        kreis(sk, P(g['x_home'], 0), KOPF_D + SPIEL_LOCKER, 'kopf_d + spiel_locker')
        extrude_z(cs, sk, g['z_schl_u'] - 1.0, g['senk_schl_t'] + 1.0, CUT, schlitten)

        # Einschmelzmuttern für den Mitnehmer (von oben)
        sk = skizze(cs, 'Mitnehmer_Inserts')
        for x, y in g['inserts']:
            kreis(sk, P(x, y), INSERT_D, 'insert_d')
        extrude_z(cs, sk, g['z_schl_o'] - INSERT_T, INSERT_T + 1.0, CUT, schlitten)

        bohrlehre(cs, g['inserts'], g['z_pl_u'] + 35.0, 'Mitnehmer')

        # ---------------- Referenzen (nicht drucken) ----------------
        occ_stangen = komponente(root, 'Fuehrungsstangen')
        cst = occ_stangen.component
        sk = skizze(cst, 'Stangen', cst.yZConstructionPlane)
        for s in (-1.0, 1.0):
            kreis(sk, sk.modelToSketchSpace(P(0, s * STANGEN_ABSTAND / 2.0, g['z_stange'])),
                  STANGE_D)
        ext = extrude_sym(cst, sk, g['stangen_l'], NEU)
        for i in range(ext.bodies.count):
            ext.bodies.item(i).name = 'Stange_{}'.format(i + 1)
        # symmetrisch gebaut -> Komponente auf Stangenmitte schieben
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(
            (g['x_bh0'] + g['x_bv1']) / 20.0, 0, 0)          # cm
        occ_stangen.transform2 = m
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        occ_servo = komponente(root, 'SG90_Referenz')
        csv = occ_servo.component
        sk = skizze(csv, 'Gehaeuse')
        rechteck(sk, g['cx'] - SERVO_L / 2.0, -SERVO_B / 2.0,
                 g['cx'] + SERVO_L / 2.0, SERVO_B / 2.0)
        servo = extrude_z(csv, sk, SERVO_LUFT_UNTEN, SERVO_GEHAEUSE_H, NEU).bodies.item(0)
        servo.name = 'SG90 (Referenz)'
        sk = skizze(csv, 'Laschen')
        rechteck(sk, g['cx'] - SERVO_LASCHEN_L / 2.0, -SERVO_B / 2.0,
                 g['cx'] + SERVO_LASCHEN_L / 2.0, SERVO_B / 2.0)
        extrude_z(csv, sk, g['z_rahmen'], SERVO_FLANSCH_T, JOIN, servo)
        welle_h = g['z_horn_oben'] - HORN_T - g['z_servo_o'] + 0.5
        if welle_h > 0.6:                    # nur wenn das Horn über dem Gehäuse sitzt
            sk = skizze(csv, 'Welle')
            kreis(sk, P(0, 0), SERVO_WELLE_D)
            extrude_z(csv, sk, g['z_servo_o'] - 0.5, welle_h, JOIN, servo)
        sk = skizze(ck, 'Horn_Referenz')          # dreht mit der Kurbelscheibe
        horn_umriss(sk, 0.0)
        ext = extrude_z(ck, sk, g['z_horn_oben'] - HORN_T, HORN_T, NEU)
        for i in range(ext.bodies.count):
            ext.bodies.item(i).name = 'Horn (Referenz)'

        # ---------------- Materialien ----------------
        for occ, mat in ((occ_basis, 'PETG'), (occ_kurbel, 'PETG'),
                         (occ_pleuel, 'PETG'), (occ_schlitten, 'PETG'),
                         (occ_stangen, 'Stainless Steel'),
                         (occ_servo, 'ABS Plastic')):
            comp = occ.component
            for i in range(comp.bRepBodies.count):
                b = comp.bRepBodies.item(i)
                if b.name.startswith('Bohrlehre_'):
                    material_zuweisen(app, design, b, 'PLA')
                elif '(Referenz)' in b.name:
                    material_zuweisen(app, design, b, 'ABS Plastic')
                else:
                    material_zuweisen(app, design, b, mat)

        # ---------------- Gelenke ----------------
        occ_basis.isGrounded = True
        occ_stangen.isGrounded = True
        occ_servo.isGrounded = True
        Z = (0, 0, 1)
        X = (1, 0, 0)
        gelenk(root, occ_kurbel, occ_basis,
               zylinder(scheibe, (0, 0, 0), Z, SCHEIBE_D / 2.0),
               'dreh', 'Kurbel', hinweise)
        gelenk(root, occ_schlitten, occ_basis,
               zylinder(schlitten, (0, STANGEN_ABSTAND / 2.0, g['z_stange']), X,
                        (STANGE_D + SPIEL_GLEIT) / 2.0),
               'schieb', 'Schlitten', hinweise)
        gelenk(root, occ_pleuel, occ_kurbel,
               zylinder(pleuel, (r, 0, 0), Z, GELENK_LOCH_D / 2.0),
               'dreh', 'Pleuel_Kurbel', hinweise)
        # zylindrisch statt Drehgelenk, damit die geschlossene Kette nicht überbestimmt ist
        gelenk(root, occ_pleuel, occ_schlitten,
               zylinder(pleuel, (g['x_home'], 0, 0), Z, GELENK_LOCH_D / 2.0),
               'zyl', 'Pleuel_Schlitten', hinweise)

        # ---------------- Bericht ----------------
        app.activeViewport.fit()
        validierungs_bericht(app, design, ui, hinweise=g['warnungen'] + hinweise + [
            'Hub {:.1f} mm (r = {:.1f}), Pleuel {:.1f} mm, Schlittengelenk x = {:.1f} (LOAD) … {:.1f} (HOME)'.format(
                2 * r, r, PLEUEL_L, g['x_load'], g['x_home']),
            'Passungen (live im Parameter-Dialog): Schlitten Ø{:.2f}, Halter Ø{:.2f}, '
            'Gelenke Ø{:.1f} -> auf 3,0 aufreiben, Kopfsenkung Ø{:.1f}, Insert Ø{:.1f}'.format(
                STANGE_D + SPIEL_GLEIT, STANGE_D + SPIEL_PRESS, GELENK_LOCH_D,
                KOPF_D + SPIEL_LOCKER, INSERT_D),
            '[?] Servo-/Horn-Maße nachmessen (Block MASSE), v. a. HORN_OBEN_UEBER_FLANSCH und HORN_T. '
            'Spalt Servo <-> Kurbelscheibe laut Modell: {:.1f} mm'.format(g['z_sch_u'] - g['z_servo_o']),
            'Stangen: 2 × Ø{:.0f} × {:.0f} mm, Abstand {:.0f} mm'.format(
                STANGE_D, g['stangen_l'], STANGEN_ABSTAND),
            'Schrauben: 2 × M3×{} DIN 912 (min. {:.1f} mm unter Kopf), von unten; '
            'je 1 Mutter + 2 U-Scheiben + Stoppmutter; 2 × M3-Einschmelzmutter'.format(
                g['schraube'], g['schraube_min']),
            'Druck: Grundplatte flach (Halterbohrungen liegen waagrecht -> mit 4,0 nachbohren), '
            'Schlitten stehend (Stangenbohrungen senkrecht), '
            'Kurbelscheibe mit Horntasche nach oben, Pleuel flach',
            'Nicht drucken: Fuehrungsstangen, SG90 (Referenz), Horn (Referenz)',
            'Prüfen: Gelenk "Kurbel" rechtsklicken -> Gelenk antreiben, 0–360°',
        ])

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
