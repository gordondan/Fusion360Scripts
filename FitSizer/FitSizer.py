import adsk.core, adsk.fusion, traceback

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
    Add centered text at the given position (in mm).
    """
    texts = sketch.sketchTexts
    # Convert to cm
    height_cm = textHeightMM / 10.0
    cx = mm(centerX_mm)
    cy = mm(centerY_mm)

    # Create a bounding box around the center point
    boxSize = mm(15)  # 15mm box should be enough for text
    corner1 = adsk.core.Point3D.create(cx - boxSize/2, cy - boxSize/2, 0)
    corner2 = adsk.core.Point3D.create(cx + boxSize/2, cy + boxSize/2, 0)

    heightInput = adsk.core.ValueInput.createByReal(height_cm)
    textInput = texts.createInput3(f"'{textString}'", heightInput)
    textInput.setAsMultiLine(
        corner1,
        corner2,
        adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
        adsk.core.VerticalAlignments.MiddleVerticalAlignment,
        0
    )
    texts.add(textInput)
    print(f"[DEBUG] Text '{textString}' added at center ({centerX_mm}, {centerY_mm})mm")

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

        originX = 0.0
        w = minW
        while w <= maxW + 1e-6:
            # Draw the wrench shape and get handle center for text
            handleCenterX, handleCenterY = addWrenchU(
                sketch, originX, w,
                jawDepth=jawDepth,
                jawThickness=jawThickness,
                handleHeight=handleHeight
            )

            # Add centered text in the handle area
            try:
                addText(sketch, f"{w:.1f}", handleCenterX, handleCenterY, textHeightMM=3.0)
            except Exception as e:
                print(f"[ERROR] Text add failed for width {w:.2f} mm: {e}")

            originX += spacing + w + 2 * jawThickness  # Space based on shape width
            w += step

        # Extrude all profiles
        print("[INFO] Extruding profiles...")
        extrudes = rootComp.features.extrudeFeatures
        for i, profile in enumerate(sketch.profiles):
            try:
                extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                distance = adsk.core.ValueInput.createByReal(mm(extrudeDepth))
                extInput.setDistanceExtent(False, distance)
                extrudes.add(extInput)
                print(f"[DEBUG] Extruded profile {i+1}")
            except Exception as e:
                print(f"[ERROR] Extrude failed for profile {i+1}: {e}")

        print("[INFO] Done.")
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        else:
            print('Failed:\n{}'.format(traceback.format_exc()))
