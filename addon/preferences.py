import os
import shutil

import bpy

from . import config, utils
from .. import addon_updater_ops


class ResetProject(bpy.types.Operator):
    """Deletes the addon's data from the current project"""

    bl_idname = "checkpoint.reset_project"
    bl_label = "Reset checkpoints"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=430)

    def draw(self, context):
        layout = self.layout

        layout.separator()

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="ARE YOU SURE?")

        layout.separator()

        row = layout.row()
        row.label(
            text="This will delete all the addon's data from the current project",
            icon="TRASH",
        )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        _root_path = config.get_paths(filepath)[config.PATHS_KEYS.ROOT_FOLDER]

        if os.path.exists(_root_path):
            shutil.rmtree(_root_path)

            context.window_manager.checkpoint.isInitialized = False

            self.report({"INFO"}, "Checkpoints data deleted successfully!")
        else:
            self.report({"WARNING"}, "Checkpoints not found in the current directory!")

        return {"FINISHED"}


@addon_updater_ops.make_annotations
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = utils.addon_name

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

    # Addon updater preferences.
    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )

    updater_interval_months = bpy.props.IntProperty(
        name="Months",
        description="Number of months between checking for updates",
        default=0,
        min=0,
    )

    updater_interval_days = bpy.props.IntProperty(
        name="Days",
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31,
    )

    updater_interval_hours = bpy.props.IntProperty(
        name="Hours",
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23,
    )

    updater_interval_minutes = bpy.props.IntProperty(
        name="Minutes",
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59,
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

        addon_updater_ops.update_settings_ui(self, context)


"""ORDER MATTERS"""
classes = (ResetProject, AddonPreferences)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
