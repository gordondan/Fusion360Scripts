import adsk.core, adsk.fusion, adsk.cam, traceback, os, importlib, sys

# Global list to keep all event handlers in scope.
# This is necessary because the event handlers are not referenced anywhere else
# and would be garbage collected, causing the script to fail.
handlers = []

# Constants for lumber dimensions
NOMINAL_DIMENSIONS = {
    "2x4": (3.5, 1.5),
    "2x6": (5.5, 1.5),
    "2x8": (7.25, 1.5),
    "2x10": (9.25, 1.5),
    "2x12": (11.25, 1.5),
}
ACTUAL_DIMENSIONS = {
    "2x4": (4.0, 2.0),
    "2x6": (6.0, 2.0),
    "2x8": (8.0, 2.0),
    "2x10": (10.0, 2.0),
    "2x12": (12.0, 2.0),
}

class LumberSelector:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.handlers = []

    def create_command_definition(self):
        # Get the current directory of the script
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # Construct the path to the resources directory
        icon_path = os.path.join(script_dir, 'resources')

        # Check if the path exists
        if not os.path.exists(icon_path):
            raise Exception("Resource folder not found at: {}".format(icon_path))
        """Creates the command definition in Fusion 360 UI."""
        try:
            cmd_defs = self.ui.commandDefinitions
            cmd_def = cmd_defs.itemById("lumberDimensionSelector")
            if cmd_def:
                cmd_def.deleteMe()

            # Get the current directory of the script
            script_dir = os.path.dirname(os.path.realpath(__file__))

            # Construct the path to the resources directory
            icon_path = os.path.join(script_dir, 'resources')

            cmd_def = cmd_defs.addButtonDefinition(
                "lumberDimensionSelector",
                "Lumber Dimension Selector",
                "Select dimensions for lumber placement",
                icon_path  # Use the icon from the resources folder
            )
            return cmd_def
        except Exception:
            self.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

    def add_command_inputs(self, command):
        """Adds the necessary user inputs to the command."""
        inputs = command.commandInputs

        # Dimension Type as radio buttons
        dimension_type_input = inputs.addRadioButtonGroupCommandInput(
            "dimensionType", "Dimension Type"
        )
        dimension_type_input.listItems.add("Nominal", False)
        dimension_type_input.listItems.add("Actual", True)

        # Lumber Size as radio buttons
        lumber_size_input = inputs.addRadioButtonGroupCommandInput(
            "lumberSize", "Lumber Size"
        )
        sizes = ["2x4", "2x6", "2x8", "2x10", "2x12"]
        for size in sizes:
            is_default = size == "2x4"
            lumber_size_input.listItems.add(size, is_default)

        # Value input for Length
        length_input = inputs.addValueInput(
            "length", "Length (feet)", "ft", adsk.core.ValueInput.createByReal(96)
        )

        # Selection input for axis and starting point
        inputs.addSelectionInput("axisSelection", "Select Axis", "Select an axis")
        inputs.addSelectionInput(
            "pointSelection", "Starting Point", "Select a starting point"
        )

        # Ensure the selections are limited to edges and sketch points
        axis_input = inputs.itemById("axisSelection")
        axis_input.addSelectionFilter("LinearEdges")

        point_input = inputs.itemById("pointSelection")
        point_input.setSelectionLimits(1)
        point_input.addSelectionFilter("SketchPoints")
        point_input.addSelectionFilter("Vertices")

    def get_selected_axis(self, selection):
        """Retrieves the selected axis entity."""
        entity = selection.entity
        if entity.objectType == adsk.fusion.BRepEdge.classType():
            return entity
        return None

    def get_selected_point(self, selection):
        """Retrieves the selected point entity."""
        entity = selection.entity
        if entity.objectType == adsk.fusion.SketchPoint.classType():
            return entity.worldGeometry
        elif entity.objectType == adsk.fusion.BRepVertex.classType():
            return entity.geometry
        return None

    def get_lumber_dimensions(self, dimension_type, lumber_size):
        """Retrieves the dimensions based on type and size."""
        if dimension_type == "Actual":
            return ACTUAL_DIMENSIONS[lumber_size]
        else:
            return NOMINAL_DIMENSIONS[lumber_size]

    def draw_rectangular_prism(self, point, axis, length, width, height):
        """Draws a rectangular prism based on the given parameters."""
        app = adsk.core.Application.get()
        design = app.activeProduct
        rootComp = design.rootComponent

        # Create a new sketch on the same plane as the selected point
        sketches = rootComp.sketches
        sketch = sketches.add(rootComp.xYConstructionPlane) # Default to XY plane for simplicity
        
        # Project the point onto the sketch
        sketch_point = sketch.project(point).item(0)

        # Calculate the direction vectors for width and height
        # Assuming axis is along Z-direction for simplicity
        axis_vector = adsk.core.Vector3D.create(0, 0, 1)  # Placeholder, should ideally derive from axis
        width_vector = adsk.core.Vector3D.create(1, 0, 0)
        height_vector = adsk.core.Vector3D.create(0, 1, 0)


        # Calculate corners of the rectangle in the sketch plane
        point2 = adsk.core.Point3D.create(
            sketch_point.geometry.x + width_vector.x * width,
            sketch_point.geometry.y + width_vector.y * width,
            sketch_point.geometry.z + width_vector.z * width,
        )
        point3 = adsk.core.Point3D.create(
            point2.x + height_vector.x * height,
            point2.y + height_vector.y * height,
            point2.z + height_vector.z * height,
        )
        point4 = adsk.core.Point3D.create(
            sketch_point.geometry.x + height_vector.x * height,
            sketch_point.geometry.y + height_vector.y * height,
            sketch_point.geometry.z + height_vector.z * height,
        )

        # Draw the rectangle
        lines = sketch.sketchCurves.sketchLines
        lines.addByTwoPoints(sketch_point, sketch.project(point2).item(0))
        lines.addByTwoPoints(sketch.project(point2).item(0), sketch.project(point3).item(0))
        lines.addByTwoPoints(sketch.project(point3).item(0), sketch.project(point4).item(0))
        lines.addByTwoPoints(sketch.project(point4).item(0), sketch_point)

        # Create a profile from the rectangle
        profile = sketch.profiles.item(0)

        # Extrude the profile along the axis to the specified length
        extrudes = rootComp.features.extrudeFeatures
        ext_input = extrudes.createInput(
            profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        distance = adsk.core.ValueInput.createByReal(length)
        ext_input.setDistanceExtent(False, distance)
        extrudes.add(ext_input)


    def start(self):
        """Starts the add-in's command."""
        try:
            # Create the command definition
            cmd_def = self.create_command_definition()

            # Connect to the command created event
            on_command_created = CommandCreatedEventHandler(self)
            cmd_def.commandCreated.add(on_command_created)
            self.handlers.append(on_command_created)

            # Add the command to the toolbar
            panel = self.ui.allToolbarPanels.itemById("SolidCreatePanel")  # Example: Add to the "CREATE" panel
            button = panel.controls.addCommand(cmd_def)
            button.isPromotedByDefault = True
            button.isPromoted = True
        except Exception:
            if self.ui:
                self.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

    def stop(self):
        """Stops the add-in and cleans up the UI."""
        try:
            # Clean up the UI
            panel = self.ui.allToolbarPanels.itemById("SolidCreatePanel")
            button = panel.controls.itemById("lumberDimensionSelector")
            if button:
                button.deleteMe()

            # Clean up the command definition
            cmd_def = self.ui.commandDefinitions.itemById("lumberDimensionSelector")
            if cmd_def:
                cmd_def.deleteMe()
        except Exception:
            if self.ui:
                self.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    """Event handler for command execution."""
    def __init__(self, lumber_selector):
        super().__init__()
        self.lumber_selector = lumber_selector

    def notify(self, args):
        try:
            event_args = adsk.core.CommandEventArgs.cast(args)
            command = event_args.command
            inputs = command.commandInputs

            # Get user selections
            axis_selection = inputs.itemById("axisSelection").selection(0)
            point_selection = inputs.itemById("pointSelection").selection(0)
            dimension_type = inputs.itemById("dimensionType").selectedItem.name
            lumber_size = inputs.itemById("lumberSize").selectedItem.name
            length_feet = inputs.itemById("length").value

            # Validate selections
            axis = self.lumber_selector.get_selected_axis(axis_selection)
            point = self.lumber_selector.get_selected_point(point_selection)

            if not axis:
                self.lumber_selector.ui.messageBox("Please select a valid axis.")
                return

            if not point:
                self.lumber_selector.ui.messageBox("Please select a valid starting point.")
                return

            # Get lumber dimensions
            width_in, height_in = self.lumber_selector.get_lumber_dimensions(dimension_type, lumber_size)

            # Convert length to inches for consistency
            length_in = length_feet * 12

            # Draw the rectangular prism
            self.lumber_selector.draw_rectangular_prism(point, axis, length_in, width_in, height_in)

        except Exception:
            self.lumber_selector.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    """Event handler for command creation."""
    def __init__(self, lumber_selector):
        super().__init__()
        self.lumber_selector = lumber_selector

    def notify(self, args):
        try:
            event_args = adsk.core.CommandCreatedEventArgs.cast(args)
            command = event_args.command

            # Add inputs
            self.lumber_selector.add_command_inputs(command)

            # Connect execute event handler
            on_execute = CommandExecuteHandler(self.lumber_selector)
            command.execute.add(on_execute)
            self.lumber_selector.handlers.append(on_execute)

        except Exception:
            self.lumber_selector.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

# Command to reload the script
class ReloadCommand:
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.handlers = []

    def start(self):
        try:
            # Get the command definitions.
            cmd_defs = self.ui.commandDefinitions

            # Create a command definition.
            cmd_def = cmd_defs.itemById("reloadInsertTwoBy")
            if cmd_def:
                cmd_def.deleteMe()
            cmd_def = cmd_defs.addButtonDefinition(
                "reloadInsertTwoBy", "Reload Insert Two By", "Reloads the Insert Two By add-in"
            )

            # Connect to the command created event.
            on_command_created = ReloadCommandHandler(self)
            cmd_def.commandCreated.add(on_command_created)
            self.handlers.append(on_command_created)

            # Add the command to the toolbar.
            panel = self.ui.allToolbarPanels.itemById("SolidScriptsAddinsPanel")
            button = panel.controls.addCommand(cmd_def)
        except Exception:
            if self.ui:
                self.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

    def stop(self):
        try:
            # Clean up the UI
            panel = self.ui.allToolbarPanels.itemById("SolidScriptsAddinsPanel")
            button = panel.controls.itemById("reloadInsertTwoBy")
            if button:
                button.deleteMe()

            # Clean up the command definition
            cmd_def = self.ui.commandDefinitions.itemById("reloadInsertTwoBy")
            if cmd_def:
                cmd_def.deleteMe()
        except Exception:
            if self.ui:
                self.ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

class ReloadCommandHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, reload_command):
        super().__init__()
        self.reload_command = reload_command

    def notify(self, args):
        try:
            # Declare lumber_selector as global before using it
            global lumber_selector 

            # Stop the add-in.
            lumber_selector.stop()

            # Dynamically reload the module.
            importlib.reload(sys.modules[__name__])

            # Start the add-in.
            lumber_selector = LumberSelector()
            lumber_selector.start()

        except Exception:
            if self.reload_command.ui:
                self.reload_command.ui.messageBox(
                    "Failed:\n{}".format(traceback.format_exc())
                )

def run(context):
    """Entry point for the script."""
    try:
        global lumber_selector
        lumber_selector = LumberSelector()
        lumber_selector.start()
        global reload_command
        reload_command = ReloadCommand()
        reload_command.start()
        adsk.autoTerminate(False)

    except Exception:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

def stop(context):
    """Clean up the UI."""
    try:
        global lumber_selector
        lumber_selector.stop()
        global reload_command
        reload_command.stop()
    except Exception:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))