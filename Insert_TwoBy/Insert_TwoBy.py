import adsk.core, adsk.fusion, adsk.cam, traceback, os, importlib, sys

# Global list to keep all event handlers in scope.
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
        print("Initializing LumberSelector...")
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.handlers = []
    
    def create_command_definition(self):
        print("Creating command definition...")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(script_dir, 'resources')
    
        print(f"Checking icon path: {icon_path}")
        if not os.path.exists(icon_path):
            raise Exception(f"Resource folder not found at: {icon_path}")
    
        try:
            cmd_defs = self.ui.commandDefinitions
            cmd_def = cmd_defs.itemById("lumberDimensionSelector")
            if cmd_def:
                print("Deleting existing command definition...")
                cmd_def.deleteMe()
    
            # Temporarily use an empty icon path to test if the resource folder is the issue.
            cmd_def = cmd_defs.addButtonDefinition(
                "lumberDimensionSelector",
                "Lumber Dimension Selector",
                "Select dimensions for lumber placement",
                ""  # Pass an empty string for now
            )
            print("Command definition created successfully.")
            return cmd_def
        except Exception as e:
            print(f"Error in create_command_definition: {e}")
            self.ui.messageBox(f"Failed:\n{traceback.format_exc()}")
    
    def add_command_inputs(self, command):
        print("Adding command inputs...")
        inputs = command.commandInputs
    
        dimension_type_input = inputs.addRadioButtonGroupCommandInput(
            "dimensionType", "Dimension Type"
        )
        dimension_type_input.listItems.add("Nominal", False)
        dimension_type_input.listItems.add("Actual", True)
    
        lumber_size_input = inputs.addRadioButtonGroupCommandInput(
            "lumberSize", "Lumber Size"
        )
        sizes = ["2x4", "2x6", "2x8", "2x10", "2x12"]
        for size in sizes:
            is_default = size == "2x4"
            lumber_size_input.listItems.add(size, is_default)
    
        length_input = inputs.addValueInput(
            "length", "Length (feet)", "ft", adsk.core.ValueInput.createByReal(96)
        )
    
        inputs.addSelectionInput("axisSelection", "Select Axis", "Select an axis")
        inputs.addSelectionInput("pointSelection", "Starting Point", "Select a starting point")
    
        axis_input = inputs.itemById("axisSelection")
        axis_input.addSelectionFilter("LinearEdges")
    
        point_input = inputs.itemById("pointSelection")
        point_input.setSelectionLimits(1)
        point_input.addSelectionFilter("SketchPoints")
        point_input.addSelectionFilter("Vertices")
        print("Command inputs added successfully.")
    
    def start(self):
        print("Starting LumberSelector...")
        try:
            cmd_def = self.create_command_definition()
            on_command_created = CommandCreatedEventHandler(self)
            cmd_def.commandCreated.add(on_command_created)
            self.handlers.append(on_command_created)
    
            panel = self.ui.allToolbarPanels.itemById("SolidCreatePanel")
            button = panel.controls.addCommand(cmd_def)
            print("LumberSelector started successfully.")
        except Exception:
            print("Error in start()")
            self.ui.messageBox(f"Failed:\n{traceback.format_exc()}")
    
    def stop(self):
        print("Stopping LumberSelector...")
        try:
            panel = self.ui.allToolbarPanels.itemById("SolidCreatePanel")
            button = panel.controls.itemById("lumberDimensionSelector")
            if button:
                button.deleteMe()
    
            cmd_def = self.ui.commandDefinitions.itemById("lumberDimensionSelector")
            if cmd_def:
                cmd_def.deleteMe()
            print("LumberSelector stopped.")
        except Exception:
            print("Error in stop()")
            self.ui.messageBox(f"Failed:\n{traceback.format_exc()}")
    
    # Example helper methods that might be needed (you mentioned them in your earlier code)
    def get_selected_axis(self, selection):
        entity = selection.entity
        if entity.objectType == adsk.fusion.BRepEdge.classType():
            return entity
        return None
    
    def get_selected_point(self, selection):
        entity = selection.entity
        if entity.objectType == adsk.fusion.SketchPoint.classType():
            return entity.worldGeometry
        elif entity.objectType == adsk.fusion.BRepVertex.classType():
            return entity.geometry
        return None
    
    def get_lumber_dimensions(self, dimension_type, lumber_size):
        if dimension_type == "Actual":
            return ACTUAL_DIMENSIONS[lumber_size]
        else:
            return NOMINAL_DIMENSIONS[lumber_size]

# The remaining classes should remain defined at the module level.
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, lumber_selector):
        super().__init__()
        self.lumber_selector = lumber_selector
    
    def notify(self, args):
        print("Command created event triggered.")
        try:
            event_args = adsk.core.CommandCreatedEventArgs.cast(args)
            command = event_args.command
    
            self.lumber_selector.add_command_inputs(command)
    
            on_execute = CommandExecuteHandler(self.lumber_selector)
            command.execute.add(on_execute)
            self.lumber_selector.handlers.append(on_execute)
            print("Command creation complete.")
        except Exception:
            print("Error in CommandCreatedEventHandler")
            self.lumber_selector.ui.messageBox(f"Failed:\n{traceback.format_exc()}")

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, lumber_selector):
        super().__init__()
        self.lumber_selector = lumber_selector
    
    def notify(self, args):
        print("Command execution started.")
        try:
            event_args = adsk.core.CommandEventArgs.cast(args)
            command = event_args.command
            inputs = command.commandInputs
    
            axis_selection = inputs.itemById("axisSelection").selection(0)
            point_selection = inputs.itemById("pointSelection").selection(0)
            dimension_type = inputs.itemById("dimensionType").selectedItem.name
            lumber_size = inputs.itemById("lumberSize").selectedItem.name
            length_feet = inputs.itemById("length").value
    
            print(f"User selected: Axis={axis_selection}, Point={point_selection}, "
                  f"Type={dimension_type}, Size={lumber_size}, Length={length_feet}ft")
    
            axis = self.lumber_selector.get_selected_axis(axis_selection)
            point = self.lumber_selector.get_selected_point(point_selection)
    
            if not axis:
                print("Invalid axis selected.")
                self.lumber_selector.ui.messageBox("Please select a valid axis.")
                return
    
            if not point:
                print("Invalid point selected.")
                self.lumber_selector.ui.messageBox("Please select a valid starting point.")
                return
    
            width_in, height_in = self.lumber_selector.get_lumber_dimensions(dimension_type, lumber_size)
            length_in = length_feet * 12
            print(f"Calculated dimensions: Width={width_in}, Height={height_in}, Length={length_in}")
    
        except Exception:
            print("Error during command execution.")
            self.lumber_selector.ui.messageBox(f"Failed:\n{traceback.format_exc()}")

def run(context):
    print("Running LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector = LumberSelector()  # Instance name can be lower-case
        lumber_selector.start()
        print("LumberSelector is now running.")
    except Exception:
        print("Error in run()")
        adsk.core.Application.get().userInterface.messageBox(f"Failed:\n{traceback.format_exc()}")

def stop(context):
    print("Stopping LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector.stop()
        print("LumberSelector stopped.")
    except Exception:
        print("Error in stop()")
        adsk.core.Application.get().userInterface.messageBox(f"Failed:\n{traceback.format_exc()}")
