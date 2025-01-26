import adsk.core, adsk.fusion

def create_frame_board(rootComp, face, board_length, board_width, board_thickness, inset_depth):
    """
    Creates a single framing board on the given planar face by:
      1. Creating a new sketch in the local plane of 'face'.
      2. Drawing a rectangle in local 2D coordinates.
      3. Extruding that rectangle in the face's normal direction by 'board_thickness'.

    Args:
        rootComp        : The root component of the design.
        face            : The planar face on which to create the board (e.g., the right face of plywood).
        board_length    : The 2D length (in local X) of the board in that plane.
        board_width     : The 2D width (in local Y) of the board in that plane.
        board_thickness : How far to extrude normal to the face (inches).
        inset_depth     : How much to “inset” or offset the board in the sketch plane, if needed.

    Returns:
        The extruded board body, or None if creation failed.
    """
    app = adsk.core.Application.get()
    ui  = app.userInterface

    # --------------------------------------------------------------------------
    # 1) Create a new sketch on the specified face (2D plane).
    # --------------------------------------------------------------------------
    frame_sketch = rootComp.sketches.add(face)

    # --------------------------------------------------------------------------
    # 2) Define a rectangle in *local plane* coordinates.
    #    - (0, 0) is the origin in the sketch plane.
    #    - If you want to offset/inset, just shift your corner points accordingly.
    # --------------------------------------------------------------------------
    # For example, let's position the rectangle from (inset_depth, inset_depth)
    # to (board_length - inset_depth, board_width - inset_depth).
    # You can adjust as needed.
    p1_local = adsk.core.Point3D.create(inset_depth, inset_depth, 0)
    p2_local = adsk.core.Point3D.create(
        board_length - inset_depth,
        board_width - inset_depth,
        0
    )

    # Draw the rectangle
    lines = frame_sketch.sketchCurves.sketchLines
    rect_lines = lines.addTwoPointRectangle(p1_local, p2_local)

    # Check we got a profile
    if frame_sketch.profiles.count == 0:
        ui.messageBox("No profiles found for the frame board rectangle.")
        return None

    # We expect the rectangle to give us 1 profile:
    frame_profile = frame_sketch.profiles.item(0)

    # --------------------------------------------------------------------------
    # 3) Extrude the profile in the face normal direction by board_thickness.
    # --------------------------------------------------------------------------
    extrudes = rootComp.features.extrudeFeatures
    thickness_input = adsk.core.ValueInput.createByReal(board_thickness)

    frame_ext = extrudes.addSimple(
        frame_profile,
        thickness_input,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    if not frame_ext or frame_ext.bodies.count == 0:
        ui.messageBox("Extrude failed for frame board.")
        return None

    board_body = frame_ext.bodies.item(0)
    board_body.name = "Frame Board"
    return board_body
