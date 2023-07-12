import os
import bpy
import json
import shutil

import re
from unicodedata import normalize

from datetime import datetime, timezone

from . import config


# Format: Fri Sep  2 19:36:07 2022 +0530
CP_TIME_FORMAT = "%c %z"

TIMELINE_ICON = "WINDOW"
DELETE_ICON = "TRASH"
PROTECTED_ICON = "FAKE_USER_ON"


TIMELINE_ACTION_OPTIONS_2_83_POLYFILL = (
    "DEFAULT_CLOSED" if (2, 84, 0) > bpy.app.version else "INSTANCED"
)
TIMELINES_DEFAULT_POLYFILL_2_83 = None if (2, 84, 0) > bpy.app.version else -1


class CheckpointsPanelMixin:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"


addon_name = __name__.partition(".")[0]


def prefs(context=None):
    return bpy.context.preferences.addons.get(addon_name, None).preferences


def slugify(text):
    """
    Simplifies a string, converts it to lowercase, removes non-word characters
    and spaces, converts spaces and apostrophes to hyphens.
    """
    text = normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    text = re.sub(r"[^\w\s\'-]", "", text).strip().lower()
    text = re.sub(r'[-\s\'"]+', "-", text)
    return text


def get_disk_usage(filepath):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(filepath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    # Convert to MB
    return total_size / (1024 * 1024)


def getLastModifiedStr(date):
    """
    Returns last modified string
    date: offset-aware datetime.datetime object
    """

    # Get time difference
    now = datetime.now(timezone.utc)
    delta = now - date

    output = ""

    days = delta.days
    if days <= 0:
        hours = delta.seconds // 3600
        if hours <= 0:
            mins = (delta.seconds // 60) % 60
            if mins <= 0:
                secs = delta.seconds - hours * 3600 - mins * 60
                if secs <= 0:
                    output = "now"

                # Secs
                elif secs == 1:
                    output = f"{secs} sec"
                else:
                    output = f"{secs} sec"

            # Mins
            elif mins == 1:
                output = f"{mins} min"
            else:
                output = f"{mins} mins"

        # Hours
        elif hours == 1:
            output = f"{hours} hr"
        else:
            output = f"{hours} hrs"

    # Days
    elif days == 1:
        output = f"{days} day"
    else:
        output = f"{days} days"

    return output


def get_checkpoints(filepath, timeline=config.PATHS_KEYS.ORIGINAL_TL_FILE):
    _paths = config.get_paths(filepath)

    timeline_path = os.path.join(_paths[config.PATHS_KEYS.TIMELINES_FOLDER], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)

        return timeline_history


def listall_timelines(filepath):
    _paths = config.get_paths(filepath)
    return os.listdir(_paths[config.PATHS_KEYS.TIMELINES_FOLDER])


def switch_timeline(filepath, timeline=config.PATHS_KEYS.ORIGINAL_TL_FILE):
    _paths = config.get_paths(filepath)
    state = config.get_state(filepath)

    config.set_state(filepath, "current_timeline", timeline)

    timeline_path = os.path.join(_paths[config.PATHS_KEYS.TIMELINES_FOLDER], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)
        first_checkpoint = timeline_history[0]
        checkpoint = os.path.join(
            _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER], first_checkpoint["id"]
        )

        config.set_state(filepath, "active_checkpoint", first_checkpoint["id"])

        filename = state["filename"]
        destination_file = os.path.join(filepath, filename)
        shutil.copy(checkpoint, destination_file)


def check_is_modified(filepath):
    state = config.get_state(filepath)
    _paths = config.get_paths(filepath)
    _saves = _paths[config.PATHS_KEYS.CHECKPOINTS_FOLDER]

    filename = state["filename"]
    active_checkpoint = state["active_checkpoint"]

    source_file = os.path.join(filepath, filename)
    active_checkpoint_file = os.path.join(_saves, active_checkpoint)

    stat1 = os.stat(source_file)
    stat2 = os.stat(active_checkpoint_file)
    return stat1.st_size != stat2.st_size
