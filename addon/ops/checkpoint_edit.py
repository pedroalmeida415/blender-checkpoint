import json
import os
import bpy

from .. import config


class EditCheckpoint(bpy.types.Operator):
    """Edit checkpoint description"""

    bl_label = __doc__
    bl_idname = "cps.edit_checkpoint"

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        cps_context = context.window_manager.cps

        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="New description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(cps_context, "checkpointDescription")

    def execute(self, context):
        cps_context = context.window_manager.cps

        if not cps_context.checkpointDescription:
            return {"CANCELLED"}

        filepath = bpy.path.abspath("//")

        edit_checkpoint(
            filepath, cps_context.selectedListIndex, cps_context.checkpointDescription
        )

        # Clean up
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        self.report({"INFO"}, "Description edited successfully!")
        return {"FINISHED"}


def edit_checkpoint(filepath, checkpoint_index, description):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    current_timeline = os.path.join(
        _paths[config.PATHS_KEYS.TIMELINES_FOLDER], state["current_timeline"]
    )
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        timeline_history[checkpoint_index]["description"] = description

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()
