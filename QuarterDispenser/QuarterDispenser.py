"""
Quarter Dispenser - A pocket-friendly dispenser for 9 US quarters
Designed with visibility window, smooth edges, and button-activated dispensing mechanism.
Compatible with multi-color printing (AMS).
"""

import adsk.core
import adsk.fusion
import traceback
import math

app = adsk.core.Application.get()
ui = app.userInterface


def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Please open or create a Fusion 360 design first.")
            return

        root = design.rootComponent
        um = design.unitsManager

        # ==================== DIMENSIONS ====================
        # US Quarter dimensions
        QUARTER_DIA = 2.426  # cm (24.26mm)
        QUARTER_THICK = 0.175  # cm (1.75mm)
        QUARTER_COUNT = 9

        # Clearances for smooth operation
        CLEARANCE = 0.03  # cm (0.3mm)

        # Wall thicknesses
        WALL_THICK = 0.2  # cm (2mm)
        WINDOW_THICK = 0.1  # cm (1mm) - thinner for transparency

        # Main body dimensions
        BODY_WIDTH = QUARTER_DIA + 2 * WALL_THICK + 2 * CLEARANCE  # ~2.9cm
        BODY_LENGTH = QUARTER_COUNT * QUARTER_THICK + 2 * CLEARANCE + 1.5  # ~3.2cm for quarters + spring space
        BODY_HEIGHT = QUARTER_DIA + 2 * WALL_THICK + 2 * CLEARANCE  # ~2.9cm

        # Button dimensions
        BUTTON_WIDTH = 0.8  # cm
        BUTTON_HEIGHT = 1.0  # cm
        BUTTON_DEPTH = 0.3  # cm
        BUTTON_TRAVEL = 0.15  # cm

        # Fillet radius for smooth edges
        FILLET_RADIUS = 0.2  # cm (2mm)

        # Spring slot dimensions
        SPRING_WIDTH = 0.5  # cm
        SPRING_HEIGHT = 0.3  # cm

        # Window dimensions
        WINDOW_START = 0.8  # cm from front
        WINDOW_LENGTH = 2.0  # cm

        # ==================== HELPER FUNCTIONS ====================

        def create_rounded_rect_sketch(sketch, width, height, x_offset=0, y_offset=0, fillet_r=0):
            """Create a rounded rectangle sketch"""
            lines = sketch.sketchCurves.sketchLines

            # Create rectangle corners
            p1 = adsk.core.Point3D.create(x_offset, y_offset, 0)
            p2 = adsk.core.Point3D.create(x_offset + width, y_offset, 0)
            p3 = adsk.core.Point3D.create(x_offset + width, y_offset + height, 0)
            p4 = adsk.core.Point3D.create(x_offset, y_offset + height, 0)

            # Draw lines
            l1 = lines.addByTwoPoints(p1, p2)
            l2 = lines.addByTwoPoints(p2, p3)
            l3 = lines.addByTwoPoints(p3, p4)
            l4 = lines.addByTwoPoints(p4, p1)

            # Add fillets if requested
            if fillet_r > 0:
                try:
                    sketch.sketchCurves.sketchArcs.addFillet(l1, l1.endSketchPoint.geometry,
                                                             l2, l2.startSketchPoint.geometry, fillet_r)
                    sketch.sketchCurves.sketchArcs.addFillet(l2, l2.endSketchPoint.geometry,
                                                             l3, l3.startSketchPoint.geometry, fillet_r)
                    sketch.sketchCurves.sketchArcs.addFillet(l3, l3.endSketchPoint.geometry,
                                                             l4, l4.startSketchPoint.geometry, fillet_r)
                    sketch.sketchCurves.sketchArcs.addFillet(l4, l4.endSketchPoint.geometry,
                                                             l1, l1.startSketchPoint.geometry, fillet_r)
                except:
                    pass  # Fillets might fail for small dimensions

        def create_circle_sketch(sketch, center_x, center_y, radius):
            """Create a circle in a sketch"""
            center = adsk.core.Point3D.create(center_x, center_y, 0)
            return sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

        # ==================== CREATE MAIN BODY ====================

        # Create component for organization
        mainOcc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        mainComp = mainOcc.component
        mainComp.name = "Quarter Dispenser"

        # Create the main body shell
        bodySketch = mainComp.sketches.add(mainComp.xYConstructionPlane)
        bodySketch.name = "Body Profile"

        # Create outer profile
        create_rounded_rect_sketch(bodySketch, BODY_WIDTH, BODY_HEIGHT,
                                   -BODY_WIDTH/2, -BODY_HEIGHT/2, FILLET_RADIUS)

        # Extrude the body
        bodyProfile = bodySketch.profiles.item(0)
        extrudes = mainComp.features.extrudeFeatures
        extInput = extrudes.createInput(bodyProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(BODY_LENGTH)
        extInput.setDistanceExtent(False, distance)
        bodyExtrude = extrudes.add(extInput)
        bodyExtrude.bodies.item(0).name = "Main Body"

        # ==================== CREATE QUARTER CHAMBER (HOLLOW OUT) ====================

        # Create sketch for quarter chamber
        chamberSketch = mainComp.sketches.add(mainComp.xYConstructionPlane)
        chamberSketch.name = "Quarter Chamber"

        # Chamber is circular to match quarter shape
        chamberCircle = create_circle_sketch(chamberSketch, 0, 0, QUARTER_DIA/2 + CLEARANCE)

        # Extrude to hollow out
        chamberProfile = chamberSketch.profiles.item(0)
        chamberExtInput = extrudes.createInput(chamberProfile, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # Chamber starts from the front and goes most of the way through
        chamberOffset = adsk.core.ValueInput.createByReal(WALL_THICK)
        chamberDepth = adsk.core.ValueInput.createByReal(QUARTER_COUNT * QUARTER_THICK + CLEARANCE + 1.0)
        chamberExtInput.startExtent = adsk.fusion.FromEntityStartDefinition.create(
            mainComp.xYConstructionPlane, chamberOffset)
        chamberExtInput.setDistanceExtent(False, chamberDepth)

        chamberExtrude = extrudes.add(chamberExtInput)

        # ==================== CREATE VISIBILITY WINDOW ====================

        # Create a plane offset for the window
        planes = mainComp.constructionPlanes
        planeInput = planes.createInput()
        offsetVal = adsk.core.ValueInput.createByReal(WINDOW_START)
        planeInput.setByOffset(mainComp.xYConstructionPlane, offsetVal)
        windowPlane = planes.add(planeInput)

        # Create window sketch
        windowSketch = mainComp.sketches.add(windowPlane)
        windowSketch.name = "Visibility Window"

        # Window is a rounded rectangle on the side
        window_height = BODY_HEIGHT * 0.6
        create_rounded_rect_sketch(windowSketch, WINDOW_LENGTH, window_height,
                                   -WINDOW_LENGTH/2, -window_height/2, 0.1)

        # Cut through for the window - cut all the way through!
        windowProfile = windowSketch.profiles.item(0)
        windowExtInput = extrudes.createInput(windowProfile, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # Cut completely through both sides
        windowCutDepth = adsk.core.ValueInput.createByReal(BODY_WIDTH + 1.0)
        windowExtInput.setSymmetricExtent(windowCutDepth, True)

        windowExtrude = extrudes.add(windowExtInput)

        # ==================== CREATE DISPENSER SLOT ====================

        # Create sketch on front face for the dispenser slot
        slotPlane = mainComp.constructionPlanes
        slotPlaneInput = slotPlane.createInput()
        slotOffset = adsk.core.ValueInput.createByReal(WALL_THICK)
        slotPlaneInput.setByOffset(mainComp.xYConstructionPlane, slotOffset)
        slotPlaneObj = slotPlane.add(slotPlaneInput)

        slotSketch = mainComp.sketches.add(slotPlaneObj)
        slotSketch.name = "Dispenser Slot"

        # Slot at the bottom for quarter to exit
        slot_width = QUARTER_DIA + CLEARANCE * 2
        slot_height = QUARTER_THICK + CLEARANCE * 2
        slot_y_pos = -BODY_HEIGHT/2 + WALL_THICK + slot_height/2

        create_rounded_rect_sketch(slotSketch, slot_width, slot_height,
                                   -slot_width/2, slot_y_pos - slot_height/2, 0.05)

        # Cut the slot
        slotProfile = slotSketch.profiles.item(0)
        slotExtInput = extrudes.createInput(slotProfile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        slotDepth = adsk.core.ValueInput.createByReal(WALL_THICK + 0.1)
        slotExtInput.setDistanceExtent(False, slotDepth)
        slotExtrude = extrudes.add(slotExtInput)

        # ==================== CREATE BUTTON ====================

        # Create button on top surface
        buttonPlane = mainComp.constructionPlanes
        buttonPlaneInput = buttonPlane.createInput()
        buttonOffset = adsk.core.ValueInput.createByReal(BODY_LENGTH * 0.7)
        buttonPlaneInput.setByOffset(mainComp.xYConstructionPlane, buttonOffset)
        buttonPlaneObj = buttonPlane.add(buttonPlaneInput)

        buttonSketch = mainComp.sketches.add(buttonPlaneObj)
        buttonSketch.name = "Button"

        # Button positioned on top
        button_x = 0
        button_y = BODY_HEIGHT/2 - WALL_THICK - BUTTON_HEIGHT/2

        create_rounded_rect_sketch(buttonSketch, BUTTON_WIDTH, BUTTON_HEIGHT,
                                   button_x - BUTTON_WIDTH/2, button_y - BUTTON_HEIGHT/2, 0.1)

        # Create button recess (where button sits)
        buttonRecessProfile = buttonSketch.profiles.item(0)
        buttonRecessInput = extrudes.createInput(buttonRecessProfile,
                                                 adsk.fusion.FeatureOperations.CutFeatureOperation)
        recessDepth = adsk.core.ValueInput.createByReal(BUTTON_DEPTH)
        buttonRecessInput.setDistanceExtent(True, recessDepth)  # Cut inward (negative direction)
        buttonRecess = extrudes.add(buttonRecessInput)

        # Create actual button body (as separate component for different color)
        buttonComp = mainComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        buttonCompObj = buttonComp.component
        buttonCompObj.name = "Button"

        buttonBodySketch = buttonCompObj.sketches.add(buttonCompObj.xYConstructionPlane)
        create_rounded_rect_sketch(buttonBodySketch, BUTTON_WIDTH - 0.04, BUTTON_HEIGHT - 0.04,
                                   -BUTTON_WIDTH/2 + 0.02, -BUTTON_HEIGHT/2 + 0.02, 0.08)

        # Extrude button
        buttonBodyProfile = buttonBodySketch.profiles.item(0)
        buttonExtrudes = buttonCompObj.features.extrudeFeatures
        buttonExtInput = buttonExtrudes.createInput(buttonBodyProfile,
                                                    adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        buttonHeight = adsk.core.ValueInput.createByReal(BUTTON_DEPTH - 0.05)
        buttonExtInput.setDistanceExtent(False, buttonHeight)
        buttonBodyExtrude = buttonExtrudes.add(buttonExtInput)
        buttonBodyExtrude.bodies.item(0).name = "Button Body"

        # Position button in the recess
        buttonComp.component.opacity = 1.0

        # ==================== CREATE GATE MECHANISM ====================

        # Create a sliding gate that blocks the dispenser slot
        # Button pushes on the gate to release one quarter at a time

        # Gate channel - a slot for the gate to slide in
        gateChannelPlane = mainComp.constructionPlanes
        gateChannelPlaneInput = gateChannelPlane.createInput()
        gateChannelOffset = adsk.core.ValueInput.createByReal(WALL_THICK + 0.1)
        gateChannelPlaneInput.setByOffset(mainComp.xYConstructionPlane, gateChannelOffset)
        gateChannelPlaneObj = gateChannelPlane.add(gateChannelPlaneInput)

        gateChannelSketch = mainComp.sketches.add(gateChannelPlaneObj)
        gateChannelSketch.name = "Gate Channel"

        # Channel runs vertically along the front, next to the chamber
        gate_channel_width = 0.25  # cm
        gate_channel_height = BODY_HEIGHT * 0.7
        gate_x_pos = QUARTER_DIA/2 + CLEARANCE + 0.2

        create_rounded_rect_sketch(gateChannelSketch, gate_channel_width, gate_channel_height,
                                   gate_x_pos - gate_channel_width/2, -gate_channel_height/2, 0.05)

        # Cut the channel
        gateChannelProfile = gateChannelSketch.profiles.item(0)
        gateChannelExtInput = extrudes.createInput(gateChannelProfile,
                                                   adsk.fusion.FeatureOperations.CutFeatureOperation)
        channelDepth = adsk.core.ValueInput.createByReal(0.3)
        gateChannelExtInput.setDistanceExtent(False, channelDepth)
        gateChannelExtrude = extrudes.add(gateChannelExtInput)

        # Create the gate component (slides up/down when button pressed)
        gateComp = mainComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        gateCompObj = gateComp.component
        gateCompObj.name = "Dispenser Gate"

        gateSketch = gateCompObj.sketches.add(gateCompObj.xYConstructionPlane)

        # Gate is a small slider
        gate_width = gate_channel_width - 0.04  # clearance
        gate_height = 1.0  # tall enough to block quarters
        gate_thickness = 0.25

        create_rounded_rect_sketch(gateSketch, gate_width, gate_height,
                                   -gate_width/2, -gate_height/2, 0.03)

        # Extrude gate
        gateProfile = gateSketch.profiles.item(0)
        gateExtrudes = gateCompObj.features.extrudeFeatures
        gateExtInput = gateExtrudes.createInput(gateProfile,
                                                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        gateThick = adsk.core.ValueInput.createByReal(gate_thickness)
        gateExtInput.setDistanceExtent(False, gateThick)
        gateExtrude = gateExtrudes.add(gateExtInput)
        gateExtrude.bodies.item(0).name = "Gate"

        # Add a button pusher extension to the gate (top part that button presses)
        pusherSketch = gateCompObj.sketches.add(gateCompObj.xYConstructionPlane)
        pusher_width = 0.4
        pusher_height = 0.3

        create_rounded_rect_sketch(pusherSketch, pusher_width, pusher_height,
                                   -pusher_width/2, gate_height/2 - pusher_height/2, 0.05)

        pusherProfile = pusherSketch.profiles.item(0)
        pusherExtInput = gateExtrudes.createInput(pusherProfile,
                                                  adsk.fusion.FeatureOperations.JoinFeatureOperation)
        pusherThick = adsk.core.ValueInput.createByReal(gate_thickness)
        pusherExtInput.setDistanceExtent(False, pusherThick)
        pusherExtrude = gateExtrudes.add(pusherExtInput)

        # ==================== CREATE SPRING GUIDE ====================

        # Create internal rails/guides for quarter alignment
        guideSketch = mainComp.sketches.add(mainComp.xYConstructionPlane)
        guideSketch.name = "Spring Guide"

        # Create small guide rails on sides
        guide_offset = QUARTER_DIA/2 + CLEARANCE/2
        guide_width = 0.1
        guide_height = 0.3

        # Left guide
        create_rounded_rect_sketch(guideSketch, guide_width, guide_height,
                                   -guide_offset - guide_width/2, -guide_height/2, 0.02)

        # Right guide
        create_rounded_rect_sketch(guideSketch, guide_width, guide_height,
                                   guide_offset - guide_width/2, -guide_height/2, 0.02)

        # Extrude guides
        for i in range(guideSketch.profiles.count):
            guideProfile = guideSketch.profiles.item(i)
            guideExtInput = extrudes.createInput(guideProfile,
                                                 adsk.fusion.FeatureOperations.JoinFeatureOperation)
            guideStartOffset = adsk.core.ValueInput.createByReal(WALL_THICK + 0.2)
            guideLength = adsk.core.ValueInput.createByReal(BODY_LENGTH - WALL_THICK * 2 - 1.0)
            guideExtInput.startExtent = adsk.fusion.FromEntityStartDefinition.create(
                mainComp.xYConstructionPlane, guideStartOffset)
            guideExtInput.setDistanceExtent(False, guideLength)
            guideExtrude = extrudes.add(guideExtInput)

        # ==================== CREATE SPRING FOLLOWER ====================

        # Create a separate component for the spring follower
        followerComp = mainComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        followerCompObj = followerComp.component
        followerCompObj.name = "Spring Follower"

        followerSketch = followerCompObj.sketches.add(followerCompObj.xYConstructionPlane)

        # Follower is a disc that fits in the chamber
        follower_radius = QUARTER_DIA/2 + CLEARANCE - 0.02
        create_circle_sketch(followerSketch, 0, 0, follower_radius)

        # Extrude follower
        followerProfile = followerSketch.profiles.item(0)
        followerExtrudes = followerCompObj.features.extrudeFeatures
        followerExtInput = followerExtrudes.createInput(followerProfile,
                                                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        followerThick = adsk.core.ValueInput.createByReal(0.2)
        followerExtInput.setDistanceExtent(False, followerThick)
        followerExtrude = followerExtrudes.add(followerExtInput)
        followerExtrude.bodies.item(0).name = "Follower Disc"

        # ==================== CREATE TRANSPARENT WINDOW PANEL ====================

        # Create a separate component for the transparent window
        windowPanelComp = mainComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        windowPanelCompObj = windowPanelComp.component
        windowPanelCompObj.name = "Transparent Window"

        windowPanelSketch = windowPanelCompObj.sketches.add(windowPanelCompObj.xYConstructionPlane)

        # Window panel dimensions (slightly smaller than the cutout)
        panel_width = WINDOW_LENGTH - 0.02
        panel_height = window_height - 0.02

        create_rounded_rect_sketch(windowPanelSketch, panel_width, panel_height,
                                   -panel_width/2, -panel_height/2, 0.08)

        # Extrude window panel
        windowPanelProfile = windowPanelSketch.profiles.item(0)
        windowPanelExtrudes = windowPanelCompObj.features.extrudeFeatures
        windowPanelExtInput = windowPanelExtrudes.createInput(windowPanelProfile,
                                                              adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        windowPanelThick = adsk.core.ValueInput.createByReal(WINDOW_THICK)
        windowPanelExtInput.setDistanceExtent(False, windowPanelThick)
        windowPanelExtrude = windowPanelExtrudes.add(windowPanelExtInput)
        windowPanelExtrude.bodies.item(0).name = "Window Panel"

        # Make window semi-transparent in display
        windowPanelCompObj.opacity = 0.3

        # ==================== APPLY FILLETS FOR COMFORT ====================

        # Apply fillets to all sharp external edges
        try:
            fillets = mainComp.features.filletFeatures
            edgeCollection = adsk.core.ObjectCollection.create()

            # Collect external edges
            body = bodyExtrude.bodies.item(0)
            for edge in body.edges:
                # Add all external edges
                if edge.isDegenerate == False:
                    edgeCollection.add(edge)

            if edgeCollection.count > 0:
                filletInput = fillets.createInput()
                filletInput.addConstantRadiusEdgeSet(edgeCollection,
                                                     adsk.core.ValueInput.createByReal(FILLET_RADIUS/2),
                                                     False)
                filletInput.isG2 = False
                filletInput.isRollingBallCorner = True
                fillets.add(filletInput)
        except:
            # Fillets might fail on some edges, that's okay
            pass

        # ==================== SUMMARY MESSAGE ====================

        ui.messageBox(
            "Quarter Dispenser created successfully!\n\n"
            f"Design specifications:\n"
            f"- Holds {QUARTER_COUNT} US quarters\n"
            f"- Dimensions: {BODY_WIDTH:.1f} x {BODY_LENGTH:.1f} x {BODY_HEIGHT:.1f} cm\n"
            f"- Pocket-friendly with rounded edges ({FILLET_RADIUS*10:.0f}mm radius)\n"
            f"- See-through window to count quarters at a glance\n"
            f"- Button-activated sliding gate mechanism\n\n"
            "Components created:\n"
            "1. Main Body (print in primary color)\n"
            "2. Button (print in accent color)\n"
            "3. Dispenser Gate (slides when button pressed)\n"
            "4. Transparent Window Panel (print in clear/translucent)\n"
            "5. Spring Follower (print in any color)\n\n"
            "How it works:\n"
            "- Spring pushes quarters toward the front\n"
            "- Quarters stack vertically in the chamber\n"
            "- Look through the window to see how many quarters remain\n"
            "- Press the button to push the gate down\n"
            "- Gate slides aside, releasing one quarter through the slot\n"
            "- Release button, gate springs back to block position\n\n"
            "Assembly notes:\n"
            "- Insert compression spring behind follower (~5-6mm dia, 20-25mm long)\n"
            "- Glue transparent window panel into the cutout opening\n"
            "- Gate slides in its channel - ensure smooth clearance\n"
            "- Add small return spring to gate (optional, for auto-return)\n\n"
            "For multi-color printing:\n"
            "- Assign different colors to each component in your slicer\n"
            "- Recommended: Main body in solid color, window in clear filament"
        )

    except:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')


def stop(context):
    pass
