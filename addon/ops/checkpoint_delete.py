import json
import os
import bpy

from .. import config, utils


class DeleteCheckpoint(bpy.types.Operator):
    """Delete checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.delete_checkpoint"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=385)

    def draw(self, context):
        layout = self.layout

        layout.separator()

        row = layout.row()
        row.alignment = "CENTER"
        row.label(text="ARE YOU SURE?")

        layout.separator()

        row = layout.row()
        row.label(
            text="This will delete the selected checkpoint - (won't affect other timelines)",
            icon="UNLINKED",
        )

    def execute(self, context):
        cps_context = context.window_manager.cps

        filepath = bpy.path.abspath("//")

        delete_checkpoint(filepath, cps_context.selectedListIndex)

        # Clean up
        self.id = ""
        cps_context.selectedListIndex = 0

        self.report({"INFO"}, "Checkpoint deleted successfully!")
        return {"FINISHED"}


def delete_checkpoint(filepath, checkpoint_index):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    _checkpoints = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]

    current_timeline = os.path.join(_timelines, state["current_timeline"])
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        checkpoint_id = timeline_history[checkpoint_index]["id"]

        del timeline_history[checkpoint_index]

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()

    timelines = list(
        filter(lambda f: f != state["current_timeline"], os.listdir(_timelines))
    )

    shouldDelete = True

    if timelines:
        for tl in timelines:
            if not shouldDelete:
                break
            with open(os.path.join(_timelines, tl)) as f:
                checkpoints_data = json.load(f)
                for obj in checkpoints_data:
                    if obj["id"] == checkpoint_id:
                        shouldDelete = False
                        break

    if shouldDelete:
        os.remove(os.path.join(_checkpoints, checkpoint_id))
        config.set_state(
            filepath,
            "disk_usage",
            utils.get_disk_usage(
                os.path.join(filepath, config.PATHS_KEYS.ROOT_FOLDER)
            ),
        )
