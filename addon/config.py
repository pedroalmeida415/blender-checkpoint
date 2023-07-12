import os
import json
import textwrap


class PATHS_KEYS:
    ROOT_FOLDER = ".checkpoints"
    TIMELINES_FOLDER = "timelines"
    CHECKPOINTS_FOLDER = "saves"
    OBJECTS_FOLDER = "objects"

    ORIGINAL_TL_FILE = "Original.json"
    PERSISTED_STATE_FILE = "_persisted_state.json"


# Singleton for storing global state
class _CheckpointState:
    # __slots__ = (
    #     "placeholder",
    # )

    # def __init__(self):
    #     self.placeholder = placeholder_value
    pass


# One state to rule them all (otherwise known as a singleton)
cp_state = _CheckpointState()
del _CheckpointState


def multiline_label(context, text, parent, icon="NONE"):
    chars = int(context.region.width / 8)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for i, text_line in enumerate(text_lines):
        if i == 0:
            parent.label(text=text_line, icon=icon)
            continue
        parent.label(text=text_line)


def get_paths(filepath):
    _root_folder_path = os.path.join(
        filepath, PATHS_KEYS.ROOT_FOLDER)

    _timelines_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.TIMELINES_FOLDER)

    _saves_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.CHECKPOINTS_FOLDER)

    _objects_folder_path = os.path.join(
        _root_folder_path, PATHS_KEYS.OBJECTS_FOLDER)

    _persisted_state_path = os.path.join(
        _root_folder_path, PATHS_KEYS.PERSISTED_STATE_FILE)

    return {
        PATHS_KEYS.ROOT_FOLDER: _root_folder_path,
        PATHS_KEYS.TIMELINES_FOLDER: _timelines_folder_path,
        PATHS_KEYS.CHECKPOINTS_FOLDER: _saves_folder_path,
        PATHS_KEYS.OBJECTS_FOLDER: _objects_folder_path,
        PATHS_KEYS.PERSISTED_STATE_FILE: _persisted_state_path
    }


def get_state(filepath):
    _paths = get_paths(
        filepath)

    with open(_paths[PATHS_KEYS.PERSISTED_STATE_FILE]) as f:
        state = json.load(f)
        return state


def set_state(filepath, prop, value):
    _paths = get_paths(filepath)
    with open(_paths[PATHS_KEYS.PERSISTED_STATE_FILE], 'r+') as f:
        state = json.load(f)

        if prop in state:
            state[prop] = value
        else:
            raise ValueError(f"Property '{prop}' not found in state")

        f.seek(0)
        json.dump(state, f, indent=4)
        f.truncate()


def has_root_folder(filepath):
    _paths = get_paths(
        filepath)
    _root = _paths[PATHS_KEYS.ROOT_FOLDER]

    return os.path.exists(_root)
