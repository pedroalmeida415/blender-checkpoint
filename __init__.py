import importlib
import sys
bl_info = {
    "name": "Checkpoint",
    "authon": "Nameless",
    "description": "Backup and version control for Blender - Supercharged",
    "blender": (3, 4, 1),
    "category": "Development",
    "version": (1, 0, 0),
    "location": "Properties > Scene > Checkpoints Panel",
}

# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = ("operators", "postSaveDialog",
                "checkpointsPanel", "appHandlers", "preferences")
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
