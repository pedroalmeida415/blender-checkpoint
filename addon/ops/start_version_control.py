from datetime import datetime, timezone
import json
import os
import shutil
import uuid
import bpy

from .. import config
from .. import utils


class StartVersionControl(bpy.types.Operator):
    """Initialize addon on the current project"""

    bl_idname = "checkpoint.start_version_control"
    bl_label = "Start Version Control"

    def execute(self, context):
        filepath = bpy.path.abspath("//")
        filename = bpy.path.basename(bpy.data.filepath)

        checkpoint_context = context.window_manager.checkpoint

        if checkpoint_context.isInitialized:
            return {"CANCELLED"}

        bpy.ops.wm.save_mainfile()
        initialize_version_control(filepath, filename)

        checkpoint_context.isInitialized = True
        checkpoint_context.selectedListIndex = 0

        self.report({"INFO"}, "Version control started!")

        return {"FINISHED"}


def initialize_version_control(filepath, filename):
    _paths = config.get_paths(filepath)

    _root = _paths[config.PATHS_KEYS.ROOT_FOLDER]
    _timelines = _paths[config.PATHS_KEYS.TIMELINES_FOLDER]
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]
    _objects = _paths[config.PATHS_KEYS.OBJECTS_FOLDER]
    _persisted_state = _paths[config.PATHS_KEYS.PERSISTED_STATE_FILE]

    # generate folder structure
    if not os.path.exists(_root):
        os.mkdir(_root)

    if not os.path.exists(_timelines):
        os.mkdir(_timelines)

    if not os.path.exists(_saves):
        os.mkdir(_saves)

    if not os.path.exists(_objects):
        os.mkdir(_objects)

    _original_tl_path = os.path.join(_timelines, config.PATHS_KEYS.ORIGINAL_TL_FILE)
    if not os.path.exists(_original_tl_path):
        # generate first checkpoint
        _initial_checkpoint_id = f"{uuid.uuid4().hex}.blend"

        source_file = os.path.join(filepath, filename)
        destination_file = os.path.join(_saves, _initial_checkpoint_id)
        shutil.copy(source_file, destination_file)

        datetimeString = datetime.now(timezone.utc).strftime(utils.CP_TIME_FORMAT)

        with open(_original_tl_path, "w") as file:
            first_checkpoint = [
                {
                    "id": _initial_checkpoint_id,
                    "description": "Initial checkpoint",
                    "date": datetimeString,
                }
            ]
            json.dump(first_checkpoint, file)

    if not os.path.exists(_persisted_state):
        # generate initial state
        with open(_persisted_state, "w") as file:
            initial_state = {
                "current_timeline": config.PATHS_KEYS.ORIGINAL_TL_FILE,
                "active_checkpoint": _initial_checkpoint_id,
                "disk_usage": 0,
                "filename": filename,
            }
            json.dump(initial_state, file)
