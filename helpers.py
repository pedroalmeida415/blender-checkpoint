import os
import json
import uuid
import shutil

from datetime import datetime, timezone, timedelta

# Format: Fri Sep  2 19:36:07 2022 +0530
CP_TIME_FORMAT = "%c %z"

ROOT = ".checkpoints"
TIMELINES = "timelines"
CHECKPOINTS = "saves"
PERSISTED_STATE = "_persisted_state.json"
ORIGINAL_TL = "Original.json"


def _get_disk_usage(filepath):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(filepath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def _get_paths(filepath):
    _root_folder_path = os.path.join(
        filepath, ROOT)

    _timelines_folder_path = os.path.join(
        _root_folder_path, TIMELINES)

    _saves_folder_path = os.path.join(
        _root_folder_path, CHECKPOINTS)

    _persisted_state_path = os.path.join(
        _root_folder_path, PERSISTED_STATE)

    return {ROOT: _root_folder_path,
            TIMELINES: _timelines_folder_path,
            CHECKPOINTS: _saves_folder_path,
            PERSISTED_STATE: _persisted_state_path}


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


def initialize_version_control(filepath, filename):
    _paths = _get_paths(filepath)

    _root = _paths[ROOT]
    _timelines = _paths[TIMELINES]
    _saves = _paths[CHECKPOINTS]
    _persisted_state = _paths[PERSISTED_STATE]

    # generate folder structure
    if not os.path.exists(_root):
        os.mkdir(_root)

    if not os.path.exists(_timelines):
        os.mkdir(_timelines)

    if not os.path.exists(_saves):
        os.mkdir(_saves)

    _original_tl_path = os.path.join(_timelines, ORIGINAL_TL)
    if not os.path.exists(_original_tl_path):
        # generate first checkpoint
        _initial_checkpoint_id = f"{uuid.uuid4().hex}.blend"

        source_file = os.path.join(filepath, filename)
        destination_file = os.path.join(_saves, _initial_checkpoint_id)
        shutil.copy(source_file, destination_file)

        datetimeString = datetime.now(timezone.utc).strftime(CP_TIME_FORMAT)

        with open(_original_tl_path, "w") as file:
            first_checkpoint = [{
                "id": _initial_checkpoint_id,
                "description": f"{filename} - Initial checkpoint",
                "date": datetimeString
            }]
            json.dump(first_checkpoint, file)

    if not os.path.exists(_persisted_state):
        # generate initial state
        with open(_persisted_state, "w") as file:
            initial_state = {
                "current_timeline": ORIGINAL_TL,
                "active_checkpoint": _initial_checkpoint_id,
                "disk_usage": 0,
                "filename": filename
            }
            json.dump(initial_state, file)


def listall_timelines(filepath):
    _paths = _get_paths(
        filepath)
    return os.listdir(_paths[TIMELINES])


def get_checkpoints(filepath, timeline=ORIGINAL_TL):
    _paths = _get_paths(filepath)

    timeline_path = os.path.join(_paths[TIMELINES], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)

        return timeline_history


def get_state(filepath):
    _paths = _get_paths(
        filepath)

    with open(_paths[PERSISTED_STATE]) as f:
        state = json.load(f)
        return state


def set_state(filepath, prop, value):
    _paths = _get_paths(filepath)
    with open(_paths[PERSISTED_STATE], 'r+') as f:
        state = json.load(f)

        if prop in state:
            state[prop] = value
        else:
            raise ValueError(f"Property '{prop}' not found in state")

        f.seek(0)
        json.dump(state, f, indent=4)
        f.truncate()


def add_checkpoint(filepath, description):
    _paths = _get_paths(filepath)
    _saves = _paths[CHECKPOINTS]
    _timelines = _paths[TIMELINES]
    state = get_state(filepath)
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
    with open(timeline_path, 'r+') as f:
        timeline_history = json.load(f)

        datetimeString = datetime.now(timezone.utc).strftime(CP_TIME_FORMAT)

        checkpoint = {
            "id": checkpoint_id,
            "description": description.strip(" \t\n\r"),
            "date": datetimeString
        }

        timeline_history.insert(0, checkpoint)

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()

    set_state(filepath, "active_checkpoint", checkpoint_id)
    set_state(filepath, "disk_usage", _get_disk_usage(
        os.path.join(filepath, ROOT)))


def load_checkpoint(filepath, checkpoint_id):
    _paths = _get_paths(filepath)
    state = get_state(filepath)

    set_state(filepath, "active_checkpoint", checkpoint_id)

    checkpoint_path = os.path.join(_paths[CHECKPOINTS], checkpoint_id)
    filename = state["filename"]
    destination_file = os.path.join(filepath, filename)

    shutil.copy(checkpoint_path, destination_file)


def remove_checkpoint(filepath, checkpoint_index):
    _paths = _get_paths(filepath)
    state = get_state(filepath)

    current_timeline = os.path.join(
        _paths[TIMELINES], state["current_timeline"])
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        del timeline_history[checkpoint_index]

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()


def edit_checkpoint(filepath, checkpoint_index, description):
    _paths = _get_paths(filepath)
    state = get_state(filepath)

    current_timeline = os.path.join(
        _paths[TIMELINES], state["current_timeline"])
    with open(current_timeline, "r+") as f:
        timeline_history = json.load(f)

        timeline_history[checkpoint_index]["description"] = description

        f.seek(0)
        json.dump(timeline_history, f, indent=4)
        f.truncate()


def switch_timeline(filepath, timeline=ORIGINAL_TL):
    _paths = _get_paths(filepath)
    state = get_state(filepath)

    set_state(filepath, "current_timeline", timeline)

    timeline_path = os.path.join(_paths[TIMELINES], timeline)
    with open(timeline_path) as f:
        timeline_history = json.load(f)
        first_checkpoint = timeline_history[0]
        checkpoint = os.path.join(_paths[CHECKPOINTS], first_checkpoint["id"])

        set_state(filepath, "active_checkpoint", first_checkpoint["id"])

        filename = state["filename"]
        destination_file = os.path.join(filepath, filename)
        shutil.copy(checkpoint, destination_file)


def check_is_modified(filepath):
    state = get_state(filepath)
    _paths = _get_paths(filepath)
    _saves = _paths[CHECKPOINTS]

    filename = state["filename"]
    active_checkpoint = state["active_checkpoint"]

    source_file = os.path.join(filepath, filename)
    active_checkpoint_file = os.path.join(_saves, active_checkpoint)

    stat1 = os.stat(source_file)
    stat2 = os.stat(active_checkpoint_file)
    return stat1.st_size != stat2.st_size


def create_new_timeline(filepath, name, start_checkpoint_index, keep_history):
    state = get_state(filepath)
    _paths = _get_paths(filepath)
    _timelines = _paths[TIMELINES]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)

    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    # Get current timeline history
    # TODO test if "get_checkpoints" can be switched with cps_context.checkpoints
    current_timeline = state["current_timeline"]
    timeline_history = get_checkpoints(filepath, current_timeline)

    if keep_history:
        new_tl_history = timeline_history[start_checkpoint_index:]
    else:
        new_tl_history = [timeline_history[start_checkpoint_index]]

    # create new timeline file
    with open(new_tl_path, "w") as file:
        json.dump(new_tl_history, file)

    return new_name


def delete_timeline(filepath, name):
    _paths = _get_paths(filepath)
    _timelines = _paths[TIMELINES]

    delete_tl_path = os.path.join(_timelines, name)

    os.remove(delete_tl_path)


def rename_timeline(filepath, name):
    state = get_state(filepath)
    _paths = _get_paths(filepath)
    _timelines = _paths[TIMELINES]

    new_name = f"{name}.json"
    new_tl_path = os.path.join(_timelines, new_name)
    if os.path.exists(new_tl_path):
        raise FileExistsError(f"File '{name}' already exists")

    previous_tl_name = state["current_timeline"]
    previous_tl_path = os.path.join(_timelines, previous_tl_name)

    os.rename(previous_tl_path, new_tl_path)
    set_state(filepath, "current_timeline", new_name)


def export_checkpoint(filepath, checkpoint_id, description):
    _paths = _get_paths(filepath)

    # get checkpoint wth the provided id
    checkpoint = os.path.join(_paths[CHECKPOINTS], checkpoint_id)

    # create folder "exported"
    export_path = os.path.join(filepath, "exported")
    if not os.path.exists(export_path):
        os.mkdir(export_path)

    export_name = os.path.join(export_path, f"{description}.blend")
    shutil.copy(checkpoint, export_name)
