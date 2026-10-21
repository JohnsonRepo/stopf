# Huelsenschieber_Kurbel.py — Kurbeltrieb für den Hülsenschieber (SG90)
#
# Rev. 3: Pleuel dreht sich auf Messinghülsen (5×1), die M3-Schrauben klemmen
# die Hülsen nur fest – kein Gewinde läuft im Lager.
# Rev. 2: passt zum vorhandenen Aufbau. Das Messingrohr (Ø5) bleibt im
# Gleitlager, das ist die einzige Führung. Der Servo bleibt seitlich neben dem
# Rohr. Ersetzt werden nur Hornarm und Hebel:
#   Kurbelscheibe   sitzt auf dem Doppelarm-Horn, Kurbelzapfen bei KURBEL_R
#   Pleuel          Länge so berechnet, dass Kurbel und Pleuel in HOME gestreckt
#                   in einer Linie stehen (Totpunkt -> Servospiel wirkt kaum)
#   Rohrklemme      M3-Schraube quer durch Klemme UND Rohr = Gelenkzapfen
#   SG90_Referenz, Messingrohr   nur zur Kontrolle, werden nicht gedruckt
#
# Lage: Servowelle bei x = y = 0, Schub in +X (Richtung Trommel), Rohrachse
# bei y = SEITLICH, Z = 0 = Grundplatte. Gebaut in HOME-Stellung.
#
# Alle Maße stehen im Block MASSE. Die Bohrungs-Passungen lassen sich nach dem
# Testdruck live im Parameter-Dialog ändern (spiel_*, gelenk_loch_d,
# pleuel_loch_d, kopf_d, rohr_d). Alles andere: Wert im Block ändern und Skript neu ausführen.
#
# Daneben gehört die gleichnamige .manifest-Datei.

import adsk.core, adsk.fusion, traceback, math

SKRIPT_NAME = 'Huelsenschieber_Kurbel'   # = Dateiname des Skripts
REVISION = 3                             # bei jeder Änderung hochzählen

# ============================== MASSE (mm) ==================================
# [?] = Datenblatt-/Erfahrungswert, am eigenen Teil mit dem Messschieber prüfen.

# --- Einbaulage (gemessen, Rohr in HOME) ---
SEITLICH = 28.0             # Servowelle -> Rohrachse, quer zum Rohr
AXIAL_HOME = 25.0           # Servowelle -> Gelenkschraube am Rohr, entlang des Rohrs,
                            # positiv = Gelenk liegt näher an der Trommel als die Welle
HORN_OBEN = 40.0            # Oberseite Horn über der Grundplatte
ROHR_Z = 40.0               # Rohrachse über der Grundplatte
HUB = 30.0                  # Rückweg HOME -> LOAD

# --- Kurbel ---
KURBEL_R = 15.0             # Pleuellänge ergibt sich: Abstand Welle-Gelenk in HOME - KURBEL_R

# --- Passungen (werden als User-Parameter angelegt) ---
SPIEL_PRESS = 0.05          # diametral: Rohr in der Klemme
SPIEL_LOCKER = 0.4          # diametral: Schraubenköpfe

# --- Gelenke (M3) ---
# Aufbau von unten: Schraube, Kurbelscheibe bzw. Klemme, U-Scheibe, Messinghülse
# (im Pleuel), U-Scheibe, Stoppmutter fest. Die Hülse ist etwas länger als das
# Pleuel -> die Schraube klemmt nur die Hülse, das Pleuel dreht frei darauf.
GELENK_LOCH_D = 2.8         # Kurbelscheibe/Klemme, gedruckt; mit 3,0 aufreiben
KOPF_D = 5.5                # M3 DIN 912 Kopf-Ø
KOPF_T = 3.0                # M3 DIN 912 Kopfhöhe
U_SCHEIBE_T = 0.5           # M3 DIN 125
STOPPMUTTER_T = 4.0         # M3 DIN 985
HUELSE_D = 5.0              # Messingrohr 5×1 als Lagerhülse
HUELSE_UEBERSTAND = 0.25    # Hülse länger als das Pleuel = axiales Spiel
PLEUEL_LOCH_D = 4.8         # gedruckt; mit 5,0 aufreiben, Hülse läuft darin

