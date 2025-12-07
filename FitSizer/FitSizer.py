import adsk.core, adsk.fusion, traceback, math

# Helper: convert mm to internal units (Fusion 360 API uses centimeters internally)
def mm(val):
    return val / 10.0  # Convert mm to cm for Fusion 360 API

def addWrenchU(sketch, originX, mouthWidth, jawDepth=3.0, jawThickness=1.0, handleHeight=12.0):
    """
    Draws a single closed 2D profile of a wrench shape with U-shaped mouth opening.
    Returns the profile for extrusion and the center point of the handle for text placement.

    originX: X coordinate of left inner edge of mouth at Y = 0
    mouthWidth: width of the mouth opening (the test dimension)
    jawDepth: how deep the mouth goes into the body
    jawThickness: thickness of the jaw walls on each side
    handleHeight: height of the body above the jaw (where text goes)
    """
    lines = sketch.sketchCurves.sketchLines

    # Convert all dimensions from mm to cm (Fusion internal units)
    x0 = mm(originX)
    mw = mm(mouthWidth)
    jd = mm(jawDepth)
    jt = mm(jawThickness)
    hh = mm(handleHeight)

    # Define points for a single closed profile (clockwise from bottom-left outer)
    # Bottom of shape (jaw area)
    p_bl_outer = adsk.core.Point3D.create(x0 - jt, 0, 0)          # bottom-left outer
    p_bl_inner = adsk.core.Point3D.create(x0, 0, 0)               # bottom-left inner (mouth edge)
    p_br_inner = adsk.core.Point3D.create(x0 + mw, 0, 0)          # bottom-right inner (mouth edge)
    p_br_outer = adsk.core.Point3D.create(x0 + mw + jt, 0, 0)     # bottom-right outer

    # Top of jaw / bottom of handle
    p_tl_inner = adsk.core.Point3D.create(x0, jd, 0)              # top-left inner (inside mouth)
    p_tr_inner = adsk.core.Point3D.create(x0 + mw, jd, 0)         # top-right inner (inside mouth)

    # Top of handle
    p_tl_outer = adsk.core.Point3D.create(x0 - jt, jd + hh, 0)    # top-left of handle
    p_tr_outer = adsk.core.Point3D.create(x0 + mw + jt, jd + hh, 0)  # top-right of handle

    # Draw single closed profile (clockwise from bottom-left outer)
    # Left side going up
    lines.addByTwoPoints(p_bl_outer, p_tl_outer)
    # Top of handle
    lines.addByTwoPoints(p_tl_outer, p_tr_outer)
    # Right side going down
    lines.addByTwoPoints(p_tr_outer, p_br_outer)
    # Bottom right, going inward to mouth
    lines.addByTwoPoints(p_br_outer, p_br_inner)
    # Right inner wall of mouth going up
    lines.addByTwoPoints(p_br_inner, p_tr_inner)
    # Top of mouth (inside)
    lines.addByTwoPoints(p_tr_inner, p_tl_inner)
    # Left inner wall of mouth going down
    lines.addByTwoPoints(p_tl_inner, p_bl_inner)
    # Bottom left, going outward to close
    lines.addByTwoPoints(p_bl_inner, p_bl_outer)

    # Calculate handle center for text placement (return in mm for caller)
    handleCenterX = originX + mouthWidth / 2.0
    handleCenterY = jawDepth + handleHeight / 2.0

    print(f"[DEBUG] Wrench: mouthWidth={mouthWidth}mm, handleCenter=({handleCenterX}, {handleCenterY})mm")

    return handleCenterX, handleCenterY

