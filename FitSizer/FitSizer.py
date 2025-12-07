import adsk.core, adsk.fusion, traceback, math


def mm(val):
    """Convert mm to cm (Fusion 360 API internal units)."""
    return val / 10.0


def create_wrench_profile(sketch, origin_x, mouth_width, jaw_depth, jaw_thickness, handle_height):
    """
    Draw a closed wrench profile on the given sketch.
    Returns the handle center position (x, y) in mm.
    """
    lines = sketch.sketchCurves.sketchLines

    # Convert to internal units
    x0 = mm(origin_x)
    mw = mm(mouth_width)
    jd = mm(jaw_depth)
    jt = mm(jaw_thickness)
    hh = mm(handle_height)

    # Define profile points (clockwise from bottom-left outer)
    points = [
        adsk.core.Point3D.create(x0 - jt, 0, 0),           # bottom-left outer
        adsk.core.Point3D.create(x0 - jt, jd + hh, 0),     # top-left outer
        adsk.core.Point3D.create(x0 + mw + jt, jd + hh, 0),# top-right outer
        adsk.core.Point3D.create(x0 + mw + jt, 0, 0),      # bottom-right outer
        adsk.core.Point3D.create(x0 + mw, 0, 0),           # bottom-right inner
        adsk.core.Point3D.create(x0 + mw, jd, 0),          # top-right inner
        adsk.core.Point3D.create(x0, jd, 0),               # top-left inner
        adsk.core.Point3D.create(x0, 0, 0),                # bottom-left inner
    ]

    # Draw closed profile
    for i in range(len(points)):
        lines.addByTwoPoints(points[i], points[(i + 1) % len(points)])

    # Return handle center in mm
    handle_center_x = origin_x + mouth_width / 2.0
    handle_center_y = jaw_depth + handle_height / 2.0
    return handle_center_x, handle_center_y


def extrude_profile(extrudes, profile, depth_mm, operation):
    """Extrude a profile and return the resulting body."""
    ext_input = extrudes.createInput(profile, operation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(depth_mm)))
    result = extrudes.add(ext_input)
    return result.bodies.item(0) if result.bodies.count > 0 else None


def create_text_profiles(sketch, text, position_x, position_y, height_mm):
    """
    Create text on a sketch, explode it, and return the profiles.
    Text is rotated 90 degrees and centered horizontally.
    """
    texts = sketch.sketchTexts
    position = adsk.core.Point3D.create(mm(position_x), mm(position_y), 0)

    text_input = texts.createInput(text, mm(height_mm), position)
    text_input.horizontalAlignment = adsk.core.HorizontalAlignments.CenterHorizontalAlignment
    text_input.angle = math.pi / 2

    sketch_text = texts.add(text_input)
    sketch_text.explode()

    return sketch.profiles


def engrave_profiles(extrudes, profiles, depth_mm):
    """Cut profiles into existing bodies. Returns (success_count, fail_count)."""
    success = 0
    fail = 0

    for i in range(profiles.count):
        try:
            profile = profiles.item(i)
            ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
            distance = adsk.fusion.DistanceExtentDefinition.create(
                adsk.core.ValueInput.createByReal(mm(depth_mm))
            )
            ext_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.NegativeExtentDirection)
            extrudes.add(ext_input)
            success += 1
        except:
            fail += 1

    return success, fail


def create_offset_plane(root_comp, z_offset_mm):
    """Create a construction plane offset from XY plane."""
    planes = root_comp.constructionPlanes
    plane_input = planes.createInput()
    offset = adsk.core.ValueInput.createByReal(mm(z_offset_mm))
    plane_input.setByOffset(root_comp.xYConstructionPlane, offset)
    return planes.add(plane_input)


def create_labeled_wrench(root_comp, extrudes, label, origin_x, config):
    """
    Create a single wrench body with engraved label.
    Returns debug info string.
    """
    # Create wrench body sketch on XY plane
    body_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)

    handle_x, handle_y = create_wrench_profile(
        body_sketch,
        origin_x,
        config['mouth_width'],
        config['jaw_depth'],
        config['jaw_thickness'],
        config['handle_height']
    )

    # Extrude wrench body
    if body_sketch.profiles.count == 0:
        return f"{label}: No profile created"

    body = extrude_profile(
        extrudes,
        body_sketch.profiles.item(0),
        config['extrude_depth'],
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    if body is None:
        return f"{label}: Extrude failed"

    body.name = label

    # Create text sketch on a plane at the top of the body
    text_plane = create_offset_plane(root_comp, config['extrude_depth'])
    text_sketch = root_comp.sketches.add(text_plane)

    # Create and engrave text
    profiles = create_text_profiles(
        text_sketch,
        label,
        handle_x,
        handle_y,
        config['text_height']
    )

    success, fail = engrave_profiles(extrudes, profiles, config['emboss_depth'])

    return f"{label}: {profiles.count} profiles, {success} engraved, {fail} failed"


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root_comp = design.rootComponent
        extrudes = root_comp.features.extrudeFeatures

        # Configuration
        config = {
            'mouth_width': 3.0,
            'jaw_depth': 5.0,
            'jaw_thickness': 2.0,
            'handle_height': 12.0,
            'extrude_depth': 2.0,
            'text_height': 2.5,
            'emboss_depth': 0.5,
            'spacing': 20.0,
        }

        labels = ["T1", "T2", "T3", "T4"]
        debug_info = []

        # Create each wrench completely before moving to the next
        for i, label in enumerate(labels):
            origin_x = i * config['spacing']
            result = create_labeled_wrench(root_comp, extrudes, label, origin_x, config)
            debug_info.append(result)

        ui.messageBox('\n'.join(debug_info), "Results")

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
