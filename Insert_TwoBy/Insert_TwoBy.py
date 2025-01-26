import adsk.core, adsk.fusion, adsk.cam, traceback

def create_lumber_command(ui):
    try:
        # Check if the command definition already exists
        cmdDef = ui.commandDefinitions.itemById('lumberDimensionSelector')
        if cmdDef:
            cmdDef.deleteMe()  # Delete the existing command definition if it exists
        
        # Create a new command definition
        cmdDef = ui.commandDefinitions.addButtonDefinition('lumberDimensionSelector', 'Lumber Dimension Selector', 'Select dimensions for lumber placement')
        
        # Create and add the event handler
        onCreate = CommandCreatedEventHandler()
        cmdDef.commandCreated.add(onCreate)
        handlers.append(onCreate)  # Keep the handler referenced beyond this function
        
        # Execute the command
        cmdDef.execute()
        
        # Prevent automatic termination of the script
        adsk.autoTerminate(False)
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command
        inputs = cmd.commandInputs

        # Dimension Type as radio buttons
        dimensionTypeInput = inputs.addRadioButtonGroupCommandInput('dimensionType', 'Dimension Type')
        dimensionTypeInput.listItems.add('Nominal', False)
        dimensionTypeInput.listItems.add('Actual', True)
        
        # Lumber Size as radio buttons
        lumberSizeInput = inputs.addRadioButtonGroupCommandInput('lumberSize', 'Lumber Size')
        sizes = ['2x4', '2x6', '2x8', '2x10', '2x12']
        for size in sizes:
            is_default = (size == '2x4')
            lumberSizeInput.listItems.add(size, is_default)
        
        # Value input for Length, correctly setting default value
        lengthInput = inputs.addValueInput('length', 'Length (feet)', 'ft', adsk.core.ValueInput.createByReal(8))

        # Selection input for axis and starting point
        inputs.addSelectionInput('axisSelection', 'Select Axis', 'Select an axis')
        inputs.addSelectionInput('pointSelection', 'Starting Point', 'Select a starting point')
        
        # Ensure the selections are limited to edges and sketch points
        axisInput = inputs.itemById('axisSelection')
        axisInput.addSelectionFilter('LinearEdges')  # Allows only linear edges to be selected
        
        pointInput = inputs.itemById('pointSelection')
        pointInput.addSelectionFilter('SketchPoints')  # Allows only sketch points to be selected

handlers = []

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    create_lumber_command(ui)

def stop(context):
    adsk.terminate()
