import os
import shutil
import bpy

from .. import config


class LoadCheckpoint(bpy.types.Operator):
    """Load selected checkpoint"""

    bl_label = __doc__
    bl_idname = "checkpoint.load_checkpoint"

    id: bpy.props.StringProperty(name="", description="ID of checkpoint to load")

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        activeCheckpointId = context.window_manager.checkpoint.activeCheckpointId

        if activeCheckpointId == self.id:
            return {"CANCELLED"}

        load_checkpoint(filepath, self.id)

        bpy.ops.wm.revert_mainfile()

        return {"FINISHED"}


def load_checkpoint(filepath, checkpoint_id):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    config.set_state(filepath, "active_checkpoint", checkpoint_id)

    checkpoint_path = os.path.join(
        _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], checkpoint_id
    )
    filename = state["filename"]
    destination_file = os.path.join(filepath, filename)

    shutil.copy(checkpoint_path, destination_file)
