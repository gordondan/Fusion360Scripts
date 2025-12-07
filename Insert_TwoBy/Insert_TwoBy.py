import adsk.core, adsk.fusion, adsk.cam, traceback, os

# Global list to keep event handlers in scope.
handlers = []

class LumberSelector:
    def __init__(self):
        print("Initializing LumberSelector...")
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.handlers = []
    
    def create_command_definition(self):
        print("Creating command definition...")
        # Use your script directory to locate the resources folder.
        # (For now, we're passing an empty string as the icon so we don't run into icon issues.)
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        iconPath = os.path.join(scriptDir, 'resources')
        print(f"Checking icon path: {iconPath}")
        if not os.path.exists(iconPath):
            print(f"Resource folder not found at: {iconPath}")
            # For testing, we ignore the icons by passing an empty string.
            iconPath = ""
    
        try:
            cmdDefs = self.ui.commandDefinitions
            # Delete any existing definition.
            cmdDef = cmdDefs.itemById('lumberDimensionSelector')
            if cmdDef:
                cmdDef.deleteMe()
    
            cmdDef = cmdDefs.addButtonDefinition(
                'lumberDimensionSelector',
                'Lumber Dialog',
                'Open the lumber dialog',
                iconPath  # Using empty icon path if resources not set up.
            )
            print("Command definition created successfully.")
            return cmdDef
        except Exception:
            self.ui.messageBox('Error in create_command_definition:\n{}'.format(traceback.format_exc()))
    
    def add_command_inputs(self, command):
        print("Adding command inputs...")
        inputs = command.commandInputs
        
        # Radio button for Dimension Type
        dimInput = inputs.addRadioButtonGroupCommandInput('dimensionType', 'Dimension Type', '')
        dimInput.listItems.add('Nominal', True)
        dimInput.listItems.add('Actual', False)
        
        # Radio button for Lumber Size
        sizeInput = inputs.addRadioButtonGroupCommandInput('lumberSize', 'Lumber Size', '')
        for s in ['2x4', '2x6', '2x8', '2x10', '2x12']:
            sizeInput.listItems.add(s, s == '2x4')
        import adsk.core, adsk.fusion, adsk.cam, traceback, os

handlers = []  # Global list for event handlers

class LumberSelector:
    def __init__(self):
        print("Initializing LumberSelector...")
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        self.handlers = []
    
    def create_command_definition(self):
        print("Creating command definition...")
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        iconPath = os.path.join(scriptDir, 'resources')
        print(f"Checking icon path: {iconPath}")
        if not os.path.exists(iconPath):
            raise Exception(f"Resource folder not found at: {iconPath}")
    
        try:
            cmdDefs = self.ui.commandDefinitions
            cmdDef = cmdDefs.itemById('lumberDimensionSelector')
            if cmdDef:
                print("Deleting existing command definition...")
                cmdDef.deleteMe()
    
            # IMPORTANT: The resource folder MUST contain valid icon files,
            # e.g. 'SmallIcon.png' (and optionally 'LargeIcon.png')
            cmdDef = cmdDefs.addButtonDefinition(
                'lumberDimensionSelector',
                'Lumber Dialog',
                'Open the lumber dialog',
                iconPath  # Use the folder with valid icon images
            )
            print("Command definition created successfully.")
            return cmdDef
        except Exception:
            self.ui.messageBox('Error in create_command_definition:\n{}'.format(traceback.format_exc()))
    
    def add_command_inputs(self, command):
        print("Adding command inputs...")
        inputs = command.commandInputs
        
        # Add a radio button group for dimension type.
        dimInput = inputs.addRadioButtonGroupCommandInput('dimensionType', 'Dimension Type', '')
        dimInput.listItems.add('Nominal', True)
        dimInput.listItems.add('Actual', False)
        
        # Add a radio button group for lumber size.
        sizeInput = inputs.addRadioButtonGroupCommandInput('lumberSize', 'Lumber Size', '')
        for s in ['2x4', '2x6', '2x8', '2x10', '2x12']:
            sizeInput.listItems.add(s, s == '2x4')
        
        # Add a value input for length.
        inputs.addValueInput('length', 'Length (feet)', 'ft', adsk.core.ValueInput.createByReal(96))
        
        # Add a selection input for an axis.
        axisInput = inputs.addSelectionInput('axisSelection', 'Select Axis', 'Select an axis')
        axisInput.addSelectionFilter('LinearEdges')
        
        # Add a selection input for a starting point.
        pointInput = inputs.addSelectionInput('pointSelection', 'Starting Point', 'Select a starting point')
        pointInput.setSelectionLimits(1)
        pointInput.addSelectionFilter('SketchPoints')
        pointInput.addSelectionFilter('Vertices')
        print("Command inputs added successfully.")
    
    def command_created(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            command = eventArgs.command
            self.add_command_inputs(command)
    
            onExecute = CommandExecuteHandler(self)
            command.execute.add(onExecute)
            self.handlers.append(onExecute)
            print("Command creation complete.")
        except Exception:
            self.ui.messageBox('Error in command_created:\n{}'.format(traceback.format_exc()))
    
    def start(self):
        print("Starting LumberSelector...")
        try:
            cmdDef = self.create_command_definition()
            onCommandCreated = CommandCreatedEventHandler(self)
            cmdDef.commandCreated.add(onCommandCreated)
            self.handlers.append(onCommandCreated)
    
            panel = self.ui.allToolbarPanels.itemById('SolidCreatePanel')
            panel.controls.addCommand(cmdDef)
            print("LumberSelector started successfully.")
        except Exception:
            self.ui.messageBox('Error in start():\n{}'.format(traceback.format_exc()))
    
    def stop(self):
        print("Stopping LumberSelector...")
        try:
            panel = self.ui.allToolbarPanels.itemById('SolidCreatePanel')
            button = panel.controls.itemById('lumberDimensionSelector')
            if button:
                button.deleteMe()
    
            cmdDef = self.ui.commandDefinitions.itemById('lumberDimensionSelector')
            if cmdDef:
                cmdDef.deleteMe()
            print("LumberSelector stopped.")
        except Exception:
            self.ui.messageBox('Error in stop():\n{}'.format(traceback.format_exc()))

class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, lumberSelector):
        super().__init__()
        self.lumberSelector = lumberSelector
    
    def notify(self, args):
        print("Command created event triggered.")
        self.lumberSelector.command_created(args)

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, lumberSelector):
        super().__init__()
        self.lumberSelector = lumberSelector
    
    def notify(self, args):
        print("Command execution started.")
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs
            dimensionType = inputs.itemById('dimensionType').selectedItem.name
            lumberSize = inputs.itemById('lumberSize').selectedItem.name
            lengthValue = inputs.itemById('length').value
            
            msg = f"Selected: {dimensionType} {lumberSize} at {lengthValue} ft"
            print(msg)
            self.lumberSelector.ui.messageBox(msg)
        except Exception:
            self.lumberSelector.ui.messageBox('Error in command execution:\n{}'.format(traceback.format_exc()))