# --- Pleuel ---
PLEUEL_B = 10.0             # 2,5 mm Wand um die Ø5-Hülse
PLEUEL_T = 4.0

# --- Kurbelscheibe ---
SCHEIBE_D = 40.0
SCHEIBE_T = 6.0
UNTER_KOPF = 1.0            # Material unter dem Kopf der Hornschraube

# --- Rohrklemme ---
ROHR_D = 5.0
KLEMME_L = 12.0             # entlang des Rohrs
KLEMME_B = 12.0             # quer zum Rohr
KLEMME_BODEN = 2.0          # Wand unter dem Rohr
ROHR_REF_VORNE = 60.0       # Länge des Referenzrohrs vor der Klemme

# --- Doppelarm-Horn [?] ---
HORN_L = 35.0               # Länge Spitze bis Spitze
HORN_NABE_D = 7.5           # Breite an der Nabe
HORN_SPITZE_D = 4.5         # Breite an den Spitzen
HORN_T = 2.0                # Dicke der Arme
HORN_SPIEL = 0.1            # radial, Horntasche
HORNSCHRAUBE_D = 2.4        # Durchgang Hornschraube
HORNSCHRAUBE_KOPF_D = 4.5   # Kopf-Ø Hornschraube

# --- SG90 [?] (nur Referenzkörper) ---
SERVO_L = 22.8
SERVO_B = 12.2
SERVO_GEHAEUSE_H = 22.7
SERVO_WELLE_ENDE = 5.9      # Wellenmitte -> nahes Gehäuseende
SERVO_WELLE_D = 4.8
HORN_LUFT = 1.5             # Hornunterseite -> Gehäuseoberkante

# --- Servo (für die Kraftabschätzung) ---
SERVO_MOMENT = 170.0        # N·mm, SG90 Haltemoment ca. 1,8 kg·cm
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


def kinematik(r, L):
    """Versetzter Schubkurbeltrieb: Welle in (0,0), Gelenk läuft auf y = SEITLICH
    von s = AXIAL_HOME (HOME, Strecklage) bis s = AXIAL_HOME - HUB (LOAD).
    Kurbelwinkel in rad, 0 = +X, gegen den Uhrzeigersinn."""
    def theta(s):
        d = math.hypot(s, SEITLICH)
        c = (r * r - L * L + d * d) / (2.0 * d * r)
        if c < -1.0 - 1e-9 or c > 1.0 + 1e-9:
            return None
        return math.atan2(SEITLICH, s) + math.acos(max(-1.0, min(1.0, c)))

    def lage(th):
        cx, cy = r * math.cos(th), r * math.sin(th)
        return cx + math.sqrt(L * L - (SEITLICH - cy) ** 2), cx, cy

    n = 600
    ss = [AXIAL_HOME - HUB * i / n for i in range(n + 1)]
    ths = [theta(s) for s in ss]
    if any(t is None for t in ths):
        return None
    k = {'th_home': ths[0], 'th_load': ths[-1],
         'servoweg': math.degrees(ths[-1] - ths[0]),
         'monoton': all(ths[i + 1] >= ths[i] - 1e-12 for i in range(n))}
    w_max, v_max = 0.0, 0.0
    for i in range(n + 1):
        _, cx, cy = lage(ths[i])
        w_max = max(w_max, math.degrees(math.atan2(abs(SEITLICH - cy), ss[i] - cx)))
        if i < n and ths[i + 1] != ths[i]:
            v_max = max(v_max, abs((ss[i + 1] - ss[i]) / (ths[i + 1] - ths[i])))
    k['pleuelwinkel_max'] = w_max                # Pleuel <-> Rohrachse
    k['kraft_min'] = SERVO_MOMENT / v_max if v_max else 0.0
    k['fehler_3grad'] = max(AXIAL_HOME - lage(ths[0] + math.radians(d))[0]
                            for d in (-3.0, 3.0))
    return k


