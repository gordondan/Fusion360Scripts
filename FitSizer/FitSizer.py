import adsk.core, adsk.fusion, traceback, math

# Helper: convert mm to internal units (Fusion 360 API uses centimeters internally)
def mm(val):
    return val / 10.0  # Convert mm to cm for Fusion 360 API

def addWrenchU(sketch, originX, mouthWidth, jawDepth=3.0, jawThickness=1.0, handleHeight=12.0):
    """
    Draws a single closed 2D profile of a wrench shape with U-shaped mouth opening.
    Returns the handle center position in mm for text placement.
    """
    lines = sketch.sketchCurves.sketchLines

    # Convert all dimensions from mm to cm (Fusion internal units)
    x0 = mm(originX)
    mw = mm(mouthWidth)
    jd = mm(jawDepth)
    jt = mm(jawThickness)
    hh = mm(handleHeight)

    # Define points for a single closed profile (clockwise from bottom-left outer)
    p_bl_outer = adsk.core.Point3D.create(x0 - jt, 0, 0)
    p_bl_inner = adsk.core.Point3D.create(x0, 0, 0)
    p_br_inner = adsk.core.Point3D.create(x0 + mw, 0, 0)
    p_br_outer = adsk.core.Point3D.create(x0 + mw + jt, 0, 0)
    p_tl_inner = adsk.core.Point3D.create(x0, jd, 0)
    p_tr_inner = adsk.core.Point3D.create(x0 + mw, jd, 0)
    p_tl_outer = adsk.core.Point3D.create(x0 - jt, jd + hh, 0)
    p_tr_outer = adsk.core.Point3D.create(x0 + mw + jt, jd + hh, 0)

    # Draw single closed profile
    lines.addByTwoPoints(p_bl_outer, p_tl_outer)
    lines.addByTwoPoints(p_tl_outer, p_tr_outer)
    lines.addByTwoPoints(p_tr_outer, p_br_outer)
    lines.addByTwoPoints(p_br_outer, p_br_inner)
    lines.addByTwoPoints(p_br_inner, p_tr_inner)
    lines.addByTwoPoints(p_tr_inner, p_tl_inner)
    lines.addByTwoPoints(p_tl_inner, p_bl_inner)
    lines.addByTwoPoints(p_bl_inner, p_bl_outer)

    # Return handle center in mm
    handleCenterX = originX + mouthWidth / 2.0
    handleCenterY = jawDepth + handleHeight / 2.0
    return handleCenterX, handleCenterY

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # Parameters
        testSize = 3.0      # Single size for testing
        spacing = 20.0      # Spacing between shapes in mm
        jawDepth = 5.0      # Depth of the mouth
        jawThickness = 2.0  # Thickness of jaw walls
        handleHeight = 12.0 # Height of handle area (for text)
        extrudeDepth = 2.0  # Extrusion depth in mm
        textHeight = 2.5    # Text height in mm
        embossDepth = 0.5   # How deep to engrave text in mm

        # Test permutations: just labels for now - simplify to debug
        labels = ["T1", "T2", "T3", "T4"]

        extrudes = rootComp.features.extrudeFeatures
        bodies = []
        handleCenters = []

        # Step 1: Create each wrench body individually
        originX = 0.0
        for i, label in enumerate(labels):
            # Create a fresh sketch for each wrench
            sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

            # Draw wrench profile
            hcX, hcY = addWrenchU(
                sketch, originX, testSize,
                jawDepth=jawDepth,
                jawThickness=jawThickness,
                handleHeight=handleHeight
            )
            handleCenters.append((hcX, hcY))

            # Extrude the profile
            if sketch.profiles.count > 0:
                profile = sketch.profiles.item(0)
                extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(extrudeDepth)))
                ext = extrudes.add(extInput)

                if ext.bodies.count > 0:
                    body = ext.bodies.item(0)
                    body.name = label
                    bodies.append(body)
                    print(f"[DEBUG] Created body: {body.name}")

            originX += spacing

        # Step 2: For each body, find top face and add text
        debugInfo = []
        debugInfo.append(f"Created {len(bodies)} bodies")

        for i, body in enumerate(bodies):
            label = labels[i]
            hcX, hcY = handleCenters[i]

            # Find the top face (face with normal pointing in +Z direction)
            topFace = None
            for face in body.faces:
                evaluator = face.evaluator
                (success, point) = evaluator.getPointAtParameter(adsk.core.Point2D.create(0.5, 0.5))
                if success:
                    (success, normal) = evaluator.getNormalAtPoint(point)
                    if success and normal.z > 0.9:
                        topFace = face
                        break

            if topFace is None:
                debugInfo.append(f"{label}: No top face found!")
                continue

            # Create sketch on the top face
            textSketch = rootComp.sketches.add(topFace)

            # Transform handle center from world to sketch coordinates
            transform = textSketch.transform
            invTransform = transform.copy()
            invTransform.invert()

            worldPoint = adsk.core.Point3D.create(mm(hcX), mm(hcY), mm(extrudeDepth))
            sketchPoint = worldPoint.copy()
            sketchPoint.transformBy(invTransform)

            # Add text
            texts = textSketch.sketchTexts
            position = adsk.core.Point3D.create(sketchPoint.x, sketchPoint.y, 0)
            textInput = texts.createInput(label, mm(textHeight), position)
            textInput.horizontalAlignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment
            textInput.angle = math.pi / 2
            sketchText = texts.add(textInput)

            # Explode text to curves so it creates proper profiles for extrusion
            sketchText.explode()

            profileCount = textSketch.profiles.count
            debugInfo.append(f"{label}: {profileCount} profiles")

            # Engrave text using extrude cut operation
            if profileCount > 0:
                for j in range(profileCount):
                    profile = textSketch.profiles.item(j)
                    try:
                        extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
                        # Use negative direction to cut into the body (not away from it)
                        distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(mm(embossDepth)))
                        extInput.setOneSideExtent(distance, adsk.fusion.ExtentDirections.NegativeExtentDirection)
                        extrudes.add(extInput)
                        debugInfo.append(f"  - Engraved profile {j}")
                    except Exception as e:
                        debugInfo.append(f"  - Engrave {j} FAILED: {e}")

        ui.messageBox('\n'.join(debugInfo), "Debug Info")

        print("[INFO] Done.")
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        else:
            print('Failed:\n{}'.format(traceback.format_exc()))
