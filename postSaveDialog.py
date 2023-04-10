import sys
import importlib

import bpy
from pygit2._pygit2 import GitError

# Local imports implemented to support Blender refreshes
modulesNames = ("gitHelpers", "sourceControl")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


NEW_PROJECT_ICON = 'NEWFOLDER'


class GitPostSaveDialog(bpy.types.Operator):
    """Dialog to commit changes after saving file"""

    bl_label = "Commit changes"
    bl_idname = "git.post_save_dialog"

    def invoke(self, context, event):
        wm = context.window_manager
        filepath = bpy.path.abspath("//")

        try:
            gitHelpers.getRepo(filepath)
            return wm.invoke_props_dialog(self, width=400)
        except GitError:
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(context.window_manager.git, "commitMessage")

        layout.separator()

    def execute(self, context):
        message = context.window_manager.git.commitMessage

        if not message:
            self.report({'ERROR_INVALID_INPUT'},
                        "Description cannot be empty.")
            return {'CANCELLED'}

        operatorName = sourceControl.GitCommit.bl_idname.split(".")

        commitOperator = getattr(
            getattr(bpy.ops, operatorName[0]), operatorName[1])

        commitOperator('INVOKE_DEFAULT', message=message)

        self.report({"INFO"}, "Successfully saved commit changes!")

        return {'FINISHED'}


def register():
    bpy.utils.register_class(GitPostSaveDialog)


def unregister():
    bpy.utils.unregister_class(GitPostSaveDialog)
