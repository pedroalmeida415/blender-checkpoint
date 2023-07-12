import json
import os
import bpy

from .. import config
from .. import utils


class NewTimeline(bpy.types.Operator):
    """Creates a new timeline from the selected checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.new_timeline"

    name: bpy.props.StringProperty(
        name="",
        options={"TEXTEDIT_UPDATE"},
        description="Name of new timeline. (will be slugified)",
    )

    new_tl_keep_history: bpy.props.BoolProperty(
        name="", description="Keep previous checkpoints"
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        slugfied_name = utils.slugify(self.name)
        try:
            new_name = create_new_timeline(
                filepath,
                slugfied_name,
                cps_context.selectedListIndex,
                self.new_tl_keep_history,
            )
        except FileExistsError:
            self.report({"ERROR"}, f"A timeline with name {self.name} already exists")
            return {"CANCELLED"}

        # Clean up
        cps_context.selectedListIndex = 0

        utils.switch_timeline(filepath, new_name)

        self.name = ""
        self.new_tl_keep_history = False
        if cps_context.newTimelineName:
            cps_context.newTimelineName = ""

        bpy.ops.wm.revert_mainfile()

        return {"FINISHED"}


def create_new_timeline(filepath, name, start_checkpoint_index, keep_history):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)

    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    # Get current timeline history
    # TODO test if "get_checkpoints" can be switched with cps_context.checkpoints
    current_timeline = state["current_timeline"]
    timeline_history = utils.get_checkpoints(filepath, current_timeline)

    if keep_history:
        new_tl_history = timeline_history[start_checkpoint_index:]
    else:
        new_tl_history = [timeline_history[start_checkpoint_index]]

    # create new timeline file
    with open(new_tl_path, "w") as file:
        json.dump(new_tl_history, file)

    return new_name