def geometrie():
    """Alle abgeleiteten Lagen (mm). Hängen an den MASSE-Konstanten,
    nicht live an den User-Parametern."""
    g = {}
    r = KURBEL_R
    g['r'] = r
    g['abstand_home'] = math.hypot(AXIAL_HOME, SEITLICH)
    g['L'] = g['abstand_home'] - r                   # Strecklage in HOME
    g['k'] = kinematik(r, g['L'])

    g['taschen_t'] = HORN_T - 0.3                    # Scheibe 0,3 über Hornunterseite
    g['z_sch_u'] = HORN_OBEN - g['taschen_t']
    g['z_sch_o'] = g['z_sch_u'] + SCHEIBE_T
    g['z_pl_u'] = g['z_sch_o'] + U_SCHEIBE_T
    g['huelse_l'] = PLEUEL_T + HUELSE_UEBERSTAND
    g['senk_horn_t'] = SCHEIBE_T - g['taschen_t'] - UNTER_KOPF
    g['rest_unter_kopf'] = SCHEIBE_T - (KOPF_T + 0.3)

    # Rohrklemme: Oberkante = Scheibenoberkante -> Pleuel liegt waagrecht
    g['z_kl_o'] = g['z_sch_o']
    g['z_kl_u'] = ROHR_Z - ROHR_D / 2.0 - KLEMME_BODEN
    g['kl_decke'] = g['z_kl_o'] - (ROHR_Z + ROHR_D / 2.0)

    # Servo-Referenz: Gehäuse unter dem Horn, Welle am Gehäuseende Richtung -X
    g['z_servo_o'] = HORN_OBEN - HORN_T - HORN_LUFT

    # Schraubenlängen (unter Kopf): Teil, U-Scheibe, Hülse, U-Scheibe, Stoppmutter
    stapel = U_SCHEIBE_T + g['huelse_l'] + U_SCHEIBE_T + STOPPMUTTER_T
    g['schraube_kurbel_min'] = g['rest_unter_kopf'] + stapel
    g['schraube_klemme_min'] = (g['z_kl_o'] - g['z_kl_u']) + stapel
    for key in ('kurbel', 'klemme'):
        g['schraube_' + key] = next((l for l in (12, 16, 20, 25, 30, 35)
                                     if l >= g['schraube_' + key + '_min'] + 1.0), 40)

    w = []
    k = g['k']
    if k is None or not k['monoton']:
        w.append('FEHLER: Mit diesen Maßen erreicht die Kurbel LOAD nicht sauber – KURBEL_R ändern')
    else:
        if k['servoweg'] > 160:
            w.append('WARNUNG: Servoweg {:.0f}° – mehr als ein SG90 sicher schafft'.format(k['servoweg']))
        if k['pleuelwinkel_max'] > 70:
            w.append('WARNUNG: Pleuel steht bis {:.0f}° schräg zum Rohr – Klemmgefahr im Gleitlager'.format(
                k['pleuelwinkel_max']))
    if g['L'] < PLEUEL_B + 2.0:
        w.append('WARNUNG: Pleuel kürzer als {:.0f} mm'.format(PLEUEL_B + 2.0))
    if SEITLICH - SCHEIBE_D / 2.0 - KLEMME_B / 2.0 < 1.0:
        w.append('WARNUNG: Kurbelscheibe streift die Rohrklemme')
    if SCHEIBE_D / 2.0 - r < KOPF_D / 2.0 + SPIEL_LOCKER / 2.0 + 1.5:
        w.append('WARNUNG: Kurbelzapfen zu nah am Scheibenrand')
    if g['kl_decke'] < 1.5:
        w.append('WARNUNG: Klemme über dem Rohr nur {:.1f} mm dick'.format(g['kl_decke']))
    if g['senk_horn_t'] < 1.0:
        w.append('WARNUNG: Kurbelscheibe zu dünn für die Senkung der Hornschraube')
    g['warnungen'] = w
    return g


