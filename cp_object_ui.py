import bpy
from bpy.types import Panel

from .cp_object_ops import *


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
        return bool(context.selected_objects)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(AddObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(LoadObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(DeleteObjectCheckpoint.bl_idname)


"""ORDER MATTERS"""
classes = (ObjectCheckpointsPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
