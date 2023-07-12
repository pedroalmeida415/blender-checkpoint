import os
import bpy

from .. import config, utils


class RenameTimeline(bpy.types.Operator):
    """Edit current timeline name"""

    bl_label = __doc__
    bl_idname = "cps.edit_timeline"

    name: bpy.props.StringProperty(
        name="",
        options={"TEXTEDIT_UPDATE"},
        description="New timeline name. (will be slugified)",
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        cps_context = context.window_manager.cps

        slugified_name = utils.slugify(self.name)

        try:
            rename_timeline(filepath, slugified_name)
        except FileExistsError:
            self.report({"ERROR"}, f"A timeline with name {self.name} already exists")
            return {"CANCELLED"}

        self.name = ""
        if cps_context.newTimelineName:
            cps_context.newTimelineName = ""

        self.report({"INFO"}, "Renamed timeline")

        return {"FINISHED"}


def rename_timeline(filepath, name):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)
    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    previous_tl_name = state["current_timeline"]
    previous_tl_path = os.path.join(_timelines, previous_tl_name)

    os.rename(previous_tl_path, new_tl_path)
    config.set_state(filepath, "current_timeline", new_name)
