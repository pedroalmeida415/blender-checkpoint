from datetime import datetime, timezone
import json
import os
import shutil
import uuid
import bpy

from .. import config, utils


class AddCheckpoint(bpy.types.Operator):
    """Add checkpoint"""

    bl_label = __doc__
    bl_idname = "cps.add_checkpoint"

    description: bpy.props.StringProperty(
        name="",
        options={"TEXTEDIT_UPDATE"},
        description="A short description of the changes made",
    )

    def execute(self, context):
        filepath = bpy.path.abspath("//")

        cps_context = context.window_manager.cps

        cps_context.should_display_dialog__ = False

        bpy.ops.wm.save_mainfile()

        add_checkpoint(filepath, self.description)

        self.description = ""
        cps_context.selectedListIndex = 0
        cps_context.should_display_dialog__ = True
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        return {"FINISHED"}


class PostSaveDialog(bpy.types.Operator):
    """Dialog to quickly add checkpoints"""

    bl_label = "Add checkpoint"
    bl_idname = "cps.post_save_dialog"

    @classmethod
    def poll(cls, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        cps_context = context.window_manager.cps

        try:
            state = config.get_state(filepath)
        except FileNotFoundError:
            return False

        return (
            cps_context.isInitialized
            and cps_context.should_display_dialog__
            and state["filename"] == filename
        )

    def invoke(self, context, event):
        wm = context.window_manager
        filepath = bpy.path.abspath("//")

        try:
            config.get_state(filepath)
            return wm.invoke_props_dialog(self, width=400)
        except FileNotFoundError:
            return {"CANCELLED"}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        col1 = row.column()
        col1.alignment = "LEFT"
        col1.label(text="Description: ")

        col2 = row.column()
        col2.alignment = "EXPAND"
        col2.prop(context.window_manager.cps, "checkpointDescription")

    def execute(self, context):
        cps_context = context.window_manager.cps
        description = cps_context.checkpointDescription

        if not description:
            self.report({"ERROR_INVALID_INPUT"}, "Description cannot be empty.")
            return {"CANCELLED"}

        filepath = bpy.path.abspath("//")

        add_checkpoint(filepath, description)

        cps_context.selectedListIndex = 0
        if cps_context.checkpointDescription:
            cps_context.checkpointDescription = ""

        self.report({"INFO"}, "Successfully saved!")

        return {"FINISHED"}


def add_checkpoint(filepath, description):
    _paths = config.get_paths(filepath)
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    state = config.get_state(filepath)
    filename = state["filename"]
    current_timeline = state["current_timeline"]

    # new checkpoint ID
    checkpoint_id = f"{uuid.uuid4().hex}.blend"

    # Copy current file and pastes into saves
    source_file = os.path.join(filepath, filename)
    destination_file = os.path.join(_saves, checkpoint_id)
    shutil.copy(source_file, destination_file)

    # updates timeline info
    timeline_path = os.path.join(_timelines, current_timeline)
    with open(timeline_path, "r+") as f:
        timeline_history = json.load(f)

        datetimeString = datetime.now(timezone.utc).strftime(utils.CP_TIME_FORMAT)

        checkpoint = {
            "id": checkpoint_id,
            "description": description.strip(" \t\n\r"),
            "date": datetimeString,
        }

        timeline_history.insert(0, checkpoint)

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()

    config.set_state(filepath, "active_checkpoint", checkpoint_id)
    config.set_state(
        filepath,
        "disk_usage",
        utils.get_disk_usage(os.path.join(filepath, config.PATHS_KEYS.ROOT_FOLDER)),
    )
