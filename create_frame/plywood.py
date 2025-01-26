import adsk.core, adsk.fusion

def create_plywood(rootComp, width, length, thickness):
    """Creates the plywood component.

    Args:
        rootComp:   The root component of the design.
        width:      The width of the plywood (in inches).
        length:     The length of the plywood (in inches).
        thickness:  The thickness of the plywood (in inches).

    Returns:
        The plywood body.
    """
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    # Debug: Print the current distance display units in Fusion
    unitsMgr = app.activeProduct.unitsManager
    print(f"[DEBUG] Current Distance Units: {unitsMgr.distanceDisplayUnits}")
    
    # Debug: Print the parameters we're about to use
    print(f"[DEBUG] create_plywood called with:")
    print(f" - width: {width} in")
    print(f" - length: {length} in")
    print(f" - thickness: {thickness} in")

    # Create a new sketch on the XZ plane.
    sketch = rootComp.sketches.add(rootComp.xZConstructionPlane)

    # Create a rectangle for the plywood
    plywood_rect_lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(width, thickness, 0)
    )

    # Debug: Print info about the rectangle lines
    for i, line in enumerate(plywood_rect_lines):
        line_length = line.length
        print(f"[DEBUG] Rectangle line {i} length: {line_length:.4f} in")

    # Retrieve the profile formed by the rectangle
    if sketch.profiles.count == 0:
        print("[DEBUG] No profiles found in the sketch!")
        return None

    plywood_prof = sketch.profiles.item(0)

    # Debug: Print the area of the profile
    prof_area = plywood_prof.areaProperties().area
    print(f"[DEBUG] Plywood profile area: {prof_area:.4f} square units")

    # Extrude the plywood by `length` along the sketch's normal (Z direction for XZ plane)
    extrudes = rootComp.features.extrudeFeatures
    plywood_ext = extrudes.addSimple(
        plywood_prof,
        adsk.core.ValueInput.createByReal(length),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    if not plywood_ext or plywood_ext.bodies.count == 0:
        print("[DEBUG] Plywood extrusion failed!")
        return None

    plywood_body = plywood_ext.bodies.item(0)
    plywood_body.name = "Plywood"

    # Debug: Print the bounding box of the newly created body
    bbox = plywood_body.boundingBox
    print("[DEBUG] Plywood body bounding box:")
    print(f" - minPoint = ({bbox.minPoint.x:.3f}, {bbox.minPoint.y:.3f}, {bbox.minPoint.z:.3f})")
    print(f" - maxPoint = ({bbox.maxPoint.x:.3f}, {bbox.maxPoint.y:.3f}, {bbox.maxPoint.z:.3f})")

    return plywood_body