def addText(sketch, textString, centerX_mm, centerY_mm, textHeightMM=3.0):
    """
    Add text at the given position (in mm), rotated 90° counter-clockwise.
    """
    texts = sketch.sketchTexts
    # Convert to cm
    height_cm = textHeightMM / 10.0
    cx = mm(centerX_mm)
    cy = mm(centerY_mm)

    # Create text using simple method
    position = adsk.core.Point3D.create(cx, cy, 0)
    textInput = texts.createInput(textString, height_cm, position)
    textInput.angle = math.pi / 2  # 90° CCW
    textInput.horizontalAlignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment

    sketchText = texts.add(textInput)
    print(f"[DEBUG] Text '{textString}' added at ({centerX_mm}, {centerY_mm})mm, angle={textInput.angle}")

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        # Create sketch for wrench profiles
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

        # Parameters
        minW = 2.0
        maxW = 3.5  # 4 shapes: 2.0, 2.5, 3.0, 3.5
        step = 0.5
        spacing = 15.0     # Spacing between shapes in mm
        jawDepth = 5.0     # Depth of the mouth
        jawThickness = 2.0 # Thickness of jaw walls
        handleHeight = 10.0 # Height of handle area (for text)
        extrudeDepth = 2.0 # Extrusion depth in mm

        # Track sizes for naming bodies
        sizes = []

        originX = 0.0
        w = minW
        while w <= maxW + 1e-6:
            sizes.append(w)

            # Draw the wrench shape and get handle center for text
            handleCenterX, handleCenterY = addWrenchU(
                sketch, originX, w,
                jawDepth=jawDepth,
                jawThickness=jawThickness,
                handleHeight=handleHeight
            )

            originX += spacing + w + 2 * jawThickness  # Space based on shape width
            w += step

        # Count wrench profiles BEFORE adding text
        numWrenchProfiles = sketch.profiles.count
        print(f"[DEBUG] Found {numWrenchProfiles} wrench profiles before adding text")

        # Extrude wrench profiles first
        print("[INFO] Extruding wrench profiles...")
        extrudes = rootComp.features.extrudeFeatures
        moveFeatures = rootComp.features.moveFeatures
        bodies = []  # Track bodies for text cutting

        for i in range(numWrenchProfiles):
            profile = sketch.profiles.item(i)
            try:
                extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                distance = adsk.core.ValueInput.createByReal(mm(extrudeDepth))
                extInput.setDistanceExtent(False, distance)
                ext = extrudes.add(extInput)
                # Name the body S{size}
                if ext.bodies.count > 0:
                    body = ext.bodies.item(0)
                    body.name = f"S{sizes[i]:.1f}"
                    bodies.append(body)
                    print(f"[DEBUG] Extruded and named body: {body.name}")

                    # Rotate body 90° CCW around Z axis at body center
                    bodyCollection = adsk.core.ObjectCollection.create()
                    bodyCollection.add(body)

                    # Get body center for rotation pivot
                    bbox = body.boundingBox
                    centerX = (bbox.minPoint.x + bbox.maxPoint.x) / 2
                    centerY = (bbox.minPoint.y + bbox.maxPoint.y) / 2
                    centerZ = (bbox.minPoint.z + bbox.maxPoint.z) / 2

                    # Create rotation transform (90° CCW = pi/2 radians around Z axis)
                    zAxis = adsk.core.Vector3D.create(0, 0, 1)
                    centerPoint = adsk.core.Point3D.create(centerX, centerY, centerZ)
                    rotateMatrix = adsk.core.Matrix3D.create()
                    rotateMatrix.setToRotation(math.pi / 2, zAxis, centerPoint)

                    moveInput = moveFeatures.createInput2(bodyCollection)
                    moveInput.defineAsFreeMove(rotateMatrix)
                    moveFeatures.add(moveInput)
                    print(f"[DEBUG] Rotated body {body.name} 90° CCW")

            except Exception as e:
                print(f"[ERROR] Extrude/rotate failed for profile {i+1}: {e}")

        # Now add text and emboss into each body
        print("[INFO] Adding and embossing text...")
        embossFeatures = rootComp.features.embossFeatures
        textCutDepth = mm(0.5)  # Cut 0.5mm deep for text

        originX = 0.0
        for idx, size in enumerate(sizes):
            if idx >= len(bodies):
                break

            body = bodies[idx]
            handleCenterX = originX + size / 2.0
            handleCenterY = jawDepth + handleHeight / 2.0

            try:
                # Get the top face of the body (face with highest Z)
                topFace = None
                maxZ = -float('inf')
                for face in body.faces:
                    bbox = face.boundingBox
                    if bbox.maxPoint.z > maxZ:
                        maxZ = bbox.maxPoint.z
                        topFace = face

                if topFace:
                    # Create a sketch on the top face
                    textSketch = rootComp.sketches.add(topFace)

                    # After 90° CCW rotation, the handle is on the left (negative X)
                    # We want text centered on handle, not geometric center of whole face
                    # Offset towards handle area (away from mouth)
                    faceBbox = topFace.boundingBox

                    # Handle is on the min X side after rotation, mouth on max X side
                    # Center text more towards the handle (offset by half the jaw depth)
                    handleCenterX = faceBbox.minPoint.x + mm(handleHeight) / 2
                    handleCenterY = (faceBbox.minPoint.y + faceBbox.maxPoint.y) / 2

                    handleCenterWorld = adsk.core.Point3D.create(
                        handleCenterX,
                        handleCenterY,
                        faceBbox.maxPoint.z
                    )

                    # Use modelToSketchSpace for proper coordinate conversion
                    handleCenterSketch = textSketch.modelToSketchSpace(handleCenterWorld)

                    # Add text to this sketch at the handle center
                    texts = textSketch.sketchTexts
                    position = adsk.core.Point3D.create(handleCenterSketch.x, handleCenterSketch.y, 0)
                    textInput = texts.createInput(f"{size:.1f}", mm(3.0), position)
                    textInput.angle = math.pi / 2  # 90° to align with handle direction
                    textInput.horizontalAlignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment
                    sketchText = texts.add(textInput)

                    print(f"[DEBUG] Size {size}: handle center sketch=({handleCenterSketch.x:.3f}, {handleCenterSketch.y:.3f})")

                    # Create emboss (engrave) using the text
                    textCollection = adsk.core.ObjectCollection.create()
                    textCollection.add(sketchText)

                    embossInput = embossFeatures.createInput(
                        textCollection,
                        topFace,
                        adsk.fusion.EmbossFeatureTypes.EngraveEmbossFeatureType
                    )
                    embossInput.depth = adsk.core.ValueInput.createByReal(textCutDepth)
                    embossFeatures.add(embossInput)
                    print(f"[DEBUG] Embossed text '{size:.1f}' into body {body.name}")

            except Exception as e:
                print(f"[ERROR] Text emboss failed for size {size:.2f} mm: {e}")

            originX += spacing + size + 2 * jawThickness

        print("[INFO] Done.")
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        else:
            print('Failed:\n{}'.format(traceback.format_exc()))
