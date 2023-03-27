import os
import sys
import importlib

import bpy
from bpy.app import handlers
from bpy.app.handlers import persistent

# Local imports implemented to support Blender refreshes
modulesNames = ("reports", "subscriptions")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


def regenFile(_):
    # Load new blend file
    bpy.ops.wm.read_homefile()
    # Regenerate blend file
    window = bpy.context.window_manager.windows[0]
    area = window.screen.areas[0]
    with bpy.context.temp_override(window=window, area=area):
        # Current area type
        currentType = area.type

        # Change area type to INFO and delete all content
        area.type = 'VIEW_3D'

        # Restore area type
        area.type = currentType


@persistent
def loadPreferencesHandler(_):
    print("Changing Preference Defaults!")

    prefs = bpy.context.preferences
    prefs.use_preferences_save = False


@persistent
def savePostHandler(_):
    bpy.ops.object.post_save_commit('INVOKE_DEFAULT')


@persistent
def loadPostHandler(_):
    bpy.ops.wm.splash('INVOKE_DEFAULT')


def register():
    print("Registering to Change Defaults")
    handlers.load_post.append(loadPostHandler)
    handlers.save_post.append(savePostHandler)
    handlers.load_factory_preferences_post.append(loadPreferencesHandler)


def unregister():
    print("Unregistering to Change Defaults")
    handlers.load_post.remove(loadPostHandler)
    handlers.save_post.remove(savePostHandler)
    handlers.load_factory_preferences_post.remove(loadPreferencesHandler)
