import os
import shutil

import bpy
from bpy.props import StringProperty

from .app_helpers import *


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

        root_path = os.path.join(filepath, ROOT)
        if os.path.exists(root_path):
            shutil.rmtree(root_path)

            context.window_manager.cps.isInitialized = False

            self.report({"INFO"}, "Checkpoints data deleted successfully!")
        else:
            self.report(
                {"WARNING"}, "Checkpoints not found in the current directory!")

        return {"FINISHED"}


class ActivateLicense(bpy.types.Operator):
    bl_idname = "cps.activate_license"
    bl_label = "Activate License"

    license_key: StringProperty(
        name="license_key",
    )

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=430)

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "license_key", text="Enter key")

    def execute(self, context):
        if not self.license_key:
            return {'CANCELLED'}

        error = check_license_key(self.license_key)

        if error:
            self.report(
                {"ERROR"}, error)
            return {"CANCELLED"}
        else:
            CHECKPOINT_KEY = True
            self.license_key = ""
            self.report(
                {"INFO"}, "License activated successfully!")

        return {"FINISHED"}


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shouldDisplayPostSaveDialog: bpy.props.BoolProperty(
        name="Post Save Dialog",
        description="After saving, display dialog box to add checkpoint",
        default=True,
    )

    shouldAutoStart: bpy.props.BoolProperty(
        name="Auto start version control",
        description="Uppon saving a new project, start version control automatically",
        default=False,
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

        if not CHECKPOINT_KEY:
            row = layout.row()
            row.operator(ActivateLicense.bl_idname)


"""ORDER MATTERS"""
classes = (ResetProject, ActivateLicense, AddonPreferences)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
