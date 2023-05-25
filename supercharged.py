import sys
import importlib

import bpy
from bpy.types import Panel, Operator

modulesNames = ("helpers",)
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        parent = ".".join(__name__.split(".")[:-1])
        globals()[module] = importlib.import_module(f"{parent}.{module}")


class AddObjectCheckpoint(Operator):
    """Add"""

    bl_label = __doc__
    bl_idname = "cps.add_object_checkpoint"

    def execute(self, context):

        return {'FINISHED'}


class LoadObjectCheckpoint(Operator):
    """Load"""

    bl_label = __doc__
    bl_idname = "cps.load_object_checkpoint"

    def execute(self, context):

        return {'FINISHED'}


class DeleteObjectCheckpoint(Operator):
    """Delete"""

    bl_label = __doc__
    bl_idname = "cps.delete_object_checkpoint"

    def execute(self, context):

        return {'FINISHED'}


class ObjectCheckpointsPanelMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Checkpoints'
    bl_context = "objectmode"


class ObjectCheckpointsPanel(ObjectCheckpointsPanelMixin, Panel):
    bl_idname = "CPS_PT_object_checkpoints"
    bl_label = "Object"

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(AddObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(LoadObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(DeleteObjectCheckpoint.bl_idname)


"""ORDER MATTERS"""
classes = (AddObjectCheckpoint, LoadObjectCheckpoint,
           DeleteObjectCheckpoint, ObjectCheckpointsPanel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