def run(context):
    print("Running LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector = LumberSelector()
        lumber_selector.start()
        print("LumberSelector is now running.")
    except Exception:
        adsk.core.Application.get().userInterface.messageBox('Error in run():\n{}'.format(traceback.format_exc()))

def stop(context):
    print("Stopping LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector.stop()
        print("LumberSelector stopped.")
    except Exception:
        adsk.core.Application.get().userInterface.messageBox('Error in stop():\n{}'.format(traceback.format_exc()))

        # Value input for Length
        inputs.addValueInput('length', 'Length (feet)', 'ft', adsk.core.ValueInput.createByReal(96))
        
        # Selection input for Axis (for example purposes)
        axisInput = inputs.addSelectionInput('axisSelection', 'Select Axis', 'Select an axis')
        axisInput.addSelectionFilter('LinearEdges')
        
        # Selection input for Starting Point
        pointInput = inputs.addSelectionInput('pointSelection', 'Starting Point', 'Select a starting point')
        pointInput.setSelectionLimits(1)
        pointInput.addSelectionFilter('SketchPoints')
        pointInput.addSelectionFilter('Vertices')
        print("Command inputs added successfully.")
    
    def command_created(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            command = eventArgs.command
            self.add_command_inputs(command)
    
            onExecute = CommandExecuteHandler(self)
            command.execute.add(onExecute)
            self.handlers.append(onExecute)
            print("Command creation complete.")
        except Exception:
            self.ui.messageBox('Error in command_created:\n{}'.format(traceback.format_exc()))
    
    def start(self):
        print("Starting LumberSelector...")
        try:
            cmdDef = self.create_command_definition()
            onCommandCreated = CommandCreatedEventHandler(self)
            cmdDef.commandCreated.add(onCommandCreated)
            self.handlers.append(onCommandCreated)
    
            panel = self.ui.allToolbarPanels.itemById('SolidCreatePanel')
            panel.controls.addCommand(cmdDef)
            print("LumberSelector started successfully.")
        except Exception:
            self.ui.messageBox('Error in start():\n{}'.format(traceback.format_exc()))
    
    def stop(self):
        print("Stopping LumberSelector...")
        try:
            panel = self.ui.allToolbarPanels.itemById('SolidCreatePanel')
            button = panel.controls.itemById('lumberDimensionSelector')
            if button:
                button.deleteMe()
    
            cmdDef = self.ui.commandDefinitions.itemById('lumberDimensionSelector')
            if cmdDef:
                cmdDef.deleteMe()
            print("LumberSelector stopped.")
        except Exception:
            self.ui.messageBox('Error in stop():\n{}'.format(traceback.format_exc()))

# Event handler for command creation.
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, lumberSelector):
        super().__init__()
        self.lumberSelector = lumberSelector
    
    def notify(self, args):
        print("Command created event triggered.")
        self.lumberSelector.command_created(args)

# Event handler for command execution.
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, lumberSelector):
        super().__init__()
        self.lumberSelector = lumberSelector
    
    def notify(self, args):
        print("Command execution started.")
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs
            # Get the user selections.
            dimensionType = inputs.itemById('dimensionType').selectedItem.name
            lumberSize = inputs.itemById('lumberSize').selectedItem.name
            lengthValue = inputs.itemById('length').value
            
            msg = f"Selected: {dimensionType} {lumberSize} at {lengthValue} ft"
            print(msg)
            self.lumberSelector.ui.messageBox(msg)
        except Exception:
            self.lumberSelector.ui.messageBox('Error in command execution:\n{}'.format(traceback.format_exc()))

def run(context):
    print("Running LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector = LumberSelector()
        lumber_selector.start()
        print("LumberSelector is now running.")
    except Exception:
        adsk.core.Application.get().userInterface.messageBox('Error in run():\n{}'.format(traceback.format_exc()))

def stop(context):
    print("Stopping LumberSelector add-in...")
    try:
        global lumber_selector
        lumber_selector.stop()
        print("LumberSelector stopped.")
    except Exception:
        adsk.core.Application.get().userInterface.messageBox('Error in stop():\n{}'.format(traceback.format_exc()))
