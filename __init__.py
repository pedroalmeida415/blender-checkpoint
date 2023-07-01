import importlib
import sys

bl_info = {
    "name": "Checkpoint - Full",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (2, 83, 20),
    "category": "Development",
    "version": (1, 0, 4),
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


def register():
    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    for module in modulesNames:
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
