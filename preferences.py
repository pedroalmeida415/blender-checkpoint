import os
import sys
import shutil
import importlib

import bpy

# Local imports implemented to support Blender refreshes
modulesNames = ("helpers",)
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


def get_user_preferences(context=None):
    """Intermediate method for pre and post blender 2.8 grabbing preferences"""
    if not context:
        context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)
    if prefs:
        return prefs.preferences
    # To make the addon stable and non-exception prone, return None
    # raise Exception("Could not fetch user preferences")
    return None


class ResetProject(bpy.types.Operator):
    """Deletes the addon's data from the current project"""

    bl_idname = "cps.reset_project"
    bl_label = "Reset checkpoints"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=430)

    def draw(self, context):
        layout = self.layout

        layout.separator()

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="ARE YOU SURE?")

        layout.separator()

        row = layout.row()
        row.label(
            text="This will delete all the addon's data from the current project", icon="TRASH")

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        root_path = os.path.join(filepath, helpers.ROOT)
        if os.path.exists(root_path):
            shutil.rmtree(root_path)

            context.window_manager.cps.isInitialized = False

            self.report({"INFO"}, "Checkpoints removed successfully!")
        else:
            self.report(
                {"WARNING"}, "Checkpoints not found in the current directory!")

        return {"FINISHED"}


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shouldDisplayPostSaveDialog: bpy.props.BoolProperty(
        name="Post Save Dialog",
        description="Should display dialog after saving project?",
        default=True,
    )

    shouldAutoStart: bpy.props.BoolProperty(
        name="Auto start",
        description="Should start right after saving new project?",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "shouldDisplayPostSaveDialog")

        row = layout.row()
        row.prop(self, "shouldAutoStart")

        layout.separator()

        row = layout.row()
        row.operator(ResetProject.bl_idname)


classes = (ResetProject, AddonPreferences)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
