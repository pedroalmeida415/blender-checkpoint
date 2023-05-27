import bpy
from bpy.types import Panel

from . import object_ops
from . import app_helpers


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
        if not app_helpers.HAS_CHECKPOINT_KEY:
            return False

        return context.window_manager.cps.isInitialized and bool(context.selected_objects)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(object_ops.AddObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(object_ops.LoadObjectCheckpoint.bl_idname)

        row = layout.row()
        row.operator(object_ops.DeleteObjectCheckpoint.bl_idname)


"""ORDER MATTERS"""
classes = (ObjectCheckpointsPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
