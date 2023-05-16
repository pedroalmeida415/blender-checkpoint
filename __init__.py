import importlib
import sys
import os

bl_info = {
    "name": "Checkpoint",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (3, 4, 1),
    "category": "Development",
    "version": (1, 0, 0),
    "location": "Properties > Active Tool and Workspace settings > Checkpoints Panel",
}


# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = ("operators", "postSaveDialog",
                "checkpointsPanel", "appHandlers", "preferences", "helpers")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        globals()[module] = importlib.import_module(f"{__name__}.{module}")

if helpers._CHECKPOINT_KEY:
    with open(helpers._CHECKPOINT_KEY_FILE_PATH, "r") as f:
        # Create a dictionary from the lines in the file
        env_vars = dict(line.strip().split("=") for line in f)
        license_key = env_vars["LICENSE_KEY"]

    error = helpers.check_license_key(license_key)

    if error:
        os.remove(helpers._CHECKPOINT_KEY_FILE_PATH)
        helpers._CHECKPOINT_KEY = False


def register():
    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    for module in modulesNames:
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
