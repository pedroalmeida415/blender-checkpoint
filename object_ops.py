import bpy
from bpy.types import Operator


class AddObjectCheckpoint(Operator):
    """Add"""

    bl_label = __doc__
    bl_idname = "cps.add_object_checkpoint"

    def execute(self, context):
        filepath = bpy.path.abspath("//")

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


classes = (AddObjectCheckpoint, LoadObjectCheckpoint, DeleteObjectCheckpoint)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
