import importlib
import sys
import os

# Updater ops import, all setup in this file.
from . import addon_updater_ops


bl_info = {
    "name": "Checkpoint - Supercharged",
    "author": "Flowerboy Studio",
    "description": "Backup and version control for Blender",
    "blender": (2, 80, 0),
    "category": "Development",
    "version": (0, 1, 0),
    "location": "Properties > Active Tool and Workspace settings > Checkpoints Panel",
}


# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = ("config", "project_helpers", "object_helpers",
                "project_ops", "object_ops",
                "project_ui", "object_ui",
                "app_preferences", "app_handlers")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        globals()[module] = importlib.import_module(f"{__name__}.{module}")


def register():
    # Addon updater code and configurations.
    # In case of a broken version, try to register the updater first so that
    # users can revert back to a working version.
    addon_updater_ops.register(bl_info)

    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    addon_updater_ops.unregister()

    for module in reversed(modulesNames):
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
