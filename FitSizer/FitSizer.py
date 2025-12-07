import adsk.core, adsk.fusion, traceback

# Helper: convert mm to internal units (Fusion 360 API uses centimeters internally)
def mm(val):
    return val / 10.0  # Convert mm to cm for Fusion 360 API

def addWrenchU(sketch, originX, mouthWidth, jawDepth=3.0, jawThickness=1.0, handleLength=12.0, handleWidth=5.0):
    """
    Draws a 2D profile of a half-wrench with an open U-shaped mouth:
      - Two parallel jaw walls separated by 'mouthWidth'
      - Jaw depth in Y-direction given by jawDepth (thickness of the jaw, front-to-back)
      - Handle is attached to the back of the jaw walls, with width 'handleWidth' and length 'handleLength'
    originX: X coordinate of left inner jaw wall (inside mouth) at Y = 0
    """
    lines = sketch.sketchCurves.sketchLines

    # Convert all dimensions from mm to cm (Fusion internal units)
    x0 = mm(originX)
    y0 = 0
    mw = mm(mouthWidth)
    jd = mm(jawDepth)
    jt = mm(jawThickness)
    hl = mm(handleLength)

    # Left inner jaw wall
    p1 = adsk.core.Point3D.create(x0, y0, 0)
    p2 = adsk.core.Point3D.create(x0, y0 + jd, 0)

    # Right inner jaw wall
    p3 = adsk.core.Point3D.create(x0 + mw, y0, 0)
    p4 = adsk.core.Point3D.create(x0 + mw, y0 + jd, 0)

    # Outer walls (with thickness)
    p1o = adsk.core.Point3D.create(x0 - jt, y0, 0)
    p2o = adsk.core.Point3D.create(x0 - jt, y0 + jd, 0)
    p3o = adsk.core.Point3D.create(x0 + mw + jt, y0, 0)
    p4o = adsk.core.Point3D.create(x0 + mw + jt, y0 + jd, 0)

    # Draw jaw walls (rectangular U-shape)
    # Left wall
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p2o)
    lines.addByTwoPoints(p2o, p1o)
    lines.addByTwoPoints(p1o, p1)

    # Right wall
    lines.addByTwoPoints(p3, p4)
    lines.addByTwoPoints(p4, p4o)
    lines.addByTwoPoints(p4o, p3o)
    lines.addByTwoPoints(p3o, p3)

    # Back of the jaw connecting outer walls (where handle attaches)
    lines.addByTwoPoints(p2o, p4o)

    # Handle rectangle (attached to back of jaw)
    hx0 = x0 - jt
    hx1 = x0 + mw + jt
    hy0 = y0 + jd
    hy1 = hy0 + hl

    p_handle_bl = adsk.core.Point3D.create(hx0, hy0, 0)
    p_handle_tl = adsk.core.Point3D.create(hx0, hy1, 0)
    p_handle_br = adsk.core.Point3D.create(hx1, hy0, 0)
    p_handle_tr = adsk.core.Point3D.create(hx1, hy1, 0)

    lines.addByTwoPoints(p_handle_bl, p_handle_tl)
    lines.addByTwoPoints(p_handle_tl, p_handle_tr)
    lines.addByTwoPoints(p_handle_tr, p_handle_br)
    lines.addByTwoPoints(p_handle_br, p_handle_bl)

    # Debug print of coordinates
    print(f"[DEBUG] Wrench: originX={originX}, mouthWidth={mouthWidth}, "
          f"jaw walls at X = {x0},{x0+mouthWidth}; jawDepth={jawDepth}, handle top Y={hy1}")

def addText(sketch, textString, insertX, insertY, textHeightMM=5.0):
    texts = sketch.sketchTexts
    # Convert height to cm
    height_cm = textHeightMM / 10.0
    heightInput = adsk.core.ValueInput.createByReal(height_cm)
    expr = f"'{textString}'"
    print(f"[DEBUG] Creating text: {expr} at ({insertX}, {insertY}), height(cm)={height_cm}")
    textInput = texts.createInput3(expr, heightInput)
    ok = textInput.setAsMultiLine(
        adsk.core.Point3D.create(insertX, insertY, 0),
        adsk.core.Point3D.create(insertX + 1.0, insertY + 1.0, 0),
        adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
        adsk.core.VerticalAlignments.BottomVerticalAlignment,
        0
    )
    print(f"[DEBUG] setAsMultiLine returned: {ok}")
    texts.add(textInput)
    print("[DEBUG] Text added.")

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
        minW = 2.0
        maxW = 3.5  # Reduced to 4 shapes for debugging (2.0, 2.5, 3.0, 3.5)
        step = 0.5
        spacing = 20.0  # Spacing in mm between shapes
        originX = 0.0
        w = minW
        while w <= maxW + 1e-6:
            addWrenchU(sketch, originX, w, jawDepth=4.0, jawThickness=1.0, handleLength=15.0, handleWidth=5.0)
            # Convert text position to cm for Fusion API
            textX = mm(originX + w/2.0)
            textY = mm(-5.0)
            try:
                addText(sketch, f"{w:.1f} mm", textX, textY, textHeightMM=5.0)
            except Exception as e:
                print(f"[ERROR] Text add failed for width {w:.2f} mm: {e}")
            originX += spacing
            w += step
        print("[INFO] Done.")
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        else:
            print('Failed:\n{}'.format(traceback.format_exc()))