def parameter_anlegen(design):
    up = design.userParameters
    up.add('spiel_press', vs('{} mm'.format(SPIEL_PRESS)), 'mm',
           'Presspassung, diametral (Rohr in der Klemme)')
    up.add('spiel_locker', vs('{} mm'.format(SPIEL_LOCKER)), 'mm',
           'Montagespiel, diametral (Schraubenköpfe)')
    up.add('rohr_d', vs('{} mm'.format(ROHR_D)), 'mm', 'Ø Messingrohr (gemessen)')
    up.add('gelenk_loch_d', vs('{} mm'.format(GELENK_LOCH_D)), 'mm',
           'Gelenklöcher gedruckt, auf 3,0 aufreiben')
    up.add('pleuel_loch_d', vs('{} mm'.format(PLEUEL_LOCH_D)), 'mm',
           'Pleuellöcher gedruckt, auf 5,0 aufreiben (Messinghülse)')
    up.add('kopf_d', vs('{} mm'.format(KOPF_D)), 'mm', 'Kopf-Ø M3 DIN 912')

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
        ext_in.participantBodies = (koerper if isinstance(koerper, list)
                                    else [koerper])
    return feats.add(ext_in)

def extrude_sym(comp, sk, laenge, op, koerper=None):
    """Alle Profile symmetrisch zur Skizzenebene extrudieren (Gesamtlänge in mm).
    Richtungsunabhängig – für Durchgangsschnitte und das Rohr."""
    feats = comp.features.extrudeFeatures
    ext_in = feats.createInput(alle_profile(sk), op)
    ext_in.setSymmetricExtent(vmm(laenge), True)
    if koerper is not None:
        ext_in.participantBodies = (koerper if isinstance(koerper, list)
                                    else [koerper])
    return feats.add(ext_in)

def cut_durch(comp, sk, koerper):
    return extrude_sym(comp, sk, 400.0, CUT, koerper)

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


