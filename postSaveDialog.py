import sys
import importlib

import bpy

# Local imports implemented to support Blender refreshes
modulesNames = ("helpers", "operators")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


NEW_PROJECT_ICON = 'NEWFOLDER'


class PostSaveDialog(bpy.types.Operator):
    """Dialog to quickly add checkpoints"""

    bl_label = "Save"
    bl_idname = "cps.post_save_dialog"

    def invoke(self, context, event):
        wm = context.window_manager
        filepath = bpy.path.abspath("//")

        try:
            helpers.get_state(filepath)
            return wm.invoke_props_dialog(self, width=400)
        except FileNotFoundError:
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(context.window_manager.cps, "checkpointDescription")

        layout.separator()

    def execute(self, context):
        description = context.window_manager.cps.checkpointDescription

        if not description:
            self.report({'ERROR_INVALID_INPUT'},
                        "Description cannot be empty.")
            return {'CANCELLED'}

        operatorName = operators.AddCheckpoint.bl_idname.split(".")

        add_checkpoint_operator = getattr(
            getattr(bpy.ops, operatorName[0]), operatorName[1])

        add_checkpoint_operator('INVOKE_DEFAULT', description=description)

        self.report({"INFO"}, "Successfully saved!")

        return {'FINISHED'}


def register():
    bpy.utils.register_class(PostSaveDialog)


def unregister():
    bpy.utils.unregister_class(PostSaveDialog)
