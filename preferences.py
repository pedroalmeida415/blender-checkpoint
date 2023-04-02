import os
import sys
import shutil
import importlib
from stat import S_IWRITE

import bpy

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers",)
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


class RemoveVersionControlOperator(bpy.types.Operator):
    """Remove version control from the current directory"""

    bl_idname = "git.remove_version_control"
    bl_label = "Remove Version Control from current project"

    def remove_readonly(self, func, path, excinfo):
        os.chmod(path, S_IWRITE)
        func(path)

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
            text='This will delete all backups and remove versioning from the current directory.', icon="TRASH")

    def execute(self, context):
        current_dir = bpy.path.abspath("//")
        git_folder_path = os.path.join(current_dir, ".git")
        if os.path.exists(git_folder_path):
            shutil.rmtree(git_folder_path, onerror=self.remove_readonly)

            context.window_manager.git.isRepoInitialized = False

            self.report({"INFO"}, "Version Control removed successfully!")
        else:
            self.report(
                {"WARNING"}, "Version Control not found in the current directory!")

        return {"FINISHED"}


class MyAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    shouldDisplayCommitDialog: bpy.props.BoolProperty(
        name="Show Commit Dialog",
        description="Should display commit dialog after saving project?",
        default=True,
    )

    shouldAutoStartVersionControl: bpy.props.BoolProperty(
        name="Automatically start version control on new projects",
        description="Should start version control right after saving new project?",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "shouldDisplayCommitDialog")

        row = layout.row()
        row.prop(self, "shouldAutoStartVersionControl")

        layout.separator()

        row = layout.row()
        row.operator(RemoveVersionControlOperator.bl_idname)


classes = (RemoveVersionControlOperator, MyAddonPreferences)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