def platzieren(occ, winkel_rad, dx, dy):
    """Occurrence um Z drehen (um den Ursprung) und dann in XY verschieben (mm)."""
    m = adsk.core.Matrix3D.create()
    if winkel_rad:
        m.setToRotation(winkel_rad, adsk.core.Vector3D.create(0, 0, 1),
                        adsk.core.Point3D.create(0, 0, 0))
    m.translation = adsk.core.Vector3D.create(dx / 10.0, dy / 10.0, 0)
    occ.transform2 = m


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
        r, L, k = g['r'], g['L'], g['k']
        th_home = k['th_home'] if k else math.atan2(SEITLICH, AXIAL_HOME)

        # ---------------- SG90-Referenz (fest) ----------------
        occ_servo = komponente(root, 'SG90_Referenz')
        csv = occ_servo.component
        sk = skizze(csv, 'Gehaeuse')
        rechteck(sk, -SERVO_WELLE_ENDE, -SERVO_B / 2.0,
                 SERVO_L - SERVO_WELLE_ENDE, SERVO_B / 2.0)
        servo = extrude_z(csv, sk, g['z_servo_o'] - SERVO_GEHAEUSE_H,
                          SERVO_GEHAEUSE_H, NEU).bodies.item(0)
        servo.name = 'SG90 (Referenz)'
        welle_h = HORN_OBEN - HORN_T - g['z_servo_o'] + 0.5
        if welle_h > 0.6:
            sk = skizze(csv, 'Welle')
            kreis(sk, P(0, 0), SERVO_WELLE_D)
            extrude_z(csv, sk, g['z_servo_o'] - 0.5, welle_h, JOIN, servo)

        # ---------------- Kurbelscheibe (lokal: Zapfen auf +X) ----------------
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

        # Kurbelzapfen: Loch + Kopfsenkung von unten
        sk = skizze(ck, 'Kurbelzapfen')
        kreis(sk, P(r, 0), GELENK_LOCH_D, 'gelenk_loch_d')
        cut_durch(ck, sk, scheibe)
        sk = skizze(ck, 'Kurbelzapfen_Kopf')
        kreis(sk, P(r, 0), KOPF_D + SPIEL_LOCKER, 'kopf_d + spiel_locker')
        extrude_z(ck, sk, g['z_sch_u'] - 1.0, SCHEIBE_T - g['rest_unter_kopf'] + 1.0,
                  CUT, scheibe)

        # Horn als Referenz – dreht mit der Scheibe
        sk = skizze(ck, 'Horn_Referenz')
        horn_umriss(sk, 0.0)
        ext = extrude_z(ck, sk, HORN_OBEN - HORN_T, HORN_T, NEU)
        for i in range(ext.bodies.count):
            ext.bodies.item(i).name = 'Horn (Referenz)'

        # ---------------- Pleuel (lokal: von (0,0) nach (L,0)) ----------------
        occ_pleuel = komponente(root, 'Pleuel')
        cp = occ_pleuel.component

        sk = skizze(cp, 'Pleuel')
        stadion(sk, 0.0, L, 0.0, PLEUEL_B)
        pleuel = extrude_z(cp, sk, g['z_pl_u'], PLEUEL_T, NEU).bodies.item(0)
        pleuel.name = 'Pleuel'

        sk = skizze(cp, 'Gelenkloecher')
        for x in (0.0, L):
            kreis(sk, P(x, 0), PLEUEL_LOCH_D, 'pleuel_loch_d')
        cut_durch(cp, sk, pleuel)

        # ---------------- Schieber: Rohrklemme + Messingrohr ----------------
        # Lokaler Ursprung in Rohrmitte (x_c) -> Rohr symmetrisch extrudierbar
        x_a = AXIAL_HOME - KLEMME_L / 2.0 - 3.0
        x_b = AXIAL_HOME + ROHR_REF_VORNE
        x_c = (x_a + x_b) / 2.0
        xk = AXIAL_HOME - x_c                       # Gelenk, lokal

        occ_schieber = komponente(root, 'Schieber')
        cr = occ_schieber.component

        sk = skizze(cr, 'Rohrklemme')
        rechteck(sk, xk - KLEMME_L / 2.0, SEITLICH - KLEMME_B / 2.0,
                 xk + KLEMME_L / 2.0, SEITLICH + KLEMME_B / 2.0)
        klemme = extrude_z(cr, sk, g['z_kl_u'], g['z_kl_o'] - g['z_kl_u'], NEU).bodies.item(0)
        klemme.name = 'Rohrklemme'

        sk = skizze(cr, 'Messingrohr', cr.yZConstructionPlane)
        kreis(sk, sk.modelToSketchSpace(P(0, SEITLICH, ROHR_Z)), ROHR_D)
        rohr = extrude_sym(cr, sk, x_b - x_a, NEU).bodies.item(0)
        rohr.name = 'Messingrohr (Referenz)'

        sk = skizze(cr, 'Rohrbohrung', cr.yZConstructionPlane)
        kreis(sk, sk.modelToSketchSpace(P(0, SEITLICH, ROHR_Z)),
              ROHR_D + SPIEL_PRESS, 'rohr_d + spiel_press')
        cut_durch(cr, sk, klemme)

        # Gelenkschraube quer durch Klemme und Rohr (Klemme = Bohrlehre fürs Rohr)
        sk = skizze(cr, 'Klemmengelenk')
        kreis(sk, P(xk, SEITLICH), GELENK_LOCH_D, 'gelenk_loch_d')
        cut_durch(cr, sk, [klemme, rohr])

        # ---------------- Lage in HOME ----------------
        platzieren(occ_kurbel, th_home, 0.0, 0.0)
        platzieren(occ_pleuel, th_home, r * math.cos(th_home), r * math.sin(th_home))
        platzieren(occ_schieber, 0.0, x_c, 0.0)
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

        # ---------------- Materialien ----------------
        for occ, mat in ((occ_kurbel, 'PETG'), (occ_pleuel, 'PETG'),
                         (occ_schieber, 'PETG'), (occ_servo, 'ABS Plastic')):
            comp = occ.component
            for i in range(comp.bRepBodies.count):
                b = comp.bRepBodies.item(i)
                if b.name.startswith('Messingrohr'):
                    material_zuweisen(app, design, b, 'Brass')
                elif '(Referenz)' in b.name:
                    material_zuweisen(app, design, b, 'ABS Plastic')
                else:
                    material_zuweisen(app, design, b, mat)

        # ---------------- Gelenke ----------------
        occ_servo.isGrounded = True
        Z = (0, 0, 1)
        X = (1, 0, 0)
        gelenk(root, occ_kurbel, occ_servo,
               zylinder(scheibe, (0, 0, 0), Z, SCHEIBE_D / 2.0),
               'dreh', 'Kurbel', hinweise)
        gelenk(root, occ_schieber, occ_servo,
               zylinder(rohr, (0, SEITLICH, ROHR_Z), X, ROHR_D / 2.0),
               'schieb', 'Rohr_Gleitlager', hinweise)
        gelenk(root, occ_pleuel, occ_kurbel,
               zylinder(pleuel, (0, 0, 0), Z, PLEUEL_LOCH_D / 2.0),
               'dreh', 'Pleuel_Kurbel', hinweise)
        # zylindrisch statt Drehgelenk, damit die geschlossene Kette nicht überbestimmt ist
        gelenk(root, occ_pleuel, occ_schieber,
               zylinder(pleuel, (L, 0, 0), Z, PLEUEL_LOCH_D / 2.0),
               'zyl', 'Pleuel_Klemme', hinweise)

        # ---------------- Bericht ----------------
        app.activeViewport.fit()
        bericht = g['warnungen'] + hinweise + [
            'Kurbelradius {:.1f} mm, Pleuel {:.1f} mm Lochabstand (Strecklage in HOME, '
            'Welle -> Gelenk {:.1f} mm)'.format(r, L, g['abstand_home'])]
        if k:
            bericht += [
                'Servoweg HOME -> LOAD {:.0f}°, Pleuel max. {:.0f}° schräg zum Rohr, '
                'Schubkraft min. {:.1f} N (bei {:.0f} N·mm)'.format(
                    k['servoweg'], k['pleuelwinkel_max'], k['kraft_min'], SERVO_MOMENT),
                'HOME-Fehler bei ±3° Servospiel: {:.3f} mm'.format(k['fehler_3grad']),
            ]
        bericht += [
            'Kalibrieren: HOME = Kurbelzapfen zeigt genau auf die Klemmschraube '
            '(Rohr am weitesten vorn); LOAD = ca. {:.0f}° weiter, Kurbel schwenkt zum Rohr hin'.format(
                k['servoweg'] if k else 0),
            'Schrauben DIN 912: Kurbel M3×{}, Klemme M3×{} (quer durchs Rohr); '
            'je 2 U-Scheiben + Stoppmutter, fest anziehen'.format(
                g['schraube_kurbel'], g['schraube_klemme']),
            'Lagerhülsen: 2 × Messingrohr 5×1, je {:.2f} mm lang ({:.2f} mm länger als das Pleuel) – '
            'Pleuel muss nach dem Festziehen frei drehen'.format(g['huelse_l'], HUELSE_UEBERSTAND),
            'Rohr: Klemme in HOME-Lage aufschieben, durch das Gelenkloch 3 mm quer durchbohren',
            '[?] Horn-Maße und SEITLICH/AXIAL_HOME/HORN_OBEN prüfen (Block MASSE)',
            'Druck: Kurbelscheibe mit Horntasche nach oben, Pleuel und Klemme flach; '
            'Pleuellöcher mit 5,0 aufreiben (Rohrbohrung der Klemme ggf. auch)',
            'Nicht drucken: SG90 (Referenz), Horn (Referenz), Messingrohr (Referenz)',
            'Prüfen: Gelenk "Kurbel" rechtsklicken -> Gelenk antreiben',
        ]
        validierungs_bericht(app, design, ui, hinweise=bericht)

    except:
        if ui:
            ui.messageBox('Skript fehlgeschlagen:\n{}'.format(
                traceback.format_exc()))
