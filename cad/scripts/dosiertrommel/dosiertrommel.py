# =====================================================
# dosiertrommel.py
# Autodesk Fusion - Script (Utilities > Scripts and Add-Ins > Run)
#
# Erzeugt ein NEUES Dokument mit der volumetrischen Dosiertrommel:
#   - Vollzylinder (Trommelkoerper)
#   - eine Tasche (fixes Volumen) radial in den Mantel gefraest
#   - zentrale Bohrung fuer die Servo-Achse
#   - flache Aussparung an der Vorderseite fuer ein rundes Servo-Horn
#
# Alle Masse sind User-Parameter (Aenderbar unter "Modify > Change Parameters").
# Das TASCHEN-Volumen = pocket_circ x pocket_w x pocket_depth bestimmt die Dosis.
# Zum Eintrimmen einfach pocket_depth (oder _circ/_w) anpassen und neu rechnen.
#
# Konvention: legt immer ein neues Dokument an, baut als Einzelteil im
# rootComponent (keine Baugruppe noetig - nur ein Teil).
# =====================================================

import adsk.core
import adsk.fusion
import traceback


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # --- 1) Neues Dokument (aktives Projekt bleibt unberuehrt) ---
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        # Hinweis: root.name laesst sich per API nicht setzen (an den Dokumentnamen
        # gekoppelt). Stattdessen wird unten der Trommel-Body benannt.

        # --- 2) User-Parameter (mm) - hier zum Trimmen der Dosis aendern ---
        up = design.userParameters

        def addp(name, expr, comment):
            up.add(name, adsk.core.ValueInput.createByString(expr), 'mm', comment)

        addp('drum_dia',     '40 mm',  'Trommel-Durchmesser')
        addp('drum_len',     '40 mm',  'Trommel-Laenge (axial)')
        addp('bore_dia',     '5 mm',   'Bohrung fuer Servo-Achse')
        addp('pocket_circ',  '16 mm',  'Tasche tangential (Oeffnungsbreite)')
        addp('pocket_w',     '22 mm',  'Tasche axial (Laenge, zentriert)')
        addp('pocket_depth', '12 mm',  'Tasche radial (Tiefe = Dosis-Stellgroesse)')
        addp('horn_dia',     '22 mm',  'Servo-Horn-Aussparung Durchmesser')
        addp('horn_depth',   '2.5 mm', 'Servo-Horn-Aussparung Tiefe')

        def cm(name):
            # API rechnet intern in cm; User-Parameter .value liefert cm.
            return up.itemByName(name).value

        extrudes = root.features.extrudeFeatures

        # --- 3) Trommelkoerper: Kreis auf XY, Extrusion entlang +Z ---
        sk1 = root.sketches.add(root.xYConstructionPlane)
        circ = sk1.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm('drum_dia') / 2.0)
        d1 = sk1.sketchDimensions.addDiameterDimension(
            circ, adsk.core.Point3D.create(cm('drum_dia') / 2.0, 0, 0))
        d1.parameter.expression = 'drum_dia'

        extIn = extrudes.createInput(
            sk1.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extIn.setDistanceExtent(False, adsk.core.ValueInput.createByString('drum_len'))
        drum = extrudes.add(extIn).bodies.item(0)
        drum.name = 'Trommel'

        # --- 4) Tasche: Rechteck auf YZ-Ebene, Cut mit radialem Start-Offset ---
        # YZ-Ebene: Sketch-X -> Welt-Y (tangential), Sketch-Y -> Welt-Z (axial),
        # Normale -> +X. Cut startet bei Radius-Tiefe und faehrt nach aussen.
        sk2 = root.sketches.add(root.yZConstructionPlane)
        cz = cm('drum_len') / 2.0          # axiale Mitte -> Tasche zentriert
        hw = cm('pocket_circ') / 2.0
        aw = cm('pocket_w') / 2.0
        sk2.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(-hw, cz - aw, 0),
            adsk.core.Point3D.create(hw, cz + aw, 0))

        cutIn = extrudes.createInput(
            sk2.profiles.item(0),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        cutIn.startExtent = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByString('drum_dia / 2 - pocket_depth'))
        cutIn.setDistanceExtent(False, adsk.core.ValueInput.createByString('pocket_depth + 3 mm'))
        cutIn.participantBodies = [drum]
        extrudes.add(cutIn)

        # --- 5) Zentrale Bohrung fuer Servo-Achse (durch die Trommel) ---
        sk3 = root.sketches.add(root.xYConstructionPlane)
        cb = sk3.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm('bore_dia') / 2.0)
        d3 = sk3.sketchDimensions.addDiameterDimension(
            cb, adsk.core.Point3D.create(cm('bore_dia') / 2.0, 0, 0))
        d3.parameter.expression = 'bore_dia'

        boreIn = extrudes.createInput(
            sk3.profiles.item(0),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        boreIn.setDistanceExtent(False, adsk.core.ValueInput.createByString('drum_len'))
        boreIn.participantBodies = [drum]
        extrudes.add(boreIn)

        # --- 6) Servo-Horn-Aussparung an der Vorderseite (z=0) ---
        sk4 = root.sketches.add(root.xYConstructionPlane)
        ch = sk4.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm('horn_dia') / 2.0)
        d4 = sk4.sketchDimensions.addDiameterDimension(
            ch, adsk.core.Point3D.create(cm('horn_dia') / 2.0, 0, 0))
        d4.parameter.expression = 'horn_dia'

        hornIn = extrudes.createInput(
            sk4.profiles.item(0),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        hornIn.setDistanceExtent(False, adsk.core.ValueInput.createByString('horn_depth'))
        hornIn.participantBodies = [drum]
        extrudes.add(hornIn)

        # --- 7) Ergebnis sichtbar rahmen ---
        app.activeViewport.fit()

    except:  # noqa: E722
        if ui:
            ui.messageBox('Fehler:\n{}'.format(traceback.format_exc()))
