import os
import shutil
import bpy

from .. import config


class ExportCheckpoint(bpy.types.Operator):
    """Export checkpoint"""

    bl_label = __doc__
    bl_idname = "checkpoint.export_checkpoint"

    id: bpy.props.StringProperty(name="", description="ID of checkpoint to export")

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        checkpoint_context = context.window_manager.checkpoint
        checkpointDescription = checkpoint_context.checkpoints[
            checkpoint_context.selectedListIndex
        ]["description"]

        export_checkpoint(filepath, self.id, checkpointDescription)

        # Clean up
        self.id = ""
        self.report({"INFO"}, "Checkpoint exported successfully!")
        return {"FINISHED"}


def export_checkpoint(filepath, checkpoint_id, description):
    _paths = config.get_paths(filepath)

    # get checkpoint wth the provided id
    checkpoint = os.path.join(
        _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], checkpoint_id
    )

    # create folder "exported"
    export_path = os.path.join(filepath, "exported")
    if not os.path.exists(export_path):
        os.mkdir(export_path)

    export_name = os.path.join(export_path, f"{description}.blend")
    shutil.copy(checkpoint, export_name)
