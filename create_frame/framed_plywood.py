import adsk.core, adsk.fusion, adsk.cam, traceback
import os.path

# Get the absolute path of the directory where the script is located.
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute paths to the module files.
plywood_module_path = os.path.join(script_dir, "plywood.py")
framing_board_module_path = os.path.join(script_dir, "framing_board.py")

# Import the modules using their absolute paths.
import importlib.util
plywood_spec = importlib.util.spec_from_file_location("plywood", plywood_module_path)
plywood = importlib.util.module_from_spec(plywood_spec)
plywood_spec.loader.exec_module(plywood)

framing_board_spec = importlib.util.spec_from_file_location("framing_board", framing_board_module_path)
framing_board = importlib.util.module_from_spec(framing_board_spec)
framing_board_spec.loader.exec_module(framing_board)

def create_framed_plywood():
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Set units to inches.
        unitsMgr = design.unitsManager
        unitsMgr.expressionUnits = 'in'

        # --- Define dimensions (in inches) ---
        plywood_width = 48.0  # inches
        plywood_length = 96.0  # inches
        plywood_thickness = 0.75  # inches (e.g., 3/4 inch plywood)

        frame_thickness = 0.75  # inches (1x3 nominal size, approx. 0.75 x 2.5 inches actual)
        frame_width = 2.5  # inches

        inset_depth = 0.25  # inches (how deep the plywood sits in the frame)

        # --- Create the plywood ---
        plywood_body = plywood.create_plywood(rootComp, plywood_width, plywood_length, plywood_thickness)

        # --- Create the frame boards ---
        # Find the right face of the plywood for the frame
        max_x_face = None
        for face in plywood_body.faces:
            face_x_value = face.boundingBox.maxPoint.x
            if max_x_face is None or face_x_value > max_x_face.boundingBox.maxPoint.x:
                max_x_face = face
# Dimensions for this particular side of the frame
        # board_length   = plywood_length   # how long we want the board in the local X direction
        # board_width    = frame_width      # how wide we want the board in local Y
        # board_thickness = frame_thickness

        # frame_board_body = framing_board.create_frame_board(
        #     rootComp,
        #     max_x_face,        # the planar face you want to sketch on
        #     board_length,      # length in local X of the face
        #     board_width,       # width in local Y of the face
        #     board_thickness,
        #     inset_depth
        # )


        # if frame_board_body is None:
        #     ui.messageBox("Frame board body is None. Extrude likely failed.")
        #     return

        # --- Move the Frame forward by inset depth ---
        # transform = adsk.core.Matrix3D.create()
        # transform.translation = adsk.core.Vector3D.create(0, 0, inset_depth)

        # moveFeats = rootComp.features.moveFeatures
        # moveFeatureInput = moveFeats.createInput(adsk.core.ObjectCollection.create(), transform)
        # moveFeatureInput.bodies.add(frame_board_body)
        # moveFeats.add(moveFeatureInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))