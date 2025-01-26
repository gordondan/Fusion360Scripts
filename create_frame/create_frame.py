import adsk.core, adsk.fusion, adsk.cam, traceback
import os.path

for _ in range(50):  # Adjust the range as needed to "clear" the visible portion
    print("\n")

print(f"Da Start")
# Construct the absolute path to the FramedPlywood module.
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"[DEBUG] Script directory: {script_dir}")

framed_plywood_module_path = os.path.join(script_dir, "framed_plywood.py")
print(f"[DEBUG] FramedPlywood module path: {framed_plywood_module_path}")

# Import FramedPlywood module using its absolute path.
import importlib.util
framed_plywood_spec = importlib.util.spec_from_file_location("framed_plywood", framed_plywood_module_path)
framed_plywood = importlib.util.module_from_spec(framed_plywood_spec)
framed_plywood_spec.loader.exec_module(framed_plywood)
print("[DEBUG] FramedPlywood module imported successfully.")

def run(context):
    print("[DEBUG] Entered run(context).")
    ui = None
    try:
        # Get the application and user interface objects
        app = adsk.core.Application.get()
        ui = app.userInterface
        print("[DEBUG] Application and UI initialized.")

        # Call the function to create the framed plywood assembly
        print("[DEBUG] Calling framed_plywood.create_framed_plywood().")
        framed_plywood.create_framed_plywood()
        print("[DEBUG] framed_plywood.create_framed_plywood() completed.")

    except Exception as e:
        print("[DEBUG] Exception occurred in run(context):")
        print(traceback.format_exc())
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
