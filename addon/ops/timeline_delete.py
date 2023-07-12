import os
import bpy

from .. import config, utils
from . import checkpoint_delete


class DeleteTimeline(bpy.types.Operator):
    """Delete current timeline"""

    bl_label = __doc__
    bl_idname = "checkpoint.delete_timeline"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        state = config.get_state(filepath)
        checkpoint_context = context.window_manager.checkpoint

        # get current timeline's checkpoints that will be deleted
        tl_checkpoints_count = len(checkpoint_context.checkpoints)

        to_delete_tl = state["current_timeline"]

        # delete previous timeline
        delete_timeline(filepath, to_delete_tl, tl_checkpoints_count)

        # switch to original timeline
        utils.switch_timeline(filepath)

        bpy.ops.wm.revert_mainfile()

        return {"FINISHED"}


def delete_timeline(filepath, name, checkpoints_count):
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    # Set the iteration number to 1
    i = 0
    # Loop through the collection while the iteration number is less than or equal to the length of the collection
    while i < checkpoints_count:
        checkpoint_delete.delete_checkpoint(filepath, 0)
        # Increment the iteration number
        i += 1

    delete_tl_path = os.path.join(_timelines, name)
    os.remove(delete_tl_path)
